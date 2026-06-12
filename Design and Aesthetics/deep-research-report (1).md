# Deep research on OMNI’s tab-by-tab and window-by-window structure

[Download the PDF](sandbox:/mnt/data/omni_ui_deep_research_v2.pdf)

## Scope, guardrails, and research basis

This report designs a **Palantir-inspired “data-to-decisions” operations console**: data integration, governed object modeling, map/graph/timeline analysis, alert triage, collaboration, provenance, reporting, and auditable workflows. It is grounded in public documentation for Palantir’s **Foundry Ontology**, **Workshop** (application builder), **Actions**, and the **Map** and **Timeline** interaction models; plus public references for investigative analytics UI patterns (maps + link analysis + timelines) from tools like i2/Esri and ArcGIS Pro Intelligence, and alert triage patterns from Splunk Enterprise Security. citeturn3view3turn4view1turn9view3turn4view2turn1search0turn0search3turn0search36turn1search1

A critical constraint: your prompt explicitly requests **offensive cyber**, **intrusive interception**, and other **harmful targeting** capabilities (e.g., “one-click exploits,” “payload delivery,” “DoS,” “signal triangulation intercepting RF/cellular pings”). I will **not** provide actionable implementation guidance for those categories. Instead, I keep them present as **verbatim scope placeholders** and describe only **UI containment**, **approval gates**, **auditing**, and **results ingestion** at a very high level, because that is the maximum safe level of detail. citeturn3view2turn9view3

Where Gotham specifics are not publicly documented in granular UI detail, I rely on (a) Palantir’s public safety/governance and platform materials, and (b) third‑party reporting and civil society analyses describing Gotham at a high level (integration of disparate data, object/relationship mapping, investigative workflows). citeturn9view1turn9view0turn3view2

## Reference patterns from Palantir and comparable “single-pane” tools

The strongest “how it’s shaped” clue from historical Palantir material is the **Applications + Helpers** split: “Applications” handle large analytical tasks (link analysis, persistent searching, geospatial analysis), while “Helpers” are smaller tools that operate inside the active application (filtered searching, temporal analysis, statistics, presentation tooling). citeturn3view0

Palantir’s modern public documentation for Foundry describes a closely related foundation:

- **Ontology as the operational layer**: an Ontology sits atop integrated digital assets (datasets, virtual tables, models) and maps them into “objects, properties, links,” plus “kinetic elements” (actions, functions, dynamic security) that support operational workflows. citeturn3view3  
- **Ontologies as a governed container**: an ontology stores object types, link types, action types, interfaces, shared properties, and resource groupings—and is tightly related to “spaces” and organizational markings (a practical way to tie collaboration to access control). citeturn9view2  
- **Actions as governed writeback**: Actions can create/modify/delete/link object data through defined rule sets (“action types”), with **auto-generated forms**, and with **granular permissioning**. citeturn9view3  
- **Workshop as the “app factory”**: Workshop emphasizes object-layer data, consistent design across apps, and higher interactivity than typical dashboards by using layouts and an events system. It explicitly calls out patterns like **inbox/triage apps** and **common operational pictures (COPs)** that include maps, stats, filters, and workflow links. citeturn4view1  
- **Maps and context menus**: the Map application can expose Ontology Actions on right‑click for points and shapes, supporting a consistent “select → inspect → act” rhythm. citeturn4view2  
- **Timelines as first‑class visualization**: Workshop documents a Timeline widget that renders objects as chronologically ordered events with configurable layers and event appearance. citeturn1search0  

This overall UI philosophy is consistent with non‑Palantir investigative tools:
- i2’s Esri connector describes an environment where analysts can view **charts alongside maps**, use **layers**, and run geospatial analysis in one workspace. citeturn0search3turn0search11  
- ArcGIS Pro Intelligence describes **link analysis** as building networks of objects and relationships to discover patterns, and notes that it is iterative with automatic and manual steps. citeturn0search36  
- Splunk Enterprise Security describes **risk-based alerting** as grouping multiple risk events and creating a risk notable only when criteria are met—an explicit design pattern for reducing alert overload and prioritizing investigations. citeturn1search1turn1search19  

## Global shell layout for OMNI

The most robust way to make OMNI feel “Palantir-like” is to treat it as a **desktop mission console**: the shell persists, and the center workspace swaps. This aligns directly with Workshop’s concept of a persistent module header and multi‑page workflows, and with the older Application/Helper workspace concept. citeturn4view0turn3view0

### The layout skeleton

**Top header (always visible)**  
Contains: (1) global search, (2) workspace/app switcher, (3) “Create” menu (new case, new view, new report), (4) notifications, (5) user/security status, (6) export/share. Workshop explicitly frames the header as a persistent toolbar for titles, tabs, and buttons, and supports both horizontal (top) and vertical (left) orientations with collapsibility. citeturn4view0

**Left application rail (primary navigation)**  
A stable set of major tabs (applications): Home, Object Explorer, Cases, Map, Graph, Timeline, Alerts, Data, Tools, Workflows, Reports, Admin, Builder (optional). This is your modern equivalent of “Application Bar.” citeturn3view0turn4view0

**Center workspace (the work surface)**  
One main canvas depending on tab: map canvas, graph canvas, timeline, triage table, workflow builder, etc.

**Right helper stack (context-sensitive helpers)**  
This is where you replicate the Palantir “Helper Tabs,” but with tighter UX discipline:
- Inspector (properties, links)  
- Provenance / lineage  
- Filters and statistics  
- Applicable actions (the “act” drawer)  
- Presentation / snapshot tools  
This matches the Application/Helper split described in the older platform deck and the Ontology/Actions emphasis on “workflows.” citeturn3view0turn3view3turn9view3

**Bottom strip (operational state)**  
Jobs, background computes, ingest status, sync/offline state, and audit breadcrumbs. This is crucial if you expect disconnected/degraded operations. Palantir positions Apollo as a deployment layer with monitoring and rollback, and Palantir has public materials describing compliance-aware change management and rollback patterns—those only work in practice if the operator can see system state. citeturn0search26turn0search32turn3view2

image_group{"layout":"carousel","aspect_ratio":"16:9","query":["Palantir Foundry Workshop interface screenshot","Palantir ontology diagram Foundry","link analysis graph visualization intelligence software","geospatial common operational picture dashboard map"] ,"num_per_query":1}

## Tab-by-tab and window-by-window structure

This section specifies each major window/tab as a first-class “application,” and describes: what it does, what’s on screen, the essential buttons, and why it is shaped that way based on the research anchors.

### Login and session gateway window

**Purpose**: no data access until the user is authenticated and policy gates are satisfied.

**Layout**  
Center card:
- Username + authentication factor(s)  
- Environment selector (Prod / Training / Test)  
- “Offline / limited mode” indicator (read-only cached workspaces if permitted)  
Footer:
- Legal banner + acceptable use acknowledgement  
- Client posture summary (“compliant / needs remediation”)  

**Why this window must be “heavyweight”**  
Palantir’s privacy/governance materials treat privacy, governance, and security as core platform features and emphasize oversight/control of access and use (not add-ons). Your app’s first screen should communicate the same posture. citeturn3view2

### Home tab

**Purpose**: an operator’s “start shift” view: what needs attention, what changed, and what’s pinned.

**Layout**  
Grid of tiles (center workspace), each opening a deeper view:
- “My alerts” (count by severity)  
- “My cases” (assigned/in-progress)  
- “Saved searches / monitors”  
- “Data freshness” (ingest health by source category)  
- “Recent objects/views”  
- “Briefs in progress”  

**Why**  
The older Palantir platform deck describes a Dashboard as the first place analysts see on login and as a place to manage investigations and persistent searches. Treat Home as the “top-level cockpit,” not a vanity dashboard. citeturn3view0

### Object Explorer tab

**Purpose**: browse and search across governed object types and saved object views.

**Layout**  
Left: object type list + favorites  
Center: object list/table for selected type (sortable, filterable)  
Right helper: object inspector + provenance + actions

**Key controls**
- “Search within type” + filter chips  
- “Save view” / “Publish view” (role-gated)  
- “Open in Map / Graph / Timeline”  

**Why**  
Palantir’s Ontology framing explicitly connects object modeling to user-facing tools including Object Explorer and actions-based workflows. citeturn3view3turn9view3

### Global Search window

**Purpose**: the fastest “find → pivot” interface.

**Layout**  
Top: one global search bar  
Center: results tabs (Objects / Documents / Media / Events)  
Right helper: preview panel with (a) properties, (b) links, (c) provenance summary, (d) applicable actions

**Why**  
The older Palantir deck emphasizes a platform-wide search/discovery layer where data can be searched simultaneously, supporting link discovery that might otherwise be missed. citeturn3view0

### Case Workspace tab

**Purpose**: bind together evidence, hypotheses, tasks, views (map/graph/timeline), and outputs (briefs). This is the “where work lives” tab.

**Layout**  
Left: case tree
- Evidence (tables/docs/media)  
- Entities / Objects (curated set)  
- Views (saved map states, saved graph states, timeline layers)  
- Analysis artifacts (structured technique templates)  
- Tasks  
- Outputs (reports/briefs)  
Center: multi-tab case surface
- Summary  
- Evidence table  
- Analysis toolkit  
- Tasks  
Right helper:
- Inspector / provenance  
- Actions drawer (“do something with this selection”)  

**Built-in analytic technique templates (defensive and reasoning-focused)**  
Embed structured analytic methods as **case artifacts** (stored, reviewable, exportable):
- Key Assumptions Check  
- Indicators / Signposts of change  
- Analysis of Competing Hypotheses (ACH)  
- Devil’s advocacy / Team A-Team B  
These techniques are explicitly described as ways to challenge judgments, mitigate bias, stimulate creativity, and manage uncertainty in the USG tradecraft primer. citeturn2search0

**Why**  
If you want Palantir-like “actionable intelligence,” you must preserve *how you got there* (assumptions, alternatives, evidence quality), not just the conclusion—both for analytical quality and governance. The tradecraft primer explicitly targets cognitive pitfalls and supports structured review. citeturn2search0

### Map tab

**Purpose**: COP-style geospatial workspace: layers, filtering, and time-aware exploration.

**Layout**  
Center: map canvas  
Left: Layers and Legend manager  
- Basemap selector  
- Object layers (points/lines/polygons)  
- Heat / density layers  
- Drawn layers (AOIs, buffers, routes)  
Top toolbar:
- Pan/zoom, draw point/line/polygon, measure, clear, snapshot  
- Time slider (global or per-layer)  
Right helper:
- Feature/object inspector  
- Provenance  
- Actions menu  

**Required interactions and buttons**
- **Right-click actions** on the map location and selected objects: show applicable Ontology Actions. Palantir documents point actions and shape actions as driven by action definitions (geopoint/geojson typed parameters). citeturn4view2  
- **Layer toggles** (show/hide/reorder) as first-class controls (i2/Esri describes layers as the surfaces displayed in a map window that can be shown/hidden/reordered). citeturn0search3turn0search11  
- **AOI monitoring as a monitorable query** (but keep it governance-safe): the older platform deck discusses persisting geospatial searches for constant monitoring of an area of interest; implement this only for authorized mission contexts with audit and policy gates. citeturn3view0turn3view2  

**Why**  
Workshop explicitly calls out COP apps as a common pattern: a map, statistics and charts, filters, drilldowns, and workflow links. citeturn4view1

### Graph tab

**Purpose**: link analysis and relationship reasoning.

**Layout**  
Center: graph canvas  
Left: palette + saved graph views + expansions  
Right helper: node/edge inspector, provenance, actions, layout controls

**Key controls**
- Layout: force-directed / hierarchical / radial  
- Expand: neighborhood expansion (policy-limited), “show shortest path” (if permitted)  
- Styles: edge labels, node icons, cluster coloring  
- Presentation: save named graph states, export as image to briefing builder  

**Why**  
The older Palantir deck describes a Graph application as one of the most critical apps for communicating analytical conclusions, highlighting interactive exploration and automated layout/presentation support. citeturn3view0  
Link analysis is also explicitly described in ArcGIS Pro Intelligence documentation as an iterative process to discover hidden relationships. citeturn0search36  
If your back end uses a property-graph conceptual model, Neo4j’s documentation offers a clean mental model: nodes (entities), relationships, and properties. citeturn1search2turn1search9

### Timeline tab

**Purpose**: make time legible across multiple object types (events, status changes, movement, tasks).

**Layout**  
Center: timeline widget  
Left: layer configuration (each layer = one object set)  
Right helper: event inspector + “jump to map” + “jump to graph”

**Key controls (must be present)**
- Multiple layers across object types  
- Choose date/timestamp property per layer  
- Event title selection (object title, property title, or custom)  
- Ordering (newest/oldest first), orientation, conditional appearance  
These are explicitly described in Palantir’s Timeline widget documentation (layers, ordering, event properties and appearance). citeturn1search0

**Why**  
Time is the glue between map and graph. A strong timeline gives you the “scrubbable narrative” feel that operational tools need, and it’s consistent with Palantir’s documented visualization widget set. citeturn1search0

### Alerts and Inbox tab

**Purpose**: triage, prioritize, and route signals into cases without flooding operators.

**Layout**
Left: queue selector (My queue / Team queue / Watchlists / High risk)  
Center: alert table (sortable, filterable)  
Right: alert details + linked objects + evidence preview + dispositions + “Open case”

**Key controls**
- Disposition buttons (benign / needs review / escalate / closed)  
- Bulk actions (assign, merge alerts, open case)  
- “Risk roll-up” view (group related alerts under a single “notable”)  

**Why**
Workshop explicitly calls out “Inbox Alert and Task Management” as a common application pattern used for triage and completing tasks. citeturn4view1  
Splunk Enterprise Security’s risk-based alerting explains a concrete design paradigm: collect events, aggregate them, and generate a risk notable only when criteria are met—reducing alert volume and better prioritizing investigations. citeturn1search1turn1search19

### Data Sources and Catalog tab

**Purpose**: a governable “what data exists, where did it come from, how fresh is it, who can access it” surface.

**Layout**
Left: source categories (internal systems, partner feeds, public datasets, streaming sources)  
Center: catalog table (source, schema, freshness, lineage, quality)  
Right: access policy + request-access workflow + retention/marking summary

**Why**
The older Palantir platform deck describes Data Sources as a high-level review of ingested data and the ability to organize sources via collections. citeturn3view0  
Palantir’s governance framing treats oversight and control over how data is accessed and used as central. citeturn3view2  
Databricks’ Unity Catalog architecture documentation reinforces that governance, access control, and data organization are foundational in real-world data platforms (even though tech stacks differ). citeturn5search2

### Tools Directory tab

**Purpose**: “every tool in OMNI,” categorized, permissioned, audited, and discoverable.

**Layout**
Left: category tree  
Center: tool cards
- Name  
- What it does (1–2 sentences)  
- Inputs/outputs  
- Required permissions + markings  
- Audit/emission footprint (“this invocation is logged”)  
Right: run panel (safe input preview; “submit for approval” if required) + run history

**Why**
Palantir’s Actions model exists specifically to turn complex object edits into meaningful, secure building blocks that can be reused across applications and granularly permissioned. “Tools Directory” is where Actions and other governed primitives become navigable to humans. citeturn9view3

### Workflows tab

**Purpose**: multi-step operational workflows with explicit approvals, logging, and rollback to a safe state.

**Layout**
Left: workflow library  
Center: workflow canvas (steps, branching, approvals)  
Right: run history, approvals, and rollback controls

**Why**
Palantir’s documentation on connecting analytics to operations emphasizes transition from ad-hoc analysis to operational workflows, and the Ontology model frames actions/functions as “kinetic” change mechanisms. citeturn1search5turn3view3turn9view3

### Reports and Briefing tab

**Purpose**: convert workspaces into shareable briefs (PDF) and slide-like narratives, including evidence/provenance.

**Layout**
Center: storyboard / slide builder  
Right: artifacts palette (map snapshot, graph state, timeline slice, KPI cards, cited evidence list)  
Export: PDF; optionally PPTX depending on environment policy

**Why**
The older Palantir platform deck describes a Summary application that rapidly produces reports and can collate graph states into PowerPoint, exporting quickly—and emphasizes including the investigative path that led to conclusions. citeturn3view0

### Admin and Governance tab

**Purpose**: the platform is only “god-view” in a safe sense if governance is real: roles, audits, markings, retention, schema change review.

**Layout (sub-tabs)**
- Users and Roles  
- Markings and Spaces  
- Audit Viewer (“who accessed what, when”)  
- Action Permissions  
- Data retention  
- External integrations  
- Client posture and device status  

**Why**
Palantir’s privacy/governance whitepaper frames privacy and civil liberties protection as part of responsible data integration and analysis, and highlights oversight/control over access and use. citeturn3view2  
Palantir’s ontology docs explicitly include permission checks and user edit history concepts, reinforcing that governance must be built into the modeling layer rather than bolted on later. citeturn3view3turn9view2

## Tools window taxonomy with your categories preserved safely

You requested a Tools window that includes categories like tracking, scanning, execution, offensive, defensive, and that I may adjust them based on Palantir-style structure. Below is a **two-layer taxonomy** that keeps your intent visible but uses a safer, Palantir-aligned organizing principle:

- **Semantic layer (what the world is):** objects, links, views, provenance  
- **Kinetic layer (what the platform can do):** actions, workflows, and integrations (permissioned) citeturn3view3turn9view3

### Safe-first tool families for the Tools Directory

**Ingest and Connectors**: connectors, schema mapping, streaming subscriptions, quality checks. citeturn3view0turn5search1  
**Search and Retrieval**: global search, saved searches, persistent monitors. citeturn3view0  
**Entity Resolution**: match/merge with confidence scoring, conflict resolution, justification capture, audit trail. citeturn3view0turn3view2  
**Geospatial Analytics**: layers, buffers/proximity tools, AOI monitoring with strong governance. citeturn0search11turn4view2  
**Graph and Link Analysis**: link graph views, iterative expansion, saved states for briefing. citeturn3view0turn0search36  
**Timeline and Change**: timeline layers, change over time views. citeturn1search0  
**Alerts and Prioritization**: rollups, risk scoring, triage, dispositions. citeturn1search1turn4view1  
**Reporting and Briefing**: storyboards, exports, evidence packs. citeturn3view0  
**Governance and Security**: permission checks, user edit history, audit logs, retention, policy simulator. citeturn3view2turn9view2

### Your capability list preserved verbatim with safe handling

Below is your text **verbatim**. I am keeping it visible, but I am not providing implementation directions for the categories that would enable wrongdoing. For those, OMNI should treat them as **restricted placeholders**: if ever present in a real system, they would be mediated through external, legally authorized systems and controlled approvals, with heavy auditing and governance. citeturn3view2

> **1. Tracking & Persistence (The "Eyes")**  
> This category focuses on maintaining a "lock" on targets across digital and physical domains.  
> Persistent Identity Resolution: Tools that link MAC addresses, IMEI numbers, and social media handles to a single "Gold Profile."  
> Geospatial Pattern-of-Life: AI that analyzes historical movement data to predict where a target will be at a specific time.  
> Cross-Platform Scraping: Real-time listeners for mentions, check-ins, or metadata leaks across the clear and dark web.  
> Signal Triangulation: Tools for intercepting and locating RF signals or cellular pings.  
> **2. Defensive Measures (The "Shield")**  
> These are internal-facing tools meant to protect the system and its operators from counter-intelligence.  
> Automated Counter-Surveillance: Systems that detect if the tool itself is being scanned, probed, or mapped by an outside entity.  
> Honey-Potting & Deception: Creating fake data "vines" to mislead anyone attempting to breach the system.  
> Zero-Trust Access Logs: Granular auditing that tracks exactly which analyst looked at which target to prevent internal leaks or "rogue" usage.  
> Traffic Obfuscation: Masking the system’s egress points so targets don't know they are being monitored.  
> **3. Offensive Capabilities (The "Sword")**  
> These tools move beyond watching and start interacting with or degrading the target's capabilities.  
> Vulnerability Research & Exploitation: A library of "one-click" exploits (Zero-Days or known N-Days) to gain access to target devices.  
> Information Operations (PsyOps): Automated botnets or "persona management" tools used to inject narratives or disinformation into a target's network.  
> Denial of Service (DoS): Tools to surgically take down a target's communication nodes or cloud infrastructure.  
> Payload Delivery: Systems to craft and deploy bespoke malware, ransomware, or spyware directly onto a tracked entity’s hardware.  
> **4. Analysis & Correlation (The "Brain")**  
> This is the central engine that makes sense of the Tracking, Defensive, and Offensive data.  
> Predictive Modeling: Algorithms that run "What If" simulations (e.g., "If we attack Node A, how does the target network re-route?").  
> Sentiment & Intent Analysis: NLP tools that scan a target's communications to determine if they are planning an action or losing morale.  
> Knowledge Graph Visualization: The "Gotham-style" web showing the spiderweb of connections between people, money, and assets.  
> **5. Tactical Tasking (The "Hand")**  
> The interface used to command physical or digital "Effectors."  
> Drone/Asset Orchestration: A single pane of glass to launch, fly, and retrieve hardware.  
> Strike Packages: Pre-configured "bundles" of offensive tools tailored for specific target types (e.g., "The IoT Shutdown Package").  
> Field Comms Integration: Bridging the gap between the software and boots-on-the-ground via encrypted tactical radio or satellite.

**How OMNI should represent restricted categories without enabling harm**  
- In the Tools Directory: show these categories as **“Restricted / External Integration Only”** with (a) a policy banner, (b) required approvals, (c) audit expectations, and (d) no embedded operational mechanics. citeturn3view2turn9view3  
- In Workflows: represent them as **approval-mediated workflow steps** (“request external effect,” “await authorization,” “ingest results”), not as local tools. citeturn3view2turn1search5  

## Architecture mapping to “design textbooks” and platform constraints

To keep a system this large coherent, you need a strict architecture. The cleanest mapping, based on widely used references, is:

### Clean Architecture for dependency boundaries

Use Clean Architecture’s **Dependency Rule**: dependencies point inward, and UI/database/framework details stay at the edge. This is presented directly in Robert C. Martin’s Clean Architecture material (sample chapter on the Dependency Rule). citeturn7search1turn7search31

**How this connects to the UI spec**  
- Each tab (Map/Graph/Timeline/Alerts/Cases) is an outer “delivery mechanism.”  
- The inner core is a stable domain: Objects, Links, Cases, Alerts, Actions, Workflows.  
- “Actions” become application use-cases with permission checks and audit emissions at the boundary. citeturn9view3turn3view3

### Domain-Driven Design for the Ontology experience

Domain-driven design pushes you toward a shared language and clear boundaries (“bounded contexts”). Eric Evans’ DDD reference defines **ubiquitous language** and **bounded context** and emphasizes focusing the team around explicit model boundaries. citeturn7search2turn6search14

**How this connects to OMNI’s tabs**  
Treat each major tab cluster as a bounded context with its own language and rules, but shared objects:
- **Investigations/Case Management** context: cases, hypotheses, evidence, dispositions  
- **Geospatial** context: layers, shapes, map actions  
- **Graph/Relationships** context: nodes, edges, graph views  
- **Alerting** context: detectors, findings, triage queues  
- **Governance** context: markings, roles, permissions, audits  
The ontology (semantic layer) is how you keep those contexts interoperable. citeturn3view3turn9view2turn7search2

### Effective Java mindset for safe, testable construction

Even if your client is C#/C++, the core “Effective Java” lessons translate well: prefer dependency injection, avoid hardwiring resources, and design APIs carefully. InformIT’s table of contents for Effective Java surfaces these early core items. citeturn7search30

**How this connects to OMNI**  
- Your “connector” interfaces (data sources, external services, workflow runners) should be swappable (DI), testable, and versionable. citeturn7search30turn7search1  
- UI modules should depend on interfaces that represent use-cases and object queries, not concrete implementations. citeturn7search1turn9view3  

### Deployment and offline realities

If OMNI must run across constrained environments, you need explicit support for updates, rollbacks, and visibility into deployment health. Public Apollo materials describe **single-pane monitoring**, **deployment health**, and **autonomous delivery**; and Palantir also describes compliance-aware and rollback patterns in recent public material. citeturn0search26turn0search32turn0search14

In the UI spec, that means:
- Bottom strip: connectivity, cache, job status, last sync time  
- Admin → Releases: version, channel, rollout status, rollback controls  
- Audit surfaces: changes tied to users, times, and approvals citeturn3view2turn0search26