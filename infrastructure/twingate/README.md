# Twingate Connector Setup for Invincible.Inc

## 🔐 Deployment Strategy
We are using **Docker** for the Twingate Connector to ensure maximum isolation and scalability for our OSINT/SIGINT infrastructure.

### 1. Prerequisites
- Docker & Docker Compose installed on the host (Linux/Proxmox/Unraid).
- A Twingate account (https://www.twingate.com).

### 2. Configuration
1. Log in to your Twingate Admin Console.
2. Create a new **Remote Network** (e.g., "Invincible HQ").
3. Add a **Connector** and generate the tokens.
4. Create a `.env` file in this directory with the following:
   ```env
   TWINGATE_NETWORK="your-network-slug"
   TWINGATE_ACCESS_TOKEN="your-access-token"
   TWINGATE_REFRESH_TOKEN="your-refresh-token"
   ```

### 3. Execution
Run the following command to establish the secure tunnel:
```bash
docker-compose up -d
```

## 🚀 Sovereign Intelligence Use-Cases
- **Stealth Dev Ops:** Access `http://127.0.0.1:8742/#dev/ops` from any remote device without port forwarding.
- **Alfred Remote Bridge:** Dispatch prompts to Gemini/Claude CLI via Twingate's secure internal DNS.
- **SIGINT Data Backhaul:** Securely route raw SDR data from remote "Scout" nodes to the central Argus engine.
