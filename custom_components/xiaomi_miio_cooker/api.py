"""Blocking Xiaomi Electric Rice Cooker client helpers."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from miio import Cooker, Device

from .const import DEFAULT_NAME, DOMAIN, SUPPORTED_MODELS


class UnsupportedModelError(Exception):
    """Raised when the cooker model is unsupported."""


@dataclass(slots=True, frozen=True)
class CookerDeviceMetadata:
    """Static metadata about a Xiaomi cooker."""

    model: str | None
    firmware_version: str | None
    hardware_version: str | None
    mac_address: str | None


@dataclass(slots=True, frozen=True)
class CookerData:
    """Combined runtime data for the coordinator."""

    device_info: CookerDeviceMetadata
    status: "CookerStatusData"
    settings: "CookerSettingsData | None"
    interaction_timeouts: "CookerInteractionTimeoutsData | None"
    temperature: Any | None


@dataclass(slots=True, frozen=True)
class CookerStageData:
    """Runtime stage data used by the exposed sensors."""

    state: Any
    rice_id: Any
    taste: Any
    taste_phase: Any
    name: Any
    description: Any


@dataclass(slots=True, frozen=True)
class CookerStatusData:
    """Runtime cooker data used by the exposed sensors."""

    mode: Any
    status: Any
    menu: Any
    remaining: Any
    duration: Any
    favorite: Any
    stage: CookerStageData | None


@dataclass(slots=True, frozen=True)
class CookerSettingsData:
    """Cooker settings exposed by python-miio."""

    led_on: bool | None
    lid_open_warning: bool | None
    lid_open_warning_delayed: bool | None


@dataclass(slots=True, frozen=True)
class CookerInteractionTimeoutsData:
    """Cooker interaction timeout settings exposed by python-miio."""

    led_off: int | None
    lid_open: int | None
    lid_open_warning: int | None


def normalize_mac(mac_address: str | None) -> str | None:
    """Normalize a MAC address into aa:bb:cc:dd:ee:ff form."""
    if not mac_address:
        return None

    raw_mac = mac_address.lower().replace("-", "").replace(":", "")
    if len(raw_mac) != 12:
        return None

    return ":".join(raw_mac[index : index + 2] for index in range(0, 12, 2))


def build_unique_id(
    mac_address: str | None,
    model: str | None,
) -> str:
    """Build a stable unique ID for a cooker."""
    normalized_mac = normalize_mac(mac_address)
    normalized_model = (model or DOMAIN).replace(".", "_")
    if not normalized_mac:
        return normalized_model

    return f"{normalized_model}_{normalized_mac.replace(':', '')}"


def build_entry_title() -> str:
    """Build a config entry title."""
    return DEFAULT_NAME


def _build_stage_data(stage: Any) -> CookerStageData | None:
    """Convert a python-miio stage object into an immutable snapshot."""
    if stage is None:
        return None

    return CookerStageData(
        state=getattr(stage, "state", None),
        rice_id=getattr(stage, "rice_id", None),
        taste=getattr(stage, "taste", None),
        taste_phase=getattr(stage, "taste_phase", None),
        name=getattr(stage, "name", None),
        description=getattr(stage, "description", None),
    )


def _build_status_data(status: Any) -> CookerStatusData:
    """Convert a python-miio status object into an immutable snapshot."""
    raw_data = getattr(status, "data", {}) or {}
    raw_func = str(raw_data.get("func", "")).lower()
    raw_menu = str(raw_data.get("menu", "")).lower()

    return CookerStatusData(
        mode=_map_cook_mode(raw_menu),
        status=_map_work_status(raw_func),
        menu=_parse_menu(raw_menu),
        remaining=getattr(status, "remaining", None),
        duration=getattr(status, "duration", None),
        favorite=getattr(status, "favorite", None),
        stage=_build_stage_data(getattr(status, "stage", None)),
    )


def _parse_menu(raw_menu: str) -> int | None:
    """Parse the raw menu value into an integer."""
    if not raw_menu:
        return None

    try:
        return int(raw_menu, 16)
    except ValueError:
        return None


def _map_cook_mode(raw_menu: str) -> str:
    """Map the raw cooker menu value to a stable cook mode enum."""
    return {
        "0001": "fine_cook",
        "0002": "quick_cook",
        "0003": "cook_congee",
        "0004": "keep_warm",
    }.get(raw_menu, "unknown")


def _map_work_status(raw_func: str) -> str:
    """Map the raw func value to a stable work status enum."""
    return {
        "waiting": "idle",
        "running": "running",
        "cooking": "running",
        "autokeepwarm": "keep_warm",
        "keepwarm": "keep_warm",
        "keep_temp": "keep_warm",
        "finish": "keep_warm",
        "finisha": "keep_warm",
        "precook": "busy",
        "set02": "busy",
        "start": "busy",
        "startp": "busy",
        "resume": "busy",
        "resumep": "busy",
    }.get(raw_func, "unknown")


def _build_settings_data(settings: Any) -> CookerSettingsData | None:
    """Convert python-miio settings into an immutable snapshot."""
    if settings is None:
        return None

    return CookerSettingsData(
        led_on=getattr(settings, "led_on", None),
        lid_open_warning=getattr(settings, "lid_open_warning", None),
        lid_open_warning_delayed=getattr(settings, "lid_open_warning_delayed", None),
    )


def _build_interaction_timeouts_data(
    interaction_timeouts: Any,
) -> CookerInteractionTimeoutsData | None:
    """Convert python-miio interaction timeouts into an immutable snapshot."""
    if interaction_timeouts is None:
        return None

    return CookerInteractionTimeoutsData(
        led_off=getattr(interaction_timeouts, "led_off", None),
        lid_open=getattr(interaction_timeouts, "lid_open", None),
        lid_open_warning=getattr(interaction_timeouts, "lid_open_warning", None),
    )


class XiaomiMiioCookerApi:
    """Blocking API wrapper around python-miio."""

    def __init__(self, host: str, token: str, model: str | None) -> None:
        """Initialize the cooker client."""
        self.host = host
        self.token = token
        self.configured_model = model
        self._device = Device(host, token)
        self._cooker = Cooker(host, token)
        self._device_info: CookerDeviceMetadata | None = None

    def validate(self) -> CookerData:
        """Validate connectivity and return the initial data snapshot."""
        return self.fetch_data(force_device_info=True)

    def fetch_device_info(self) -> CookerDeviceMetadata:
        """Fetch static device metadata for model detection."""
        return self._get_device_info(force_refresh=True)

    def fetch_data(self, force_device_info: bool = False) -> CookerData:
        """Fetch state and optional temperature history."""
        device_info = self._get_device_info(force_refresh=force_device_info)
        resolved_model = self.configured_model or device_info.model
        if resolved_model not in SUPPORTED_MODELS:
            raise UnsupportedModelError(
                f"Unsupported device found: {resolved_model or device_info.model}"
            )

        raw_status = self._cooker.status()
        raw_status_data = getattr(raw_status, "data", {}) or {}
        raw_func = str(raw_status_data.get("func", "")).lower()
        temperature = getattr(raw_status, "temperature", None)
        if temperature is None and raw_func in {"running", "autokeepwarm", "keepwarm"}:
            temperature_history = self._cooker.get_temperature_history()
            temperatures = getattr(temperature_history, "temperatures", None)
            if temperatures:
                temperature = temperatures[-1]

        return CookerData(
            device_info=device_info,
            status=_build_status_data(raw_status),
            settings=_build_settings_data(getattr(raw_status, "settings", None)),
            interaction_timeouts=_build_interaction_timeouts_data(
                getattr(raw_status, "interaction_timeouts", None)
            ),
            temperature=temperature,
        )

    def start(self, profile: str) -> Any:
        """Start a cooking profile."""
        return self._cooker.start(profile)

    def stop(self) -> Any:
        """Stop the current cooking process."""
        return self._cooker.stop()

    def _get_device_info(self, force_refresh: bool = False) -> CookerDeviceMetadata:
        """Fetch and cache static device metadata."""
        if self._device_info is not None and not force_refresh:
            return self._device_info

        info = self._device.info()
        self._device_info = CookerDeviceMetadata(
            model=getattr(info, "model", self.configured_model),
            firmware_version=getattr(info, "firmware_version", None),
            hardware_version=getattr(info, "hardware_version", None),
            mac_address=normalize_mac(
                getattr(info, "mac_address", None) or getattr(info, "mac", None)
            ),
        )
        return self._device_info
