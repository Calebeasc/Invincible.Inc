"""
medic.py — hardware/system "medic" diagnostics API.

⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
Imported and mounted by app/main.py (router at /api) but never committed to the
repo. This stub exposes a basic health/diagnostics endpoint so the backend
boots. Replace with the real implementation. See scanner-map/SETUP_NOTES.md.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/medic/status")
def medic_status():
    return {"status": "placeholder", "implemented": False, "diagnostics": []}
