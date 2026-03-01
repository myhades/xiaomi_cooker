"""Button platform for Xiaomi Electric Rice Cooker."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DOMAIN
from .entity import XiaomiMiioCookerEntity


@dataclass(frozen=True, kw_only=True)
class XiaomiCookerButtonDescription(ButtonEntityDescription):
    """Describes a Xiaomi cooker button entity."""


BUTTON_DESCRIPTIONS: tuple[XiaomiCookerButtonDescription, ...] = (
    XiaomiCookerButtonDescription(
        key="start_cooking",
        name="Start cooking",
        translation_key="start_cooking",
        icon="mdi:play",
    ),
    XiaomiCookerButtonDescription(
        key="stop_cooking",
        name="Stop cooking",
        translation_key="stop_cooking",
        icon="mdi:stop",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Xiaomi cooker buttons from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(
        XiaomiCookerButton(coordinator, description)
        for description in BUTTON_DESCRIPTIONS
    )


class XiaomiCookerButton(XiaomiMiioCookerEntity, ButtonEntity):
    """Representation of a Xiaomi cooker button."""

    entity_description: XiaomiCookerButtonDescription

    def __init__(self, coordinator, description: XiaomiCookerButtonDescription) -> None:
        """Initialize the button."""
        super().__init__(
            coordinator,
            unique_key=description.key,
            name=description.name or description.key,
            translation_key=description.translation_key,
        )
        self.entity_description = description
        self._attr_icon = description.icon

    async def async_press(self) -> None:
        """Handle button presses."""
        if self.entity_description.key == "start_cooking":
            await self.coordinator.async_start_selected_profile()
            return

        await self.coordinator.async_stop()
