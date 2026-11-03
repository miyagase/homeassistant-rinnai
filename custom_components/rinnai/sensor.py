from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import RinnaiCoordinator

STATUS_MAP = {
    "OFF": "停止中",
    "RUN": "運転中",
    "STANDBY": "待機中",
    "ERROR": "エラー",
}


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    coordinator: RinnaiCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        RinnaiStatusSensor(coordinator, entry),
        RinnaiCourseSensor(coordinator, entry),
        RinnaiTimeRemainingSensor(coordinator, entry),
    ])


class RinnaiBaseSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator: RinnaiCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "乾太くん",
            "manufacturer": "Rinnai",
        }


class RinnaiStatusSensor(RinnaiBaseSensor):
    _attr_name = "乾太くん ステータス"
    _attr_icon = "mdi:tumble-dryer"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_status"

    @property
    def native_value(self):
        if self.coordinator.data:
            raw = self.coordinator.data.get("status", "")
            return STATUS_MAP.get(raw, raw)
        return None

    @property
    def extra_state_attributes(self):
        if self.coordinator.data:
            return {"raw_status": self.coordinator.data.get("status"), "updated_at": self.coordinator.data.get("updatedAt")}
        return {}


class RinnaiCourseSensor(RinnaiBaseSensor):
    _attr_name = "乾太くん コース"
    _attr_icon = "mdi:cog"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_course"

    @property
    def native_value(self):
        return self.coordinator.data.get("course") if self.coordinator.data else None


class RinnaiTimeRemainingSensor(RinnaiBaseSensor):
    _attr_name = "乾太くん 残り時間"
    _attr_icon = "mdi:timer"
    _attr_native_unit_of_measurement = "min"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_time_remaining"

    @property
    def native_value(self):
        if self.coordinator.data:
            val = self.coordinator.data.get("timeRemaining")
            try:
                return int(val)
            except (TypeError, ValueError):
                return None
        return None
