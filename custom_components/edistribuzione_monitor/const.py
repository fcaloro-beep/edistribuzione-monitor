from __future__ import annotations

from datetime import timedelta

DOMAIN = "edistribuzione_monitor"

API_URL = "https://ineuportalgis.enel.com/server/rest/services/Hosted/ITA_power_cut_map_layer_View/FeatureServer/0/query"

CONF_REFERENCE_LATITUDE = "reference_latitude"
CONF_REFERENCE_LONGITUDE = "reference_longitude"
CONF_RADIUS_KM = "radius_km"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_NOTIFY_INITIAL_EVENTS = "notify_initial_events"
CONF_PLACE_NAME = "place_name"

DEFAULT_NAME = "e-distribuzione Vetralla"
DEFAULT_PLACE_NAME = "Vetralla"
DEFAULT_REFERENCE_LATITUDE = 42.317
DEFAULT_REFERENCE_LONGITUDE = 12.083
DEFAULT_RADIUS_KM = 50.0
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL)

EVENT_NEW = "edistribuzione_event_new"
EVENT_CLOSED = "edistribuzione_event_closed"
EVENT_UPDATED = "edistribuzione_event_updated"

SENSOR_EVENTI = "eventi_vicini"
SENSOR_GUASTI = "guasti_vicini"
SENSOR_LAVORI = "lavori_vicini"
SENSOR_UTENZE = "utenze_coinvolte"
