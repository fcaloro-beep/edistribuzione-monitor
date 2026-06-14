from __future__ import annotations

from html import escape
import json
from typing import Any

from aiohttp import web

from homeassistant.components.http import HomeAssistantView
from homeassistant.core import HomeAssistant

from .const import (
    DEFAULT_PLACE_NAME,
    DEFAULT_RADIUS_KM,
    DEFAULT_REFERENCE_LATITUDE,
    DEFAULT_REFERENCE_LONGITUDE,
    DOMAIN,
)


def async_register_http_views(hass: HomeAssistant) -> None:
    if hass.data.setdefault(DOMAIN, {}).get("_http_registered"):
        return
    hass.http.register_view(EDistribuzioneEventsView)
    hass.http.register_view(EDistribuzioneMapView)
    hass.data[DOMAIN]["_http_registered"] = True


def _first_payload(hass: HomeAssistant) -> dict[str, Any]:
    domain_data = hass.data.get(DOMAIN, {})
    for key, coordinator in domain_data.items():
        if key.startswith("_"):
            continue
        data = getattr(coordinator, "data", None)
        if data:
            return data
    return {
        "count": 0,
        "guasti": 0,
        "lavori": 0,
        "utenze_coinvolte": 0,
        "raggio_km": DEFAULT_RADIUS_KM,
        "nome_luogo": DEFAULT_PLACE_NAME,
        "latitudine_riferimento": DEFAULT_REFERENCE_LATITUDE,
        "longitudine_riferimento": DEFAULT_REFERENCE_LONGITUDE,
        "eventi": [],
    }


class EDistribuzioneEventsView(HomeAssistantView):
    url = "/api/edistribuzione_monitor/events"
    name = "api:edistribuzione_monitor:events"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        payload = _first_payload(request.app["hass"])
        return web.Response(
            text=json.dumps(payload, ensure_ascii=False),
            content_type="application/json",
        )


class EDistribuzioneMapView(HomeAssistantView):
    url = "/api/edistribuzione_monitor/map"
    name = "api:edistribuzione_monitor:map"
    requires_auth = False

    async def get(self, request: web.Request) -> web.Response:
        payload = _first_payload(request.app["hass"])
        html = _map_html(
            place_name=str(payload.get("nome_luogo") or DEFAULT_PLACE_NAME),
            latitude=float(payload.get("latitudine_riferimento") or DEFAULT_REFERENCE_LATITUDE),
            longitude=float(payload.get("longitudine_riferimento") or DEFAULT_REFERENCE_LONGITUDE),
            radius_km=float(payload.get("raggio_km") or DEFAULT_RADIUS_KM),
        )
        return web.Response(text=html, content_type="text/html")


def _map_html(place_name: str, latitude: float, longitude: float, radius_km: float) -> str:
    place_name_html = escape(place_name)
    return f"""<!doctype html>
<html lang="it">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>e-distribuzione {place_name_html}</title>
  <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
  <style>
    html, body, #map {{ height: 100%; margin: 0; }}
    body {{ font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
    .summary {{
      position: absolute;
      z-index: 1000;
      top: 10px;
      left: 10px;
      background: rgba(255,255,255,.94);
      border-radius: 6px;
      padding: 10px 12px;
      box-shadow: 0 2px 10px rgba(0,0,0,.18);
      font-size: 14px;
      line-height: 1.35;
    }}
    .summary strong {{ display: block; margin-bottom: 4px; }}
    .legend {{
      position: absolute;
      z-index: 1000;
      bottom: 18px;
      left: 10px;
      background: rgba(255,255,255,.94);
      border-radius: 6px;
      padding: 9px 11px;
      box-shadow: 0 2px 10px rgba(0,0,0,.18);
      font-size: 13px;
      line-height: 1.45;
    }}
    .legend-row {{ display: flex; align-items: center; gap: 7px; white-space: nowrap; }}
    .dot {{ width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 1px 4px rgba(0,0,0,.35); }}
    .dot-fault {{ background: #d32f2f; }}
    .dot-work {{ background: #f9a825; }}
    .dot-center {{ background: #1976d2; }}
  </style>
</head>
<body>
  <div id="map"></div>
  <div class="summary" id="summary">Caricamento eventi...</div>
  <div class="legend">
    <div class="legend-row"><span class="dot dot-fault"></span><span>Guasto</span></div>
    <div class="legend-row"><span class="dot dot-work"></span><span>Lavoro programmato</span></div>
    <div class="legend-row"><span class="dot dot-center"></span><span>{place_name_html}</span></div>
    <div class="legend-row"><span style="width:16px;text-align:center;color:#1976d2;">○</span><span>Raggio {radius_km:g} km</span></div>
  </div>
  <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
  <script>
    const placeName = {json.dumps(place_name)};
    const center = [{latitude}, {longitude}];
    const radiusKm = {radius_km};
    const map = L.map('map').setView(center, 10);
    L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap'
    }}).addTo(map);
    L.circle(center, {{
      radius: radiusKm * 1000,
      color: '#1976d2',
      weight: 2,
      opacity: 0.65,
      fillColor: '#1976d2',
      fillOpacity: 0.035
    }}).addTo(map).bindPopup(`Raggio monitorato: ${{radiusKm}} km`);
    L.circleMarker(center, {{
      radius: 8,
      color: '#ffffff',
      weight: 2,
      fillColor: '#1976d2',
      fillOpacity: 1
    }}).addTo(map).bindPopup(placeName);

    function colorFor(evento) {{
      const tipo = String(evento.tipo || '').toLowerCase();
      if (tipo.includes('guasto')) return '#d32f2f';
      if (tipo.includes('lavor')) return '#f9a825';
      return '#455a64';
    }}

    function markerIcon(evento) {{
      const color = colorFor(evento);
      return L.divIcon({{
        className: '',
        html: `<div style="width:16px;height:16px;border-radius:50%;background:${{color}};border:2px solid white;box-shadow:0 1px 5px rgba(0,0,0,.4)"></div>`,
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      }});
    }}

    fetch('/api/edistribuzione_monitor/events')
      .then(r => r.json())
      .then(data => {{
        const eventi = data.eventi || [];
        document.getElementById('summary').innerHTML =
          `<strong>e-distribuzione - zona ${{placeName}}</strong>` +
          `Guasti: ${{data.guasti || 0}}<br>` +
          `Lavori programmati: ${{data.lavori || 0}}<br>` +
          `Utenze coinvolte: ${{data.utenze_coinvolte || 0}}`;

        eventi.forEach(e => {{
          if (!e.latitudine || !e.longitudine) return;
          const pos = [Number(e.latitudine), Number(e.longitudine)];
          L.marker(pos, {{ icon: markerIcon(e) }}).addTo(map).bindPopup(
            `<b>${{e.tipo || 'Evento'}}</b><br>` +
            `${{e.zona || ''}} (${{e.provincia || ''}})<br>` +
            `Utenze: ${{e.utenti || 0}}<br>` +
            `Distanza: ${{e.distanza_km || '-'}} km<br>` +
            `Ripristino: ${{e.ripristino || '-'}}`
          );
        }});
      }})
      .catch(() => {{
        document.getElementById('summary').textContent = 'Impossibile caricare gli eventi.';
      }});
  </script>
</body>
</html>"""
