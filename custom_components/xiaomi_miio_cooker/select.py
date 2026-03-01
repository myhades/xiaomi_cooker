"""Select platform for Xiaomi Electric Rice Cooker."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.components.select import SelectEntity, SelectEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DATA_COORDINATORS, DOMAIN
from .entity import XiaomiMiioCookerEntity


@dataclass(frozen=True, kw_only=True)
class XiaomiCookerSelectDescription(SelectEntityDescription):
    """Describes a Xiaomi cooker select entity."""


SELECT_DESCRIPTIONS: tuple[XiaomiCookerSelectDescription, ...] = (
    XiaomiCookerSelectDescription(
        key="cooking_menu",
        name="Cooking menu",
        translation_key="cooking_menu",
        icon="mdi:format-list-bulleted-square",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Xiaomi cooker select entities from a config entry."""
    coordinator = hass.data[DOMAIN][DATA_COORDINATORS][entry.entry_id]
    async_add_entities(
        XiaomiCookerSelect(coordinator, description)
        for description in SELECT_DESCRIPTIONS
    )


class XiaomiCookerSelect(XiaomiMiioCookerEntity, SelectEntity):
    """Representation of a Xiaomi cooker select entity."""

    entity_description: XiaomiCookerSelectDescription

    def __init__(self, coordinator, description: XiaomiCookerSelectDescription) -> None:
        """Initialize the select entity."""
        super().__init__(
            coordinator,
            unique_key=description.key,
            name=description.name or description.key,
            translation_key=description.translation_key,
        )
        self.entity_description = description
        self._attr_icon = description.icon

    @property
    def current_option(self) -> str | None:
        """Return the currently selected option."""
        return self.coordinator.selected_cooking_menu

    @property
    def options(self) -> list[str]:
        """Return the available options."""
        return self.coordinator.cooking_menu_options

    async def async_select_option(self, option: str) -> None:
        """Change the selected option."""
        await self.coordinator.async_select_cooking_menu(option)
