from __future__ import annotations

import logging
import math
import time
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.storage import Store
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    API_URL,
    CONF_NOTIFY_INITIAL_EVENTS,
    CONF_PLACE_NAME,
    CONF_RADIUS_KM,
    CONF_REFERENCE_LATITUDE,
    CONF_REFERENCE_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_RADIUS_KM,
    DEFAULT_PLACE_NAME,
    DEFAULT_REFERENCE_LATITUDE,
    DEFAULT_REFERENCE_LONGITUDE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
    EVENT_CLOSED,
    EVENT_NEW,
    EVENT_UPDATED,
)

LOGGER = logging.getLogger(__name__)


class EDistribuzioneCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        options = {**entry.data, **entry.options}
        self.entry = entry
        self.place_name = str(options.get(CONF_PLACE_NAME, DEFAULT_PLACE_NAME)).strip() or DEFAULT_PLACE_NAME
        self.latitude = float(options.get(CONF_REFERENCE_LATITUDE, DEFAULT_REFERENCE_LATITUDE))
        self.longitude = float(options.get(CONF_REFERENCE_LONGITUDE, DEFAULT_REFERENCE_LONGITUDE))
        self.radius_km = float(options.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM))
        self.notify_initial_events = bool(options.get(CONF_NOTIFY_INITIAL_EVENTS, False))
        self.store: Store[dict[str, Any]] = Store(hass, 1, f"{DOMAIN}_{entry.entry_id}")
        self._state: dict[str, Any] | None = None

        interval_minutes = int(options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(minutes=interval_minutes),
        )

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            raw_events = await self._async_fetch_all_events()
        except Exception as err:
            raise UpdateFailed(f"Errore API e-distribuzione: {err}") from err

        events = self._nearby_events(raw_events)
        current = {str(event["key"]): event for event in events}
        state = await self._async_load_state()
        previous = state.get("events", {})
        first_run = not state.get("initialized", False)

        self._fire_change_events(previous, current, first_run)
        await self._async_save_state(current)

        return {
            "count": len(events),
            "guasti": sum(1 for event in events if is_fault(event)),
            "lavori": sum(1 for event in events if is_planned_work(event)),
            "utenze_coinvolte": sum(event["utenti"] for event in events),
            "raggio_km": self.radius_km,
            "nome_luogo": self.place_name,
            "latitudine_riferimento": self.latitude,
            "longitudine_riferimento": self.longitude,
            "eventi": events,
        }

    async def _async_fetch_all_events(self) -> list[dict[str, Any]]:
        session = async_get_clientsession(self.hass)
        page_size = 2000
        offset = 0
        events: list[dict[str, Any]] = []

        while True:
            params = {
                "where": "1=1",
                "f": "json",
                "returnGeometry": "false",
                "outFields": "*",
                "resultOffset": offset,
                "resultRecordCount": page_size,
            }
            async with session.get(API_URL, params=params, timeout=30) as response:
                response.raise_for_status()
                data = await response.json(content_type=None)

            if "error" in data:
                raise UpdateFailed(str(data["error"]))

            features = data.get("features", [])
            events.extend(feature.get("attributes", {}) for feature in features)

            if len(features) < page_size and not data.get("exceededTransferLimit"):
                break
            offset += len(features)
            if not features:
                break

        return events

    def _nearby_events(self, raw_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        events = [event for raw in raw_events if (event := self._normalize_event(raw))]
        return sorted(events, key=lambda event: (event["distanza_km"], event["id"]))

    def _normalize_event(self, raw: dict[str, Any]) -> dict[str, Any] | None:
        try:
            event_id = int(raw["id_interruzione"])
            latitude = float(raw["latitudine"])
            longitude = float(raw["longitudine"])
        except (KeyError, TypeError, ValueError):
            return None

        distance = haversine_km(self.latitude, self.longitude, latitude, longitude)
        if distance > self.radius_km:
            return None

        event_key = raw.get("objectid1") or raw.get("objectid") or f"{event_id}_{latitude:.6f}_{longitude:.6f}"

        return {
            "key": str(event_key),
            "id": event_id,
            "tipo": raw.get("causa_disalimentazione") or "Sconosciuto",
            "zona": raw.get("descrizione_territoriale") or "Sconosciuta",
            "provincia": raw.get("provincia") or "",
            "comune": raw.get("comune"),
            "utenti": int(raw.get("num_cli_disalim") or 0),
            "inizio": raw.get("data_interruzione") or "",
            "ripristino": raw.get("data_prev_ripristino") or "",
            "ultimo_aggiornamento": raw.get("dataultimoaggiornamento") or "",
            "latitudine": latitude,
            "longitudine": longitude,
            "distanza_km": round(distance, 1),
        }

    async def _async_load_state(self) -> dict[str, Any]:
        if self._state is None:
            self._state = await self.store.async_load() or {"events": {}, "initialized": False}
        return self._state

    async def _async_save_state(self, events_by_id: dict[str, dict[str, Any]]) -> None:
        self._state = {
            "initialized": True,
            "events": events_by_id,
            "updated_at": int(time.time()),
        }
        await self.store.async_save(self._state)

    def _fire_change_events(
        self,
        previous: dict[str, dict[str, Any]],
        current: dict[str, dict[str, Any]],
        first_run: bool,
    ) -> None:
        previous_ids = set(previous)
        current_ids = set(current)

        should_publish_initial = self.notify_initial_events or not first_run
        if should_publish_initial:
            for event_id in sorted(current_ids - previous_ids):
                self.hass.bus.async_fire(EVENT_NEW, current[event_id])

        for event_id in sorted(previous_ids - current_ids):
            self.hass.bus.async_fire(EVENT_CLOSED, previous[event_id])

        for event_id in sorted(previous_ids & current_ids):
            old = previous[event_id]
            new = current[event_id]
            if old.get("ripristino") != new.get("ripristino"):
                self.hass.bus.async_fire(
                    EVENT_UPDATED,
                    {
                        **new,
                        "ripristino_precedente": old.get("ripristino", ""),
                        "ripristino_nuovo": new.get("ripristino", ""),
                    },
                )


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    earth_radius_km = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(delta_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
    )
    return earth_radius_km * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def is_fault(event: dict[str, Any]) -> bool:
    return "guasto" in event["tipo"].lower()


def is_planned_work(event: dict[str, Any]) -> bool:
    text = event["tipo"].lower()
    return "lavor" in text or "program" in text
