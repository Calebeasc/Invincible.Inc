# Omni-Mesh field reporter — setup & enrollment

This is what runs on the machine with the Alfa adapter (your driving laptop) and
feeds the Omni-Mesh server. It captures Wi-Fi off the Alfa, **hires** the roadside
devices you drive past, and **reports** what it hears so the server can fuse,
classify (Flock / Axon / LEA), localize, and mark targets on the Arion map.

> **Reality check:** a roadside device (a streetlight, a Flock camera) does **not**
> send data to the server itself. *Your Alfa is the reporter.* "Hiring" enrolls and
> labels the roadside node so it shows on the map; the live LEA-signal reporting is
> your Alfa overhearing devices as you drive. One Alfa = one reporter node.

---

## 1. The pipeline, end to end

```
 Alfa (monitor mode, in WSL2 on the laptop)
   │  tools/alfa_mesh_reporter.py
   ├─ POST /mesh/hire     ← roadside devices you pass (lights/signs/RSU/ALPR…)
   └─ POST /mesh/report   ← every Wi-Fi thing it hears, ~every 3 s
        ▼  http(s) to the server over Twingate (backend.invincible.lan:8742)
 scanner-map backend :8742 — MeshHub: fuse, classify, flag LEA, localize/track
        ▼  GET /mesh/flagged
 Omni backend :8802 — mesh_bridge → /arion/omniscience/snapshot
        ▼
 Omni app (laptop) — Arion map draws LEA as red pins (live / coasting / last-known)
```

## 2. Enrollment packet (what a hire returns)

`POST /mesh/hire` answers with the reporter's machine-readable marching orders:

```json
{ "ok": true, "device_id": "road-XXXX", "device_type": "smart_streetlight",
  "device_label": "Smart streetlight node", "confidence": 0.8, "matched_on": "keyword",
  "enrollment": {
    "report_endpoint": "/mesh/report", "method": "POST", "report_interval_s": 3.0,
    "auth": { "required": false, "header": "X-Mesh-Token" },
    "send": { "device_id": "...", "gps": {"lat": "...", "lon": "..."},
              "observations": [ {"bssid":"…","ssid":"…","rssi":-57,"chan":6,"type":"ap"} ] } } }
```

The reporter tool already speaks this; the packet is there so any client can
self-configure.

## 3. Run the reporter (Linux or WSL2)

```bash
# adapter into monitor mode (name from `ip link`, e.g. wlx00c0cababe70)
sudo ip link set IFACE down
sudo iw dev IFACE set type monitor
sudo ip link set IFACE up

# report + auto-hire roadside devices, GPS from a file the phone/GPS updates
sudo backend/.venv/bin/python tools/alfa_mesh_reporter.py \
    --iface IFACE \
    --server http://backend.invincible.lan:8742 \
    --device alfa-laptop --gps-file /run/gps.json
```

Flags: `--no-hire` (report only, don't enroll roadside devices), `--no-hop` (stay on
one channel), `--lat/--lon` (fixed position instead of `--gps-file`), `--once` (one
window, for testing), `--token` (if `MESH_INGEST_TOKEN` is set on the server).

No Alfa handy? Smoke-test the server path from a phone: open
`http://backend.invincible.lan:8742/mesh/sensor`.

## 4. Windows laptop: Alfa in WSL2 (usbipd)

Native Windows monitor mode on the RTL8812AU is unreliable, so run the Linux
reporter inside WSL2 and pass the USB adapter through.

```powershell
# (Windows, admin PowerShell) — one-time
winget install usbipd
wsl --install                 # if WSL2 isn't installed yet
usbipd list                   # find the Alfa's BUSID (e.g. 2-4)
usbipd bind   --busid 2-4
usbipd attach --wsl --busid 2-4
```

```bash
# (inside WSL2 / Ubuntu)
sudo apt update && sudo apt install -y python3-venv aircrack-ng iw
ip link                       # confirm the Alfa shows up (wlxXXXX)
# clone scanner-map (or copy tools/ + backend/.venv), then run §3.
```

Re-attach (`usbipd attach`) after each unplug/reboot. If the Alfa doesn't appear in
WSL, update to the latest WSL kernel (`wsl --update`).

## 5. Verify it's flowing

```bash
curl http://backend.invincible.lan:8742/mesh/stats     # reports_total climbing
curl http://backend.invincible.lan:8742/mesh/flagged   # flagged LEA detections
curl http://backend.invincible.lan:8742/mesh/diag?n=20 # hire/flag/stats event log
```

Diagnostics also write to `~/SafeFlightMap/mesh_diag.jsonl` on the server.

## 6. Live tracking & road-snapping (server side)

Flagged LEA targets are tracked **live → coasting → last-known**:
- **live**: ≥1 reporter hears it → RSSI-weighted triangulation.
- **coasting**: in a sensor dead-zone → dead-reckoned forward along heading at last
  speed (so the pin keeps moving), road-snapped if a road network is loaded.
- **last-known**: not re-acquired after `MESH_COAST_MAX_S` (default 30 s) → held at the
  last real fix (the "pulled over" case).

Road-snapping turns on when a road network exists at
`~/SafeFlightMap/mesh_roads.geojson` (or `MESH_ROADS_GEOJSON`). Generate one:

```bash
python tools/fetch_roads.py --bbox SOUTH,WEST,NORTH,EAST   # your operating area
sudo systemctl restart invincible-backend.service
```
