"""
adsb_scanner.py — ADS-B aircraft tracking ingest.

⚠️ AUTO-GENERATED PLACEHOLDER (created during Linux server setup, 2026-06-12).
Imported by app/main.py (`/adsb/status` route + startup) but never committed
to the repo. This stub keeps the route alive and returns an empty aircraft
list until a real ADS-B source (e.g. dump1090 / an SDR feed) is wired in.
See scanner-map/SETUP_NOTES.md.
"""
import logging

_log = logging.getLogger("adsb")


def get_active_aircraft() -> list[dict]:
    """Return currently tracked aircraft. Placeholder returns none."""
    return []


class _Scanner:
    """No-op scanner; real version would connect to a dump1090/SDR feed."""

    def __init__(self) -> None:
        self.running = False

    def start(self) -> None:
        if self.running:
            return
        self.running = True
        _log.info("adsb_scanner placeholder started (no real ADS-B source configured)")

    def stop(self) -> None:
        self.running = False


scanner = _Scanner()
