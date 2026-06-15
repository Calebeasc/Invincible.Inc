"""
Roadside-device catalog — what the Omni-Mesh "hire" flow enrolls.

Omni-Mesh reporters are FIXED roadside / highway devices that already sense Wi-Fi
or Bluetooth (traffic travel-time sensors, ITS roadside units, smart streetlights,
dynamic message signs, ALPR, smart-city sensor nodes). A user's Alfa adapter
discovers one over the air and "hires" it; this catalog is how we IDENTIFY what was
discovered — which vendor / category it is, what it can sense, and how it would
report — so a hire is grounded in a real device type instead of an anonymous MAC.

Identification is ADAPTIVE: a hire of ANY roadside device gets classified into the
best-fitting type (lights, signs, RSUs, tolling, ALPR, analytics …) by OUI, by
vendor name, or by scoring its SSID against per-type keywords — and if nothing is
recognized it still falls back to a generic roadside type, so every hire is
grounded in *something*. The seed below is a STARTER set of well-documented
commercial roadside sensors; the real, authoritative list is loaded and merged
from an external file when present (see load_external) so Caleb's pushed
`roadside_devices.json` supersedes/extends it.
"""
import os
import json
import logging

log = logging.getLogger("mesh")

# key -> entry. Matchers, best-to-worst confidence:
#   oui_prefixes  : 6-hex uppercase OUI of the device's radio (exact hardware match)
#   vendors       : brand names matched against a resolved (or SSID-borne) vendor
#   keywords      : distinctive substrings scored against the SSID (the adaptive net)
#   ssid_patterns : legacy exact-substring patterns (also fed into keyword scoring)
_SEED = {
    "bt_traveltime": {
        "label": "Bluetooth travel-time sensor", "category": "traffic-monitoring",
        "vendors": ["TrafficCast BlueTOAD", "Post Oak Traffic", "Iteris Acyclica"],
        "form_factor": "pole-mounted enclosure", "power": "AC mains / solar",
        "mounting": "signal pole / mast arm",
        "sensors": ["bluetooth", "wifi"], "bands": ["2.4GHz BT/Wi-Fi"],
        "detection_modes": ["BT inquiry scan", "Wi-Fi probe-request sniff"],
        "mac_anonymization": "hashed/salted MAC re-identification",
        "on_device_processing": "MAC hashing + match on device", "storage": "rolling buffer",
        "backhaul": ["cellular", "fiber"], "apis": ["vendor REST", "MQTT"],
        "sense_radius_m": 120, "hireable": True,
        "oui_prefixes": [], "ssid_patterns": ["bluetoad", "acyclica", "postoak"],
        "keywords": ["bluetoad", "blue toad", "acyclica", "postoak", "post oak",
                     "iteris", "traveltime", "travel time", "travel-time", "journey time"],
    },
    "wifi_analytics_ap": {
        "label": "Roadside Wi-Fi analytics AP", "category": "smart-city",
        "vendors": ["Cisco Meraki", "Purple WiFi", "Cloud4Wi", "Libelium Meshlium"],
        "form_factor": "weatherized AP", "power": "PoE / AC",
        "mounting": "pole / building edge",
        "sensors": ["wifi", "bluetooth"], "bands": ["2.4GHz", "5GHz", "BLE"],
        "detection_modes": ["probe-request capture", "BLE scan", "presence analytics"],
        "mac_anonymization": "rotating-MAC aware, hashed", "on_device_processing": "yes",
        "storage": "local + cloud", "backhaul": ["ethernet", "cellular"],
        "apis": ["Meraki Dashboard API", "CMX/Scanning API"],
        "sense_radius_m": 80, "hireable": True,
        "oui_prefixes": [], "ssid_patterns": ["meshlium", "meraki", "_analytics"],
        "keywords": ["meshlium", "meraki", "libelium", "purple", "cloud4wi",
                     "analytics", "footfall", "presence", "people counter"],
    },
    "smart_streetlight": {
        "label": "Smart streetlight node", "category": "smart-city",
        "vendors": ["Ubicquia", "Itron", "Telensa", "Signify Interact"],
        "form_factor": "NEMA/Zhaga luminaire controller", "power": "luminaire AC",
        "mounting": "streetlight head",
        "sensors": ["wifi", "bluetooth", "environmental"], "bands": ["2.4GHz", "BLE", "sub-GHz mesh"],
        "detection_modes": ["BLE scan", "Wi-Fi presence"],
        "mac_anonymization": "varies by vendor", "on_device_processing": "edge node",
        "storage": "edge buffer", "backhaul": ["cellular", "RF mesh"],
        "apis": ["vendor IoT platform"],
        "sense_radius_m": 60, "hireable": True,
        "oui_prefixes": [], "ssid_patterns": ["ubicell", "telensa", "interact"],
        "keywords": ["streetlight", "street light", "light", "lamp", "luminaire",
                     "lighting", "ubicell", "ubicquia", "itron", "telensa",
                     "interact", "signify", "nema", "zhaga", "pole light"],
    },
    "dms_sign": {
        "label": "Dynamic message / road sign", "category": "traffic-control",
        "vendors": ["Daktronics", "Ver-Mac", "Wanco", "Skyline", "Solar Tech", "ADDCO"],
        "form_factor": "trailer / overhead sign", "power": "solar / AC",
        "mounting": "gantry / trailer / mast",
        "sensors": ["wifi", "bluetooth"], "bands": ["2.4GHz", "cellular"],
        "detection_modes": ["maintenance Wi-Fi", "BT config link"],
        "mac_anonymization": "n/a", "on_device_processing": "sign controller",
        "storage": "controller", "backhaul": ["cellular"],
        "apis": ["NTCIP DMS", "vendor portal"],
        "sense_radius_m": 70, "hireable": True,
        "oui_prefixes": [], "ssid_patterns": ["daktronics", "vermac", "wanco", "dms"],
        "keywords": ["sign", "dms", "vms", "message sign", "variable message",
                     "daktronics", "ver-mac", "vermac", "wanco", "addco", "skyline",
                     "speed sign", "school zone", "beacon", "flashing", "radar sign"],
    },
    "its_rsu": {
        "label": "ITS / V2X roadside unit", "category": "connected-vehicle",
        "vendors": ["Kapsch", "Siemens", "Commsignia", "Cohda Wireless"],
        "form_factor": "RSU enclosure", "power": "AC / cabinet",
        "mounting": "gantry / signal cabinet",
        "sensors": ["DSRC/C-V2X", "wifi", "gnss"], "bands": ["5.9GHz V2X", "2.4GHz"],
        "detection_modes": ["BSM/CV2X reception", "Wi-Fi management"],
        "mac_anonymization": "V2X pseudonym certs", "on_device_processing": "yes",
        "storage": "local", "backhaul": ["fiber", "cellular"],
        "apis": ["NTCIP", "SAE J2735 feeds"],
        "sense_radius_m": 300, "hireable": True,
        "oui_prefixes": [], "ssid_patterns": ["rsu", "v2x", "kapsch", "commsignia"],
        "keywords": ["rsu", "v2x", "dsrc", "cv2x", "c-v2x", "kapsch", "commsignia",
                     "cohda", "roadside unit", "connected vehicle"],
    },
    "tolling_reader": {
        "label": "Tolling / RFID gantry reader", "category": "tolling",
        "vendors": ["Kapsch", "TransCore", "Neology"],
        "form_factor": "gantry-mounted reader", "power": "cabinet AC",
        "mounting": "overhead gantry",
        "sensors": ["RFID", "wifi"], "bands": ["915MHz RFID", "2.4GHz"],
        "detection_modes": ["RFID tag read"], "mac_anonymization": "n/a",
        "on_device_processing": "yes", "storage": "local",
        "backhaul": ["fiber"], "apis": ["vendor toll host"],
        "sense_radius_m": 50, "hireable": True,
        "oui_prefixes": [], "ssid_patterns": ["transcore", "tolltag"],
        "keywords": ["toll", "tolling", "rfid", "transcore", "tolltag", "ezpass",
                     "e-zpass", "sunpass", "fastrak", "neology", "gantry reader"],
    },
    # ALPR / surveillance cameras are already fingerprinted by device_classifier
    # (flock/axon). Mapped here so a "hire" of one is described consistently.
    "alpr_camera": {
        "label": "ALPR / surveillance camera", "category": "surveillance",
        "vendors": ["Flock Safety", "Motorola Vigilant", "Genetec"],
        "form_factor": "pole camera", "power": "solar / AC",
        "mounting": "pole / sign post",
        "sensors": ["camera", "wifi", "lte"], "bands": ["2.4GHz", "LTE"],
        "detection_modes": ["plate OCR", "Wi-Fi beacon"],
        "mac_anonymization": "none", "on_device_processing": "edge ALPR",
        "storage": "cloud", "backhaul": ["cellular"], "apis": ["vendor cloud"],
        "sense_radius_m": 70, "hireable": True,
        "oui_prefixes": ["B41E52", "0025DF"], "ssid_patterns": ["flock", "vigilant"],
        "keywords": ["flock", "vigilant", "alpr", "lpr", "plate", "genetec",
                     "license plate", "surveillance camera"],
    },
}

# Synthesized last-resort type: a hire we couldn't classify is still a roadside
# fixture the user deliberately enrolled — ground it as a generic roadside device
# rather than leaving it anonymous.
_GENERIC = {
    "label": "Roadside device (unclassified)", "category": "roadside",
    "vendors": [], "form_factor": "roadside fixture", "power": "unknown",
    "mounting": "roadside", "sensors": ["wifi"], "bands": ["2.4GHz"],
    "detection_modes": ["Wi-Fi sniff"], "mac_anonymization": "unknown",
    "on_device_processing": "unknown", "storage": "unknown",
    "backhaul": ["unknown"], "apis": [], "sense_radius_m": 80, "hireable": True,
    "oui_prefixes": [], "ssid_patterns": [], "keywords": [],
}

_CATALOG = dict(_SEED)
_EXTERNAL_LOADED = False

# Minimum keyword score (sum of matched-keyword lengths) to trust an SSID guess.
_KEYWORD_MIN_SCORE = 4
# device_classifier keys that map onto a roadside surveillance hire.
_SURVEILLANCE_KEYS = {"flock", "axon", "ring", "drone", "smartglasses"}


def _norm_oui(mac):
    """6-char uppercase OUI from a MAC, or None if it isn't hex-shaped."""
    if not mac:
        return None
    c = mac.upper().replace(":", "").replace("-", "").replace(".", "")
    if len(c) < 6:
        return None
    head = c[:6]
    # Only treat it as an OUI if it's actually hex — device ids like "ALFA-PI"
    # normalize to letters and must not masquerade as a hardware prefix.
    return head if all(ch in "0123456789ABCDEF" for ch in head) else None


def load_external():
    """
    Merge Caleb's authoritative roadside-device file over the seed, if present.
    Looked for at $MESH_ROADSIDE_CATALOG, then ~/Invincible/roadside_devices.json,
    then the Omni repo checkout. Each top-level key is an entry of the same shape;
    later sources win. Safe to call repeatedly.
    """
    global _EXTERNAL_LOADED
    paths = [
        os.getenv("MESH_ROADSIDE_CATALOG", ""),
        os.path.expanduser("~/Invincible/roadside_devices.json"),
        os.path.expanduser("~/Projects/Omni/omnimesh/roadside_devices.json"),
        os.path.expanduser("~/Projects/Omni/backend/src/app/data/roadside_devices.json"),
    ]
    for p in paths:
        if p and os.path.exists(p):
            try:
                with open(p) as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    _CATALOG.update(data)
                    log.warning("roadside catalog: merged %d entries from %s", len(data), p)
                    _EXTERNAL_LOADED = True
            except Exception:
                log.exception("roadside catalog: failed to load %s", p)
    return _EXTERNAL_LOADED


def _entry_keywords(e):
    """Distinctive substrings for an entry: curated keywords + legacy ssid_patterns."""
    kws = set()
    for k in e.get("keywords", []):
        if k:
            kws.add(k.lower())
    for p in e.get("ssid_patterns", []):
        if p:
            kws.add(p.lower())
    return kws


def _score(text, kws):
    """Sum of matched-keyword lengths — longer keyword = more specific = more weight."""
    return sum(len(kw) for kw in kws if kw and kw in text)


def _decorate(key, e, matched_on, confidence):
    """Return a COPY of the entry annotated with how/how-confidently it matched,
    so the shared seed dicts are never mutated."""
    d = dict(e)
    d["key"] = key
    d["matched_on"] = matched_on
    d["confidence"] = round(float(confidence), 2)
    return d


def _surveillance_bridge(ssid, bssid):
    """Reuse the app's Wi-Fi device classifier so a hire of known surveillance gear
    (Flock/Axon/Ring/drone/glasses) is recognized even without a catalog entry."""
    try:
        from app.core.device_classifier import classify_wifi
        key, label, _color = classify_wifi(ssid, bssid)
    except Exception:
        return None
    if key not in _SURVEILLANCE_KEYS:
        return None
    if key == "flock" and "alpr_camera" in _CATALOG:
        return "alpr_camera", _decorate("alpr_camera", _CATALOG["alpr_camera"], "classifier", 0.9)
    e = {"label": label, "category": "surveillance", "vendors": [],
         "sensors": ["wifi"], "sense_radius_m": 70, "hireable": True,
         "oui_prefixes": [], "ssid_patterns": [], "keywords": []}
    return key, _decorate(key, e, "classifier", 0.8)


def identify(ssid, bssid, vendor=None, fallback=True):
    """
    Adaptively identify a discovered device against the catalog.

    Order, highest confidence first:
      1. OUI prefix — exact hardware-vendor match on the radio's MAC.
      2. Vendor name — a resolved OUI vendor (or vendor-bearing SSID) vs each
         entry's `vendors` list.
      3. Keyword scoring — score the SSID/vendor text against every entry's
         distinctive keywords; the best-scoring type wins (this is what makes it
         work for lights, signs, RSUs, tolling … not just one device).
      4. Surveillance bridge — defer to device_classifier for known LEA gear.
      5. Generic roadside fallback (when fallback=True) — a hire is still grounded
         in *a* type rather than an anonymous MAC.

    Returns (key, entry-copy-with-confidence) or (None, None) when nothing matches
    and fallback is False (used by the discover-preview endpoint).
    """
    # 1. OUI exact
    oui = _norm_oui(bssid)
    if oui:
        for key, e in _CATALOG.items():
            if oui in [o.upper() for o in e.get("oui_prefixes", [])]:
                return key, _decorate(key, e, "oui", 0.95)

    text = " ".join(t for t in (ssid or "", vendor or "") if t).lower().strip()

    # 2. vendor-name match (strong signal when we have a resolved vendor)
    if vendor:
        vlc = vendor.lower().strip()
        for key, e in _CATALOG.items():
            for v in e.get("vendors", []):
                vl = v.lower()
                if vl and (vl in vlc or vlc in vl):
                    return key, _decorate(key, e, "vendor", 0.85)

    # 3. keyword scoring across all entries
    if text:
        best_key, best_e, best_s = None, None, 0
        for key, e in _CATALOG.items():
            s = _score(text, _entry_keywords(e))
            if s > best_s:
                best_key, best_e, best_s = key, e, s
        if best_e is not None and best_s >= _KEYWORD_MIN_SCORE:
            conf = min(0.4 + best_s / 40.0, 0.8)
            return best_key, _decorate(best_key, best_e, "keyword", conf)

    # 4. surveillance bridge (Flock/Axon/Ring/drone/glasses via device_classifier)
    bridged = _surveillance_bridge(ssid, bssid)
    if bridged:
        return bridged

    # 5. generic roadside fallback
    if fallback:
        return "roadside_generic", _decorate("roadside_generic", _GENERIC, "fallback", 0.2)
    return None, None


def catalog():
    """The full catalog (seed + any merged external entries) for the UI/API."""
    return _CATALOG
