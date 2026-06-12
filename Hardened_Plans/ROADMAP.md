# Invincible.Inc ROADMAP: Hardened Edition

## Phase 1: Foundation (COMPLETED)
- [x] Standardized Agent Fleet (.ai-agents)
- [x] Unified SIGINT/DeFlock Ingestion
- [x] High-Fidelity Tron Aesthetic Frontend
- [x] Local-First Privacy Protection

## Phase 2: Distribution (ACTIVE)
- [x] **Zero-Redirect Web Distribution:** Implement in-browser download triggers in Explainer site.
- [x] **Native Windows Packaging:** Inno Setup configuration for portable/local installation.
- [x] **Windows Desktop Launcher:** Bridge the FastAPI backend with a WebView2 native window.
- [x] **Firewall Exception Manager:** Automate port binding for scanner nodes.
- [x] **System Tray Orchestrator:** Background scanning and tray-to-foreground logic.
- [x] **Dual-Brain Lattice:** Autonomous failover to local LLMs (Qwen/Dolphin) for 100% uptime.

## Phase 3: Hardware Integration (UPCOMING)
- [ ] **SDR Node Bridge:** Integrate RTL-SDR and HackRF signals into the Lattice graph.
  > *Implementation: `Infrastructure/Scanning/SdrBridgeService.cs` — P/Invoke to `librtlsdr.dll`;
  > exposes `ISignalSource` domain interface so the use-case layer is hardware-agnostic.*
- [ ] **Drone-Link Telemetry:** Ingest remote drone-based SIGINT streams.
  > *Implementation: MAVLink UDP listener → `DroneSignalAdapter : ISignalSource` → Grid topology graph.*
- [ ] **Sovereign Mesh:** Local-to-local peer communication for field coordination.
  > *Implementation: ZeroMQ PUB/SUB on LAN; `MeshNode` is a domain `Aggregate` with
  > `INodeRepository` interface — no direct socket code in domain layer.*

## Phase 4: Data Intelligence (FUTURE)
*Detailed strategy in [FUTURE_PLAN_MAP.md](./FUTURE_PLAN_MAP.md)*
*Raw Intel: [PALANTIR_GIS_INTEL.md](./PALANTIR_GIS_INTEL.md) | [INVISION_GIS_INTEL.md](./INVISION_GIS_INTEL.md) | [PALANTIR_ONTOLOGY_INTEL.md](./PALANTIR_ONTOLOGY_INTEL.md) | [OMNI_SERVICE_ORCHESTRATION.md](./OMNI_SYSTEM_OF_ACTION.md) | [PALANTIR_AIP_MAPPING_INTEL.md](./PALANTIR_AIP_MAPPING_INTEL.md) | [WORLD_VIEW_INTEL.md](./WORLD_VIEW_INTEL.md) | [RF_SENSING_INTEL.md](./RF_SENSING_INTEL.md) | [VPS_DATA_FUSION_INTEL.md](./VPS_SURVEILLANCE_INTEL.md) | [SKYFALL_GS_INTEL.md](./SKYFALL_GS_INTEL.md) | [GAUSSIAN_SPLATTING_INTEL.md](./GAUSSIAN_SPLATTING_INTEL.md) | [TACTICAL_DEFENSIVE_INTEL.md](./TACTICAL_EVASION_INTEL.md) | [SECURITY_HARDENING_MESH_INTEL.md](./OFFENSIVE_MESH_INTEL.md) | [HARDWARE_MEDIC_INTEL.md](./HARDWARE_MEDIC_INTEL.md) | [SECURITY_HARDENING_HARDWARE_INTEL.md](./RED_TEAM_HARDWARE_INTEL.md) | [GEOSPATIAL_AI_RESEARCH_INTEL.md](./GEOSPATIAL_AI_RECON_INTEL.md)*

**[HIGH PRIORITY]**
- [ ] **The Great Partition:** Full codebase separation between Oracle and Invincible/Omni. [HIGHEST AUTHORITY]
  > *Implementation: Separate git repos (Calebeasc/Oracle, Calebeasc/Omni, Calebeasc/Grid) — DONE for code.
  > Next: shared domain primitives extracted to `@invincible/domain` npm package; CLAUDE.md in each repo
  > enforces bounded context with grep pre-commit hooks. Status: repos separated ✓, shared pkg pending.*
- [ ] **LGM Visual Geolocation:** Image-to-coordinate mapping (GeoSpy style). [DEV ONLY]
  > *Implementation: FastAPI endpoint `/api/geolocate` accepts base64 image → calls OSV5M / GeoSpy API;
  > returns `GpsCoordinate` ValueObject; rendered as LatticeObject pin on CesiumJS globe.*
- [ ] **Ghost Security Hardening Protocol:** Autonomous MAC randomization and VPN rotation. [DEV ONLY]
  > *Implementation: PowerShell `Set-NetAdapter -MacAddress` scheduled via Windows Task Scheduler;
  > Mullvad/ProtonVPN CLI toggle via `IVpnService` interface. Controlled by `OmniOpSecUseCase`.*
- [ ] **3D Global Asset Awareness Environment:** Transition to **CesiumJS** 3D globe. [ORACLE SAFE]
  > *Implementation: Replace Leaflet `MapView.jsx` with `CesiumGlobe.jsx` using `@cesium/engine`;
  > Ion token in `VITE_CESIUM_TOKEN` env var; existing `LatticeObject` arrays map to
  > `Cesium.Entity` with `LabelGraphics` and `BillboardGraphics`.*

**[MEDIUM PRIORITY]**
- [ ] **Spectre Side-Channel Bridge:** HackRF integration for encrypted leakage detection. [DEV ONLY]
- [ ] **Blue Line Calibrator:** Automated SDR tuning for law enforcement asset awareness. [ORACLE SAFE - View Only]
- [ ] **Persistent Car Asset Awareness (ALPR):** Developers set targets; users view live GPS. [ORACLE SAFE - View Only]
- [ ] **WiFi CSI Vision (DensePose):** Render 3D skeletons through walls. [DEV ONLY]

**[LOW PRIORITY]**
- [ ] **HiveMind SDR Mesh:** Distributed SIGINT net via co-opted IoT nodes. [DEV ONLY]
- [ ] **Vault Logic Verification Suite:** Biometric voice verification analysis and session logic verification. [DEV ONLY]
- [ ] **3D Projective CCTV:** Snapping live feeds to 3D geometry. [ORACLE SAFE - View Only]

## [OMNI-CORE] OMNI Development Lifecycle (Phase 0-8)
*Detailed architecture integration derived from the OMNI Builder's Book v4 and Planning Manual v5. Emphasizes the "Plugin-Edged" shell and bounded context discipline.*

- [ ] **Phase 0: Language & Model Alignment:** System metaphor, ubiquitous language, and bounded contexts.
- [x] **Phase 1: Shell & Trust Foundation:** Native desktop shell, mode badges, login, and audit spine.
  > *v1.9.1: OmniShellPage nav audit — all 27 modules wired + Download entry added to AllModules for Ctrl+K search.*
  > *2026-04-23 (v2.7.1): Shell boot fault resolved — missing XAML resources `OmniPageHeadingStyle` (added to `Styles/OmniColors.xaml`) and `OmniHeadingFont` (added to `Styles/Typography.xaml`) were tripping `CreateSafeBootWindow()` into A9-only safe-boot. OmniShellPage tab strip canonicalized from 28 -> 16 tabs to match the `AllModules` array (13 redundant tool tabs removed; tools now auto-run via UTT orchestrator + Arion passive collection). Sovereign-mode env bypass added to `backend/src/app/core/dev_auth.py` (`INVINCIBLE_APP_MODE=sovereign`) so `require_developer` / `require_tier(...)` no longer 401 on the invalid-signature sovereign JWT; localhost-bound, safe. Watchdog health-check timeout raised 3s -> 10s in `BackendService.IsAlreadyRunningAsync()` to stop false-positive restart cascades under GIL contention. v2.7.0 installer artifacts locked read-only as permanent historical reference.*
- [ ] **Phase 2: Domain Core & Contracts:** Entities, value objects, and action policies.
- [x] **Phase 3: Map & Workspace Skeleton:** Map layers, timeline, and selection panels.
  > *v1.9.1: Fullscreen toggle added to GeospatialPage (WORLDVIEW), MapLabPage (MAPS), and UttPage (UTT). Collapse header/panels/controls for full-viewport map immersion.*
- [x] **Phase 4: Entity Explorer & Case Workspace:** Identity profiles, evidence linking, and task boards.
  > *2026-04-23: Vault profile accumulator backend (V01) and Vault PROFILES UI (V03) in flight on isolated worktrees — `profile_accumulator.py` service, `profiles` + `profile_scan_history` SQLite tables, dedup precedence (email > phone > MAC > wallet > domain > IP > plate > name), `GET /api/vault/profiles` + `GET /api/vault/profile/{id}`, append-merge dossier generator, PROFILES tab default post-unlock.*
  > *2026-05-20 (22:00Z): Landed `app/core/case_workspace.py` (Case aggregate + NEW/ACTIVE/SUSPENDED/CLOSED/REOPENED state machine + transition ledger + cross-cutting rollup), `app/core/evidence_linker.py` (polymorphic linker — kinds: entity/encounter/signal/file/url/note/dossier/alert/provenance/custom; verify/reject/reclassify/tier-change + append-only chain-of-custody ledger; 32 KiB inline body cap; UNIQUE(case_id,kind,ref) dedupe), `app/core/task_board.py` (per-case Kanban: OPEN/IN_PROGRESS/BLOCKED/DONE/CANCELLED with allowed-transition guard, LOW/NORMAL/HIGH/URGENT/CRITICAL priority, `due_ms` overdue queue, `task_dependencies` edges with cycle detection + open-dependency block on DONE), `app/api/case_workspace.py` (28 distinct paths / 34 method-paths under `/api/case-workspace/`, T-2). 6 new DB tables (`cases`, `case_state_transitions`, `evidence_links`, `evidence_custody`, `case_tasks`, `task_dependencies`, `task_transitions`) with 22 indexes total. `/api/case-workspace` added to `_SPA_BYPASS_PREFIXES`. Merged `/cases/{id}/timeline` feed fuses case transitions + task transitions + evidence custody into a single chronologically-sorted dossier event stream. Strictly additive — zero existing endpoints removed.*
- [ ] **Phase 5: Alert Triage & Workflow Center:** Action forms, dry-runs, and approval chains.
  > *2026-04-23: UTT auto-run pivot landed (PR #31 / #32 / #33). `POST /api/intel/resolve` fact-resolver classifies selectors and fans out enrichment. `POST /api/missions/auto-run` orchestrates 14 tools (sigint, identity, surveillance, blockchain, easm, triage, adsb, aip, mesh-watchlist-check, recruit, zones, nmap, pcap, ports) with INTEL (passive) and ATTACK (active) modes. UttPage's 15-button tool rack was replaced with an AUTO-RUN STATUS panel; dead-zone extrapolation cap lifted from 30s to 150s with Green/Amber/Red staleness flags.*
  > *2026-05-27T00:14 local: Workflow Center backend landed — `app/core/action_forms.py` (~660 LOC) + `app/api/action_forms.py` (13 routes under `/workflow` + `/api/workflow`). Declarative `ActionTemplate` registry, `FieldSpec` schema validation, 11-state lifecycle (DRAFT→DRY_RUN_OK→AWAITING_APPROVAL→APPROVED→EXECUTING→EXECUTED with REJECTED/CANCELLED/EXPIRED/FAILED side branches), multi-tier signed approval chains (`ApprovalRequirement.min_tier` + `quorum`, double-sign rejected, mid-chain REJECT verdict locks state), and an immutable per-form execution ledger with `chain_signers` snapshot. 4 new SQLite tables: `action_forms`, `action_form_approvals`, `action_form_transitions`, `action_execution_ledger` (12 indices total). 3 built-in templates auto-registered: `workflow.broadcast.alert` (T-2), `workflow.case.retier` (T-2 + T-3), `workflow.diagnostic.echo` (T-2 self-test). `/workflow` added to `_SPA_BYPASS_PREFIXES`. Strictly additive — zero endpoints removed; the per-endpoint `dry_run=` flags in `api/arion.py` + `api/cctv_fusion.py` remain in place.*
- [x] **Phase 6: Source Explorer & Provenance:** Feed catalogs, schema health, and data lineage.
  > *2026-05-19 (16:00Z): Landed `app/core/source_catalog.py` + `app/core/provenance_ledger.py` + `app/core/source_catalog_bootstrap.py` (51 canonical feeds: 14 ingest, 19 processing, 6 external, 4 sensor, 3 operator, 5 agent) + `app/api/source_explorer.py` (11 endpoints under `/api/source-explorer/`, T-2). 3 new DB tables (`source_feeds`, `source_feed_health`, `provenance_records`) with 7 indexes. 4-tier freshness status ladder (LIVE/DEGRADED/STALE/OFFLINE). Wired into `ingest/scanner.py` (heartbeat on adapter start) and `processing/aggregator.py` (2-hop provenance per encounter, upstream-scanner → processing.aggregator linked via `parent_record_id`). WinUI 3 `SourceExplorerPage.xaml(.cs)` + `OmniShellPage` registry entry. Strictly additive — zero existing endpoints removed.*
- [x] **Phase 7: Offline & Degraded Modes:** Queued sync, local cache policy, and reconnect logic.
  > *2026-05-19 (21:00Z): Landed `app/core/offline_queue.py` (durable PENDING/IN_FLIGHT/DRAINED/DEAD queue with backoff ladder 0s..3600s, max 8 attempts, dedupe_key idempotency, 64 KiB payload cap, 24h/30d janitor TTL), `app/core/local_cache_policy.py` (4-tier RAM+SQLite cache: EPHEMERAL 8MiB / SESSION 32MiB / DURABLE 256MiB / SOVEREIGN 64MiB with seal+unseal, LRU eviction, TTL expiry tick, 4 MiB per-entry cap), `app/core/reconnect_orchestrator.py` (LIVE/DEGRADED/OFFLINE link state from registered probes, drainer-handler dispatch keyed by op_kind, event ledger), and `app/api/offline_modes.py` (16 endpoints, 18 method-paths under `/api/offline-modes/`, T-2). 3 new DB tables (`offline_queued_ops`, `local_cache_entries`, `reconnect_events`) with 10 indexes. Default `catalog.freshness` probe ties into Phase 6 source_catalog. Strictly additive — zero existing endpoints removed.*
- [x] **Phase 8: Update, Rollback, & Diagnostics:** Staged packages, snapshots, and tray-driven release control.
  > *v1.9.1: Installer built (78MB, 0 errors/warnings), `dist_installer/Invincible_Omni_Setup_v1.9.1.exe` + `latest.exe` deployed.*

## Phase 5: Strategic Expansion (FUTURE)
- [ ] **Invincible Intelligence Portal:** Dedicated dev-only palantir environment.
- [ ] **Sovereign Mesh v2:** Peer-to-peer intelligence sharing.
- [ ] **Acoustic Signature Triangulation:** ShotSpotter-style detection.

## Phase 6: Geospatial AI Foundation (FUTURE)
- [ ] **Large Geospatial Model (LGM):** Training the sovereign neural visual positioning engine.
- [ ] **Side-Effect Data Collection:** Gamified visual collection from the Oracle user base.
- [ ] **Neural City Mirrors:** Automated Skyfall GS city generation.
 
---
 
<SPECIALIST_DEPLOYMENT_MATRIX>
- **Objective: System Architecture & Coordination** -> **Lead Specialist: [@claude]**
- **Objective: Low-Level System Compilation** -> **Lead Specialist: [@weaver]**
- **Objective: High-Fidelity UI/UX Synergy** -> **Lead Specialist: [@aether]**
- **Objective: Automated Deployment & Verification** -> **Lead Specialist: [@terminus]**
</SPECIALIST_DEPLOYMENT_MATRIX>
