"""Sensor platform for Xiaomi Electric Rice Cooker."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import STATE_UNKNOWN, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DOMAIN
from .entity import XiaomiMiioCookerEntity

CAMEL_CASE_PATTERN = re.compile(r"(?<!^)(?=[A-Z])")
MODE_OPTIONS = ("off", "waiting", "running", "auto_keep_warm")
BOOLEAN_OPTIONS = ("off", "on")


@dataclass(frozen=True, kw_only=True)
class XiaomiCookerSensorDescription(SensorEntityDescription):
    """Describes a Xiaomi cooker sensor."""

    child: str | None = None
    attribute_name: str
    enum_options: tuple[str, ...] | None = None


SENSOR_DESCRIPTIONS: tuple[XiaomiCookerSensorDescription, ...] = (
    XiaomiCookerSensorDescription(
        key="mode",
        name="Mode",
        translation_key="mode",
        icon="mdi:bowl",
        device_class=SensorDeviceClass.ENUM,
        attribute_name="mode",
        enum_options=MODE_OPTIONS,
    ),
    XiaomiCookerSensorDescription(
        key="menu",
        name="Menu",
        translation_key="menu",
        icon="mdi:menu",
        attribute_name="menu",
    ),
    XiaomiCookerSensorDescription(
        key="temperature",
        name="Temperature",
        translation_key="temperature",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        attribute_name="temperature",
    ),
    XiaomiCookerSensorDescription(
        key="remaining",
        name="Remaining",
        translation_key="remaining",
        icon="mdi:timer",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        attribute_name="remaining",
    ),
    XiaomiCookerSensorDescription(
        key="duration",
        name="Duration",
        translation_key="duration",
        icon="mdi:timelapse",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        attribute_name="duration",
    ),
    XiaomiCookerSensorDescription(
        key="favorite",
        name="Favorite",
        translation_key="favorite",
        icon="mdi:information-outline",
        attribute_name="favorite",
    ),
    XiaomiCookerSensorDescription(
        key="panel_display_auto_off",
        name="Panel display auto off",
        translation_key="panel_display_auto_off",
        icon="mdi:lightbulb-outline",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute_name="panel_display_auto_off",
        enum_options=BOOLEAN_OPTIONS,
    ),
    XiaomiCookerSensorDescription(
        key="lid_open_warning",
        name="Lid open alarm",
        translation_key="lid_open_warning",
        icon="mdi:bell-ring-outline",
        device_class=SensorDeviceClass.ENUM,
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute_name="lid_open_warning",
        enum_options=BOOLEAN_OPTIONS,
    ),
    XiaomiCookerSensorDescription(
        key="lid_open_timeout",
        name="Auto keep-warm lid open timeout",
        translation_key="lid_open_timeout",
        icon="mdi:timer-cog-outline",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.MINUTES,
        entity_category=EntityCategory.DIAGNOSTIC,
        attribute_name="lid_open_timeout",
    ),
    XiaomiCookerSensorDescription(
        key="state",
        name="State",
        translation_key="state",
        icon="mdi:playlist-check",
        child="stage",
        attribute_name="state",
    ),
    XiaomiCookerSensorDescription(
        key="rice_id",
        name="Rice ID",
        translation_key="rice_id",
        icon="mdi:rice",
        child="stage",
        attribute_name="rice_id",
    ),
    XiaomiCookerSensorDescription(
        key="taste",
        name="Taste",
        translation_key="taste",
        icon="mdi:flash-outline",
        child="stage",
        attribute_name="taste",
    ),
    XiaomiCookerSensorDescription(
        key="taste_phase",
        name="Taste phase",
        translation_key="taste_phase",
        icon="mdi:flash-outline",
        child="stage",
        attribute_name="taste_phase",
    ),
    XiaomiCookerSensorDescription(
        key="stage_name",
        name="Stage name",
        translation_key="stage_name",
        icon="mdi:stairs",
        child="stage",
        attribute_name="name",
    ),
    XiaomiCookerSensorDescription(
        key="stage_description",
        name="Stage description",
        translation_key="stage_description",
        icon="mdi:stairs",
        child="stage",
        attribute_name="description",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Xiaomi cooker sensors from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(
        XiaomiCookerSensor(coordinator, description) for description in SENSOR_DESCRIPTIONS
    )


class XiaomiCookerSensor(XiaomiMiioCookerEntity, SensorEntity):
    """Representation of a Xiaomi cooker sensor."""

    entity_description: XiaomiCookerSensorDescription

    def __init__(
        self,
        coordinator,
        description: XiaomiCookerSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(
            coordinator,
            unique_key=description.key,
            name=description.name or description.key,
            translation_key=description.translation_key,
        )
        self.entity_description = description
        self._attr_device_class = description.device_class
        self._attr_icon = description.icon
        self._attr_native_unit_of_measurement = description.native_unit_of_measurement
        self._attr_state_class = description.state_class
        self._attr_entity_category = description.entity_category

    @property
    def options(self) -> list[str] | None:
        """Return enum options for sensors with a bounded state set."""
        if self.entity_description.enum_options is None:
            return None

        return list(self.entity_description.enum_options)

    @property
    def native_value(self):
        """Return the native value of the sensor."""
        raw_value = self._get_raw_value()
        if self.entity_description.enum_options is not None and raw_value is not None:
            normalized_value = self._normalize_enum_state(raw_value)
            if normalized_value in self.entity_description.enum_options:
                return normalized_value
            return STATE_UNKNOWN

        return raw_value

    def _get_raw_value(self):
        """Return the raw value provided by the coordinator snapshot."""
        data = self.coordinator.data
        if data is None:
            return None

        if self.entity_description.key == "temperature":
            return data.temperature

        if self.entity_description.key == "panel_display_auto_off":
            return self._normalize_bool_state(self.coordinator.panel_display_auto_off_enabled)

        if self.entity_description.key == "lid_open_warning":
            return self._normalize_bool_state(self.coordinator.lid_open_warning_enabled)

        if self.entity_description.key == "lid_open_timeout":
            return self.coordinator.lid_open_timeout_minutes

        if data.status is None:
            return None

        state = data.status
        if self.entity_description.child is not None:
            state = getattr(state, self.entity_description.child, None)
            if state is None:
                return None

        return getattr(state, self.entity_description.attribute_name, None)

    @staticmethod
    def _normalize_enum_state(value: Enum | str) -> str:
        """Normalize enum state values to the lowercase format HA expects."""
        if isinstance(value, Enum):
            if isinstance(value.value, str):
                raw_value = value.value
            else:
                raw_value = value.name
        else:
            raw_value = str(value)

        normalized = CAMEL_CASE_PATTERN.sub("_", raw_value)
        normalized = normalized.replace("-", "_").replace(" ", "_")
        return normalized.lower()

    @staticmethod
    def _normalize_bool_state(value: bool | None) -> str | None:
        """Normalize a boolean state into an enum string."""
        if value is None:
            return None

        return "on" if value else "off"
