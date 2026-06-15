# Linux Server Setup Notes — Invincible.Inc / scanner-map

Generated 2026-06-12 while configuring this machine as the Linux server for the
app. **Nothing here has been committed or pushed** — these are local changes on
the working tree only.

## TL;DR
- Backend boots headless on Linux: `uvicorn app.main:app` serves **91 routes** on `:8742`.
- Frontend builds: `npm run build` → `frontend/dist/` (928K).
- To make either run, several files that the committed code imports **but that
  were never committed to any branch** had to be reconstructed as minimal,
  clearly-labeled placeholders. Replace them with the real implementations.

## ⚠️ Reconstructed placeholder files (were missing from the repo)
Every file below starts with an `AUTO-GENERATED PLACEHOLDER` header.

### Backend (`scanner-map/backend/src/app/`)
| File | Why it was needed | Placeholder behavior |
|------|-------------------|----------------------|
| `core/storage.py` | imported by `main.py`, `core/daily_checkpoint.py`, and (new) `core/audit_log.py` | `get_app_data_dir()` / `get_vehicle_assets_dir()` return dirs under `~/SafeFlightMap` |
| `core/audit_log.py` | imported by `api/distribution.py` | `log_dev_action()` appends JSON lines to `~/SafeFlightMap/audit.log` |
| `ingest/adsb_scanner.py` | imported by `main.py` (`/adsb/status` + startup) | `get_active_aircraft()` → `[]`; `scanner.start()` no-op |
| `api/trophy_road.py` | mounted at `/api`; `bootstrap_legacy_assets()` called on startup | empty router + status endpoint + no-op bootstrap |
| `api/medic.py` | mounted at `/api` | status endpoint only |
| `api/unfiltered.py` | mounted at `/assistant` | status endpoint only (real one likely proxies a local LLM) |
| `api/vanguard.py` | mounted at `/vanguard` | status endpoint only |

### Backend — edits to existing committed files
| File | Edit |
|------|------|
| `core/dev_auth.py` | added `require_developer(authorization)` (imported by `api/distribution.py`, was missing) |
| `core/config.py` | added `Settings.VEHICLE_ASSET_DIR` (referenced by `main.py`/`core/storage.py`, was missing) |

### Frontend (`scanner-map/frontend/src/`)
| File | Imported by | Placeholder behavior |
|------|-------------|----------------------|
| `stores/trophyRoadStore.js` | `components/DevAssetOps.jsx` | `useTrophyRoadStore()` → `{assets:[], milestones:[], hydrate, connect}` |
| `components/DiagnosticCard.jsx` | `components/DevPanel.jsx` | renders a labeled card |
| `components/KineticThreatOverlay.jsx` | `components/MapView.jsx` | renders `null` (no-op map overlay) |
| `components/VehicleModelPreview.jsx` | `components/DevAssetOps.jsx` (lazy) | sized "preview unavailable" box |

### Frontend — dependency added
- `axios` was imported by `components/DevAssetOps.jsx` but missing from
  `package.json`. Added via `npm install axios`.

## Known Linux limitation (not a bug we introduced)
The radio/Wi-Fi/network **ingest scanners** (`ingest/network_discovery.py`,
`wifi_scanner.py`, etc.) call `subprocess.run(..., creationflags=...)`, which is
Windows-only, so those background threads throw on Linux
(`creationflags is only supported on Windows platforms`). This is **non-fatal** —
the API server and all routes work; only live local radio scanning is disabled.
Live scanning also fundamentally needs Wi-Fi/BLE radio hardware. To run scanning
on Linux, those modules need a platform guard around the Windows subprocess flags.

## How to run on this server
Backend (headless API):
```
cd ~/Projects/Invincible.Inc/scanner-map/backend
SFM_HOST=0.0.0.0 PYTHONPATH=src ./.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8742
```
Frontend (rebuild static bundle):
```
cd ~/Projects/Invincible.Inc/scanner-map/frontend && npm run build
```
A systemd service (`invincible-backend.service`) is installed to run the backend
on boot — see `~/.setup/` and `systemctl --user status invincible-backend` (or the
system unit, depending on install).
