<p align="center">
  <img src="assets/logo.jpg" alt="e-distribuzione Monitor" width="120">
</p>

# e-distribuzione Monitor

Integrazione custom per Home Assistant installabile con HACS. Monitora gli eventi attivi pubblici di e-distribuzione, filtra per distanza geografica da un punto configurabile e mantiene una dashboard con riepilogo, mappa e dettaglio eventi.

## Funzioni

- Polling API pubblica e-distribuzione ogni 30 minuti.
- Nome paese/zona, coordinate, raggio e intervallo configurabili da UI.
- Filtro Haversine entro il raggio configurato.
- Nessun filtro per provincia.
- Storico locale eventi attivi.
- Rilevazione nuovi eventi, eventi chiusi e variazioni del ripristino previsto.
- Sensori Home Assistant nativi.
- Mappa Leaflet servita da Home Assistant.
- Attributo `eventi` sul sensore principale per Lovelace.

## Sensori creati

```text
sensor.edistribuzione_eventi_vicini
sensor.edistribuzione_guasti_vicini
sensor.edistribuzione_lavori_vicini
sensor.edistribuzione_utenze_coinvolte
```

Il sensore principale espone:

```yaml
eventi:
  - id
  - tipo
  - zona
  - provincia
  - comune
  - utenti
  - inizio
  - ripristino
  - ultimo_aggiornamento
  - latitudine
  - longitudine
  - distanza_km
```

## Eventi Home Assistant

L'integrazione genera eventi interni utilizzabili nelle automazioni:

```text
edistribuzione_event_new
edistribuzione_event_closed
edistribuzione_event_updated
```

Esempio automazione:

```yaml
trigger:
  - platform: event
    event_type: edistribuzione_event_new
action:
  - service: notify.mobile_app
    data:
      title: Nuovo evento e-distribuzione
      message: >
        {{ trigger.event.data.tipo }} - {{ trigger.event.data.zona }}
        {{ trigger.event.data.distanza_km }} km dal punto configurato.
```

## Installazione manuale

1. Copiare `custom_components/edistribuzione_monitor` in `/config/custom_components/`.
2. Riavviare Home Assistant.
3. Andare in **Impostazioni > Dispositivi e servizi > Aggiungi integrazione**.
4. Cercare **e-distribuzione Monitor**.
5. Configurare nome luogo, coordinate, raggio e intervallo. Per Vetralla:

```text
Nome paese o zona: Vetralla
Latitudine: 42.317
Longitudine: 12.083
Raggio: 50
Intervallo: 30
```

## Installazione HACS

Quando il progetto è su GitHub:

1. HACS > Integrazioni > menu tre puntini > Repository personalizzati.
2. Inserire l'URL del repository: `https://github.com/fcaloro-beep/edistribuzione-monitor`.
3. Categoria: Integrazione.
4. Installare **e-distribuzione Monitor**.
5. Riavviare Home Assistant.
6. Aggiungere l'integrazione da UI.

## Crediti

Questa integrazione non è ufficiale e non è affiliata a e-distribuzione.

Un ringraziamento ad Alberto Pedron, autore del progetto Android non ufficiale [Alberto97/eGuasti](https://github.com/Alberto97/eGuasti), da cui è nata l'idea di usare le API pubbliche per visualizzare guasti e lavori programmati della rete e-distribuzione.

## Licenza

Distribuito con licenza MIT. Vedi `LICENSE`.

## Mappa

La mappa è disponibile a:

```text
/api/edistribuzione_monitor/map
```

La dashboard pronta è in `lovelace-dashboard.yaml`. Mantiene la disposizione già usata:

- riepilogo a sinistra;
- mappa eventi con raggio 50 km;
- sensori a destra;
- dettaglio eventi sotto.
- scheda dedicata agli eventi nel comune configurato.
