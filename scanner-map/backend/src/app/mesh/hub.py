"""
MeshHub — the single in-memory source of truth for Omni-Mesh.

DESIGN (why it's shaped this way):
  * Ingest is O(observations) and lock-free. uvicorn here runs one event loop in
    one process, so every coroutine that touches hub state runs to its next await
    without another coroutine interleaving mid-mutation. We never await while
    mutating a dict, so plain dict ops are safe — no asyncio.Lock on the hot path
    (locks would serialize hundreds of reports/sec for no benefit).
  * Fan-out is decoupled from ingest. Reports just mark keys dirty. A single
    background task (`_flush_loop`) wakes ~once/sec, builds ONE diff frame from the
    dirty set, and sends it to every connected app. So 500 reports/sec collapse
    into 1 broadcast/sec per client instead of 500 — this is the whole reason the
    server can carry the load the phones can't.
  * State is bounded. Detections are capped and TTL-evicted, so memory can't grow
    without limit no matter how many strangers' MACs wander past the sensors.
  * State survives restarts. A periodic snapshot to disk is reloaded on boot, so
    opening the app right after a server bounce still shows the last-known mesh.

Frame protocol (JSON text over /mesh/ws):
  {"t":"snapshot", nodes:[...], detections:[...], stats:{...}, server_ts}
  {"t":"diff", nodes_upsert:[...], nodes_remove:[...],
               det_upsert:[...], det_remove:[...], stats:{...}, server_ts}
"""
import os
import json
import time
import asyncio
import logging

log = logging.getLogger("mesh")

# Surveillance / law-enforcement device categories (from the shared classifier).
# Detections whose Wi-Fi fingerprint lands in one of these are "flagged" — the
# Flock ALPR cameras, Axon body cams, Ring, drones, smart glasses that the
# roaming reporters exist to surface live on the operator map.
THREAT_CATS = {"ring", "axon", "flock", "drone", "smartglasses"}

try:
    from app.core.device_classifier import classify_wifi
except Exception:  # pragma: no cover - classifier is always present in this app
    def classify_wifi(ssid, bssid):
        return ("wifi_ap", "Wi-Fi Access Points", "#8e8e93")

# ── Tunables (env-overridable so an operator can size for their fleet) ─────────
NODE_TTL_S      = float(os.getenv("MESH_NODE_TTL_S", "120"))      # sensor offline after this silence
DET_TTL_S       = float(os.getenv("MESH_DET_TTL_S", "900"))       # drop a detection unseen this long
MAX_DETECTIONS  = int(os.getenv("MESH_MAX_DETECTIONS", "50000"))  # hard memory cap
FLUSH_INTERVAL  = float(os.getenv("MESH_FLUSH_INTERVAL", "1.0"))  # seconds between broadcast frames
MAX_DIFF_DETS   = int(os.getenv("MESH_MAX_DIFF_DETS", "2500"))    # cap per-frame detection upserts
EVICT_EVERY_S   = float(os.getenv("MESH_EVICT_EVERY_S", "5.0"))   # how often to sweep for stale entries
SNAPSHOT_EVERY_S = float(os.getenv("MESH_SNAPSHOT_EVERY_S", "30"))
SNAPSHOT_MAX    = int(os.getenv("MESH_SNAPSHOT_MAX", "8000"))     # detections persisted (most-recent)

# ── Diagnostics (rolling JSONL the operator/AI can read to tune the system) ─────
DIAG_ENABLED    = os.getenv("MESH_DIAG", "1") not in ("0", "false", "no", "")
DIAG_EVERY_S    = float(os.getenv("MESH_DIAG_EVERY_S", "30"))     # stats heartbeat cadence
DIAG_MAX_BYTES  = int(os.getenv("MESH_DIAG_MAX_BYTES", str(16 * 1024 * 1024)))  # rotate at 16MB

# ── Localization / tracking (flagged LEA targets only) ────────────────────────
LOC_WINDOW_S    = float(os.getenv("MESH_LOC_WINDOW_S", "12"))     # sighting freshness for triangulation — short, so a moving target coasts soon after it leaves the mesh (a 45s-old fix is ~600m wrong at speed)
LOC_MIN_MOVE_M  = float(os.getenv("MESH_LOC_MIN_MOVE_M", "8"))    # min move to add a track point
LOC_TRACK_MAX   = int(os.getenv("MESH_LOC_TRACK_MAX", "30"))      # track points kept per target
LOC_MAX_SIGHT   = int(os.getenv("MESH_LOC_MAX_SIGHT", "16"))      # sensors kept per target

# ── Dead-zone coasting / pull-over inference (flagged moving targets) ──────────
COAST_MIN_SPEED = float(os.getenv("MESH_COAST_MIN_SPEED", "2.0"))  # m/s (~4.5mph); below this = parked → hold
COAST_MAX_S     = float(os.getenv("MESH_COAST_MAX_S", "30"))       # dead-reckon at most this long w/o re-acquire, then hold last-known
MESH_ROADS_GEOJSON = os.getenv("MESH_ROADS_GEOJSON", "")           # optional OSM road export → enables road-snapping


def _haversine_m(lat1, lon1, lat2, lon2):
    """Great-circle distance in meters between two lat/lon points."""
    from math import radians, sin, cos, sqrt, atan2
    r = 6371000.0
    p1, p2 = radians(lat1), radians(lat2)
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(p1) * cos(p2) * sin(dlon / 2) ** 2
    return r * 2 * atan2(sqrt(a), sqrt(1 - a))


def _bearing_deg(lat1, lon1, lat2, lon2):
    """Initial compass bearing (0=N,90=E) from point 1 to point 2."""
    from math import radians, sin, cos, atan2, degrees
    p1, p2 = radians(lat1), radians(lat2)
    dlon = radians(lon2 - lon1)
    y = sin(dlon) * cos(p2)
    x = cos(p1) * sin(p2) - sin(p1) * cos(p2) * cos(dlon)
    return (degrees(atan2(y, x)) + 360) % 360


def _state_dir():
    try:
        from app.core import storage
        return str(storage.get_app_data_dir())
    except Exception:
        return os.path.join(os.path.expanduser("~"), "SafeFlightMap")


def _project(lat, lon, heading_deg, dist_m):
    """Move dist_m metres from (lat,lon) along a compass heading (great-circle)."""
    from math import radians, degrees, sin, cos, asin, atan2
    R = 6371000.0
    brg = radians(heading_deg)
    dr = dist_m / R
    la1, lo1 = radians(lat), radians(lon)
    la2 = asin(sin(la1) * cos(dr) + cos(la1) * sin(dr) * cos(brg))
    lo2 = lo1 + atan2(sin(brg) * sin(dr) * cos(la1), cos(dr) - sin(la1) * sin(la2))
    return degrees(la2), degrees(lo2)


def _nearest_on_polyline(lat, lon, poly):
    """Nearest point on a polyline [(lat,lon), …] to (lat,lon) via a local
    equirectangular projection. Returns (lat, lon, dist_m) or None."""
    from math import radians, cos
    if not poly or len(poly) < 2:
        return None
    mx = 111320.0 * cos(radians(lat))  # metres per degree lon at this latitude
    my = 110540.0                       # metres per degree lat
    px, py = lon * mx, lat * my
    best = None
    for (alat, alon), (blat, blon) in zip(poly, poly[1:]):
        ax, ay, bx, by = alon * mx, alat * my, blon * mx, blat * my
        dx, dy = bx - ax, by - ay
        seg2 = dx * dx + dy * dy
        t = 0.0 if seg2 <= 1e-9 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg2))
        cx, cy = ax + t * dx, ay + t * dy
        dist = ((px - cx) ** 2 + (py - cy) ** 2) ** 0.5
        if best is None or dist < best[2]:
            best = (cy / my, cx / mx, dist)
    return best


def _snapshot_path():
    # Lives alongside the app's other state; storage.get_app_data_dir() is the
    # reconstructed placeholder that returns ~/SafeFlightMap on this server.
    return os.path.join(_state_dir(), "mesh_snapshot.json")


def _diag_path():
    # Rolling, machine-readable log of what the mesh is doing — hires, new LEA
    # flags, and periodic stats. Stable path so it can be tailed/analyzed offline.
    return os.path.join(_state_dir(), "mesh_diag.jsonl")


class MeshHub:
    def __init__(self):
        self.nodes = {}        # device_id -> node dict
        self.detections = {}   # bssid(mac) -> detection dict
        self._clients = set()  # set[WebSocket]
        self._task = None      # flush-loop task (strong ref so it isn't GC'd)

        # Coalesced change-set since the last flush (keys, not events).
        self._dirty_nodes = set()
        self._dirty_dets = set()
        self._removed_nodes = set()
        self._removed_dets = set()
        self._flagged = set()  # macs classified as surveillance/LEA (for fast counts)

        self._reports = 0
        self._obs = 0
        self._started = False
        self._last_evict = 0.0
        self._last_snapshot = 0.0
        self._last_diag = 0.0
        self._hires = 0      # lifetime hire count (for stats/diag)

    # ── lifecycle ─────────────────────────────────────────────────────────────
    def start(self):
        """Idempotent: load last snapshot and spin up the flush loop once."""
        if self._started:
            return
        self._started = True
        try:
            from app.mesh import roadside_catalog
            roadside_catalog.load_external()  # merge Caleb's roadside_devices.json if present
        except Exception:
            pass
        self._load_snapshot()
        # create_task (not get_event_loop().create_task) and keep a strong ref so
        # the flush task can't be garbage-collected; callers are always async here.
        self._task = asyncio.create_task(self._flush_loop())
        log.warning("MeshHub started (nodes=%d detections=%d)", len(self.nodes), len(self.detections))

    # ── ingest (hot path) ─────────────────────────────────────────────────────
    def ingest(self, report) -> dict:
        """
        Fold one MeshReport into hub state. Cheap and synchronous: only marks keys
        dirty; the flush loop does the broadcasting. Returns small ack counters.
        """
        now = time.time()
        dev = str(getattr(report, "device_id", "") or "unknown")[:64]
        gps = getattr(report, "gps", None) or {}
        try:
            slat = float(gps.get("lat")) if gps.get("lat") is not None else None
            slon = float(gps.get("lon")) if gps.get("lon") is not None else None
        except (TypeError, ValueError):
            slat = slon = None

        obs = getattr(report, "observations", []) or []
        # Node bookkeeping (rate via simple EWMA on inter-report gap).
        node = self.nodes.get(dev)
        if node is None:
            node = {"device_id": dev, "first_seen": now, "reports": 0,
                    "rate_rpm": 0.0, "label": getattr(report, "label", None)}
            self.nodes[dev] = node
        else:
            gap = max(now - node.get("last_seen", now), 1e-3)
            inst_rpm = 60.0 / gap
            node["rate_rpm"] = round(0.7 * node.get("rate_rpm", 0.0) + 0.3 * inst_rpm, 1)
        node["last_seen"] = now
        node["reports"] = node.get("reports", 0) + 1
        if slat is not None:
            node["lat"], node["lon"] = slat, slon
        if getattr(report, "label", None):
            node["label"] = report.label
        node["seen_now"] = len(obs)
        self._dirty_nodes.add(dev)
        self._removed_nodes.discard(dev)

        kept = 0
        for o in obs:
            mac = (getattr(o, "bssid", None) or "").upper().strip()
            if not mac:
                continue
            try:
                rssi = float(o.rssi) if getattr(o, "rssi", None) is not None else None
            except (TypeError, ValueError):
                rssi = None
            d = self.detections.get(mac)
            if d is None:
                if len(self.detections) >= MAX_DETECTIONS:
                    self._evict_one()
                d = {"mac": mac, "first_seen": now, "hits": 0,
                     "sensors": [], "best_rssi": rssi, "lat": slat, "lon": slon}
                self.detections[mac] = d
            d["last_seen"] = now
            d["hits"] = d.get("hits", 0) + 1
            d["last_rssi"] = rssi
            if getattr(o, "ssid", None):
                d["ssid"] = o.ssid
            if getattr(o, "chan", None) is not None:
                d["chan"] = o.chan
            if getattr(o, "type", None):
                d["type"] = o.type
            if getattr(o, "oui_vendor", None):
                d["vendor"] = o.oui_vendor
            # Classify once on first sight and again only if the SSID newly
            # appears (SSID can sharpen a generic OUI match) — cheap, not per-hit.
            if "cat" not in d or (d.get("ssid") and d["ssid"] != d.get("_ssid_seen")):
                cat, clabel, ccolor = classify_wifi(d.get("ssid"), mac)
                d["cat"], d["cat_label"], d["cat_color"] = cat, clabel, ccolor
                d["_ssid_seen"] = d.get("ssid")
                if cat in THREAT_CATS:
                    if mac not in self._flagged:  # log only the first time it lights up
                        self._diag("flag", mac=mac, cat=cat, label=clabel,
                                   ssid=d.get("ssid"), vendor=d.get("vendor"),
                                   rssi=d.get("best_rssi"), lat=d.get("lat"),
                                   lon=d.get("lon"), via=dev)
                    d["threat"] = True
                    self._flagged.add(mac)
                else:
                    d["threat"] = False
                    self._flagged.discard(mac)
            # For flagged LEA targets, remember WHERE each reporting device is and
            # HOW LOUD it heard this target — that's the raw material the flush-loop
            # localizer trilaterates into an estimated position + speed + heading.
            if d.get("threat") and slat is not None and rssi is not None:
                sights = d.setdefault("sightings", {})
                sights[dev] = {"lat": slat, "lon": slon, "rssi": rssi, "ts": now}
                if len(sights) > LOC_MAX_SIGHT:
                    # With hundreds of reporters hearing one target, keep the LOUDEST
                    # (closest) sensors — they give the tightest fix. A stale loud
                    # sighting is harmless: the localizer ignores it past LOC_WINDOW_S.
                    weakest = min(sights, key=lambda k: sights[k]["rssi"])
                    sights.pop(weakest, None)
            # Best-heard sensor wins the position estimate: the sensor that hears a
            # MAC loudest is closest to it, so its GPS is our cheap fix for the mark.
            if rssi is not None and (d.get("best_rssi") is None or rssi > d["best_rssi"]):
                d["best_rssi"] = rssi
                if slat is not None:
                    d["lat"], d["lon"] = slat, slon
            if dev not in d["sensors"]:
                d["sensors"].append(dev)
                if len(d["sensors"]) > 12:
                    d["sensors"] = d["sensors"][-12:]
            self._dirty_dets.add(mac)
            self._removed_dets.discard(mac)
            kept += 1

        self._reports += 1
        self._obs += kept
        return {"ok": True, "device_id": dev, "accepted": kept,
                "nodes": len(self.nodes), "detections": len(self.detections)}

    def hire(self, device_id, label=None, gps=None, hired_by=None, kind="roadside",
             bssid=None, ssid=None, vendor=None) -> dict:
        """
        Enroll a roadside device as an Omni-Mesh reporter node. This is what a
        user's Alfa adapter does when it drives past one: it registers the fixed
        device (a light, sign, roadside sensor) into the mesh with its location,
        so it shows on the map immediately and its later /mesh/report detections
        attach to it. Pass the discovered radio fingerprint (bssid/ssid/vendor) so
        the catalog can adaptively identify the device type — works for any roadside
        device, not one specific model. Idempotent — re-hiring refreshes it.
        """
        now = time.time()
        dev = str(device_id or "")[:64]
        if not dev:
            return {"ok": False, "error": "device_id required"}
        gps = gps if isinstance(gps, dict) else {}
        node = self.nodes.get(dev) or {"device_id": dev, "first_seen": now,
                                        "reports": 0, "rate_rpm": 0.0}
        node["hired"] = True
        node["kind"] = kind
        node["hired_by"] = hired_by
        node["hired_ts"] = node.get("hired_ts", now)
        # Remember the discovered fingerprint so identify() has something to match
        # on now and on any later re-hire (a node otherwise carries no ssid/bssid).
        # Fall back to anything ingest already learned about this MAC.
        if bssid:
            node["bssid"] = bssid
        if ssid:
            node["ssid"] = ssid
        if vendor:
            node["vendor"] = vendor
        elif node.get("bssid") and not node.get("vendor"):
            seen = self.detections.get(node["bssid"].upper())
            if seen and seen.get("vendor"):
                node["vendor"] = seen["vendor"]
        # Adaptively identify what kind of roadside device this is from its
        # fingerprint, so the hire is grounded in a real device type (vendor, what
        # it can sense, range). Matches on the discovered AP's bssid/ssid/vendor —
        # NOT device_id, which is just a sensor label and never an OUI. identify()
        # always returns a best-fit (down to a generic roadside type) so this works
        # for lights, signs, RSUs, tolling — any roadside device, not one model.
        try:
            from app.mesh import roadside_catalog
            ck, entry = roadside_catalog.identify(
                node.get("ssid"), node.get("bssid"), node.get("vendor"))
            if entry:
                node["device_type"] = ck
                node["device_label"] = entry.get("label")
                node["device_category"] = entry.get("category")
                node["device_confidence"] = entry.get("confidence")
                node["matched_on"] = entry.get("matched_on")
                node["sense_radius_m"] = entry.get("sense_radius_m")
                node["sensor_modalities"] = entry.get("sensors")
                if not label:
                    node["label"] = entry.get("label")
        except Exception:
            pass
        node["last_seen"] = node.get("last_seen", now)
        if label:
            node["label"] = label
        try:
            if gps.get("lat") is not None:
                node["lat"] = float(gps["lat"])
                node["lon"] = float(gps["lon"])
        except (TypeError, ValueError):
            pass
        self.nodes[dev] = node
        self._dirty_nodes.add(dev)
        self._removed_nodes.discard(dev)
        self._hires += 1
        self._diag("hire", device_id=dev, bssid=node.get("bssid"), ssid=node.get("ssid"),
                   vendor=node.get("vendor"), device_type=node.get("device_type"),
                   device_label=node.get("device_label"),
                   confidence=node.get("device_confidence"), matched_on=node.get("matched_on"),
                   lat=node.get("lat"), lon=node.get("lon"), hired_by=hired_by)
        return {"ok": True, "device_id": dev, "hired": True,
                "device_type": node.get("device_type"), "device_label": node.get("device_label"),
                "confidence": node.get("device_confidence"), "matched_on": node.get("matched_on"),
                "nodes": len(self.nodes)}

    def _localize(self, now):
        """
        Live multi-sensor localization for flagged LEA targets, with dead-zone
        dead-reckoning and pull-over inference. Runs once per flush tick over the
        (small) flagged set, so it stays off the ingest hot path.

        Three states per target:
        • LIVE — ≥1 hired device hears it now → RSSI-weighted centroid (a louder
          sensor is closer, weight ~10x/20 dB; several sensors triangulate). Track,
          speed and heading are updated from successive fixes.
        • COASTING — no device hears it (it drove into a gap between mesh devices)
          but it was moving → project the last live fix forward along its heading at
          its last speed, so the marker keeps moving through the dead zone instead of
          freezing. Snapped to the road when a road network is loaded.
        • LAST-KNOWN — it was crawling/stopped, or it has been dark longer than
          COAST_MAX_S and never re-appeared at a downstream device → it likely pulled
          over; hold the marker at the last place a sensor actually heard it.
        """
        for mac in list(self._flagged):
            d = self.detections.get(mac)
            if not d:
                continue
            sights = d.get("sightings") or {}
            fresh = [s for s in sights.values()
                     if now - s.get("ts", 0) <= LOC_WINDOW_S and s.get("lat") is not None]

            if fresh:
                # ── LIVE: triangulate from the sensors hearing it now ───────────
                wsum = elat = elon = 0.0
                for s in fresh:
                    w = 10 ** (s["rssi"] / 20.0)  # amplitude weight; relative only
                    wsum += w
                    elat += w * s["lat"]
                    elon += w * s["lon"]
                if wsum <= 0:
                    continue
                est_lat, est_lon = elat / wsum, elon / wsum
                d["est_lat"], d["est_lon"], d["loc_n"] = est_lat, est_lon, len(fresh)
                d["last_fix_ts"] = now
                d["track_status"], d["est_src"] = "live", "sensors"
                for k in ("coast_base_lat", "coast_base_lon", "coast_base_ts", "coast_dist_m"):
                    d.pop(k, None)

                track = d.get("track") or []
                if not track or _haversine_m(track[-1][1], track[-1][2], est_lat, est_lon) >= LOC_MIN_MOVE_M:
                    track.append([round(now, 1), est_lat, est_lon])
                    if len(track) > LOC_TRACK_MAX:
                        track = track[-LOC_TRACK_MAX:]
                    d["track"] = track
                if len(track) >= 2:
                    t0, la0, lo0 = track[-2]
                    t1, la1, lo1 = track[-1]
                    dt = max(t1 - t0, 1e-3)
                    inst = _haversine_m(la0, lo0, la1, lo1) / dt
                    d["speed_mps"] = round(0.5 * d.get("speed_mps", inst) + 0.5 * inst, 2)
                    d["heading_deg"] = round(_bearing_deg(la0, lo0, la1, lo1), 1)
                self._dirty_dets.add(mac)
                continue

            # ── No sensor hears it: COAST or hold LAST-KNOWN ───────────────────
            if d.get("est_lat") is None or d.get("last_fix_ts") is None:
                continue  # never had a real fix to project from
            gap = now - d["last_fix_ts"]
            speed = d.get("speed_mps") or 0.0
            heading = d.get("heading_deg")

            if speed < COAST_MIN_SPEED or heading is None or gap > COAST_MAX_S:
                # Pulled over / coasted too long without re-acquire → hold at the
                # last place a sensor actually heard it (revert any projection).
                if d.get("track_status") != "last_known":
                    base_lat = d.get("coast_base_lat", d["est_lat"])
                    base_lon = d.get("coast_base_lon", d["est_lon"])
                    d["est_lat"], d["est_lon"] = base_lat, base_lon
                    d["track_status"], d["est_src"] = "last_known", "last_known"
                    reason = ("slow" if speed < COAST_MIN_SPEED
                              else "no_heading" if heading is None else "coast_timeout")
                    self._diag("coast_stop", mac=mac, reason=reason, gap=round(gap, 1),
                               lat=base_lat, lon=base_lon, last_speed=speed)
                    self._dirty_dets.add(mac)
                continue

            # COASTING: dead-reckon forward from the last live fix.
            if d.get("track_status") != "coasting":
                d["coast_base_lat"], d["coast_base_lon"] = d["est_lat"], d["est_lon"]
                d["coast_base_ts"] = d["last_fix_ts"]
                self._diag("coast_start", mac=mac, lat=d["est_lat"], lon=d["est_lon"],
                           speed=speed, heading=heading)
            dist = speed * (now - d["coast_base_ts"])
            plat, plon = _project(d["coast_base_lat"], d["coast_base_lon"], heading, dist)
            plat, plon, snapped = self._snap_to_road(plat, plon, heading)
            d["est_lat"], d["est_lon"] = plat, plon
            d["track_status"] = "coasting"
            d["est_src"] = "road_dead_reckon" if snapped else "dead_reckon"
            d["coast_dist_m"] = round(dist, 1)
            self._dirty_dets.add(mac)

    def _snap_to_road(self, lat, lon, heading):
        """Snap a dead-reckoned point onto the road network, when one is loaded.

        Returns (lat, lon, snapped?). With MESH_ROADS_GEOJSON pointed at an OSM road
        export for the operating area, this is where we'd project the point onto the
        nearest road centerline and advance along its geometry (and read branch count
        at the next junction to decide between 'kept going' vs 'pulled over'). Without
        road data we keep the straight-line heading projection — still live, just not
        road-true."""
        roads = self._roads()
        if not roads:
            return lat, lon, False
        pad = 0.0006  # ~65 m: cheap bbox reject so we only do the math near the point
        best = None
        for seg in roads:
            mnla, mnlo, mxla, mxlo = seg["bb"]
            if lat < mnla - pad or lat > mxla + pad or lon < mnlo - pad or lon > mxlo + pad:
                continue
            p = _nearest_on_polyline(lat, lon, seg["poly"])
            if p and (best is None or p[2] < best[2]):
                best = p
        if best and best[2] <= 40.0:   # within 40 m of a road → snap to it
            return best[0], best[1], True
        return lat, lon, False

    def _roads(self):
        """Lazy-load + cache the optional road network. Each segment carries a
        bbox for fast spatial rejection. Source: MESH_ROADS_GEOJSON, else
        <state_dir>/mesh_roads.geojson (drop a file there, no env var needed).
        Generate one with tools/fetch_roads.py."""
        if getattr(self, "_roads_cache", "unset") != "unset":
            return self._roads_cache
        self._roads_cache = None
        path = MESH_ROADS_GEOJSON or os.path.join(_state_dir(), "mesh_roads.geojson")
        if not os.path.exists(path):
            return None
        try:
            with open(path) as f:
                gj = json.load(f)
            segs = []

            def _add(coords):
                poly = [(c[1], c[0]) for c in coords if isinstance(c, (list, tuple)) and len(c) >= 2]
                if len(poly) >= 2:
                    las = [p[0] for p in poly]
                    los = [p[1] for p in poly]
                    segs.append({"poly": poly, "bb": (min(las), min(los), max(las), max(los))})

            for feat in gj.get("features", []):
                geom = feat.get("geometry") or {}
                t = geom.get("type")
                if t == "LineString":
                    _add(geom.get("coordinates") or [])
                elif t == "MultiLineString":
                    for line in geom.get("coordinates") or []:
                        _add(line)
            self._roads_cache = segs or None
            log.warning("mesh: loaded %d road segments from %s", len(segs), path)
        except Exception:
            log.exception("mesh: failed to load roads %s", path)
        return self._roads_cache

    def _evict_one(self):
        """Make room: drop the single oldest-seen detection (LRU by last_seen)."""
        if not self.detections:
            return
        oldest = min(self.detections.values(), key=lambda d: d.get("last_seen", 0))
        mac = oldest["mac"]
        self.detections.pop(mac, None)
        self._dirty_dets.discard(mac)
        self._flagged.discard(mac)
        self._removed_dets.add(mac)

    # ── projection helpers ────────────────────────────────────────────────────
    @staticmethod
    def _node_view(n):
        return {"device_id": n["device_id"], "lat": n.get("lat"), "lon": n.get("lon"),
                "last_seen": round(n.get("last_seen", 0), 1), "reports": n.get("reports", 0),
                "rate_rpm": n.get("rate_rpm", 0.0), "seen_now": n.get("seen_now", 0),
                "label": n.get("label"), "hired": n.get("hired", False),
                "hired_by": n.get("hired_by"), "kind": n.get("kind", "sensor"),
                "device_type": n.get("device_type"), "device_label": n.get("device_label"),
                "device_category": n.get("device_category"),
                "device_confidence": n.get("device_confidence"),
                "matched_on": n.get("matched_on"),
                "sense_radius_m": n.get("sense_radius_m")}

    @staticmethod
    def _det_view(d):
        return {"mac": d["mac"], "lat": d.get("lat"), "lon": d.get("lon"),
                "ssid": d.get("ssid"), "type": d.get("type", "ap"),
                "rssi": d.get("best_rssi"), "last_rssi": d.get("last_rssi"),
                "chan": d.get("chan"), "vendor": d.get("vendor"),
                "cat": d.get("cat"), "cat_label": d.get("cat_label"),
                "cat_color": d.get("cat_color"), "threat": d.get("threat", False),
                "hits": d.get("hits", 0), "sensors": len(d.get("sensors", [])),
                "last_seen": round(d.get("last_seen", 0), 1),
                # Multi-sensor estimate (flagged targets): triangulated position,
                # how many devices located it, recent path, speed (m/s) + heading.
                "est_lat": d.get("est_lat"), "est_lon": d.get("est_lon"),
                "loc_n": d.get("loc_n"), "speed_mps": d.get("speed_mps"),
                "heading_deg": d.get("heading_deg"), "track": d.get("track"),
                # Live-tracking state: live | coasting | last_known, how the current
                # estimate was derived, and how far it's been dead-reckoned.
                "track_status": d.get("track_status"), "est_src": d.get("est_src"),
                "coast_dist_m": d.get("coast_dist_m")}

    def stats(self):
        now = time.time()
        online = sum(1 for n in self.nodes.values() if now - n.get("last_seen", 0) <= NODE_TTL_S)
        return {"nodes": len(self.nodes), "nodes_online": online,
                "detections": len(self.detections), "clients": len(self._clients),
                "flagged": len(self._flagged), "hires": self._hires,
                "reports_total": self._reports, "obs_total": self._obs,
                "server_ts": round(now, 1)}

    def snapshot_frame(self):
        return {"t": "snapshot",
                "nodes": [self._node_view(n) for n in self.nodes.values()],
                "detections": [self._det_view(d) for d in self.detections.values()],
                "stats": self.stats(), "server_ts": round(time.time(), 1)}

    def flagged_view(self):
        """Just the flagged surveillance/LEA detections — the feed the Arion bridge
        consumes (and a cheap thing to eyeball). Each carries its best position,
        triangulated estimate when available, category, label and confidence."""
        out = []
        for mac in self._flagged:
            d = self.detections.get(mac)
            if d:
                out.append(self._det_view(d))
        return out

    # ── diagnostics ────────────────────────────────────────────────────────────
    def _diag(self, event, **fields):
        """Append one JSON line to the rolling mesh diagnostic log. Never raises —
        diagnostics must not affect ingest. Rotates at DIAG_MAX_BYTES."""
        if not DIAG_ENABLED:
            return
        try:
            path = _diag_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            try:
                if os.path.getsize(path) > DIAG_MAX_BYTES:
                    os.replace(path, path + ".1")  # keep one previous generation
            except FileNotFoundError:
                pass
            rec = {"ts": round(time.time(), 2), "event": event}
            rec.update(fields)
            with open(path, "a") as f:
                f.write(json.dumps(rec, default=str) + "\n")
        except Exception:
            pass

    @staticmethod
    def read_diag(limit=200):
        """Tail of the diagnostic log as a list of dicts (newest last)."""
        path = _diag_path()
        try:
            with open(path) as f:
                lines = f.readlines()[-int(limit):]
        except FileNotFoundError:
            return []
        out = []
        for ln in lines:
            try:
                out.append(json.loads(ln))
            except Exception:
                continue
        return out

    # ── websocket registry ────────────────────────────────────────────────────
    async def connect(self, ws):
        # Send the full snapshot BEFORE adding to _clients. If we added first, the
        # flush loop could deliver a diff to this socket during the snapshot await
        # — arriving before the snapshot, and (because the flush clears the change
        # sets) carrying deltas the snapshot didn't yet include, permanently
        # diverging this client. Snapshot-then-register means the client may at
        # worst miss the in-flight ~1s diff window, which the next diff supersedes.
        await ws.send_text(json.dumps(self.snapshot_frame()))
        self._clients.add(ws)

    def disconnect(self, ws):
        self._clients.discard(ws)

    # ── flush / eviction / persistence loop ───────────────────────────────────
    async def _flush_loop(self):
        while True:
            try:
                await asyncio.sleep(FLUSH_INTERVAL)
                now = time.time()
                if now - self._last_evict >= EVICT_EVERY_S:
                    self._evict_stale(now)
                    self._last_evict = now
                self._localize(now)
                await self._broadcast_diff()
                if now - self._last_snapshot >= SNAPSHOT_EVERY_S:
                    self._save_snapshot()
                    self._last_snapshot = now
                if now - self._last_diag >= DIAG_EVERY_S:
                    self._diag("stats", **self.stats())
                    self._last_diag = now
            except asyncio.CancelledError:
                raise
            except Exception:
                log.exception("mesh flush loop error")

    def _evict_stale(self, now):
        for dev, n in list(self.nodes.items()):
            # Hired roadside devices are enrolled assets — keep them on the map even
            # when quiet; they just show 'stale'. Only auto-drop unhired sensors.
            if n.get("hired"):
                continue
            # Nodes go 'offline' (still shown) at NODE_TTL; only fully drop them
            # after a long silence so a flapping sensor doesn't vanish/reappear.
            if now - n.get("last_seen", 0) > NODE_TTL_S * 10:
                self.nodes.pop(dev, None)
                self._dirty_nodes.discard(dev)
                self._removed_nodes.add(dev)
        for mac, d in list(self.detections.items()):
            if now - d.get("last_seen", 0) > DET_TTL_S:
                self.detections.pop(mac, None)
                self._dirty_dets.discard(mac)
                self._flagged.discard(mac)
                self._removed_dets.add(mac)

    async def _broadcast_diff(self):
        if not self._clients:
            # No listeners — still drain change-sets so they don't grow unbounded.
            self._dirty_nodes.clear(); self._dirty_dets.clear()
            self._removed_nodes.clear(); self._removed_dets.clear()
            return
        if not (self._dirty_nodes or self._dirty_dets
                or self._removed_nodes or self._removed_dets):
            return

        det_keys = list(self._dirty_dets)[:MAX_DIFF_DETS]
        frame = {
            "t": "diff",
            "nodes_upsert": [self._node_view(self.nodes[d]) for d in self._dirty_nodes if d in self.nodes],
            "nodes_remove": list(self._removed_nodes),
            "det_upsert": [self._det_view(self.detections[m]) for m in det_keys if m in self.detections],
            "det_remove": list(self._removed_dets),
            "stats": self.stats(),
            "server_ts": round(time.time(), 1),
        }
        # Keep any overflow dirty for the next frame instead of dropping it.
        self._dirty_dets = set(list(self._dirty_dets)[MAX_DIFF_DETS:])
        self._dirty_nodes.clear()
        self._removed_nodes.clear()
        self._removed_dets.clear()

        payload = json.dumps(frame)
        dead = []
        for ws in list(self._clients):
            try:
                await ws.send_text(payload)
            except Exception:
                # A slow/broken app must never stall the hub — drop and move on.
                dead.append(ws)
        for ws in dead:
            self._clients.discard(ws)

    # ── persistence ───────────────────────────────────────────────────────────
    def _save_snapshot(self):
        try:
            # Persist most-recent detections only; full fleet of nodes is small.
            dets = sorted(self.detections.values(), key=lambda d: d.get("last_seen", 0),
                          reverse=True)[:SNAPSHOT_MAX]
            blob = {"saved_ts": time.time(),
                    "nodes": list(self.nodes.values()),
                    "detections": dets}
            path = _snapshot_path()
            os.makedirs(os.path.dirname(path), exist_ok=True)
            tmp = path + ".tmp"
            with open(tmp, "w") as f:
                json.dump(blob, f)
            os.replace(tmp, path)
        except Exception:
            log.exception("mesh snapshot save failed")

    def _load_snapshot(self):
        try:
            path = _snapshot_path()
            if not os.path.exists(path):
                return
            with open(path) as f:
                blob = json.load(f)
            for n in blob.get("nodes", []):
                if n.get("device_id"):
                    self.nodes[n["device_id"]] = n
            # Honor the memory cap on load too (a hand-edited/corrupt snapshot must
            # not be able to blow past MAX_DETECTIONS), and coerce the one field
            # ingest mutates in place so a bad shape can't crash the hot path.
            dets = blob.get("detections", [])
            dets.sort(key=lambda d: d.get("last_seen", 0), reverse=True)
            for d in dets[:MAX_DETECTIONS]:
                if not d.get("mac"):
                    continue
                if not isinstance(d.get("sensors"), list):
                    d["sensors"] = []
                self.detections[d["mac"]] = d
                if d.get("threat"):
                    self._flagged.add(d["mac"])
            log.warning("mesh snapshot restored: %d nodes, %d detections",
                        len(self.nodes), len(self.detections))
        except Exception:
            log.exception("mesh snapshot load failed")


_HUB = None


def get_hub() -> "MeshHub":
    global _HUB
    if _HUB is None:
        _HUB = MeshHub()
    return _HUB
