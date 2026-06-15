#!/usr/bin/env python3
"""
alfa_mesh_feeder.py — reference Omni-Mesh field sensor.

Run this on each field device (Raspberry Pi / laptop) that has an Alfa adapter in
monitor mode. It turns the adapter's Wi-Fi observations into /mesh/report POSTs to
the Omni-Mesh server, which fuses every sensor into the live map the apps show.

Two input modes:

  --airodump PREFIX   Tail an airodump-ng CSV (the standard Alfa capture). Start the
                      capture separately, e.g.:
                        sudo airmon-ng start wlan1
                        sudo airodump-ng -w /tmp/mesh --output-format csv --write-interval 2 wlan1mon
                      then:  alfa_mesh_feeder.py --server http://192.168.0.122:8742 \\
                               --device alfa-pi-07 --airodump /tmp/mesh

  --sim               No hardware — invent plausible nearby Wi-Fi for wiring tests.

GPS: pass a fixed --lat/--lon, or --gps-file pointing at a JSON file your GPS
daemon updates ({"lat":..,"lon":..}); the feeder re-reads it each cycle.

The server schema is intentionally simple, so any sensor stack (tshark, kismet,
ESP32) can target /mesh/report with the same JSON — see backend app/mesh/schemas.py.
"""
import os
import csv
import json
import time
import random
import argparse
import urllib.request
import urllib.error


def post_report(server, token, device, label, gps, observations):
    body = json.dumps({
        "device_id": device, "label": label, "ts": time.time(),
        "gps": gps, "observations": observations,
    }).encode()
    headers = {"Content-Type": "application/json"}
    if token:
        headers["X-Mesh-Token"] = token
    req = urllib.request.Request(server.rstrip("/") + "/mesh/report",
                                 data=body, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            return json.loads(r.read())
    except (urllib.error.URLError, OSError) as e:
        # A sensor must keep running through server/network blips, not crash.
        return {"error": str(e)}


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


def parse_airodump(prefix):
    """
    Parse the most recent airodump-ng CSV (`<prefix>-NN.csv`). It has two sections:
    access points then clients ('Station MAC'). We emit both as observations.
    """
    paths = sorted([p for p in (
        f"{prefix}-{i:02d}.csv" for i in range(1, 40)) if os.path.exists(p)])
    if not paths:
        if os.path.exists(f"{prefix}.csv"):
            paths = [f"{prefix}.csv"]
        else:
            return []
    path = paths[-1]
    obs, section = [], "ap"
    try:
        with open(path, newline="", errors="ignore") as f:
            for row in csv.reader(f):
                if not row:
                    continue
                head = row[0].strip()
                if head == "BSSID":
                    section = "ap"; continue
                if head == "Station MAC":
                    section = "client"; continue
                mac = head
                if len(mac) != 17 or mac.count(":") != 5:
                    continue
                try:
                    if section == "ap":
                        # BSSID, First, Last, channel, Speed, Privacy, Cipher, Auth, Power, #beacons,...,ESSID
                        rssi = float(row[8]) if row[8].strip() not in ("", "-1") else None
                        chan = int(row[3]) if row[3].strip().lstrip("-").isdigit() else None
                        ssid = row[13].strip() if len(row) > 13 else None
                        obs.append({"bssid": mac, "ssid": ssid or None, "rssi": rssi,
                                    "chan": chan, "type": "ap"})
                    else:
                        # Station MAC, First, Last, Power, # packets, BSSID, Probed ESSIDs
                        rssi = float(row[3]) if row[3].strip() not in ("", "-1") else None
                        obs.append({"bssid": mac, "rssi": rssi, "type": "client"})
                except (ValueError, IndexError):
                    continue
    except OSError:
        return []
    return obs


def sim_observations():
    macs = [":".join(f"{random.randint(0,255):02X}" for _ in range(6)) for _ in range(14)]
    ssids = ["HOME-5G", "xfinitywifi", "ATT-2401", "", "Pixel_hotspot", "SETUP-A8", None]
    return [{"bssid": m, "ssid": random.choice(ssids),
             "rssi": -30 - random.randint(0, 60),
             "chan": random.choice([1, 6, 11, 36, 149]),
             "type": random.choice(["ap", "ap", "client"])}
            for m in macs if random.random() < 0.75]


def main():
    ap = argparse.ArgumentParser(description="Omni-Mesh reference field feeder")
    ap.add_argument("--server", default=os.getenv("MESH_SERVER", "http://192.168.0.122:8742"))
    ap.add_argument("--device", default=os.getenv("MESH_DEVICE", f"alfa-{os.uname().nodename}"))
    ap.add_argument("--label", default="alfa field node")
    ap.add_argument("--token", default=os.getenv("MESH_INGEST_TOKEN", ""))
    ap.add_argument("--interval", type=float, default=3.0)
    ap.add_argument("--airodump", help="airodump-ng CSV prefix to tail")
    ap.add_argument("--sim", action="store_true", help="synthesize observations (no hardware)")
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--gps-file", help="JSON file with live {lat,lon}")
    args = ap.parse_args()

    if not args.airodump and not args.sim:
        ap.error("give --airodump PREFIX or --sim")

    print(f"[mesh] feeding {args.server} as '{args.device}' "
          f"({'sim' if args.sim else 'airodump:' + args.airodump}) every {args.interval}s")
    while True:
        obs = sim_observations() if args.sim else parse_airodump(args.airodump)
        gps = read_gps(args)
        if obs:
            ack = post_report(args.server, args.token, args.device, args.label, gps, obs)
            if "error" in ack:
                print(f"[mesh] {len(obs)} obs · server unreachable: {ack['error']}")
            else:
                print(f"[mesh] {len(obs)} obs · accepted={ack.get('accepted')} "
                      f"mesh detections={ack.get('detections')}")
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
