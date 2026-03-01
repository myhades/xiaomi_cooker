"""Binary sensor platform for Xiaomi Electric Rice Cooker."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.binary_sensor import (
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DOMAIN
from .entity import XiaomiMiioCookerEntity


@dataclass(frozen=True, kw_only=True)
class XiaomiCookerBinarySensorDescription(BinarySensorEntityDescription):
    """Describes a Xiaomi cooker binary sensor."""


BINARY_SENSOR_DESCRIPTIONS: tuple[XiaomiCookerBinarySensorDescription, ...] = (
    XiaomiCookerBinarySensorDescription(
        key="panel_display_auto_off",
        name="Panel display auto off",
        translation_key="panel_display_auto_off",
        icon="mdi:led-outline",
        entity_category=EntityCategory.CONFIG,
    ),
    XiaomiCookerBinarySensorDescription(
        key="lid_open_warning",
        name="Lid open alarm",
        translation_key="lid_open_warning",
        icon="mdi:bell-ring-outline",
        entity_category=EntityCategory.CONFIG,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Xiaomi cooker binary sensors from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(
        XiaomiCookerBinarySensor(coordinator, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class XiaomiCookerBinarySensor(XiaomiMiioCookerEntity, BinarySensorEntity):
    """Representation of a Xiaomi cooker binary sensor."""

    entity_description: XiaomiCookerBinarySensorDescription

    def __init__(
        self,
        coordinator,
        description: XiaomiCookerBinarySensorDescription,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(
            coordinator,
            unique_key=description.key,
            name=description.name or description.key,
            translation_key=description.translation_key,
        )
        self.entity_description = description
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category

    @property
    def available(self) -> bool:
        """Return entity availability."""
        return super().available

    @property
    def is_on(self) -> bool | None:
        """Return the binary sensor state."""
        if self.entity_description.key == "panel_display_auto_off":
            return self.coordinator.panel_display_auto_off_enabled

        return self.coordinator.lid_open_warning_enabled
