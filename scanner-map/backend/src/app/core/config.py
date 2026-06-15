"""Central configuration for SafeFlight Map / Invincible.Inc"""
import os, secrets

class Settings:
    HOST: str = os.getenv('SFM_HOST', '127.0.0.1')
    PORT: int = int(os.getenv('SFM_PORT', '8742'))

    DB_PATH: str = os.getenv(
        'SFM_DB_PATH',
        os.path.join(os.path.expanduser('~'), 'SafeFlightMap', 'sfm.db')
    )

    _SECRET_FILE: str = os.path.join(os.path.expanduser('~'), 'SafeFlightMap', '.hmac_secret')

    @property
    def HMAC_SECRET(self) -> str:
        os.makedirs(os.path.dirname(self._SECRET_FILE), exist_ok=True)
        if os.path.exists(self._SECRET_FILE):
            with open(self._SECRET_FILE) as f:
                return f.read().strip()
        secret = secrets.token_hex(32)
        with open(self._SECRET_FILE, 'w') as f:
            f.write(secret)
        return secret

    _JWT_SECRET_FILE: str = os.path.join(os.path.expanduser('~'), 'SafeFlightMap', '.jwt_secret')

    @property
    def JWT_SECRET(self) -> str:
        os.makedirs(os.path.dirname(self._JWT_SECRET_FILE), exist_ok=True)
        if os.path.exists(self._JWT_SECRET_FILE):
            with open(self._JWT_SECRET_FILE) as f:
                return f.read().strip()
        secret = secrets.token_urlsafe(48)
        with open(self._JWT_SECRET_FILE, 'w') as f:
            f.write(secret)
        return secret

    # Scanning — runtime-editable via /settings
    WIFI_GAP_TIMEOUT_S:     float = 2.0
    BLE_GAP_TIMEOUT_S:      float = 1.0
    HEAT_CELL_METERS:       float = 100.0
    RSSI_FLOOR:             float = -95.0
    WIFI_SCAN_INTERVAL_S:   float = 3.0
    ALERT_RADIUS_M:         int   = 300
    ALERT_COOLDOWN_S:       int   = 30

    TARGETS_FILE: str = os.getenv(
        'SFM_TARGETS_FILE',
        os.path.join(os.path.expanduser('~'), 'SafeFlightMap', 'targets.json')
    )

    # Directory of dynamically-served vehicle image assets (mounted at
    # /dynamic-assets/vehicles by main.py). Added during Linux server setup
    # (2026-06-12): referenced by main.py + core/storage.py but absent from the
    # committed Settings. See scanner-map/SETUP_NOTES.md.
    VEHICLE_ASSET_DIR: str = os.getenv(
        'SFM_VEHICLE_ASSET_DIR',
        os.path.join(os.path.expanduser('~'), 'SafeFlightMap', 'vehicle-assets')
    )

    OUI_FUN_WATCHER: str = '00:25:DF'
    OUI_FUN_STOPPER: str = 'B4:1E:52'

    # ── Feature thresholds ────────────────────────────────────────────────────
    # Feature 2: Tail detection — how many separate encounters before "keeps appearing" alert
    TAIL_ENCOUNTER_THRESHOLD: int = 3
    # Feature 3: Daily Stopper surge — unique Stoppers in one day before broadcast alert
    STOPPER_SURGE_THRESHOLD: int = 5
    # Feature 4: Hotspot — how many distinct days in 7-day window to promote a cell
    HOTSPOT_MIN_DAYS: int = 3
    # Feature 4: Hotspot proximity alert radius (meters)
    HOTSPOT_PROXIMITY_M: int = 500
    # Feature 4: Hotspot ahead-of-heading projection distance (meters)
    HOTSPOT_AHEAD_M: int = 1000

    # ── GitHub / auto-update ──────────────────────────────────────────────────
    # Set to your actual GitHub repo (e.g. "Invincible-Inc/safeflight") or via
    # the GITHUB_REPO environment variable.  Placeholder disables update checks.
    GITHUB_REPO: str = os.getenv('GITHUB_REPO', 'YOUR_ORG/safeflight')

settings = Settings()
