"""
storage.py — application data-directory helpers.

⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
This module was imported by the codebase but never committed to the repo
(`app.core.storage` was missing from every branch). It is a minimal,
cross-platform reconstruction so the backend boots. Replace with the real
implementation when available. See scanner-map/SETUP_NOTES.md.
"""
import os
from pathlib import Path

from app.core.config import settings


def get_app_data_dir() -> Path:
    """Root directory for all persistent app data (DB, secrets, saves)."""
    # Derive from the configured DB path so everything lives together.
    root = Path(settings.DB_PATH).parent
    root.mkdir(parents=True, exist_ok=True)
    return root


def get_vehicle_assets_dir() -> Path:
    """Directory holding dynamically served vehicle image assets."""
    # Honor the same env override main.py uses (settings.VEHICLE_ASSET_DIR).
    configured = getattr(settings, "VEHICLE_ASSET_DIR", None)
    d = Path(configured) if configured else get_app_data_dir() / "vehicle-assets"
    d.mkdir(parents=True, exist_ok=True)
    return d
