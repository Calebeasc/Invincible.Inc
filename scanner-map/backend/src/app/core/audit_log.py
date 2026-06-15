"""
audit_log.py — developer-action audit trail.

⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
Imported by app/api/distribution.py but never committed to the repo. This
minimal version appends structured JSON lines to an audit log file so the
backend boots and dev actions are still recorded. Replace with the real
implementation when available. See scanner-map/SETUP_NOTES.md.
"""
import json
import logging
import time
from typing import Any, Mapping

from app.core.storage import get_app_data_dir

_log = logging.getLogger("audit")


def log_dev_action(
    action: str,
    subject: str = "",
    details: Mapping[str, Any] | None = None,
    ip: str = "",
) -> None:
    """Record a developer/operator action to the audit log (best-effort)."""
    entry = {
        "ts": time.time(),
        "action": action,
        "subject": subject,
        "ip": ip,
        "details": dict(details or {}),
    }
    try:
        path = get_app_data_dir() / "audit.log"
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry) + "\n")
    except Exception:  # never let auditing break a request
        _log.info("audit %s", entry)
