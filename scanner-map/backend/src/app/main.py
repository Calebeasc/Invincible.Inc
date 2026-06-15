"""SafeFlight Map / Invincible.Inc – FastAPI backend v0.3"""
import sys, os
from pathlib import Path

_HERE = os.path.dirname(os.path.abspath(__file__))
_SRC  = os.path.join(_HERE, "..", "..")
if _SRC not in sys.path:
    sys.path.insert(0, _SRC)

import time
import collections
import threading
from fastapi import FastAPI, Request, Response
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.db.database import init_db
from app.api import control, targets, heatmap, encounters, exports
from app.api import settings_api, gps_ws, route_stats, users, scan, device_filter
from app.api import replay, hotspots, accounts, dev_auth
from app.api import achievements
from app.api import stoppers
from app.api import flock_cameras
from app.api import trophy_road
from app.api import medic
from app.api import distribution
from app.api import unfiltered
from app.api import identity, geolocation
from app.api import mesh
from app.core.daily_checkpoint import ensure_daily_save
from app.core.storage import get_vehicle_assets_dir
from app.core.distribution import get_source_root, get_windows_download_targets, iter_file_chunks, resolve_download_path

APP_VERSION = "1.1.0"

app = FastAPI(title="Invincible.Inc Scanner", version=APP_VERSION)

# ── Security headers middleware ───────────────────────────────────────────────
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response: Response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(self), microphone=(), camera=()"
        # Only add HSTS if served over HTTPS (local dev is HTTP)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response

app.add_middleware(SecurityHeadersMiddleware)

# ── Simple in-memory rate limiter ─────────────────────────────────────────────
_rate_lock = threading.Lock()
_rate_store: dict = collections.defaultdict(list)  # ip → [ts, ...]

_RATE_RULES = {
    "/control":  (100, 60),  # 100 req / 60 s
    "/accounts": (100, 60),  # 100 req / 60 s
    "/scan":     (200, 10),  # 200 req / 10 s (Lab tab polls 4 endpoints every 5s)
    "/assistant": (40, 60),  # 40 req / 60 s for the in-app question tool
}

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        client_ip = (request.headers.get("x-forwarded-for") or
                     (request.client.host if request.client else "local"))
        now = time.time()
        for prefix, (limit, window) in _RATE_RULES.items():
            if path.startswith(prefix):
                key = f"{client_ip}:{prefix}"
                with _rate_lock:
                    hits = _rate_store[key]
                    hits[:] = [t for t in hits if now - t < window]
                    if len(hits) >= limit:
                        return Response(
                            content='{"detail":"rate limit exceeded"}',
                            status_code=429,
                            media_type="application/json",
                            headers={"Retry-After": str(window)},
                        )
                    hits.append(now)
                break
        return await call_next(request)

app.add_middleware(RateLimitMiddleware)

# ── CORS: localhost origins only (Vite dev + production same-origin) ──────────
_LOCALHOST_ORIGINS = [
    "null",
    "http://localhost:5173",
    "http://localhost:8000",
    "http://localhost:8080",
    "http://localhost:8742",
    "http://localhost:8743",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:8080",
    "http://127.0.0.1:8742",
    "http://127.0.0.1:8743",
    "http://127.0.0.1:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_LOCALHOST_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Device-ID"],
    allow_credentials=False,
)

# ── App Mode Detection ───────────────────────────────────────────────────────
# Detects if we are running in 'user' or 'system' (dev) mode.
APP_MODE = "user"
if os.getenv("INVINCIBLE_APP_MODE", "").strip().lower() == "sovereign" or "--mode=sovereign" in sys.argv:
    APP_MODE = "sovereign"
IS_SOVEREIGN = APP_MODE == "sovereign"

@app.get("/health")
def get_health():
    return {
        "status": "online",
        "mode": APP_MODE,
        "version": APP_VERSION
    }

@app.get("/adsb/status")
def get_adsb_status():
    from app.ingest import adsb_scanner
    return {"aircraft": adsb_scanner.get_active_aircraft()}

from app.api import vanguard
app.include_router(vanguard.router,       prefix="/vanguard",    tags=["vanguard"])
app.include_router(control.router,        prefix="/control",    tags=["control"])
app.include_router(targets.router,        prefix="/targets",    tags=["targets"])
app.include_router(heatmap.router,        prefix="/heatmap",    tags=["heatmap"])
app.include_router(encounters.router,     prefix="/encounters", tags=["encounters"])
app.include_router(exports.router,        prefix="/export",     tags=["exports"])
app.include_router(settings_api.router,   prefix="/settings",   tags=["settings"])
app.include_router(gps_ws.router,         prefix="",            tags=["gps"])
app.include_router(route_stats.router,    prefix="",            tags=["route"])
app.include_router(users.router,          prefix="/users",       tags=["users"])
app.include_router(scan.router,           prefix="/scan",          tags=["scan"])
app.include_router(device_filter.router,  prefix="/devices/filter", tags=["devices"])
app.include_router(replay.router,         prefix="/replay",         tags=["replay"])
app.include_router(hotspots.router,       prefix="/hotspots",       tags=["hotspots"])
app.include_router(accounts.router,       prefix="/accounts",       tags=["accounts"])
app.include_router(achievements.router,   prefix="/achievements",   tags=["achievements"])
app.include_router(stoppers.router,       prefix="/stoppers",        tags=["stoppers"])
app.include_router(flock_cameras.router,  prefix="/flock",            tags=["flock"])
app.include_router(trophy_road.router,    prefix="/api",              tags=["trophy-road"])
app.include_router(medic.router,          prefix="/api",              tags=["medic"])
app.include_router(unfiltered.router,     prefix="/assistant",        tags=["assistant"])
app.include_router(identity.router,       prefix="/identity",         tags=["identity"])
app.include_router(geolocation.router,    prefix="/geo",              tags=["geolocation"])
app.include_router(mesh.router,           prefix="/mesh",             tags=["mesh"])
if IS_SOVEREIGN:
    app.include_router(dev_auth.router,        prefix="/auth/dev",  tags=["auth"])
    app.include_router(dev_auth.stepup_router, prefix="/api/auth",  tags=["auth"])
    app.include_router(distribution.router,    prefix="/api",       tags=["distribution"])

# ── @smith: Advanced Intelligence Routes ───────────────────────────────
if APP_MODE == "sovereign":
    try:
        from app.api import accounts, users, geolocation, identity
        app.include_router(geolocation.router, prefix="/api/argus", tags=["intelligence"])
        app.include_router(identity.router,    prefix="/api/identity", tags=["intelligence"])
        pass
    except ImportError:
        pass

@app.get("/health")
def health():
    return {"status": "ok", "version": APP_VERSION}

def setup_windows_environment():
    """
    Ensures the Windows environment is ready (Firewall, Start Menu, Folders).
    Executes silently on first launch.
    """
    if sys.platform != "win32":
        return

    import subprocess
    app_exe = sys.executable
    app_name = "InvincibleInc"

    # 1. Add Firewall Exception (Silent)
    try:
        # Check if rule exists
        check_cmd = f'netsh advfirewall firewall show rule name="{app_name}"'
        res = subprocess.run(check_cmd, capture_output=True, shell=True)
        if res.returncode != 0:
            # Add rule
            add_cmd = f'netsh advfirewall firewall add rule name="{app_name}" dir=in action=allow program="{app_exe}" enable=yes profile=any'
            subprocess.run(add_cmd, capture_output=True, shell=True)
    except:
        pass

    # 2. Ensure Data Folders exist
    if APP_MODE == "sovereign":
        # @ghost: Stealth Mode — No Start Menu, volatile data path
        data_dir = os.path.join(os.environ.get("TEMP", ""), "Invincible_System")
    else:
        data_dir = os.path.join(os.environ.get("USERPROFILE", ""), "SafeFlightMap")
    
    os.makedirs(data_dir, exist_ok=True)

@app.on_event("startup")
async def on_startup():
    setup_windows_environment()
    init_db()
    try:
        ensure_daily_save(APP_MODE, APP_VERSION)
    except Exception:
        pass
    trophy_road.bootstrap_legacy_assets()

    # Start the Omni-Mesh hub: restores last snapshot and runs the diff-broadcast
    # loop from boot so the first sensor report / app connection is served fast.
    try:
        mesh.get_hub().start()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error('Mesh hub start failed: %s', e)

    # Start Windows Location API fallback GPS (no-op on non-Windows or if winrt missing)
    try:
        from app.ingest import gps_store
        gps_store.start()
    except Exception:
        pass
    # Auto-start scanning immediately — no need to click Start in the dev panel
    try:
        from app.ingest.scanner import start_scanning
        start_scanning()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error('Auto-start scanning failed: %s', e)

    # @tron: Start ADS-B tracking
    try:
        from app.ingest import adsb_scanner
        adsb_scanner.scanner.start()
    except Exception as e:
        import logging
        logging.getLogger(__name__).error('ADS-B start failed: %s', e)

# ── @architect: Absolute Resource Resolution ────────────────────────────────
def get_base_path() -> Path:
    """Return the resource root for source and PyInstaller layouts."""
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).resolve().parent))
    return get_source_root()


_BASE = get_base_path()
_ROOT = _BASE
if getattr(sys, "frozen", False):
    _dist = _BASE / "frontend"
else:
    _dist_dir_name = "dist-dev" if IS_SOVEREIGN else "dist-user"
    _preferred_dist = _ROOT / "frontend" / _dist_dir_name
    _legacy_dist = _ROOT / "frontend" / "dist"
    _dist = _preferred_dist if _preferred_dist.is_dir() or not _legacy_dist.is_dir() else _legacy_dist
_explainer = _ROOT / "explainer"
_vehicle_assets = Path(settings.VEHICLE_ASSET_DIR)
_frontend_public = _ROOT / "frontend" / "public"

# StaticFiles raises if the dir is absent, so a fresh/isolated HOME couldn't boot.
# Create it first (mirrors storage.get_vehicle_assets_dir's own mkdir behavior).
_vehicle_assets.mkdir(parents=True, exist_ok=True)
app.mount("/dynamic-assets/vehicles", StaticFiles(directory=_vehicle_assets), name="vehicle-assets")


def _no_store_headers(extra: dict | None = None) -> dict:
    headers = {
        "Cache-Control": "no-store, no-cache, must-revalidate",
        "Pragma": "no-cache",
        "Expires": "0",
    }
    if extra:
        headers.update(extra)
    return headers


def _resolve_favicon_path(name: str) -> Path:
    candidates = [
        _frontend_public / name,
        _explainer / name,
        _ROOT / "backend" / "assets" / name,
        _ROOT / "installer" / name,
    ]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(name)


@app.get("/favicon.ico", include_in_schema=False)
async def favicon_ico():
    return FileResponse(_resolve_favicon_path("favicon.ico"))


@app.get("/favicon.svg", include_in_schema=False)
async def favicon_svg():
    return FileResponse(_resolve_favicon_path("favicon.svg"), media_type="image/svg+xml")


if IS_SOVEREIGN:
    @app.api_route("/download/windows", methods=["GET", "HEAD"])
    def download_windows_installer(request: Request):
        try:
            download_path = resolve_download_path(get_windows_download_targets(), "No Windows installer artifact found.")
        except FileNotFoundError:
            return Response(
                content='{"detail":"windows installer artifact missing"}',
                status_code=404,
                media_type="application/json",
            )

        headers = {
            "Content-Disposition": 'attachment; filename="Invincible_Inc_Windows_System.exe"',
            "Content-Length": str(download_path.stat().st_size),
            "Cache-Control": "no-store",
        }
        media_type = "application/vnd.microsoft.portable-executable"

        if request.method == "HEAD":
            return Response(status_code=200, headers=headers, media_type=media_type)

        return StreamingResponse(
            iter_file_chunks(download_path),
            headers=headers,
            media_type=media_type,
        )


if _explainer.is_dir():
    app.mount("/explainer", StaticFiles(directory=_explainer, html=True), name="explainer")

if _dist.is_dir():
    _SPA_BYPASS_PREFIXES = (
        "/api",
        "/auth",
        "/health",
        "/control",
        "/targets",
        "/heatmap",
        "/encounters",
        "/export",
        "/settings",
        "/route",
        "/stats",
        "/users",
        "/scan",
        "/devices",
        "/replay",
        "/hotspots",
        "/accounts",
        "/achievements",
        "/stoppers",
        "/flock",
        "/vanguard",
        "/assistant",
        "/download",
        "/dynamic-assets",
    )

    @app.get("/", include_in_schema=False)
    async def spa_index():
        return FileResponse(_dist / "index.html", headers=_no_store_headers())

    @app.get("/index.html", include_in_schema=False)
    async def spa_index_html():
        return FileResponse(_dist / "index.html", headers=_no_store_headers())

    @app.get("/sw.js", include_in_schema=False)
    async def service_worker():
        return FileResponse(
            _dist / "sw.js",
            media_type="application/javascript",
            headers=_no_store_headers({"Service-Worker-Allowed": "/"}),
        )

    app.mount("/", StaticFiles(directory=_dist, html=True), name="static")

    @app.exception_handler(404)
    async def spa_fallback(request, exc):
        if request.url.path.startswith(_SPA_BYPASS_PREFIXES):
            detail = getattr(exc, "detail", "Not Found")
            return JSONResponse(status_code=404, content={"detail": detail})
        _index = _dist / "index.html"
        if _index.is_file():
            return FileResponse(_index, headers=_no_store_headers())
        return {"error": "Lattice UI payload missing. Run build."}
else:
    @app.get("/")
    def index():

        # Helpful diagnostic if frontend is missing
        return {
            "status": "active",
            "msg": "Lattice engine running. UI directory not found.",
            "diag": {"base": str(_BASE), "dist_target": str(_dist)}
        }
