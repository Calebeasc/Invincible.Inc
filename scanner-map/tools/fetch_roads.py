#!/usr/bin/env python3
"""
fetch_roads.py — pull an OSM road network for a bounding box (via Overpass) and
write it as GeoJSON LineStrings for the Omni-Mesh road-snapper.

The mesh localizer uses this to (a) snap dead-reckoned LEA positions onto real
roads while a target is in a sensor dead-zone, and (b) reason about junctions.
Drop the output where the hub looks for it — by default
~/SafeFlightMap/mesh_roads.geojson (no env var needed) — then restart the backend.

  python tools/fetch_roads.py --bbox 33.48,-112.16,33.54,-112.10
  python tools/fetch_roads.py --bbox S,W,N,E --out /path/to/mesh_roads.geojson

Keep the bbox to your operating area — a whole-metro export loads slower and the
snapper scans more segments. (It bbox-rejects far segments, so it stays usable,
but tight is better.)
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.parse
import urllib.error

OVERPASS = os.getenv("OVERPASS_URL", "https://overpass-api.de/api/interpreter")
# Drivable ways only (skip footway/cycleway/service-spur noise).
HIGHWAYS = ("motorway|trunk|primary|secondary|tertiary|residential|unclassified|"
            "living_street|motorway_link|trunk_link|primary_link|secondary_link|tertiary_link")


def fetch(south, west, north, east):
    q = (f'[out:json][timeout:180];'
         f'way["highway"~"{HIGHWAYS}"]({south},{west},{north},{east});'
         f'out geom;')
    body = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request(OVERPASS, data=body,
                                 headers={"User-Agent": "omni-mesh-roads/1.0"})
    with urllib.request.urlopen(req, timeout=210) as r:
        return json.loads(r.read())


def to_geojson(osm):
    feats = []
    for el in osm.get("elements", []):
        if el.get("type") != "way" or "geometry" not in el:
            continue
        coords = [[p["lon"], p["lat"]] for p in el["geometry"]]
        if len(coords) < 2:
            continue
        tags = el.get("tags", {})
        feats.append({
            "type": "Feature",
            "properties": {"id": el.get("id"), "highway": tags.get("highway"),
                           "name": tags.get("name"), "oneway": tags.get("oneway")},
            "geometry": {"type": "LineString", "coordinates": coords},
        })
    return {"type": "FeatureCollection", "features": feats}


def main():
    ap = argparse.ArgumentParser(description="OSM roads → GeoJSON for the mesh road-snapper")
    ap.add_argument("--bbox", default="33.48,-112.16,33.54,-112.10",
                    help="south,west,north,east (default: ~6 km around GCU/Phoenix)")
    ap.add_argument("--out", default=os.path.expanduser("~/SafeFlightMap/mesh_roads.geojson"))
    args = ap.parse_args()
    try:
        south, west, north, east = [float(x) for x in args.bbox.split(",")]
    except ValueError:
        print("bbox must be 'south,west,north,east'", file=sys.stderr)
        sys.exit(2)

    print(f"[roads] querying Overpass for bbox {south},{west},{north},{east} …", file=sys.stderr)
    try:
        osm = fetch(south, west, north, east)
    except (urllib.error.URLError, OSError) as e:
        print(f"[roads] Overpass request failed: {e}", file=sys.stderr)
        sys.exit(1)
    gj = to_geojson(osm)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w") as f:
        json.dump(gj, f)
    print(f"[roads] wrote {len(gj['features'])} road segments → {args.out}", file=sys.stderr)
    if not gj["features"]:
        print("[roads] WARNING: 0 segments — check the bbox order (south,west,north,east).",
              file=sys.stderr)


if __name__ == "__main__":
    main()
