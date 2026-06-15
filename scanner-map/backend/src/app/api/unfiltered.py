"""
unfiltered.py — assistant ("unfiltered") API.

⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
Imported and mounted by app/main.py (router at /assistant) but never committed
to the repo. This stub exposes a status endpoint so the backend boots. The real
version presumably proxies to a local LLM (e.g. the LM Studio server at
http://localhost:1234). Replace with the real implementation.
See scanner-map/SETUP_NOTES.md.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def assistant_status():
    return {"status": "placeholder", "implemented": False, "backend": None}
