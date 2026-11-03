from __future__ import annotations

from homeassistant.components.binary_sensor import BinarySensorDeviceClass, BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RinnaiCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: RinnaiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RinnaiRunningBinarySensor(coordinator, entry)])


class RinnaiRunningBinarySensor(CoordinatorEntity, BinarySensorEntity):
    _attr_name = "乾太くん 運転中"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_icon = "mdi:tumble-dryer"

    def __init__(self, coordinator: RinnaiCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_running"

    @property
    def is_on(self):
        return self.coordinator.data.get("status") == "RUN" if self.coordinator.data else False

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "乾太くん",
            "manufacturer": "Rinnai",
        }
