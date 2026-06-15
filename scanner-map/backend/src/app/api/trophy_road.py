"""
trophy_road.py — gamification / "trophy road" progression API.

⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
Imported and mounted by app/main.py (router at /api, plus
bootstrap_legacy_assets() called on startup) but never committed to the repo.
This stub exposes a status endpoint and a no-op bootstrap so the backend boots.
Replace with the real implementation. See scanner-map/SETUP_NOTES.md.
"""
import logging

from fastapi import APIRouter

router = APIRouter()
_log = logging.getLogger("trophy_road")


@router.get("/trophy-road/status")
def trophy_road_status():
    return {"status": "placeholder", "implemented": False, "tiers": []}


def bootstrap_legacy_assets() -> None:
    """Migrate/seed legacy trophy assets on startup. Placeholder no-op."""
    _log.info("trophy_road.bootstrap_legacy_assets placeholder — nothing to do")
