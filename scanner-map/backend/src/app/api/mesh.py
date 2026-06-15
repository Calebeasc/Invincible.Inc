"""
Omni-Mesh API surface (mounted at /mesh).

  POST /mesh/report   field sensors push Wi-Fi observations here (the load path)
  WS   /mesh/ws       user apps subscribe; get one snapshot then live diffs
  GET  /mesh/snapshot full state as JSON (non-WS clients, debugging, SW fallback)
  GET  /mesh/stats    counters
  GET  /mesh/sensor   a browser "sim sensor" page for testing without an Alfa rig

Auth: ingest is open on the LAN by default (these are your own field devices).
Set MESH_INGEST_TOKEN to require an `X-Mesh-Token` header on /mesh/report.
"""
import os
import json
import logging
import aiohttp # Added for Section 1: Unified Hiring Endpoint - communication with Omni RAM-injection engine
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Header, HTTPException
from fastapi.responses import HTMLResponse

from app.mesh.hub import get_hub
from app.mesh.schemas import MeshReport

router = APIRouter()
log = logging.getLogger("mesh")

_INGEST_TOKEN = os.getenv("MESH_INGEST_TOKEN", "")


@router.post("/report")
async def mesh_report(report: MeshReport, x_mesh_token: str = Header(default="")):
    if _INGEST_TOKEN and x_mesh_token != _INGEST_TOKEN:
        raise HTTPException(status_code=401, detail="bad mesh token")
    hub = get_hub()
    hub.start()  # idempotent — guarantees the flush loop exists even before any WS
    return hub.ingest(report)


@router.post("/hire")
async def mesh_hire(body: dict, x_mesh_token: str = Header(default="")):
    """
    Enroll a roadside device as a mesh reporter. Called by a user's Alfa-equipped
    app when it drives past one: body { device_id, label?, gps:{lat,lon}, hired_by?,
    kind?, bssid?, ssid?, vendor? }. Pass the discovered device's radio fingerprint
    (bssid/ssid/vendor) so the catalog can adaptively identify what kind of roadside
    device it is — light, sign, RSU, tolling reader, ALPR, analytics AP — falling
    back to a generic roadside type. The device then reports via /mesh/report.
    """
    if _INGEST_TOKEN and x_mesh_token != _INGEST_TOKEN:
        raise HTTPException(status_code=401, detail="bad mesh token")
    hub = get_hub()
    hub.start()

    # ── Section 1: Unified Hiring Endpoint (Exploit Path) ───────────────────
    # Added for CYB-400: If exploit_required is set, we attempt a RAM injection 
    # on the target process before enrolling it in the mesh. This bridges the 
    # mesh registry with the Omni RAM-injection lab module.
    exploit_ok = True
    exploit_data = {}
    
    if body.get("exploit_required"):
        # We call the Omni RAM-injection engine (localhost:8802) to trigger the breach.
        # This mirrors the real-world "hiring" flow where a device is compromised
        # via memory manipulation before being onboarded.
        async with aiohttp.ClientSession() as session:
            try:
                payload = {
                    "pid": body.get("target_pid", 0),
                    "address": body.get("target_address", "0x0"),
                    "value": 0 # Default to UNLOCK for hiring
                }
                async with session.post("http://127.0.0.1:8802/api/ram-injection/inject", json=payload) as resp:
                    if resp.status == 200:
                        exploit_data = await resp.json()
                        log.warning(f"Mesh: roadside device {body.get('device_id')} HIRED via RAM injection (SUCCESS)")
                    else:
                        exploit_ok = False
                        log.error(f"Mesh: RAM injection failed for {body.get('device_id')} (status {resp.status})")
            except Exception as e:
                exploit_ok = False
                log.error(f"Mesh: Exploit bridge error: {e}")

    if not exploit_ok:
        raise HTTPException(status_code=500, detail="Hiring failed: RAM injection exploit failed or timed out.")

    # " result = hub.hire(
    # "     device_id=body.get("device_id"),
    # "     label=body.get("label"),
    # "     gps=body.get("gps"),
    # "     hired_by=body.get("hired_by"),
    # "     kind=body.get("kind", "roadside"),
    # "     bssid=body.get("bssid"),
    # "     ssid=body.get("ssid"),
    # "     vendor=body.get("vendor") or body.get("oui_vendor"),
    # " ) "
    # Original logic above is preserved in comments per user instruction.
    
    result = hub.hire(
        device_id=body.get("device_id"),
        label=body.get("label"),
        gps=body.get("gps"),
        hired_by=body.get("hired_by"),
        kind=body.get("kind", "roadside"),
        bssid=body.get("bssid"),
        ssid=body.get("ssid"),
        vendor=body.get("vendor") or body.get("oui_vendor"),
    )
    
    if exploit_data:
        # Attach proof of exploit to the hiring result for the Arion UI
        result["exploit_proof"] = exploit_data

    # Hand the freshly-hired reporter its marching orders: where and how to report.
    if result.get("ok"):
        result["enrollment"] = _enrollment_packet(result.get("device_id"))
    return result


def _lea_targets() -> dict:
    """LEA/surveillance scan signatures, from the shared classifier (single source)."""
    try:
        from app.core.device_classifier import lea_target_signatures
        return lea_target_signatures()
    except Exception:
        return {}


def _enrollment_packet(device_id: str) -> dict:
    return {
        "device_id": device_id,
        "report_endpoint": "/mesh/report",
        "method": "POST",
        "report_interval_s": float(os.getenv("MESH_REPORT_INTERVAL_S", "3")),
        "auth": {"required": bool(_INGEST_TOKEN), "header": "X-Mesh-Token"},
        "priority": {"flagged_immediate": True, "match_on": ["oui_prefix", "ssid_pattern"]},
        "scan": {
            "radio": "wifi",
            "mode": "monitor",
            "channels": [1, 6, 11, 1, 6, 11, 3, 9, 36, 44, 149, 157],
            "dwell_ms": 400,
            "rssi_select": "max_per_mac_per_window",
        },
        "lea_targets": _lea_targets(),
        "lea_targets_endpoint": "/mesh/targets",
        "observation_schema": {
            "bssid": "string",
            "ssid": "string|null",
            "rssi": "int",
            "chan": "int",
            "type": "ap|client",
            "oui_vendor": "string|null",
        },
        "report_schema": {
            "device_id": "string",
            "gps": {"lat": "float", "lon": "float"},
            "observations": "observation[]",
        },
    }


@router.get("/stats")
async def mesh_stats():
    return get_hub().stats()


@router.get("/snapshot")
async def mesh_snapshot():
    return get_hub().snapshot_frame()


@router.get("/flagged")
async def mesh_flagged():
    """Only the flagged surveillance/LEA detections — the feed the Arion bridge
    consumes and the quickest way to see what the mesh currently considers LEA."""
    hub = get_hub()
    return {"detections": hub.flagged_view(), "stats": hub.stats()}


@router.get("/targets")
async def mesh_targets():
    """The LEA/surveillance scan signatures (OUI prefixes + SSID patterns per
    category) a reporter should identify and report ASAP. Reporters fetch this on
    startup so they always match the server's current classification."""
    return {"surveillance_cats": ["ring", "axon", "flock", "drone", "smartglasses"],
            "lea_targets": _lea_targets()}


@router.get("/diag")
async def mesh_diag(n: int = 200):
    """Tail of the rolling mesh diagnostic log (hires, new LEA flags, stats
    heartbeats) so the system can be tuned from real field data."""
    hub = get_hub()
    return {"stats": hub.stats(), "events": hub.read_diag(n)}


@router.get("/catalog")
async def mesh_catalog():
    """The roadside-device catalog the Alfa 'hire' flow matches against — used by
    the app to show what kind of device a discovered candidate is."""
    from app.mesh import roadside_catalog
    roadside_catalog.load_external()
    return {"devices": roadside_catalog.catalog()}


@router.get("/identify")
async def mesh_identify(ssid: str = "", bssid: str = "", vendor: str = ""):
    """Preview the adaptive classification of a single discovered device (for the
    Alfa tab's discover view). Returns null when nothing is recognized — unlike the
    hire path, the preview does NOT force a generic fallback."""
    from app.mesh import roadside_catalog
    roadside_catalog.load_external()
    key, entry = roadside_catalog.identify(
        ssid or None, bssid or None, vendor or None, fallback=False)
    return {"key": key, "device": entry}


@router.websocket("/ws")
async def mesh_ws(ws: WebSocket):
    await ws.accept()
    hub = get_hub()
    hub.start()
    await hub.connect(ws)
    try:
        while True:
            # Clients aren't required to send anything; this keeps the socket open
            # and lets us notice a clean disconnect promptly.
            await ws.receive_text()
    except WebSocketDisconnect:
        pass
    except Exception:
        log.debug("mesh ws closed", exc_info=True)
    finally:
        hub.disconnect(ws)


# ── Browser "sim sensor" — lets a phone/laptop act as a sensor for testing ─────
SENSOR_PAGE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1">
<title>Omni-Mesh Sim Sensor</title>
<style>
 *{box-sizing:border-box;margin:0;padding:0}
 body{background:#0b0f14;color:#c8d8e8;font-family:'Courier New',monospace;
   min-height:100vh;display:flex;flex-direction:column;align-items:center;
   justify-content:center;padding:24px;gap:16px}
 h1{font-size:16px;color:#00d4ff;letter-spacing:.15em;text-transform:uppercase}
 .s{font-size:13px;padding:10px 16px;border:1px solid #1e2d3d;border-radius:4px;min-width:260px;text-align:center}
 .s.ok{border-color:#00e676;color:#00e676}.s.err{border-color:#ff4d6d;color:#ff4d6d}
 button{background:#00d4ff;color:#001018;border:0;border-radius:6px;padding:12px 20px;
   font:700 14px 'Courier New';letter-spacing:.1em;cursor:pointer}
 .t{font-size:11px;color:#3a5a76;max-width:280px;text-align:center;line-height:1.6}
</style></head><body>
 <h1>Omni-Mesh · Sim Sensor</h1>
 <div id="s" class="s">Idle</div>
 <button id="b">Start reporting</button>
 <div class="t">Simulates an Alfa field node: invents nearby Wi-Fi MACs around your
   GPS and POSTs them to /mesh/report every 3s. For wiring/testing only.</div>
<script>
 const dev='sim-'+Math.random().toString(36).slice(2,7);
 let on=false, gps=null;
 navigator.geolocation && navigator.geolocation.watchPosition(
   p=>{gps={lat:p.coords.latitude,lon:p.coords.longitude}},()=>{},{enableHighAccuracy:true});
 const macs=Array.from({length:14},()=>Array.from({length:6},
   ()=>('0'+Math.floor(Math.random()*256).toString(16)).slice(-2)).join(':').toUpperCase());
 const ssids=['HOME-5G','xfinitywifi','ATT-2401','TG-Guest','','Pixel_hotspot','SETUP-A8'];
 function set(c,m){const e=document.getElementById('s');e.className='s '+c;e.textContent=m}
 async function tick(){
   if(!on)return;
   const g=gps||{lat:33.4484+Math.random()*.01,lon:-112.074+Math.random()*.01};
   const obs=macs.filter(()=>Math.random()<.7).map(m=>({bssid:m,
     ssid:ssids[Math.floor(Math.random()*ssids.length)]||null,
     rssi:-30-Math.floor(Math.random()*60),chan:[1,6,11,36,149][Math.floor(Math.random()*5)],
     type:Math.random()<.7?'ap':'client'}));
   try{const r=await fetch('/mesh/report',{method:'POST',headers:{'Content-Type':'application/json'},
     body:JSON.stringify({device_id:dev,gps:g,label:'sim sensor',observations:obs})});
     const j=await r.json();set('ok','● reporting · '+obs.length+' seen · '+(j.detections||0)+' mesh');
   }catch(e){set('err','✕ server unreachable — retrying')}
 }
 document.getElementById('b').onclick=()=>{on=!on;
   document.getElementById('b').textContent=on?'Stop':'Start reporting';
   if(on)set('ok','starting…')};
 setInterval(tick,3000);
</script></body></html>"""


@router.get("/sensor", response_class=HTMLResponse)
async def mesh_sensor_page():
    return HTMLResponse(content=SENSOR_PAGE)
