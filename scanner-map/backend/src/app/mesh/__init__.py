"""
Omni-Mesh — the field-sensor fusion subsystem.

WHAT: Hundreds of field devices (Alfa Wi-Fi adapters, SDRs, ESP32 nodes) report
their 802.11 observations to this server. The server fuses those reports into a
single live picture — a mesh of sensor *nodes* and the *detections* they see —
and pushes that picture to the lightweight user apps (the scanner-map PWA) as
small diffs over one WebSocket, so a phone never has to do the heavy lifting.

WHY a dedicated subsystem: ingest rate (hundreds of reports/sec) must be
decoupled from fan-out rate (one coalesced diff/sec to every connected app),
or the server would melt re-broadcasting full state on every report. The hub
(see hub.py) is the single in-memory source of truth that makes that split.
"""

from app.mesh.hub import MeshHub, get_hub  # noqa: F401
