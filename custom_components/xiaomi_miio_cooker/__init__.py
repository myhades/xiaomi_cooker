"""The Xiaomi Electric Rice Cooker integration."""

from __future__ import annotations

import asyncio
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import ATTR_DEVICE_ID, CONF_HOST, CONF_TOKEN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.typing import ConfigType

from .api import XiaomiMiioCookerApi, build_unique_id
from .const import (
    ATTR_PROFILE,
    CONF_MODEL,
    DATA_COORDINATORS,
    DATA_SERVICES_REGISTERED,
    DOMAIN,
    PLATFORMS,
    SERVICE_START,
)
from .coordinator import XiaomiMiioCookerCoordinator

SERVICE_START_SCHEMA = vol.Schema(
    {
        vol.Optional(ATTR_DEVICE_ID): vol.All(cv.ensure_list, [cv.string]),
        vol.Required(ATTR_PROFILE): cv.string,
    }
)

def _get_domain_data(hass: HomeAssistant) -> dict:
    """Return the integration data container."""
    return hass.data.setdefault(
        DOMAIN,
        {
            DATA_COORDINATORS: {},
            DATA_SERVICES_REGISTERED: False,
        },
    )


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Xiaomi cooker integration."""
    _get_domain_data(hass)
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Xiaomi cooker from a config entry."""
    domain_data = _get_domain_data(hass)

    api = XiaomiMiioCookerApi(
        host=entry.data[CONF_HOST],
        token=entry.data[CONF_TOKEN],
        model=entry.data.get(CONF_MODEL),
    )
    coordinator = XiaomiMiioCookerCoordinator(hass, entry, api)
    await coordinator.async_config_entry_first_refresh()
    expected_unique_id = build_unique_id(
        coordinator.data.device_info.mac_address,
        coordinator.data.device_info.model or entry.data.get(CONF_MODEL),
    )
    if entry.unique_id != expected_unique_id:
        hass.config_entries.async_update_entry(
            entry,
            unique_id=expected_unique_id,
        )
        coordinator.device_unique_id = expected_unique_id

    domain_data[DATA_COORDINATORS][entry.entry_id] = coordinator
    await _async_register_services(hass)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    domain_data = _get_domain_data(hass)
    domain_data[DATA_COORDINATORS].pop(entry.entry_id, None)

    if not domain_data[DATA_COORDINATORS] and domain_data[DATA_SERVICES_REGISTERED]:
        hass.services.async_remove(DOMAIN, SERVICE_START)
        domain_data[DATA_SERVICES_REGISTERED] = False

    return True


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload a config entry."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_services(hass: HomeAssistant) -> None:
    """Register integration services."""
    domain_data = _get_domain_data(hass)
    if domain_data[DATA_SERVICES_REGISTERED]:
        return

    async def async_start_service(call: ServiceCall) -> None:
        """Start a cooking profile on the target cooker."""
        coordinators = _async_resolve_coordinators(hass, call)
        await asyncio.gather(
            *(coordinator.async_start(call.data[ATTR_PROFILE]) for coordinator in coordinators)
        )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START,
        async_start_service,
        schema=SERVICE_START_SCHEMA,
    )

    domain_data[DATA_SERVICES_REGISTERED] = True


def _async_resolve_coordinators(
    hass: HomeAssistant,
    call: ServiceCall,
) -> list[XiaomiMiioCookerCoordinator]:
    """Resolve target coordinators for a service call."""
    domain_data = _get_domain_data(hass)
    coordinators = domain_data[DATA_COORDINATORS]
    device_ids = call.data.get(ATTR_DEVICE_ID)

    if not device_ids:
        if len(coordinators) == 1:
            return list(coordinators.values())

        raise HomeAssistantError(
            "Multiple Xiaomi cookers are configured; target a device_id explicitly."
        )

    device_registry = dr.async_get(hass)
    resolved_entry_ids: set[str] = set()

    for device_id in device_ids:
        device_entry = device_registry.async_get(device_id)
        if device_entry is None:
            raise HomeAssistantError(f"Device {device_id} was not found.")

        matched_entry_id = next(
            (
                entry_id
                for entry_id in device_entry.config_entries
                if entry_id in coordinators
            ),
            None,
        )
        if matched_entry_id is None:
            raise HomeAssistantError(f"Device {device_id} does not belong to this integration.")

        resolved_entry_ids.add(matched_entry_id)

    return [coordinators[entry_id] for entry_id in resolved_entry_ids]
