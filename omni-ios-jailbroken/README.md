# OMNI-iOS-JAILBROKEN: Kinetic Node [A9-SE]

This is a specialized pure-native iOS application designed for the A9 iPhone SE (1st Gen). It acts as a physical probe for the OMNI Lattice, optimized for 4-inch display operations.

## 📱 Small-Screen Optimizations (640x1136)
- **Bottom-Tab Navigation:** Replaces the sidebar to maximize vertical scanning space.
- **Dense List UI:** Monospace font (Courier New) at 10pt for high information density.
- **Thumb-Primary Layout:** All interactive buttons are positioned in the lower 40% of the screen for one-handed use.
- **Dynamic Font Scaling:** UI scales automatically to ensure critical signal metrics are never clipped.

## 🛠 Tactical Handheld Features
- **NFC Copier:** Direct access to raw card sectors (MIFARE/NDEF).
- **Wi-Fi Sniper:** Promiscuous mode scanning via `MobileWiFi.framework`.
- **ESP32 Controller:** Serial bridge for sub-GHz radio backpacks.
- **Grid Sync:** Secure `usbmuxd` channel to the OMNI Desktop environment.

## 💉 Injection
This app is designed to be injected via the desktop **A9 Diagnostic** panel using the `checkm8` exploit chain.
