"""
Wire schemas for Omni-Mesh field-device reports.

Kept deliberately lenient: field sensors run on flaky links and varied firmware,
so a malformed observation should be dropped, not 422 the whole batch. Validation
that matters (coords in range, rssi numeric) happens in the hub on ingest; these
models just give a typed, documented shape for /mesh/report.
"""
from typing import List, Optional
from pydantic import BaseModel, Field


class Observation(BaseModel):
    """One 802.11 thing a sensor heard in this report window."""
    bssid: str = Field(..., description="MAC of the AP or client (the detection key)")
    ssid: Optional[str] = Field(None, description="Network name, APs only")
    rssi: Optional[float] = Field(None, description="Signal strength in dBm (e.g. -57)")
    chan: Optional[int] = Field(None, description="Wi-Fi channel")
    type: Optional[str] = Field("ap", description="'ap' or 'client'")
    oui_vendor: Optional[str] = Field(None, description="Resolved OUI vendor, if known")


class MeshReport(BaseModel):
    """A single field device's batch of observations for one window."""
    device_id: str = Field(..., description="Stable sensor id (e.g. alfa-pi-07)")
    ts: Optional[float] = Field(None, description="Sensor unix time; server stamps if absent")
    gps: Optional[dict] = Field(None, description="{lat, lon} of the sensor at report time")
    label: Optional[str] = Field(None, description="Human label for the sensor")
    observations: List[Observation] = Field(default_factory=list)
