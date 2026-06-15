#!/usr/bin/env python3
"""
alfa_mesh_reporter.py — native Omni-Mesh field reporter (Linux monitor mode).

Captures live 802.11 straight off an Alfa adapter in monitor mode (via scapy),
channel-hops across the common bands, and POSTs what it hears to the Omni-Mesh
server as /mesh/report batches. No airodump-ng required — this avoids the CSV
round-trip and the driver quirks, and is the reference "reporter" the Omni app
hires to feed the mesh.

Prereqs on the field device:
  - adapter in monitor mode, e.g.:
      sudo ip link set wlx00c0cababe70 down
      sudo iw dev wlx00c0cababe70 set type monitor
      sudo ip link set wlx00c0cababe70 up
  - run as root (raw capture):  sudo .venv/bin/python tools/alfa_mesh_reporter.py \\
        --iface wlx00c0cababe70 --server http://192.168.0.122:8742 --device alfa-pi-07

GPS: --lat/--lon fixed, or --gps-file JSON {lat,lon} re-read each report window.
"""
import os
import csv
import sys
import time
import json
import signal
import argparse
import threading
import subprocess
import urllib.request
import urllib.error
import urllib.parse

from scapy.all import sniff, Dot11, Dot11Beacon, Dot11ProbeResp, Dot11Elt  # noqa: E402

# 2.4GHz (1-11) + common 5GHz channels; the loud ones first.
DEFAULT_CHANNELS = [1, 6, 11, 1, 6, 11, 3, 9, 36, 44, 149, 157, 2, 7, 10]

# Minimal OUI vendor hints (extend freely; the server stores whatever we send).
OUI_HINTS = {
    "00C0CA": "Alfa", "DE4427": "Tesla", "001D0F": "TP-Link",
    "F09FC2": "Ubiquiti", "B827EB": "Raspberry Pi", "3C5AB4": "Google",
}


class Capture:
    """Accumulates observations between report windows, keyed by MAC."""
    def __init__(self):
        self.lock = threading.Lock()
        self.obs = {}  # mac -> observation dict (best rssi wins)

    def add(self, mac, ssid, rssi, chan, kind):
        with self.lock:
            o = self.obs.get(mac)
            if o is None or (rssi is not None and rssi > (o.get("rssi") or -999)):
                self.obs[mac] = {"bssid": mac, "ssid": ssid, "rssi": rssi,
                                 "chan": chan, "type": kind,
                                 "oui_vendor": OUI_HINTS.get(mac.replace(":", "")[:6].upper())}
            elif o is not None and ssid and not o.get("ssid"):
                o["ssid"] = ssid

    def drain(self):
        with self.lock:
            out = list(self.obs.values())
            self.obs.clear()
            return out


def handle_packet(cap):
    def _cb(pkt):
        if not pkt.haslayer(Dot11):
            return
        d11 = pkt.getlayer(Dot11)
        rssi = None
        try:
            rssi = float(pkt.dBm_AntSignal)  # from radiotap, when present
        except Exception:
            rssi = None
        chan = None
        ssid = None
        if pkt.haslayer(Dot11Beacon) or pkt.haslayer(Dot11ProbeResp):
            # AP: BSSID is addr3/addr2; pull SSID + channel from the info elements.
            mac = (d11.addr2 or d11.addr3 or "").upper()
            elt = pkt.getlayer(Dot11Elt)
            while isinstance(elt, Dot11Elt):
                if elt.ID == 0:  # SSID
                    try:
                        ssid = elt.info.decode(errors="ignore") or None
                    except Exception:
                        ssid = None
                elif elt.ID == 3 and elt.info:  # DS Parameter Set = channel
                    chan = elt.info[0]
                elt = elt.payload.getlayer(Dot11Elt)
            if mac:
                cap.add(mac, ssid, rssi, chan, "ap")
        else:
            # Any other frame with a source MAC counts as a client/station sighting.
            mac = (d11.addr2 or "").upper()
            if mac and mac != "FF:FF:FF:FF:FF:FF":
                cap.add(mac, None, rssi, chan, "client")
    return _cb


def channel_hopper(iface, channels, stop_evt):
    i = 0
    while not stop_evt.is_set():
        ch = channels[i % len(channels)]
        subprocess.run(["iw", "dev", iface, "set", "channel", str(ch)],
                       capture_output=True)
        i += 1
        stop_evt.wait(0.4)  # dwell ~400ms per channel


def read_gps(args):
    if args.gps_file and os.path.exists(args.gps_file):
        try:
            with open(args.gps_file) as f:
                g = json.load(f)
            return {"lat": float(g["lat"]), "lon": float(g["lon"])}
        except Exception:
            pass
    if args.lat is not None and args.lon is not None:
        return {"lat": args.lat, "lon": args.lon}
    return None


def post_report(server, token, device, label, gps, observations):
    body = json.dumps({"device_id": device, "label": label, "ts": time.time(),
                       "gps": gps, "observations": observations}).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Mesh-Token"] = token
    req = urllib.request.Request(server.rstrip("/") + "/mesh/report",
                                 data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError) as e:
        return {"error": str(e)}


def _http_get_json(url, token):
    req = urllib.request.Request(url)
    if token:
        req.add_header("X-Mesh-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=6) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError):
        return None


def _http_post_json(url, token, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(),
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("X-Mesh-Token", token)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError) as e:
        return {"error": str(e)}


def try_hire(server, token, gps, observations, hired, hired_by):
    """For each newly-seen AP, ask the server if it's a roadside device (identify
    with fallback=False → null for ordinary Wi-Fi). Real roadside hits get hired as
    a fixed node so they show on the map. Hire each BSSID at most once per run."""
    base = server.rstrip("/")
    hires = []
    for o in observations:
        if o.get("type") != "ap":
            continue
        bssid = (o.get("bssid") or "").upper()
        if not bssid or bssid in hired:
            continue
        ssid = o.get("ssid") or ""
        vendor = o.get("oui_vendor") or ""
        q = urllib.parse.urlencode({"ssid": ssid, "bssid": bssid,
                                    "vendor": vendor, "fallback": "false"})
        ident = _http_get_json(f"{base}/mesh/identify?{q}", token)
        hired.add(bssid)  # don't re-query this BSSID even if it's not roadside
        if not ident or not ident.get("key"):
            continue
        # LEA/surveillance devices (Flock/Axon/Ring/drone/glasses) are TARGETS we
        # track, not infrastructure to enroll as reporters — they get flagged via
        # /mesh/report. Never hire them.
        if (ident.get("device") or {}).get("category") == "surveillance":
            continue
        ack = _http_post_json(f"{base}/mesh/hire", token, {
            "device_id": f"road-{bssid.replace(':', '')}",
            "bssid": bssid, "ssid": ssid or None, "vendor": vendor or None,
            "gps": gps, "hired_by": hired_by, "kind": "roadside",
        })
        if ack and ack.get("ok"):
            hires.append((ack.get("device_label") or ident.get("key"),
                          ack.get("confidence")))
    return hires


def main():
    ap = argparse.ArgumentParser(description="Omni-Mesh native Alfa reporter")
    ap.add_argument("--iface", required=True, help="monitor-mode interface, e.g. wlx00c0cababe70")
    ap.add_argument("--server", default=os.getenv("MESH_SERVER", "http://192.168.0.122:8742"))
    ap.add_argument("--device", default=os.getenv("MESH_DEVICE", f"alfa-{os.uname().nodename}"))
    ap.add_argument("--label", default="alfa field node")
    ap.add_argument("--token", default=os.getenv("MESH_INGEST_TOKEN", ""))
    ap.add_argument("--interval", type=float, default=3.0, help="report window seconds")
    ap.add_argument("--channels", help="comma list to hop (default 2.4+5GHz common)")
    ap.add_argument("--no-hop", action="store_true", help="stay on the current channel")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--gps-file")
    ap.add_argument("--once", action="store_true", help="send one window then exit (for testing)")
    ap.add_argument("--no-hire", action="store_true",
                    help="don't auto-hire roadside devices we drive past")
    args = ap.parse_args()
    hired = set()  # BSSIDs already evaluated for hiring this run

    if os.geteuid() != 0:
        print("[mesh] must run as root for raw capture (use sudo)", file=sys.stderr)

    cap = Capture()
    stop_evt = threading.Event()
    if not args.no_hop:
        chans = [int(c) for c in args.channels.split(",")] if args.channels else DEFAULT_CHANNELS
        threading.Thread(target=channel_hopper, args=(args.iface, chans, stop_evt),
                         daemon=True).start()

    sniffer = threading.Thread(
        target=lambda: sniff(iface=args.iface, prn=handle_packet(cap),
                             store=False, stop_filter=lambda p: stop_evt.is_set()),
        daemon=True)
    sniffer.start()

    def _sig(*_):
        stop_evt.set()
    signal.signal(signal.SIGINT, _sig)
    signal.signal(signal.SIGTERM, _sig)

    print(f"[mesh] reporting {args.iface} -> {args.server} as '{args.device}' "
          f"(hop={'off' if args.no_hop else 'on'}, window={args.interval}s)")
    try:
        while not stop_evt.is_set():
            time.sleep(args.interval)
            obs = cap.drain()
            if not obs:
                print("[mesh] (no frames this window)")
                if args.once:
                    break
                continue
            gps = read_gps(args)
            ack = post_report(args.server, args.token, args.device, args.label,
                              gps, obs)
            if "error" in ack:
                print(f"[mesh] {len(obs)} obs · server unreachable: {ack['error']}")
            else:
                print(f"[mesh] {len(obs)} obs · accepted={ack.get('accepted')} "
                      f"· mesh detections={ack.get('detections')}")
            # Drive-by enrollment: hire any roadside devices we just heard.
            if not args.no_hire and "error" not in ack:
                for label_, conf in try_hire(args.server, args.token, gps, obs,
                                             hired, args.device):
                    print(f"[mesh]   ↳ hired roadside: {label_} (conf {conf})")
            if args.once:
                break
    finally:
        stop_evt.set()


if __name__ == "__main__":
    main()
