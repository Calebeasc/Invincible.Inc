# FOR THE LAPTOP — Invincible.Inc (scanner-map + Omni-Mesh)

> Channel between **Claude (Linux server)** and **Caleb's Windows laptop**.
> Laptop: do the "Claude → Laptop" tasks, write back under "Laptop → Claude", commit + push.

Last updated by Claude: 2026-06-13.

## What's true right now
- This repo's `scanner-map` app is the **lightweight user app** (React PWA) and runs
  live on the server as `invincible-backend.service` at `http://192.168.0.122:8742`.
- I built **Omni-Mesh** here: ingest + classification (Flock/Axon/LEA) + **hire**
  (`/mesh/hire`) + **multi-sensor localization** (triangulated position, speed,
  heading, path) + an offline-resilient PWA map layer (`src/hooks/useMesh.js`,
  MapView mesh layers). Docs: `scanner-map/OMNI_MESH.md`. Reporters: `scanner-map/tools/`.
- The PWA's server-down resilience and a critical pre-existing render crash are
  **fixed and verified** in a real browser.

## Claude → Laptop  (current asks — this one is important)
1. **The scanner-map app is running on placeholder stubs.** A previous AI had to
   reconstruct ~11 files that were imported but never committed (full list in
   `scanner-map/SETUP_NOTES.md` — `core/storage.py`, `core/audit_log.py`,
   `ingest/adsb_scanner.py`, `api/trophy_road.py`, `api/medic.py`, `api/unfiltered.py`,
   `api/vanguard.py`, frontend `stores/trophyRoadStore.js`, `components/DiagnosticCard.jsx`,
   `KineticThreatOverlay.jsx`, `VehicleModelPreview.jsx`). **If the real versions
   exist on your laptop (the original build machine), push them** — that replaces the
   stubs and lets me push the Omni-Mesh work to GitHub cleanly (right now main.py
   imports the stubs, so a clean buildable push isn't possible without them).
2. If those real files DON'T exist anywhere, tell me here and I'll treat the stubs
   as the baseline and push Omni-Mesh as a PR on top of them.

## Laptop → Claude  (write results / blockers here, then push)
- _(empty — laptop, add your replies here)_

## How to run the user app on Windows
```powershell
cd scanner-map\frontend; npm install; npm run build
cd ..\backend; python -m uvicorn app.main:app --app-dir src --host 127.0.0.1 --port 8742
# open http://127.0.0.1:8742  (the Omni-Mesh pill is top-right of the map)
```
