"""Data update coordinator for Xiaomi Electric Rice Cooker."""

from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from miio import DeviceException

from .api import CookerData, UnsupportedModelError, XiaomiMiioCookerApi
from .const import (
    COMMAND_REFRESH_DELAY,
    CONF_MODEL,
    DEFAULT_NAME,
    DEFAULT_UPDATE_INTERVAL,
    DOMAIN,
)
from .profiles import get_profiles_for_model

_LOGGER = logging.getLogger(__name__)


class XiaomiMiioCookerCoordinator(DataUpdateCoordinator[CookerData]):
    """Coordinate Xiaomi cooker updates and commands."""

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        api: XiaomiMiioCookerApi,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id}",
            update_interval=DEFAULT_UPDATE_INTERVAL,
            always_update=False,
        )
        self.api = api
        self.config_entry = entry
        self.device_unique_id = entry.unique_id or entry.entry_id
        self._command_lock = asyncio.Lock()
        self._profiles = get_profiles_for_model(entry.data.get(CONF_MODEL))
        self._profiles_by_key = {profile.key: profile for profile in self._profiles}
        self._selected_profile = None

    @property
    def device_name(self) -> str:
        """Return the device display name."""
        return DEFAULT_NAME

    @property
    def cooking_menu_options(self) -> list[str]:
        """Return selectable cooking menu options."""
        if not self._profiles:
            return []

        return [profile.key for profile in self._profiles]

    @property
    def selected_cooking_menu(self) -> str | None:
        """Return the currently selected cooking menu."""
        return self._selected_profile

    @property
    def panel_display_auto_off_enabled(self) -> bool | None:
        """Return whether idle panel display auto-off is enabled."""
        if self.data is None or self.data.settings is None:
            return None

        led_on = self.data.settings.led_on
        if led_on is None:
            return None

        return not led_on

    @property
    def lid_open_timeout_minutes(self) -> float | None:
        """Return the lid-open timeout in minutes."""
        if self.data is None or self.data.interaction_timeouts is None:
            return None

        lid_open = self.data.interaction_timeouts.lid_open
        if lid_open is None:
            return None

        return lid_open

    @property
    def lid_open_warning_enabled(self) -> bool | None:
        """Return whether delayed lid-open warning is enabled."""
        if self.data is None or self.data.settings is None:
            return None

        return self.data.settings.lid_open_warning_delayed

    async def _async_update_data(self) -> CookerData:
        """Fetch the latest cooker state."""
        try:
            return await self.hass.async_add_executor_job(self.api.fetch_data)
        except UnsupportedModelError as err:
            raise UpdateFailed(f"Unsupported Xiaomi cooker model: {err}") from err
        except DeviceException as err:
            raise UpdateFailed(f"Unable to update Xiaomi cooker state: {err}") from err

    async def async_start(self, profile: str) -> None:
        """Start a cooking profile."""
        await self._async_execute_command(self.api.start, profile)

    async def async_stop(self) -> None:
        """Stop the cooking process."""
        await self._async_execute_command(self.api.stop)

    async def async_select_cooking_menu(self, option: str) -> None:
        """Select a cooking menu for the start button."""
        if option not in self.cooking_menu_options:
            raise HomeAssistantError(f"Unsupported cooking menu: {option}")

        self._selected_profile = option
        self.async_update_listeners()

    async def async_start_selected_profile(self) -> None:
        """Start the currently selected cooking profile."""
        if not self._profiles:
            raise HomeAssistantError(
                "No cooking profiles are available for this cooker model."
            )

        if self._selected_profile is None:
            raise HomeAssistantError("Select a cooking menu before starting.")

        selected_profile = self._profiles_by_key[self._selected_profile]
        await self.async_start(selected_profile.profile)
        self._selected_profile = None
        self.async_update_listeners()

    async def _async_execute_command(self, command, *args) -> None:
        """Run a blocking command and refresh quickly afterwards."""
        async with self._command_lock:
            await self.hass.async_add_executor_job(command, *args)
            await self.async_refresh()
            self.hass.async_create_task(self._async_delayed_refresh())

    async def _async_delayed_refresh(self) -> None:
        """Perform a follow-up refresh after the device has processed a command."""
        await asyncio.sleep(COMMAND_REFRESH_DELAY)
        await self.async_refresh()
