from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    SENSOR_EVENTI,
    SENSOR_GUASTI,
    SENSOR_LAVORI,
    SENSOR_UTENZE,
)
from .coordinator import EDistribuzioneCoordinator


SENSOR_DESCRIPTIONS = {
    SENSOR_EVENTI: {
        "name": "e-distribuzione eventi vicini",
        "suggested_object_id": "edistribuzione_eventi_vicini",
        "icon": "mdi:transmission-tower",
        "value_key": "count",
    },
    SENSOR_GUASTI: {
        "name": "e-distribuzione guasti vicini",
        "suggested_object_id": "edistribuzione_guasti_vicini",
        "icon": "mdi:flash-alert",
        "value_key": "guasti",
    },
    SENSOR_LAVORI: {
        "name": "e-distribuzione lavori vicini",
        "suggested_object_id": "edistribuzione_lavori_vicini",
        "icon": "mdi:hammer-wrench",
        "value_key": "lavori",
    },
    SENSOR_UTENZE: {
        "name": "e-distribuzione utenze coinvolte",
        "suggested_object_id": "edistribuzione_utenze_coinvolte",
        "icon": "mdi:home-lightning-bolt",
        "value_key": "utenze_coinvolte",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: EDistribuzioneCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        EDistribuzioneSensor(coordinator, entry, key)
        for key in SENSOR_DESCRIPTIONS
    )


class EDistribuzioneSensor(CoordinatorEntity[EDistribuzioneCoordinator], SensorEntity):
    _attr_has_entity_name = False

    def __init__(
        self,
        coordinator: EDistribuzioneCoordinator,
        entry: ConfigEntry,
        key: str,
    ) -> None:
        super().__init__(coordinator)
        description = SENSOR_DESCRIPTIONS[key]
        self._key = key
        self._value_key = description["value_key"]
        self._attr_name = description["name"]
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_suggested_object_id = description["suggested_object_id"]
        self._attr_icon = description["icon"]
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"e-distribuzione {coordinator.place_name}",
            manufacturer="e-distribuzione",
            model="Public outage map monitor",
        )

    @property
    def native_value(self) -> int:
        return int((self.coordinator.data or {}).get(self._value_key, 0))

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        data = self.coordinator.data or {}
        if self._key == SENSOR_EVENTI:
            return {
                "eventi": data.get("eventi", []),
                "raggio_km": data.get("raggio_km"),
                "nome_luogo": data.get("nome_luogo"),
                "latitudine_riferimento": data.get("latitudine_riferimento"),
                "longitudine_riferimento": data.get("longitudine_riferimento"),
            }
        return None


class EDistribuzioneDiagnosticSensor(EDistribuzioneSensor):
    _attr_entity_category = EntityCategory.DIAGNOSTIC
