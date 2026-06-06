from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback

from .const import (
    CONF_NOTIFY_INITIAL_EVENTS,
    CONF_PLACE_NAME,
    CONF_RADIUS_KM,
    CONF_REFERENCE_LATITUDE,
    CONF_REFERENCE_LONGITUDE,
    CONF_SCAN_INTERVAL,
    DEFAULT_NAME,
    DEFAULT_PLACE_NAME,
    DEFAULT_RADIUS_KM,
    DEFAULT_REFERENCE_LATITUDE,
    DEFAULT_REFERENCE_LONGITUDE,
    DEFAULT_SCAN_INTERVAL,
    DOMAIN,
)


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_PLACE_NAME,
                default=defaults.get(CONF_PLACE_NAME, DEFAULT_PLACE_NAME),
            ): str,
            vol.Required(
                CONF_REFERENCE_LATITUDE,
                default=defaults.get(CONF_REFERENCE_LATITUDE, DEFAULT_REFERENCE_LATITUDE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_REFERENCE_LONGITUDE,
                default=defaults.get(CONF_REFERENCE_LONGITUDE, DEFAULT_REFERENCE_LONGITUDE),
            ): vol.Coerce(float),
            vol.Required(
                CONF_RADIUS_KM,
                default=defaults.get(CONF_RADIUS_KM, DEFAULT_RADIUS_KM),
            ): vol.Coerce(float),
            vol.Required(
                CONF_SCAN_INTERVAL,
                default=defaults.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            ): vol.All(vol.Coerce(int), vol.Range(min=5, max=1440)),
            vol.Required(
                CONF_NOTIFY_INITIAL_EVENTS,
                default=defaults.get(CONF_NOTIFY_INITIAL_EVENTS, False),
            ): bool,
        }
    )


class EDistribuzioneConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        await self.async_set_unique_id("edistribuzione_monitor")
        self._abort_if_unique_id_configured()

        if user_input is not None:
            place_name = user_input.get(CONF_PLACE_NAME, DEFAULT_PLACE_NAME)
            return self.async_create_entry(title=f"e-distribuzione {place_name}", data=user_input)

        return self.async_show_form(step_id="user", data_schema=_schema({}))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return EDistribuzioneOptionsFlow(config_entry)


class EDistribuzioneOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        defaults = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(step_id="init", data_schema=_schema(defaults))
