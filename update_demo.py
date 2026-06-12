import sys

new_text = r'''## [PHASE 1] Geographical & Mapping Correctness (High Priority)
- [x] **1. Remove hardcoded "Phoenix Anchor":** COMPLETED. System now defaults to host location or neutral origin.
  - **Depth Design & Implementation:** Transition from a static GPS anchor to a dynamic, multi-source geolocation engine.
  - **What/How used:** Uses Windows Location API, IP-based geolocation, and Wi-Fi BSSID triangulation to pinpoint the Omni host.
  - **Tools to connect:** Native Windows GeoLocation API, WiGLE API, IP-API.
  - **Current vs Effective:** Currently relies on host IP; can be highly improved by sniffing local Wi-Fi networks and triangulating via WiGLE for exact GPS coordinates even without a GPS chip.
  - **Beneficial Info:** Local router MAC addresses, IP addresses, surrounding cell tower IDs.
  - **Useful Features:** "Auto-Calibrate Anchor" button in UTT Map, "Ghost Origin" to spoof location for OpSec.
  - **Resources to Download:** `winsdk` Python package, WiGLE account credentials.
  - **Design/Workflow:** On startup, `gps_tracker.py` queries native APIs. If offline or GPS-denied, it scans local Wi-Fi and queries WiGLE to set the precise `_focusLat` and `_focusLng`.
  - **New Tools/Ideas for UTT:** "OpSec Geo-Spoofer" - automatically sets the anchor to a randomized, safe location 5 miles away to prevent self-doxxing if logs are compromised.

- [x] **2. Disable Cesium Demo Reseeding:** COMPLETED. Neutralized in source.
  - **Depth Design & Implementation:** Completely disconnect from public Cesium servers and implement a Sovereign Offline Tile Server.
  - **What/How used:** Run a local Docker container hosting OpenMapTiles or a cached map dataset to ensure 3D mapping works entirely offline.
  - **Tools to connect:** Local MapBox/OpenStreetMap tile server, Docker, SRTM datasets.
  - **Current vs Effective:** Currently neutralized to prevent API errors, but offline mapping is limited. Effectively, it should serve 3D terrain locally.
  - **Beneficial Info:** Downloaded SRTM (Shuttle Radar Topography Mission) data for 3D elevation.
  - **Useful Features:** "Download City Cache" button in UTT to pre-load a target city's 3D map before going offline.
  - **Resources to Download:** OpenMapTiles Docker image, regional `.mbtiles` files.
  - **Design/Workflow:** Map requests in `UttPage.xaml` point to `localhost:8080/tiles`. The local server streams the map data instantly.
  - **New Tools/Ideas for UTT:** Add high-res satellite imagery caches for specific operational zones.

- [x] **3. Eliminate UTT Synthetic Visuals:** COMPLETED. Removed from `UttPage.xaml.cs`.
  - **Depth Design & Implementation:** Replace fake animations with a hardware-accelerated, Direct2D telemetry plotting system for live data.
  - **What/How used:** Use Win2D within WinUI to plot thousands of real SIGINT data points (Wi-Fi/Bluetooth signals) without lagging the UI.
  - **Tools to connect:** `Microsoft.Graphics.Win2D` NuGet package.
  - **Current vs Effective:** Synthetic visuals are gone, but the map can feel sparse. Real data plotting needs high-performance rendering.
  - **Beneficial Info:** Real-time RSSI (signal strength) and MAC addresses from local sensors.
  - **Useful Features:** Live SIGINT heatmaps that grow and fade as targets move.
  - **Resources to Download:** Win2D libraries for native C#.
  - **Design/Workflow:** The backend streams live point data via WebSockets; `UttPage.xaml.cs` renders them on a transparent Win2D canvas overlaying the map.
  - **New Tools/Ideas for UTT:** "Signal Rewind" feature to replay the last 24 hours of signal movements on the map.

- [x] **4. Clear Hardcoded Fallbacks:** COMPLETED. Removed from source.
  - **Depth Design & Implementation:** Implement a "Degraded Mode" Intelligence Cache. If live tools fail, Omni serves real historical data instead of fakes.
  - **What/How used:** A local SQLite or Redis cache that stores every OSINT finding forever.
  - **Tools to connect:** SQLite (existing) or Redis for faster in-memory queries.
  - **Current vs Effective:** Fallbacks return null/empty. Effectively, they should return the last known good data with a "STALE" warning.
  - **Beneficial Info:** Timestamps of old data, historical target locations.
  - **Useful Features:** "Stale Data Warning" UI banner; offline Dossier access.
  - **Resources to Download:** No new downloads needed; expand SQLite schema.
  - **Design/Workflow:** If an API call (e.g., OSINT search) fails due to no internet, the backend queries `offline_cache` and returns the data to UTT with a flag.
  - **New Tools/Ideas for UTT:** Mesh-syncing of caches; if your laptop is offline, query a peer laptop in the Lattice for its cache.

- [x] **5. Fix Backend Scanner Fake-Data Crash:** COMPLETED. Implemented in `scanner.py`.
  - **Depth Design & Implementation:** Interface directly with Windows Native Wi-Fi and Bluetooth HCI interfaces for raw packet sniffing.
  - **What/How used:** Use Npcap and `scapy` to capture raw probe requests and BLE advertising packets around the laptop, ignoring OS limitations.
  - **Tools to connect:** Npcap driver, `scapy` Python library.
  - **Current vs Effective:** Currently uses basic `netsh` commands. Effectively, it needs "Monitor Mode" packet injection/sniffing.
  - **Beneficial Info:** Unencrypted MAC addresses, device names, battery levels, and SSIDs that a target's phone is searching for.
  - **Useful Features:** "Enable Monitor Mode" toggle in UTT.
  - **Resources to Download:** Npcap installer, `scapy` pip package.
  - **Design/Workflow:** `scanner.py` binds to the raw socket, filters for target MACs, and pushes live location pings to the `alerts_bus`.
  - **New Tools/Ideas for UTT:** Device Fingerprinting – guess the exact phone model (iPhone 15, Galaxy S24) based on BLE OUI and broadcast intervals.

## [PHASE 2] Intelligence & Identity Hardening (Medium Priority)
- [x] **6. Convert Identity Mock to Real OSINT Tool:** COMPLETED. Subprocess bridge implemented.
  - **Depth Design & Implementation:** Upgrade `identity.py` into a multi-threaded execution engine running dedicated Python OSINT scripts.
  - **What/How used:** Runs Holehe, Maigret, and Sherlock locally, capturing standard output and parsing JSON for the UTT Dossier.
  - **Tools to connect:** `holehe`, `maigret`, `sherlock` Python packages.
  - **Current vs Effective:** Subprocess bridge is basic. Can be made highly effective by adding concurrent execution and dynamic proxy rotation.
  - **Beneficial Info:** Emails, usernames, phone numbers.
  - **Useful Features:** "Auto-Pivot" – if Sherlock finds a Twitter handle, automatically start scraping that Twitter account.
  - **Resources to Download:** `pip install maigret holehe sherlock`.
  - **Design/Workflow:** User enters an email in UTT; backend spawns 3 threads running the CLI tools, aggregates the JSON, and streams results to the UI.
  - **New Tools/Ideas for UTT:** Social Media timeline scraping to pull the last 10 posts and run sentiment analysis on the target's mood.

- [x] **7. Implement Real GeoSpy Engine:** COMPLETED. Subprocess bridge implemented.
  - **Depth Design & Implementation:** Bridge the visual recognition module to a real Visual Place Recognition (VPR) model or GeoSpy API.
  - **What/How used:** Takes an image, extracts EXIF (if available), and if not, uses a local CLIP model or GeoSpy API to predict the coordinates based on pixels (weather, architecture, vegetation).
  - **Tools to connect:** GeoSpy API or a local HuggingFace CLIP-based VPR model.
  - **Current vs Effective:** Currently mostly relies on EXIF. Pixel-based VPR is the true NSA-level upgrade.
  - **Beneficial Info:** Target photos, background landmarks, street signs.
  - **Useful Features:** "Image to Map" button in UTT – drop an image, and it drops a pin on the map.
  - **Resources to Download:** GeoSpy API Key or `transformers` local python package.
  - **Design/Workflow:** Image is uploaded via UTT -> backend runs EXIF extraction -> if null, sends to VPR model -> returns Lat/Lon to UTT map.
  - **New Tools/Ideas for UTT:** Sun-shadow analysis script – calculate the exact time of day a photo was taken based on the angle of shadows to verify alibis.

- [x] **8. Functionalize Mission Orchestrator & UTT flows:** COMPLETED. Transitioned to async background task runner with live log streaming.
  - **Depth Design & Implementation:** Turn the UTT from a static request/response UI into a live "Terminal-style" streaming matrix.
  - **What/How used:** WebSockets and `asyncio` to push data to the WinUI frontend the millisecond it's discovered by the backend OSINT tools.
  - **Tools to connect:** FastAPI WebSockets, WinUI `WebSocket` client.
  - **Current vs Effective:** Polling is slow. WebSockets make the UTT feel "alive."
  - **Beneficial Info:** Live task progress, error logs, instantaneous discoveries.
  - **Useful Features:** Scrolling "Hacker Terminal" view in the UTT dossier panel.
  - **Resources to Download:** `websockets` python library.
  - **Design/Workflow:** `missions.py` runs tasks in the background and broadcasts events to all connected UI clients.
  - **New Tools/Ideas for UTT:** Sound alerts (beeps/chimes) when a High-Value Target piece of intel (like a live location) drops into the stream.

- [x] **9. Real Surveillance Fusion:** COMPLETED. Spatial logic implemented linking signal data to ALPR cameras.
  - **Depth Design & Implementation:** The "Digital Twin" relational graph. Linking physical camera feeds to RF signal encounters.
  - **What/How used:** If a target's Wi-Fi MAC is detected near a traffic camera's GPS coordinates, Omni automatically pulls that camera's feed to look for their license plate.
  - **Tools to connect:** OpenALPR, local SQLite `lattice_links` database.
  - **Current vs Effective:** Spatial logic exists but is basic. Needs real ALPR frame-by-frame analysis.
  - **Beneficial Info:** License plate numbers, car make/model, target MAC addresses.
  - **Useful Features:** "Correlate RF to Video" button.
  - **Resources to Download:** OpenALPR daemon, `opencv`.
  - **Design/Workflow:** `scanner.py` logs a MAC. Backend checks proximity to known CCTV coordinates. If within 50m, it triggers `cctv_broker.py` to run ALPR on the feed.
  - **New Tools/Ideas for UTT:** Vehicle color/make recognition alongside the license plate to confirm identity.

- [x] **25. Improve LE-GOLIATH Classification:** COMPLETED. Heuristic engine implemented.
  - **Depth Design & Implementation:** Advanced heuristic classification of discovered devices (e.g., distinguishing a router from an iPhone from a Police Radio).
  - **What/How used:** Uses MAC OUI databases and packet broadcast intervals to guess device types with high accuracy.
  - **Tools to connect:** Wireshark OUI database, deep packet inspection scripts.
  - **Current vs Effective:** Currently uses simple heuristics. Can be enhanced with ML-based packet timing analysis to detect hidden devices.
  - **Beneficial Info:** Device behavior, packet sizes, transmission frequency.
  - **Useful Features:** Threat Level indicator (e.g., flagging a specific radio frequency as "Known Law Enforcement").
  - **Resources to Download:** Updated IEEE OUI text files.
  - **Design/Workflow:** `scanner.py` captures a packet, compares the first 3 MAC bytes to the OUI DB, and analyzes the timing to assign a `device_type` icon in UTT.
  - **New Tools/Ideas for UTT:** Detect IMSI catchers (Stingrays) by looking for anomalous cell tower signal strengths and alerting the operator.

## [PHASE 3] Operational & Defensive Hardening (Medium Priority)
- [x] **10. Real-Time Alert Engine:** COMPLETED. Refactored to active `alerts_bus` monitoring loop.
  - **Depth Design & Implementation:** A centralized event bus for all system-wide threats, targets, and system failures.
  - **What/How used:** Redis Pub/Sub or Python `asyncio.Queue` to broadcast alerts to the UI overlay.
  - **Tools to connect:** Redis (optional), native WinUI Notification Toasts.
  - **Current vs Effective:** Currently an internal queue. Should trigger native Windows OS desktop notifications.
  - **Beneficial Info:** Critical threat vectors (e.g., "Target has come online").
  - **Useful Features:** Native Windows 10/11 Toast Notifications.
  - **Resources to Download:** `Microsoft.Toolkit.Uwp.Notifications`.
  - **Design/Workflow:** `alerts_bus` receives an event, sends it via WebSocket to UTT, and UTT triggers a Windows Toast so the operator knows even if the app is minimized.
  - **New Tools/Ideas for UTT:** SMS/Signal integration to text the operator's burner phone if a high-value target is detected locally.

- [x] **11. Live Node Telemetry:** COMPLETED. Implemented real PnP hardware discovery via PowerShell.
  - **Depth Design & Implementation:** Total hardware awareness of the operator's laptop and attached SDRs (Software Defined Radios).
  - **What/How used:** Uses PowerShell `Get-PnpDevice` to detect plugged-in RTL-SDRs, Wi-Fi antennas, and Bluetooth sniffers, updating the UTT capabilities dynamically.
  - **Tools to connect:** Native PowerShell subprocesses.
  - **Current vs Effective:** Checks basics. Should automatically configure SDR drivers (Zadig) if plugged in.
  - **Beneficial Info:** Attached hardware capabilities, antenna gain.
  - **Useful Features:** "Hardware Matrix" HUD showing active antennas.
  - **Resources to Download:** RTL-SDR drivers.
  - **Design/Workflow:** Backend runs PS script every 10s. If an RTL-SDR is found, it unlocks the "SIGINT Waterfall" tab in UTT.
  - **New Tools/Ideas for UTT:** Auto-tuning the SDR to the target's specific RF frequencies based on their identified car key fob.

- [x] **12. Digital Dummy Vault Implementation:** COMPLETED. Built functional backend and WinUI 3 VaultPage with PIN-based data partition.
  - **Depth Design & Implementation:** Plausible deniability storage. Two PINs, two completely different sets of intelligence.
  - **What/How used:** Master PIN (1337) decrypts the real UTT Dossiers. Duress PIN (9999) opens a fake vault with mundane generic documents.
  - **Tools to connect:** AES-256 encryption libraries (`cryptography` in Python).
  - **Current vs Effective:** Currently a folder swap. Effectively, the files themselves should be encrypted at rest until the exact PIN is entered.
  - **Beneficial Info:** Operator safety, OpSec during physical device seizure.
  - **Useful Features:** "Wipe on 3 Fails" logic.
  - **Resources to Download:** `pip install cryptography`.
  - **Design/Workflow:** Operator enters PIN in UTT Vault. Backend uses the PIN to derive an AES key and attempts decryption.
  - **New Tools/Ideas for UTT:** "Panic Hotkey" (e.g., F12) that instantly locks the Vault and scrambles RAM to prevent forensic recovery.

- [x] **13. Noise Generator Development:** COMPLETED. `opsec.py` functional traffic generator integrated.
  - **Depth Design & Implementation:** The "Chaff" protocol. Flooding the local network and internet connection with fake traffic to hide UTT's actual queries.
  - **What/How used:** Spawns background threads that visit random websites and broadcast randomized MAC addresses to confuse adversarial local sensors.
  - **Tools to connect:** `requests` for web noise, `scapy` for RF noise.
  - **Current vs Effective:** Basic noise. Effective noise should perfectly mimic normal human browsing and local office RF environments.
  - **Beneficial Info:** Target's baseline noise (to blend in).
  - **Useful Features:** "Deploy Chaff" button in UTT OpSec tab.
  - **Resources to Download:** Lists of top 10,000 domains.
  - **Design/Workflow:** `opsec.py` runs a loop sending DNS queries for generic sites while the real `stealth_browser.py` does the surgical targeting.
  - **New Tools/Ideas for UTT:** "Mimic Target" mode—make the operator's laptop look exactly like the Target's laptop on the network to steal their session.

- [x] **26. Validate Orchestrator Mission Controls:** COMPLETED. Hardened UI with capability audits and high-authority reporting.
  - **Depth Design & Implementation:** Ensure the UI cannot trigger missions if the backend lacks the required tools (e.g., no internet, no SDR).
  - **What/How used:** Pre-flight checks before UTT starts a mission.
  - **Tools to connect:** Backend system status endpoints.
  - **Current vs Effective:** UI locks buttons. Effective execution provides a detailed "Pre-Flight Matrix" showing exactly what tools are armed.
  - **Beneficial Info:** Network status, API key validity.
  - **Useful Features:** "Pre-Flight Dashboard" popup before mission start.
  - **Resources to Download:** None.
  - **Design/Workflow:** Click START -> Backend tests all API keys -> Returns OK -> Mission begins.
  - **New Tools/Ideas for UTT:** Automatic fallback routing—if WiGLE API is down, automatically switch to Mozilla Location Services API without throwing an error.

## [PHASE 4] Forensic & Payload Hardening (High Priority)
- [x] **14. Functionalize A9 Module:** COMPLETED (Restored & Enhanced). Service performs real file validation and TCP/SSH probing. Native page restored with real-time **Operation Progress Bars** and a functional **OMNI-iOS Tactical Injector** for the mobile node.
  - **Depth Design & Implementation:** The Payload Delivery System. Allows Omni to deploy tracking payloads (like Pegasus/NSO style zero-clicks) to target devices.
  - **What/How used:** Validates a payload file, then uses TCP/SSH probing to find open ports on a target IP to inject the mobile node code.
  - **Tools to connect:** `paramiko` for SSH probing, `nmap` for port discovery.
  - **Current vs Effective:** Uses basic TCP checks. Effectively, it should use Metasploit RPC to launch actual exploits.
  - **Beneficial Info:** Target open ports, OS versions, running services.
  - **Useful Features:** "Deploy Payload" button with live injection progress bars.
  - **Resources to Download:** `pip install paramiko`.
  - **Design/Workflow:** Operator selects a payload in UTT -> Backend scans target IP -> Finds open SSH -> Attempts brute force or exploit -> Injects payload.
  - **New Tools/Ideas for UTT:** "Canary Token Payload"—a harmless payload that just pings home with the target's GPS location when opened.

- [x] **15. Functionalize RF Integrity:** COMPLETED. `netsh` integration and real network auditing.
  - **Depth Design & Implementation:** Network defense. Scans the local network to ensure no one is wiretapping the operator.
  - **What/How used:** Parses `netsh wlan show networks` and `arp -a` to detect ARP poisoning or Rogue Access Points (Evil Twins).
  - **Tools to connect:** Native Windows networking binaries.
  - **Current vs Effective:** Reads basics. Should actively alert if the MAC address of the default gateway changes (ARP Spoofing attack).
  - **Beneficial Info:** Local router MAC, ARP table.
  - **Useful Features:** "Network Integrity Lock" – instantly disconnects from Wi-Fi if a Man-in-the-Middle attack is detected.
  - **Resources to Download:** None (Uses Windows native).
  - **Design/Workflow:** Background task hashes the ARP table every 5 seconds. If a mismatch occurs, UTT flashes RED and severs connections.
  - **New Tools/Ideas for UTT:** "Counter-Attack" option—if an Evil Twin is detected, automatically launch a Deauth attack against it to protect the area.

- [x] **16. AIP Terminal Capability:** COMPLETED. Local logic fallback and multi-turn history implemented.
  - **Depth Design & Implementation:** A local AI CLI within Omni for operator assistance without calling out to external servers.
  - **What/How used:** Integrated Ollama/Llama-3 directly into the WinUI terminal for offline tactical advice.
  - **Tools to connect:** Ollama API.
  - **Current vs Effective:** Multi-turn history works. Effective implementation ties the AI to the UTT Dossier so the AI knows everything about the target automatically.
  - **Beneficial Info:** The entire Target `.json` index.
  - **Useful Features:** "Ask AI about Target" button in the Vault.
  - **Resources to Download:** Ollama local installer.
  - **Design/Workflow:** Operator types "What is the target's weakest point?" -> AIP reads the `.json` dossier -> Returns "Target has an unpatched Axis camera at their home."
  - **New Tools/Ideas for UTT:** AI-generated "Phishing Lures"—the AI writes a custom spear-phishing email based on the target's LinkedIn profile found in Phase 1.

- [x] **23. Correct Malware YARA Contract:** COMPLETED. Native side aligned with backend GET route.
  - **Depth Design & Implementation:** Scanning incoming files (like downloaded resumes of the target) for malicious intent before the operator opens them.
  - **What/How used:** The backend uses `yara-python` to scan files against a local database of known APT signatures.
  - **Tools to connect:** `yara-python`, local `.yar` signature files.
  - **Current vs Effective:** Basic static analysis. Effective implementation uses dynamic sandboxing (Phase 6A).
  - **Beneficial Info:** Malware signatures, obfuscated scripts in target documents.
  - **Useful Features:** "Analyze File" drag-and-drop zone in UTT.
  - **Resources to Download:** `pip install yara-python`, updated YARA rulesets from GitHub.
  - **Design/Workflow:** File dropped in UI -> Sent to backend -> YARA rules applied -> Safe/Malicious flag returned to Vault.
  - **New Tools/Ideas for UTT:** Document Metadata Stripper—automatically sanitize any files Omni downloads so they can't be traced back if accidentally re-uploaded.

## [PHASE 5] Dashboard & UI Integrity (Medium Priority)
- [x] **17. Live Omni Overview:** COMPLETED. Fetches live aggregate telemetry from the backend.
  - **Depth Design & Implementation:** The "God's Eye" dashboard aggregating all active missions, nearby targets, and system health into one high-tech view.
  - **What/How used:** Uses WinUI Grid layouts with live DataBinding to the FastAPI `/summary` endpoints.
  - **Tools to connect:** WinUI DataBinding, FastAPI JSON endpoints.
  - **Current vs Effective:** Shows text. Should show live sparkline graphs of CPU, RAM, and Network I/O.
  - **Beneficial Info:** Total active operations, system load, target proximity alerts.
  - **Useful Features:** Minimalist, high-contrast dark mode aesthetic (Invincible.Inc branding).
  - **Resources to Download:** WinUI Charting libraries (LiveCharts2).
  - **Design/Workflow:** Backend calculates metrics every second -> WebSockets push to UI -> Sparklines update smoothly.
  - **New Tools/Ideas for UTT:** "Focus Mode" – dims all generic dashboard elements and expands the specific UTT target map to full screen.

- [x] **18. Real Blindspot Routing:** COMPLETED. Multi-waypoint evasion algorithm implemented.
  - **Depth Design & Implementation:** Calculating physical routes for the operator that avoid known ALPR and CCTV cameras.
  - **What/How used:** Uses a local GraphHopper or OSRM instance and a database of known camera locations (from Shodan/OSINT) to draw a "Safe Path" on the UTT map.
  - **Tools to connect:** Local OSRM (Open Source Routing Machine), OpenStreetMap data.
  - **Current vs Effective:** Basic waypoint math. Effective implementation actively avoids Shodan-discovered cameras.
  - **Beneficial Info:** Known CCTV coordinates, ALPR intersections, target locations.
  - **Useful Features:** "Draw Evasion Route" button in the UTT Map.
  - **Resources to Download:** OSRM local server binary, OSM maps.
  - **Design/Workflow:** Operator clicks Start and End -> Backend calculates path avoiding CCTV radiuses -> Draws pulsing line on UTT map.
  - **New Tools/Ideas for UTT:** Dynamic rerouting if a new camera or police radio is detected by the `scanner.py` while moving.

- [x] **19. Purge Frontend Demo States:** COMPLETED. "SOVEREIGN" naming enforced across stack.
  - **Depth Design & Implementation:** Eradicating all placeholder text, generic names, and fake data to ensure the platform feels 100% lethal and authentic.
  - **What/How used:** Global Find & Replace to enforce the "Invincible.Inc / SOVEREIGN" nomenclature.
  - **Tools to connect:** None.
  - **Current vs Effective:** UI is clean. Effective enforcement means the backend *never* sends mock data, only actual errors if something fails.
  - **Beneficial Info:** Professional psychological impact for the operator.
  - **Useful Features:** Strict error handling UI that looks like military diagnostics, not generic web errors.
  - **Resources to Download:** None.
  - **Design/Workflow:** All API responses adhere to strict JSON schemas; missing data triggers a stylized "NO SIGNAL" UI element.
  - **New Tools/Ideas for UTT:** Customizable "Agency Branding" – let the user switch the UI theme from "NSA" to "FBI" to "Syndicate."

- [x] **20. TierGate Transparency:** COMPLETED. Restricted UI component implemented.
  - **Depth Design & Implementation:** Role-Based Access Control (RBAC) within the UI. Features lock out based on the Vault PIN used (Sovereign vs. Duress).
  - **What/How used:** WinUI `Visibility` bindings tied to the global `_vault_state` mode.
  - **Tools to connect:** Internal State Management.
  - **Current vs Effective:** Hides tabs. Effective implementation disables the backend APIs entirely so they can't be bypassed with Postman/Curl.
  - **Beneficial Info:** Operator authorization level.
  - **Useful Features:** "Unauthorized" visual overlays on restricted tabs.
  - **Resources to Download:** None.
  - **Design/Workflow:** If Duress PIN is used, the UTT tab is visible but the "ATTACK" button is grayed out and clicking it shows "TIER 3 CLEARANCE REQUIRED."
  - **New Tools/Ideas for UTT:** "Biometric Gate" – require a quick webcam facial scan to unlock the ATTACK mode before deploying payloads.

- [x] **21. Safe-Boot Messaging:** COMPLETED. Professional Degraded Mode report implemented.
  - **Depth Design & Implementation:** If the laptop is offline or missing SDR hardware, the app boots cleanly and informs the operator exactly what is restricted.
  - **What/How used:** A boot-up diagnostic screen (like a BIOS check) before the main UTT loads.
  - **Tools to connect:** Hardware polling scripts.
  - **Current vs Effective:** Basic text. Effective implementation runs a visual 5-second check of all modules (Internet: OK, SDR: OFFLINE, Ollama: OK).
  - **Beneficial Info:** System readiness.
  - **Useful Features:** "Diagnostic Boot Sequence" UI.
  - **Resources to Download:** None.
  - **Design/Workflow:** App launches -> Runs `Hardware_Check()` -> Displays green/red text matrix -> Enters main dashboard.
  - **New Tools/Ideas for UTT:** Auto-troubleshooting logic—if offline, offer a one-click button to automatically spoof a MAC address and connect to the nearest open Wi-Fi.

- [x] **22. Fix Health Tab Trustworthiness:** COMPLETED. Proper GET status routes and hardened validation implemented.
  - **Depth Design & Implementation:** The Health tab must reflect absolute reality. If the database is locked, it says locked.
  - **What/How used:** API routes `/health` and `/status` that actually ping the SQLite DB and check internet connectivity via ICMP.
  - **Tools to connect:** Ping subprocesses, SQLite `PRAGMA integrity_check`.
  - **Current vs Effective:** Basic HTTP checks. Effective checks ping external services (like WiGLE/Shodan) to ensure API keys are not rate-limited.
  - **Beneficial Info:** API quota limits, disk space remaining.
  - **Useful Features:** Live API Key quota bars in the UI.
  - **Resources to Download:** None.
  - **Design/Workflow:** Health tab polls `/status` every 5s. Backend verifies disk I/O, API key status, and memory usage.
  - **New Tools/Ideas for UTT:** "Self-Destruct Readiness" indicator—showing if the system is capable of wiping the SSD instantly if compromised.

- [x] **24. Enhance API Wrappers:** COMPLETED. Overhauled Alerts, Nodes, Identity, and Triage tabs into structured cockpits.
  - **Depth Design & Implementation:** Standardizing the C# HTTP clients to handle the new autonomous backend perfectly, ensuring no crashes on malformed JSON.
  - **What/How used:** Strongly-typed C# models using `System.Text.Json` matching the FastAPI Pydantic models.
  - **Tools to connect:** Standard .NET HTTP libraries.
  - **Current vs Effective:** Basic GET/POST. Effective wrappers include automatic retry logic and circuit breakers if the local backend is overloaded by LLM tasks.
  - **Beneficial Info:** Robust error messages.
  - **Useful Features:** Smooth degradation—if an API fails, the UI simply dims instead of crashing.
  - **Resources to Download:** None.
  - **Design/Workflow:** C# `OmniApiService` uses Polly (or custom retry logic) to handle timeout spikes from heavy OSINT operations.
  - **New Tools/Ideas for UTT:** "Offline Queue"—if the operator inputs a target while offline, the UI queues the mission and autonomously executes it the second Wi-Fi connects.

## [PHASE 6] Sovereign Intelligence Expansion (Immediate Hardening)
- [ ] **31. Real Satellite Propagation:** Convert mocked `satellite_tracker.py` to use real `sgp4` math on CelesTrak TLEs.
  - **Depth Design & Implementation:** Accurately map Spy, Weather, and Comms satellites passing over the operator's current location to know when you are being watched.
  - **What/How used:** Pulls live TLE (Two-Line Element) data from CelesTrak and uses the `sgp4` library to calculate exact orbital positions and plot them on the UTT map.
  - **Tools to connect:** CelesTrak API, `sgp4` python library.
  - **Current vs Effective:** Mocked static orbits. Effective implementation shows a "Red Zone" on the map when a recon satellite is directly overhead.
  - **Beneficial Info:** Satellite footprints, pass-over times, sensor types (Optical vs. SAR).
  - **Useful Features:** "Overhead Alert" - UI flashes when a known imagery satellite enters the horizon.
  - **Resources to Download:** `pip install sgp4 skyfield`.
  - **Design/Workflow:** Backend fetches TLEs daily. UTT Map requests live satellite coords every 5 seconds. WinUI plots the satellite and draws a translucent circle representing its viewing angle.
  - **New Tools/Ideas for UTT:** "Go Dark" auto-mode—automatically disable all RF emissions (Wi-Fi, Bluetooth) on the laptop when an ELINT (Electronic Intelligence) satellite passes overhead.

- [ ] **32. AT-BLU Dynamic Discovery:** Upgrade Bluetooth command execution from hardcoded UUIDs to dynamic GATT service discovery.
  - **Depth Design & Implementation:** Turn the laptop's Bluetooth chip into an aggressive scanner that maps out the services of nearby target devices (Smartwatches, Cars, IoT).
  - **What/How used:** Uses `bleak` in Python to connect to discovered MAC addresses, enumerate all GATT characteristics (e.g., heart rate monitors, lock controls), and read their values.
  - **Tools to connect:** `bleak` Python package.
  - **Current vs Effective:** Hardcoded fake UUIDs. Effective implementation actively interacts with nearby devices.
  - **Beneficial Info:** Target device manufacturer, exact battery level, firmware version, unprotected read/write characteristics.
  - **Useful Features:** "Extract Device Tree" button next to a BLE target in UTT.
  - **Resources to Download:** `pip install bleak`.
  - **Design/Workflow:** Operator clicks a BLE target -> `scanner.py` initiates a BLE connection -> Pulls the GATT table -> Displays the readable data in the UTT Dossier.
  - **New Tools/Ideas for UTT:** "Bluetooth Hijack"—if an unprotected write characteristic is found (e.g., on a cheap smart lock or scooter), add a button to send the "Unlock" byte payload directly from the UI.

- [ ] **33. VisualRecon Real Engine:** Bridge the frontend VisualRecon module to a real OSINT/CLIP geolocation backend.
  - **Depth Design & Implementation:** Full integration of the AI Visual Intelligence pipeline from Phase 7/8.
  - **What/How used:** When an operator drops a photo into UTT, the backend runs it through a local HuggingFace CLIP model to extract text descriptions ("A street corner in Berlin with a yellow tram") and cross-references that with Google Dorks to find the exact location.
  - **Tools to connect:** HuggingFace `transformers`, PyTorch.
  - **Current vs Effective:** Exif only. True VPR (Visual Place Recognition) allows tracking targets based on background scenery alone.
  - **Beneficial Info:** Exact geolocation of a target's safehouse based on a selfie.
  - **Useful Features:** "Pixel-Hunt" mode in UTT.
  - **Resources to Download:** `pip install torch transformers`. Pre-trained CLIP models.
  - **Design/Workflow:** Photo uploaded -> CLIP generates text tags -> Backend Dorks the tags -> Returns coordinates to the UTT Map.
  - **New Tools/Ideas for UTT:** "Reflection Extraction"—automatically zoom and enhance reflections in windows or sunglasses within the photo to find more context.

- [x] **34. UTT Live Internet Search:** Removed hardcoded probabilistic metrics in UTT and integrated a real live internet search engine for contextual execution.
  - **Depth Design & Implementation:** The foundation of the Phase 8 Autonomous Engine. UTT actually hits the live internet.
  - **What/How used:** `duckduckgo_search` and `SearXNG` integration into the primary mission orchestrator.
  - **Tools to connect:** SearXNG docker instance, `requests`.
  - **Current vs Effective:** Basic DDG text search. Now superseded by the Phase 11 "Hyper-Speed Native Engine".
  - **Beneficial Info:** Live news, forum posts, pastebins containing the target's name.
  - **Useful Features:** Live parsing of search engine results straight into the UTT terminal.
  - **Resources to Download:** SearXNG.
  - **Design/Workflow:** Target input -> Search aggregators queried -> Results parsed by NLP -> Displayed in UI.
  - **New Tools/Ideas for UTT:** "Archive.org Search"—automatically check the Wayback Machine for deleted posts or old versions of the target's website.

- [x] **35. Sentinel-1 SAR Integration:** Replace optical-only satellite layers with SAR (Radar) options for night/cloud penetration in UTT missions.
  - **Depth Design & Implementation:** Give the UTT Map the ability to view the ground through clouds and at night using Synthetic Aperture Radar maps.
  - **What/How used:** Integrate APIs from Copernicus/Sentinel-1 or commercial radar providers (Capella Space) to overlay radar tiles on the UTT map.
  - **Tools to connect:** Sentinel API / Copernicus Data Space.
  - **Current vs Effective:** Optical only (useless at night). SAR provides 24/7 visibility of large vehicles and infrastructure changes.
  - **Beneficial Info:** Movement of large assets (ships, trucks) at the target location regardless of weather.
  - **Useful Features:** "Toggle SAR Radar" layer button in the Map settings.
  - **Resources to Download:** API access scripts for Sentinel Hub.
  - **Design/Workflow:** UTT Map requests tile layer -> Backend proxies the request to Sentinel API -> Radar imagery is rendered over the 3D map.
  - **New Tools/Ideas for UTT:** "Change Detection"—automatically compare yesterday's SAR map to today's and highlight new vehicles or structures in bright red.

- [x] **36. UTT Mission Engine (OSINT Pipeline):** Replaced static mock outputs for MONITOR, TRACK, ATTACK, INTEL with a live DuckDuckGo multi-vector web scraper running locally in `missions.py` to construct thorough target profiles.
  - **Depth Design & Implementation:** The core logic loop that handles the different mission modes, now fully empowered by Phase 8 and Phase 11 tools.
  - **What/How used:** INTEL runs passive scrapers. TRACK engages local sensors (Wi-Fi/BLE) and Global Beacons (Canary Tokens). ATTACK launches active payloads (Nmap, Deauth, Exploit-DB scripts).
  - **Tools to connect:** All tools from Phases 7-11.
  - **Current vs Effective:** Static text replaced by the fully autonomous "Fire and Forget" engine.
  - **Beneficial Info:** Target's entire digital and physical life.
  - **Useful Features:** Mode-specific UI changes (ATTACK turns the UI red, INTEL turns it blue).
  - **Resources to Download:** All python dependencies listed previously.
  - **Design/Workflow:** Select Mode -> Enter Target -> Auto-Run pipeline -> Save to Vault.
  - **New Tools/Ideas for UTT:** "Ghost Mode" Mission—a passive-only setting that strictly uses cached data and offline databases to ensure zero network packets are sent toward the target.

- [x] **37. True Scanner Parity (Oracle):** Hardened the `/encounters` API to bypass strictly GPS-dependent filtering, allowing real WiFi/BLE node discoveries to populate the "Nearby Target" dropdown even if the host lacks a satellite fix.
  - **Depth Design & Implementation:** Decouple local sensor data from GPS dependency, ensuring Omni works perfectly indoors, in bunkers, or deep urban canyons.
  - **What/How used:** If `_focusLat` is null, the system still logs MAC addresses, signal strengths, and timestamps, grouping them by relative distance (RSSI) instead of absolute GPS.
  - **Tools to connect:** SQLite database logic modifications.
  - **Current vs Effective:** Failed if no GPS. Effectively, it now acts as a relative radar.
  - **Beneficial Info:** Proximity of targets (e.g., "Target MAC is 10 feet away") without needing to know where in the world the laptop is.
  - **Useful Features:** "Relative Radar" view in UTT showing concentric rings of signal strength instead of a global map.
  - **Resources to Download:** None.
  - **Design/Workflow:** `scanner.py` logs encounter -> If GPS is dead, sets coords to `0,0` but flags `proximity_rssi` -> UI populates the "Nearby Target" dropdown based strictly on RSSI strength.
  - **New Tools/Ideas for UTT:** "Acoustic Triangulation"—if multiple Omni laptops are in the same building, use the microphone delay of a loud sound (like a slammed door) to triangulate indoor positions without GPS.

---
## [PHASE] Infrastructure Recovery (VERIFIED)
- [x] **27. Fix WinUI MarkupCompilePass1:** RESOLVED. Build health restored.
  - **Depth Design & Implementation:** Corrected all XAML namespace bindings to ensure the native Windows 10/11 app compiles flawlessly.
  - **What/How used:** MSBuild, Visual Studio 2022.
  - **Tools to connect:** MSBuild toolchain.
  - **Current vs Effective:** Compiles successfully. Effectively, can integrate with GitHub Actions for automated build checks.
  - **Beneficial Info:** Build logs, error traces.
  - **Useful Features:** CI/CD pipeline integration.
  - **Resources to Download:** None.
  - **Design/Workflow:** Continuous Integration ensures XAML elements map perfectly to C# code-behind.
  - **New Tools/Ideas for UTT:** "Build Status" internal indicator for developers.

- [x] **28. Implement Missing Backend Routes:** RESOLVED. All routers verified and functional.
  - **Depth Design & Implementation:** Built out the FastAPI surface area to support every single button, slider, and toggle in the WinUI frontend.
  - **What/How used:** Python FastAPI `APIRouter` structures.
  - **Tools to connect:** FastAPI framework.
  - **Current vs Effective:** Basic functional routes. Effectively, all routes should have JWT token verification and strict Pydantic models.
  - **Beneficial Info:** JSON structured data.
  - **Useful Features:** Swagger UI documentation enabled for developers.
  - **Resources to Download:** None.
  - **Design/Workflow:** Routes are clearly separated by domain (`vault.py`, `missions.py`, `scanner.py`).
  - **New Tools/Ideas for UTT:** Automatic Route Fuzzer—an internal tool to test all backend routes to ensure they never crash under malformed input.

- [ ] **29. Final Tab-by-Tab Runtime Pass:** PENDING INSTALLER BUILD.
  - **Depth Design & Implementation:** A complete QA pass of the software to ensure the Accumulation rules are met across every tab (UTT, Vault, OpSec, Health).
  - **What/How used:** Manual testing script or automated Selenium/Playwright tests against the WinUI app (via WinAppDriver).
  - **Tools to connect:** WinAppDriver.
  - **Current vs Effective:** Manual checking. Effectively, automated E2E tests should be built.
  - **Beneficial Info:** Test coverage metrics.
  - **Useful Features:** Automated QA pipeline.
  - **Resources to Download:** WinAppDriver.
  - **Design/Workflow:** Tests simulate an operator clicking every button and ensure no crashes occur.
  - **New Tools/Ideas for UTT:** "Simulated Target Environment" to run tests against fake targets to ensure all pipelines are operational without hitting real people.

- [ ] **30. Rebuild & Push v1.4.0 Installer:** READY FOR CLAUDE.
  - **Depth Design & Implementation:** Packaging the Python backend, WinUI frontend, local LLMs, Nmap, SQLite databases, and all scripts into a single, deployable `.msi` or `.exe` installer.
  - **What/How used:** InnoSetup or WiX Toolset to create a silent, robust installer that drops the ultimate espionage tool onto any Windows machine in seconds.
  - **Tools to connect:** InnoSetup or WiX.
  - **Current vs Effective:** Loose files. Effectively, a single monolithic installer.
  - **Beneficial Info:** System architecture requirements.
  - **Useful Features:** Silent installation mode for rapid deployment.
  - **Resources to Download:** InnoSetup compiler.
  - **Design/Workflow:** Compiles C#, freezes Python, bundles assets, and creates desktop shortcuts.
  - **New Tools/Ideas for UTT:** "Portable Mode" – compile Omni into a standalone folder that runs entirely from a USB stick without installation.
'''

import sys

with open('demo-to-be-real.md', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = "## [PHASE 1] Geographical & Mapping Correctness (High Priority)"
end_marker_context = "## [DEBUGGING BOUNDARIES]"

start_idx = content.find(start_marker)
end_idx = content.find(end_marker_context)
end_idx = content.rfind("---", start_idx, end_idx)

if start_idx == -1 or end_idx == -1:
    print("Markers not found")
    sys.exit(1)

new_content = content[:start_idx] + new_text + "\n" + content[end_idx:]

with open('demo-to-be-real.md', 'w', encoding='utf-8') as f:
    f.write(new_content)

print("Success")