# Omni-Mesh — field-sensor fusion on the server

Hundreds of field devices (Alfa Wi-Fi adapters, SDRs, ESP32 nodes) report what
they hear to **this server**. The server fuses every report into one live picture
and pushes it to the lightweight user apps (the scanner-map PWA) as small diffs.
The phones never run a model or crunch the firehose — the dedicated PC does, and
the apps just render the markings.

```
  hundreds of field sensors (Alfa adapter, monitor mode)
        │  POST /mesh/report   (802.11: BSSID/SSID/RSSI/chan/vendor + GPS)
        ▼
  invincible-backend  :8742   ── MeshHub: fuse + dedupe + bound + persist
        │  /mesh/ws            ── ONE coalesced diff frame ~1×/sec to every app
        ▼
  scanner-map PWA (phone)      ── 📡 sensor nodes + Wi-Fi detection markings
        • offline-safe: opens from cache, shows last-known mesh, auto-reconnects
```

## Why it scales (the load split you asked for)

The trick is **decoupling ingest rate from fan-out rate**. A report just marks
changed keys "dirty"; a single background loop wakes ~once/second, builds **one**
diff of everything that changed, and sends that to every connected app. So 500
reports/sec become ~1 broadcast/sec per client instead of 500. State is bounded
(detections capped + TTL-evicted) so memory can't run away, and a snapshot on disk
means a server restart restores the last-known mesh.

Tunables (env vars on the service, all optional):
`MESH_FLUSH_INTERVAL` (1.0s), `MESH_MAX_DETECTIONS` (50000), `MESH_MAX_DIFF_DETS`
(2500/frame), `MESH_NODE_TTL_S` (120), `MESH_DET_TTL_S` (900),
`MESH_SNAPSHOT_EVERY_S` (30), `MESH_INGEST_TOKEN` (unset = open on LAN).

## API

| Endpoint | Purpose |
|---|---|
| `POST /mesh/report` | a sensor pushes a batch of observations (schema: `app/mesh/schemas.py`) |
| `WS /mesh/ws` | an app subscribes — receives one `snapshot` then live `diff` frames |
| `GET /mesh/stats` | counters (nodes, online, detections, clients) |
| `GET /mesh/snapshot` | full state as JSON (debug / non-WS clients) |
| `GET /mesh/sensor` | a browser "sim sensor" page for testing without hardware |

Report body:
```json
{ "device_id": "alfa-pi-07", "gps": {"lat": 33.45, "lon": -112.07},
  "observations": [
    {"bssid":"AA:BB:CC:DD:EE:01","ssid":"HOME-5G","rssi":-42,"chan":6,"type":"ap","oui_vendor":"Cisco"},
    {"bssid":"AA:BB:CC:DD:EE:02","rssi":-71,"type":"client"} ] }
```

## Running a field sensor (the Alfa box)

On each device with an Alfa adapter in monitor mode:
```bash
sudo airmon-ng start wlan1
sudo airodump-ng -w /tmp/mesh --output-format csv --write-interval 2 wlan1mon
# then feed it up to the server:
python tools/alfa_mesh_feeder.py \
  --server http://192.168.0.122:8742 --device alfa-pi-07 \
  --airodump /tmp/mesh --gps-file /run/gps.json
```
No hardware handy? `python tools/alfa_mesh_feeder.py --sim --server http://192.168.0.122:8742 --device test-1`
or just open `http://192.168.0.122:8742/mesh/sensor` on a phone.

## In the app

The map shows 📡 **sensor nodes** (green = online, grey = stale, with a coverage
ring) and their **Wi-Fi detections** as signal-colored dots (green strong → blue →
dim weak; small dots = clients, larger = APs). A pill (top-right) shows
`MESH · N sensors · M detections` live, or `MESH OFFLINE · M cached` when the
server is unreachable — tap it to hide/show the layer.

## Offline / server-down behavior

Opening the app with the server down does **not** break it:
- The PWA service worker serves the cached app shell, so it still **opens**.
- `useMesh` hydrates the last-known mesh from `localStorage` on launch, so the
  **markings still show**.
- The WebSocket reconnects with capped backoff; the pill reads `MESH OFFLINE`
  until the server is back, then flips to live automatically.
- Nothing throws — a dead server is a status, not a crash.
