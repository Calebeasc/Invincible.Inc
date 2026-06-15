"""
Device type classification for BLE and WiFi signals.

Classifies observed devices into human-readable categories using:
  - Specific high-priority OUI lookups (checked first — exact manufacturer match)
  - BLE device name patterns
  - BLE service UUID profiles
  - BLE manufacturer company IDs
  - WiFi SSID patterns
  - WiFi BSSID OUI prefixes (first 3 octets of MAC)

Returns (device_type_key, display_label, hex_color).
"""

# ── Device type registry ──────────────────────────────────────────────────────
# Each entry: key → (label, color, default_enabled)

DEVICE_TYPES: dict[str, tuple[str, str, bool]] = {
    # ── Surveillance & law enforcement (shown first — high operational priority) ──
    'ring':         ('Ring Cameras',            '#FF8C00', True),
    'axon':         ('Axon Body Cameras',       '#007AFF', True),
    'flock':        ('Flock Safety / ALPR',     '#FF2D55', True),
    'drone':        ('Drones',                  '#5AC8FA', True),
    'smartglasses': ('Smart Glasses',           '#AF52DE', True),
    # ── Consumer devices ──────────────────────────────────────────────────────
    'phone':      ('Phones',               '#00d4ff', True),
    'tablet':     ('Tablets',              '#64d2ff', True),
    'laptop':     ('Laptops & Computers',  '#5ac8fa', True),
    'headphones': ('Headphones & Earbuds', '#bf5af2', True),
    'speaker':    ('Bluetooth Speakers',   '#ff9f0a', True),
    'tv':         ('Smart TVs',            '#ff6b35', True),
    'streaming':  ('Streaming Devices',    '#ff453a', True),
    'gaming':     ('Game Consoles',        '#30d158', True),
    'smartwatch': ('Smartwatches',         '#ffd60a', True),
    'smarthome':  ('Smart Home',           '#4cd964', False),
    'car':        ('Vehicle Systems',      '#5856d6', True),
    'wifi_ap':    ('Wi-Fi Access Points',  '#8e8e93', True),
    'unknown':    ('Unknown Devices',      '#636366', False),
}

# Convenience lookup: key → label
TYPE_LABELS = {k: v[0] for k, v in DEVICE_TYPES.items()}
TYPE_COLORS = {k: v[1] for k, v in DEVICE_TYPES.items()}
TYPE_DEFAULTS = {k: v[2] for k, v in DEVICE_TYPES.items()}


# ── High-priority specific OUI table ─────────────────────────────────────────
# Checked FIRST in both classify_ble() and classify_wifi(), before any name or
# pattern matching.  Format: 'XXXXXX' (uppercase, no separators) → device_type_key

_SPECIFIC_OUIS: dict[str, str] = {
    # ── Ring (doorbell / security cameras) ──────────────────────────────────
    '187F88': 'ring', '242BD6': 'ring', '343EA4': 'ring',
    '54E019': 'ring', '5C475E': 'ring', '649A63': 'ring',
    '90486C': 'ring', '9C7613': 'ring', 'AC9FC3': 'ring',
    'C4DBAD': 'ring', 'CC3BFB': 'ring',

    # ── Axon (body cameras / law enforcement) ───────────────────────────────
    '0025DF': 'axon',

    # ── Flock Safety (ALPR / surveillance cameras) ──────────────────────────
    'B41E52': 'flock',

    # ── DJI drones ───────────────────────────────────────────────────────────
    '0C9AE6': 'drone', '8C5823': 'drone', '04A85A': 'drone',
    '58B858': 'drone', 'E47A2C': 'drone', '60601F': 'drone',
    '481CB9': 'drone', '34D262': 'drone',

    # ── Parrot drones ────────────────────────────────────────────────────────
    '00121C': 'drone', '00267E': 'drone', '9003B7': 'drone',
    '903AE6': 'drone', 'A0143D': 'drone',

    # ── Skydio drones ────────────────────────────────────────────────────────
    '381D14': 'drone',

    # ── Meta / Ray-Ban Smart Glasses ─────────────────────────────────────────
    '7C2A9E': 'smartglasses', 'CC660A': 'smartglasses', 'F40343': 'smartglasses',
    '5CE91E': 'smartglasses', '985949': 'smartglasses',
}


def _oui_key(mac: str | None) -> str | None:
    """Normalize a MAC address to a 6-char uppercase OUI key, e.g. 'B41E52'."""
    if not mac:
        return None
    cleaned = mac.upper().replace(':', '').replace('-', '').replace('.', '')
    return cleaned[:6] if len(cleaned) >= 6 else None


# Surveillance / law-enforcement device categories — the things field reporters
# exist to surface. A detection classified into one of these is "flagged" LEA.
SURVEILLANCE_CATS = {'ring', 'axon', 'flock', 'drone', 'smartglasses'}

# Extra SSID substrings (lowercase) that name surveillance gear over the air, on
# top of the OUI table — used to identify devices that don't expose a known OUI.
_SURVEILLANCE_SSID_HINTS = {
    'flock': ['flock', 'flocksafety'],
    'axon':  ['axon', 'axon-dock', 'evidence'],
    'ring':  ['ring-', 'ring setup'],
    'drone': ['dji-', 'mavic', 'parrot', 'skydio', 'anafi'],
    'smartglasses': ['ray-ban', 'meta view', 'meta-glasses'],
}


def lea_target_signatures() -> dict:
    """The LEA/surveillance scan targets a reporter should look for: per category,
    the OUI prefixes (first 6 hex of the MAC) and SSID substrings that identify it.
    Handed to hired devices in their enrollment packet so they know what to flag and
    report ASAP. Single source of truth = the same table classify_wifi() uses."""
    out: dict[str, dict] = {}
    for oui, cat in _SPECIFIC_OUIS.items():
        if cat in SURVEILLANCE_CATS:
            e = out.setdefault(cat, {
                "label": TYPE_LABELS.get(cat, cat),
                "color": TYPE_COLORS.get(cat, "#ef4444"),
                "oui_prefixes": [],
                "ssid_patterns": list(_SURVEILLANCE_SSID_HINTS.get(cat, [])),
            })
            e["oui_prefixes"].append(oui)
    return out


# ── BLE name-based rules ──────────────────────────────────────────────────────
# Each entry is (device_type, list_of_substrings_to_match_in_name_lowercased)
# First match wins — order matters.

_BLE_NAME_RULES = [
    # Headphones / Earbuds (check before speaker — earbuds often have "buds")
    ('headphones', [
        'airpods', 'earpods', 'ear pods', 'buds', 'earbuds',
        'wf-', 'wh-', 'qc35', 'qc45', 'quietcomfort', 'quiet comfort',
        'studio buds', 'powerbeats', 'jabra', 'plantronics',
        'sennheiser', 'beyerdynamic', 'anker soundcore',
        'galaxy buds', 'pixel buds', 'freebuds', 'sport',
        'headphone', 'headset',
    ]),
    # Speakers (dedicated speaker devices)
    ('speaker', [
        'jbl', 'bose', 'soundlink', 'soundbar',
        'charge 4', 'charge 5', 'charge 3',
        'flip 4', 'flip 5', 'flip 6',
        'xtreme', 'pulse', 'wonderboom', 'clip',
        'sonos', 'klipsch', 'harman', 'marshall',
        'ue boom', 'ue roll', 'megaboom', 'hyperboom',
        'speaker', 'bluetooth speaker',
    ]),
    # Smart home speakers with assistant
    ('smarthome', [
        'echo dot', 'echo show', 'echo plus', 'echo studio',
        'amazon echo', 'alexa', 'google home', 'google nest',
        'nest mini', 'nest hub', 'nest audio', 'homepod',
        'nest thermostat', 'hue bridge', 'philips hue',
        'lifx', 'wemo', 'smartthings', 'particle',
    ]),
    # Game consoles and controllers
    ('gaming', [
        'xbox', 'playstation', 'ps4', 'ps5', 'ps3',
        'dualshock', 'dualsense', 'dual shock', 'dual sense',
        'nintendo', 'switch', 'joy-con', 'joycon',
        'steam controller', 'stadia',
        'game controller', 'wireless controller',
    ]),
    # Streaming
    ('streaming', [
        'roku', 'fire tv', 'firestick', 'fire stick',
        'chromecast', 'apple tv', 'nvidia shield',
        'streaming', 'mediabox',
    ]),
    # Smart TVs
    ('tv', [
        'bravia', 'samsung tv', 'lg tv', 'lg oled',
        'vizio', 'tcl tv', 'hisense', 'philips tv',
        'smart tv', 'smarttv', '[tv]',
    ]),
    # Smartwatches / fitness bands
    ('smartwatch', [
        'apple watch', 'galaxy watch', 'gear s', 'gear sport',
        'fitbit', 'garmin', 'fenix', 'forerunner', 'vivosmart',
        'amazfit', 'mi band', 'mi smart band', 'honor band',
        'whoop', 'polar', 'suunto', 'fossil', 'pebble',
        'watch', 'band ', 'wearable',
    ]),
    # Tablets
    ('tablet', [
        'ipad', ' tab ', 'tab_', 'galaxy tab', 'fire hd',
        'kindle', 'surface ', 'lenovo tab', 'nexus 7', 'nexus 9',
    ]),
    # Laptops / computers
    ('laptop', [
        'macbook', 'mac book', 'macbookpro', 'macbookair',
        'thinkpad', 'xps ', 'latitude ', 'inspiron', 'elitebook',
        'probook', 'surface book', 'surface pro', 'zenbook',
        'vivobook', 'yoga ', 'ideapad', 'chromebook',
        'laptop', 'notebook',
    ]),
    # Vehicle systems
    ('car', [
        'bmw', 'mercedes', 'benz', 'audi', 'volkswagen', 'vw ',
        'toyota', 'ford ', 'honda ', 'chevy', 'chevrolet',
        'hyundai', 'kia ', 'volvo', 'porsche', 'lexus', 'tesla',
        'parrot', 'kenwood', 'pioneer', 'alpine ', 'clarion',
        'car audio', 'car kit', 'hands free', 'hands-free',
        'car bluetooth',
    ]),
    # Phones (broad — last before unknown to avoid false positives)
    ('phone', [
        'iphone', 'galaxy s', 'galaxy a', 'galaxy m', 'galaxy note',
        'pixel ', 'oneplus', 'nord ', 'oppo ', 'realme',
        'redmi', 'poco ', 'xiaomi', 'mi ', 'moto ', 'motorola',
        'nokia ', 'lg g', 'lg v', 'huawei', 'honor ',
        'blackberry', 'nothing phone',
        'android phone', 'my phone', 'phone',
    ]),
]

# ── BLE service UUID → device type ───────────────────────────────────────────
# Bluetooth SIG assigned 16-bit UUIDs, matched as prefix of the full UUID string.

_UUID_RULES = [
    # Heart rate monitor → smartwatch / fitness
    ('smartwatch', ['0000180d']),
    # Running Speed and Cadence, Cycling Power → fitness/smartwatch
    ('smartwatch', ['00001814', '00001818']),
    # HID Device (could be controller, keyboard, mouse)
    ('gaming',  ['00001812']),
    # A2DP Sink / Source / Headset → audio
    ('headphones', ['0000110b', '0000110a', '00001108', '0000111e']),
    # OPP (file transfer, phones), Phone Book Access
    ('phone', ['00001105', '0000112f']),
]

# ── BLE manufacturer company IDs (little-endian first 2 bytes of manuf. data) ──
# 0x004C = Apple,  0x0006 = Microsoft,  0x0075 = Samsung,  0x00E0 = Google
# These are low-confidence hints — name matching wins if available.

_MFR_HINTS = {
    0x004C: 'phone',       # Apple (very broad, covers iPhone/AirPods/Watch/Mac)
    0x0075: 'phone',       # Samsung Electronics
    0x00E0: 'phone',       # Google (Pixel, etc.)
    0x0006: 'gaming',      # Microsoft (Xbox controller is the most common BLE device)
    0x0089: 'smarthome',   # Garmin
    0x0171: 'smarthome',   # Amazon
    0x01D8: 'gaming',      # Valve (Steam Controller)
}


def classify_ble(
    name: str | None,
    service_uuids: list[str] | None,
    manufacturer_data: dict | None,
    address: str | None = None,
) -> tuple[str, str, str]:
    """
    Classify a BLE device.
    Returns (device_type_key, display_label, hex_color).
    """
    # ── 0. Specific OUI lookup (highest priority — exact manufacturer match) ──
    oui = _oui_key(address)
    if oui and oui in _SPECIFIC_OUIS:
        dtype = _SPECIFIC_OUIS[oui]
        return dtype, TYPE_LABELS[dtype], TYPE_COLORS[dtype]

    name_lc = (name or '').lower().strip()

    # ── 1. Name matching (highest confidence) ─────────────────────────────────
    for dtype, substrings in _BLE_NAME_RULES:
        if any(s in name_lc for s in substrings):
            return dtype, TYPE_LABELS[dtype], TYPE_COLORS[dtype]

    # ── 2. Service UUID matching ───────────────────────────────────────────────
    if service_uuids:
        uuids_lc = [u.lower().replace('-', '') for u in service_uuids]
        for dtype, prefixes in _UUID_RULES:
            if any(any(u.startswith(p) for p in prefixes) for u in uuids_lc):
                return dtype, TYPE_LABELS[dtype], TYPE_COLORS[dtype]

    # ── 3. Manufacturer data hint (low confidence) ────────────────────────────
    if manufacturer_data:
        for company_id in manufacturer_data:
            if company_id in _MFR_HINTS:
                dtype = _MFR_HINTS[company_id]
                return dtype, TYPE_LABELS[dtype], TYPE_COLORS[dtype]

    return 'unknown', TYPE_LABELS['unknown'], TYPE_COLORS['unknown']


# ── WiFi SSID and OUI rules ───────────────────────────────────────────────────

_SSID_RULES = [
    # Phone hotspots (Wi-Fi Direct and personal hotspot naming patterns)
    ('phone', [
        'iphone', 'galaxy ', 'pixel ', 'android ', 'hotspot',
        'direct-', 'direct_', 'my phone', 'mobile hotspot',
        'oneplus', 'xiaomi', 'huawei hotspot', 'moto g',
    ]),
    # Game consoles
    ('gaming', [
        'xbox', 'playstation', 'ps4', 'ps5', 'ps3',
        'nintendo', 'steam link',
    ]),
    # Streaming devices
    ('streaming', [
        'roku', 'fire tv', 'firetv', 'chromecast', 'apple tv',
        'nvidia shield', 'googlecast', '_googlecast',
    ]),
    # Smart TVs
    ('tv', [
        'bravia', 'samsung tv', 'lg tv', 'vizio', 'hisense',
        'tcl', 'philips tv', '[tv]', 'smarttv',
    ]),
    # Smart home
    ('smarthome', [
        'alexa', 'amazon echo', 'google home', 'nest',
        'wyze', 'blink', 'philips hue', 'smartthings',
    ]),
    # Speakers
    ('speaker', [
        'jbl', 'bose', 'sonos', 'ue boom', 'harman',
    ]),
    # Printers / office
    ('laptop', [
        'hp-print', 'epson', 'canon', 'brother', 'lexmark',
    ]),
]

# OUI prefix (first 6 hex chars of BSSID, uppercased, no colons) → device type hint
_OUI_HINTS: dict[str, str] = {
    # Microsoft (Xbox, Surface)
    '2811A5': 'gaming', '3C5AB4': 'gaming', '485073': 'gaming',
    # Sony (PlayStation, Bravia TVs)
    '001905': 'gaming', '180570': 'gaming', '0013A9': 'gaming',
    'D86CE9': 'tv',
    # Nintendo
    '002709': 'gaming', '98B6E9': 'gaming', '9458CB': 'gaming',
    # Roku
    'B83E59': 'streaming', 'D4E08E': 'streaming', 'DC3A5E': 'streaming',
    'CC6EA4': 'streaming', '086986': 'streaming',
    # Amazon (Fire TV, Echo)
    '00FC8B': 'streaming', '747548': 'streaming', 'A408F5': 'streaming',
    'F0272D': 'streaming', '44650D': 'smarthome',
    # Google (Chromecast, Google Home)
    '546009': 'streaming', 'A47733': 'streaming', '6C5C14': 'streaming',
    # Apple (broad — could be any Apple device)
    '000000': None,   # placeholder, Apple OUIs are too varied to reliably classify
}


def classify_wifi(ssid: str | None, bssid: str | None) -> tuple[str, str, str]:
    """
    Classify a WiFi access point.
    Returns (device_type_key, display_label, hex_color).
    """
    # ── 0. Specific OUI lookup (highest priority — exact manufacturer match) ──
    oui = _oui_key(bssid)
    if oui and oui in _SPECIFIC_OUIS:
        dtype = _SPECIFIC_OUIS[oui]
        return dtype, TYPE_LABELS[dtype], TYPE_COLORS[dtype]

    ssid_lc = (ssid or '').lower().strip()

    # ── 1. SSID pattern matching ───────────────────────────────────────────────
    for dtype, patterns in _SSID_RULES:
        if any(p in ssid_lc for p in patterns):
            return dtype, TYPE_LABELS[dtype], TYPE_COLORS[dtype]

    # ── 2. BSSID OUI hint ─────────────────────────────────────────────────────
    if bssid:
        oui = bssid.upper().replace(':', '').replace('-', '')[:6]
        hint = _OUI_HINTS.get(oui)
        if hint:
            return hint, TYPE_LABELS[hint], TYPE_COLORS[hint]

    # Default: generic access point
    return 'wifi_ap', TYPE_LABELS['wifi_ap'], TYPE_COLORS['wifi_ap']
