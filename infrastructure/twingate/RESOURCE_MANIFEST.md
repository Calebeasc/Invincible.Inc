# Invincible.Inc — TWINGATE RESOURCE MANIFEST
# Managed by @weaver | Network: invincible.twingate.com
 
This document tracks the mapping between local Sovereign infrastructure and secure remote aliases. Add these to the **Twingate Admin Console** under **Resources**.
 
---
 
### 🛰️ Core Infrastructure
 
| Service | Local Address | Port | Secure Alias | Policy |
| :--- | :--- | :--- | :--- | :--- |
| **Sovereign Backend** | `127.0.0.1` | `8742` | `backend.invincible.lan` | **Admin Only** |
| **Sentinel Monitor** | `127.0.0.1` | `9999` | `sentinel.invincible.lan` | **Admin Only** |
| **Frontend Watcher** | `127.0.0.1` | `5173` | `frontend.invincible.lan` | **Admin Only** |
| **Argus OSINT Hub** | `127.0.0.1` | `8743` | `argus.invincible.lan` | **Restricted** |
 
---
 
### 🔒 Protocol Bindings
 
- **SSH (Management):** 
    - **Local Port:** `22`
    - **Alias:** `host.invincible.lan`
- **Twingate Connector:** 
    - **Container:** `invincible-twingate-connector`
    - **Label:** `INVINCIBLE_LATTICE_NODE_01`
 
---
 
### 🚀 Deployment Instructions
1.  Navigate to **Network > Resources** in [admin.twingate.com](https://admin.twingate.com).
2.  Click **Add Resource**.
3.  Select the **Remote Network** (e.g., "invincible").
4.  Enter the **Local Address** (`127.0.0.1`) and **Port** for each service.
5.  Set the **Alias** as defined above.
6.  Assign the resource to a **Group** (e.g., "Sovereign Operators").
