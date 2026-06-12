# OMNI v4 Builder's Book
## A conversational handbook for planning and structuring a Palantir-inspired operational application
### for the hypothetical government-use project brief, translated through *Clean Architecture*, *Domain-Driven Design*, *Effective Java*, and supporting low-level engineering lessons

---

## Before we start

This file is the version that should have existed the last time.

This one is intentionally written like a builder talking to another builder. It is longer, more literal to your prompt, more explicit about the actual app layout, and much more aggressively grounded in the textbooks. It is also more honest about where I can go deep and where I need to stay high level.

So here is the rule for reading the rest of this handbook:

- if a part of your brief is normal product, architecture, UI, layout, modularity, offline behavior, update behavior, governance, or engineering process, I go detailed
- if a part of your brief drifts into sensitive surveillance, cyber, intrusion, or targeting territory, I keep your idea present but handle it only at the abstraction, governance, and workflow level
- 

That means this document is still useful as a serious planning manual,.

---

# Part 1. What you are actually trying to build

Let’s strip the noise away first.

You are not really trying to build “an app with a map.”

You are trying to build a **decision system** that does five things at once:

1. It ingests many kinds of data.
2. It translates that data into a stable real-world model.
3. It gives users a common workspace for understanding what is happening.
4. It allows those users to move from understanding to action.
5. It keeps working even when the environment gets ugly, degraded, or disconnected.

That last point matters a lot. A lot of people accidentally design software as if the happy path is the only path. Your prompt does not do that. Your prompt keeps forcing the system into three environments:

- normal connected mode
- severe outage mode
- one-machine doomsday mode

That is actually a good architectural forcing function. It means the system cannot depend on any one fancy cloud assumption. It has to separate what is **core** from what is **optional**, what is **local** from what is **remote**, and what is **required for mission continuity** from what is **just nice when the network is perfect**.

That way of thinking lines up almost perfectly with *Clean Architecture*: the real value is the policy and use-case behavior, while databases, frameworks, web layers, and other delivery details are details that should be kept from owning the core of the system. The point is to keep options open and prevent UI, database, and framework choices from dictating the business rules. That book also argues for drawing boundaries where things change for different reasons and arranging the system as plugin-like edges around stable core rules. That is exactly the stance you want for OMNI. fileciteturn8file1 fileciteturn8file6

*Domain-Driven Design* pushes the same idea from another angle. Instead of starting from tables, endpoints, and widgets, it says you build understanding by “knowledge crunching” with domain experts, refining a shared model, binding that model to the implementation, and using a ubiquitous language so the code, the product language, and the team language line up. It also says you should define bounded contexts instead of pretending one giant model will cleanly cover everything. That is incredibly relevant for a system like this because a geospatial workspace, an alert triage system, an identity model, an approvals engine, a source catalog, and an update/rollback engine should not all be stuffed into one muddy conceptual pile. fileciteturn9file0 fileciteturn8file17

Then *Effective Java* comes in and gives you the practical engineering discipline layer: prefer dependency injection to hardwired resources, use builders when object creation gets complex, minimize mutability, favor composition over inheritance, use interfaces to define contracts, design APIs carefully, validate parameters, document exposed API elements, and use modern concurrency utilities rather than ad hoc threading. Even if OMNI is not “a Java application,” these are still excellent engineering habits for any serious multi-language system. fileciteturn8file11 fileciteturn8file12 fileciteturn8file13

And the C textbook still contributes something useful here: top-down programming and modularity. You keep the high-level behavior readable, then push the details down into smaller modules and functions. That lesson still applies whether the final shell is C#, the heavy lifting modules are C++, or some services are in other languages. fileciteturn8file5

So the short version is this:

**OMNI should be built as a domain-first, use-case-first, plugin-edged, operational desktop system with a stable core model and replaceable delivery details.**

That one sentence is the whole book in miniature.

---

# Part 2. The source brief, treated as the governing requirement

I’m going to be more literal this time.

This handbook is based on your prompt as the governing brief. Not just the cleaned-up version. The prompt itself.

There are a few sections of your brief that define the shape of the project more than anything else. I want those visible here, because if we hide them, we end up drifting away from what you actually asked for.

### Your brief, preserved in spirit and where needed in exact wording

> “We want to make a palantir look alike app visually and functionally that has a god view level of control, view and actions, like gotham and other palantir apps that take tons of data and turn it into useable actions...”

That is the visual and operational ambition.

> “The users of this app will be military and government personel... image data, gps data, signals (wifi, bluetooth, ssid, lte and all other types of signals) osint, camera data, traffic data, literally every type of data imaginable...”

That is the breadth-of-data ambition.

> “the purpose of this app will be to use the massive amount of data and intuitively use it to provide targets, generate plans of action, such as surveillance, pentesting, tracking, alerts, and others...”

That is the action-and-recommendation ambition. This is also one of the sensitive areas. So in this handbook, I keep that as a requirement statement, but any guidance around it stays at the workflow, governance, approval, orchestration, and authorized-tooling level only.

> “This apps primary platform will be on windows as a native windows app built with c#, c++, and all other langueages needed...”

That is the platform ambition.

> “the app will once downloaded have a secure login required before the actual app can be accessed... will work fully and be able to function in a doomsday scenario when all servers are down...”

That is the continuity and resilience ambition.

> “there will also be a tray icon... check for updates... revert option... saved older versions... error diagnostics... forwarded to the server...”

That is the desktop-operability ambition.

> “break up the work into attainable sections that can be made independently before being integrated into the windows app.”

That is the delivery-model ambition.

Those are the bones. Everything else in this handbook hangs on those bones.

---

# Part 3. The public-reference inspiration layer, without pretending we know proprietary internals

This is the honest way to use outside inspiration.

From Palantir’s public docs, the parts worth learning from are not “secret internals.” They are the patterns Palantir openly talks about:

- an **ontology** as an operational layer sitting on top of datasets, tables, and models and connecting them to real-world entities
- **actions** and **functions** as controlled ways to move from read-only insight into governed writeback and execution
- **Workshop** as a way to build interactive operational applications, not just static dashboards
- map/geospatial interfaces with recognizable structure: left-side layers and find/filter controls, right-side selection and action context, bottom time-series or temporal analysis, and top-level interaction tools like select, draw, measure, annotate, capture, and search-around style exploration
- operational apps that are valuable because they capture decisions and move workflows forward, rather than just displaying data

Those are publicly documented concepts and they are worth learning from. Public Palantir docs describe Workshop as a builder for interactive applications over object data, emphasize consistent design and event-driven interactivity, describe the Ontology as an operational layer or digital twin containing both semantic and action-oriented elements, and define operational applications as workflows that drive decisions and capture decisions through governed writeback. Their public map docs also show a very clear screen pattern: left panels for layers/find/histogram/info, right panels for selection and time, a bottom series panel, and a top toolbar with select, draw, capture, measure, annotate, and delete functions. citeturn397557view0turn397557view1turn397557view2turn397557view3

From Bilawal Sidhu’s public material, the useful lesson is the **feel** of a geospatial command center that layers open-source signals onto a shared globe or map and makes the combined timeline more important than any single source by itself. Public descriptions of WorldView frame it as a geospatial command center fusing open-source feeds onto a 3D globe, with the real value coming from layering multiple signal streams onto one time-synchronized visual surface. citeturn397557view4

So if we say “Palantir-like,” the safe and intellectually honest interpretation is this:

- ontology-like real-world modeling
- operational applications instead of passive dashboards
- geospatial and temporal workspaces
- action and approval flows
- a disciplined, consistent design system
- modular data integration
- human users making decisions on top of governed workflows

That is enough inspiration to build a serious system without pretending we reverse engineered somebody else’s platform.

---

# Part 4. The textbook rules, translated into OMNI build rules

This section is important, because this is where I stop talking abstractly and start turning the books into build instructions.

## 4.1 Clean Architecture translated into OMNI rules

### Rule 1: Policy beats detail

Your system should treat these as details:

- UI framework
- map vendor
- AI provider
- database technology
- message bus choice
- update transport
- telemetry provider
- storage engine
- cloud vs local hosting
- single-machine vs multi-node deployment

Your system should treat these as policy:

- what an entity means
- what a case means
- what an alert means
- what an action means
- who can do what
- what approval is required
- what state transitions are legal
- how evidence links to entities and cases
- how offline mode changes allowed operations
- what gets cached locally
- what gets synchronized later
- what “ready for action” means
- what “human review required” means

Why? Because the value of the system lives in those rules, not in whether you used one map SDK or another. *Clean Architecture* is blunt about this: policy is where the real value lives, while databases, web systems, servers, frameworks, and other IO or delivery mechanisms are details that should be kept from dictating policy. fileciteturn8file1

### Rule 2: The app should scream its use cases

If someone opens the repo or solution and the first thing they see is:

- `Controllers`
- `Db`
- `FrameworkAdapters`
- `GrpcClients`
- `EFCoreStuff`
- `MapGlue`
- `UIHelpers`

then you are already drifting.

The top-level structure should instead scream the business/application themes. Something like:

- `IdentityAndAccess`
- `EntityGraph`
- `CaseManagement`
- `AlertTriage`
- `MapWorkspace`
- `ActionOrchestration`
- `Approvals`
- `SearchAndDiscovery`
- `UpdateRollback`
- `OfflineMode`
- `AuditAndGovernance`

That way the software advertises what it does rather than what tools it uses.

### Rule 3: Put boundaries where the reasons for change diverge

Your UI changes for different reasons than your domain model.
Your data connectors change for different reasons than your action rules.
Your update system changes for different reasons than your entity-resolution logic.
Your offline cache changes for different reasons than your login screen.
Your AI provider changes for different reasons than your approval model.

So draw lines there.

*Clean Architecture* makes this point directly: boundaries should be drawn where there is an axis of change, and plugin-style arrangements are useful because they stop changes in one area from propagating into stable core rules. fileciteturn8file6

### Rule 4: Make the desktop shell a plugin edge, not the brain

This matters a lot.

Your Windows app should be a serious, native desktop shell. But it still should not own the rules of the system.

The shell is responsible for:

- composing screens
- presenting state
- coordinating user gestures
- hosting map canvas and panels
- handling local notifications
- exposing tray menu behavior
- invoking actions through application-layer services
- managing local encryption, local cache access, and sync orchestration

The shell is **not** responsible for deciding:

- what an entity is
- what constitutes a correlation
- whether a workflow step is legal
- who is allowed to run an action
- how approvals work
- how a case transitions state
- how a rollback is validated
- whether an alert is actionable

Those belong closer to the core.

### Rule 5: The system must be testable without the map, server, or cloud

If the logic cannot be tested without a full map, cloud backend, and live data feed, you have put the intelligence in the wrong place.

You should be able to run tests that answer questions like:

- when a user acknowledges an alert, what state changes happen?
- when an entity is merged, which links and evidence references survive?
- when mode drops from connected to degraded, which actions are disabled?
- when a new update package is staged, what validation gates must pass?
- when an approval chain is incomplete, what actions remain blocked?
- when an offline node reconnects, what conflict strategy is used?

None of those should require an actual map vendor or external API.

That is exactly the point of keeping details on the outside.

---

## 4.2 Domain-Driven Design translated into OMNI rules

### Rule 6: Do not start with tables. Start with language.

This is the biggest DDD lesson for this project.

Before you argue about schemas, first decide what words mean.

You need a language that both product and engineering use the same way. If you do not do this, the repo turns into a graveyard of semi-overlapping meanings.

You need crisp definitions for terms like:

- Entity
- Subject
- Asset
- Observation
- Detection
- Indicator
- Alert
- Lead
- Case
- Evidence
- Source
- Link
- Correlation
- Hypothesis
- Action
- Approval
- Assignment
- Watchlist
- Timeline Event
- Location Fix
- Route
- Sensor Layer
- Workflow
- Mission Board
- Snapshot
- Revert Package
- Mode
- Sync State
- Confidence
- Provenance

*Domain-Driven Design* argues that effective modeling comes from binding the model to the implementation, cultivating a language based on the model, building a knowledge-rich model, distilling what matters, and iterating through brainstorming and experimentation. It also stresses that good modelers are “knowledge crunchers” who refine meaning with domain experts rather than just collecting features. That is the right posture here. fileciteturn9file0

### Rule 7: Build bounded contexts on purpose

OMNI is too broad for one giant model.

So here is a sane bounded-context split.

#### Identity and Access Context
Owns:
- users
- roles
- clearances
- auth sessions
- auth methods
- environment mode restrictions
- capability grants
- local credentials cache
- break-glass access policy
- device trust

#### Source and Ingestion Context
Owns:
- source connectors
- feed metadata
- source health
- ingestion jobs
- parser definitions
- provenance metadata
- source licensing and legal-use metadata
- retention rules
- normalization pipelines

#### Entity Graph Context
Owns:
- entities
- aliases
- observations
- links
- relationship types
- deduplication/merge policies
- confidence and provenance links
- canonical identity for real-world things

#### Geospatial and Timeline Context
Owns:
- location fixes
- geometries
- routes
- overlays
- time windows
- map layers
- playback state
- bookmarks
- saved views

#### Alert and Triage Context
Owns:
- alerts
- alert severity
- alert grouping
- alert assignment
- acknowledgment
- triage decisions
- triage queues
- SLA timers

#### Case Management Context
Owns:
- cases
- case templates
- evidence bundles
- notes
- tasks
- attachments
- timelines
- case status
- case ownership

#### Workflow and Action Context
Owns:
- action definitions
- action parameters
- action policies
- approval requirements
- execution records
- writeback
- orchestration hooks
- side effects
- rollback markers for actions

#### Update and Platform Continuity Context
Owns:
- versions
- signed packages
- staged updates
- validation checks
- snapshots
- rollback points
- environment capability matrix
- offline package verification
- tray menu operations

#### Audit and Governance Context
Owns:
- immutable logs
- user activity
- decision records
- approval chains
- legal basis tags
- access audit
- retention
- tamper evidence
- review workflows

That is your first real DDD move: admit the whole thing does not belong in one model.

*DDD* is very explicit that bounded contexts are not just modules. They are boundaries where one model remains potent and coherent, while translation happens deliberately between contexts. It also says continuous integration needs to be relentless within a bounded context, while cross-context relationships must be explicit, usually via a context map. fileciteturn8file17 fileciteturn8file18

### Rule 8: Use a system metaphor so the team thinks the same way

The system metaphor I recommend is this:

**OMNI is an operations cockpit built on a living world model.**

That metaphor does useful work.

- “operations cockpit” tells you this is not a BI dashboard
- “living world model” tells you this is not just a pile of feeds
- “cockpit” implies action, permissions, alerts, queues, and operator workflows
- “world model” implies ontology, entities, relationships, provenance, and spatial/temporal context

*DDD* says a useful system metaphor should facilitate communication and guide development, but it should be dropped if it stops helping. This one is good because it helps both product and engineering talk about the same shape. fileciteturn8file15

### Rule 9: Keep business rules explicit, not buried in glue code

If a rule matters, it should be a named rule.

For example:

Bad:
- random if-statements in handlers
- magic thresholds inside a map widget callback
- approval logic scattered across controller code
- merge policy hidden in a SQL predicate
- case transition rules spread across five services

Better:
- `ApprovalPolicy`
- `EntityMergePolicy`
- `OfflineModeCapabilityPolicy`
- `AlertEscalationPolicy`
- `UpdateValidationPolicy`
- `ActionEligibilityPolicy`

That is exactly the DDD “make implicit concepts explicit” mindset. One of Evans’s examples is taking a hidden business rule and lifting it into an explicit policy object so the rule becomes visible and discussable. fileciteturn9file1

### Rule 10: Repositories should feel like domain access, not SQL leak points

If your app layer reads like this:

- `SELECT *`
- `JOIN thing`
- `hydrator`
- `DTO shape`
- `serialize row`

you are letting persistence language take over application language.

Instead, repositories should read closer to the domain:

- `FindEntityByCanonicalId`
- `SearchEntitiesMatchingWatchCriteria`
- `ListOpenAlertsForQueue`
- `LoadCaseWithEvidenceTimeline`
- `FindRoutesIntersectingArea`
- `ListPendingApprovalsForUser`
- `LoadUpdateSnapshotByVersion`

DDD does allow repositories to expose specialized query methods where useful, but the key idea is still that the model and its rules stay visible while infrastructure does the underlying persistence work. fileciteturn8file16

---

## 4.3 Effective Java translated into OMNI engineering rules

### Rule 11: Use builders for complex request objects

Anything with a lot of optional fields, environment flags, filters, or parameter groups should probably be built with a builder-style API.

Examples:
- `MapViewConfig`
- `EntitySearchRequest`
- `AlertQuery`
- `CaseCreationRequest`
- `ActionSubmissionRequest`
- `OfflineSyncPlan`
- `UpdateInstallPlan`
- `WorkspaceLayoutDefinition`

Why?

Because constructor soup becomes unreadable fast. And this project has a lot of “some required, many optional” objects.

### Rule 12: Prefer dependency injection everywhere the system touches the outside world

Hardwiring resources is how systems become rigid and untestable.

Inject:
- clock
- auth provider
- update feed provider
- map provider
- local secure store
- AI service adapter
- source connector registry
- export renderer
- audit sink
- encryption provider
- workflow executor
- cache policy provider

That way connected mode, degraded mode, simulation mode, and offline mode can use different implementations without ripping apart core logic.

### Rule 13: Favor interfaces and composition over inheritance

This one matters for plugins and UI panels.

Do not make one huge base class and derive half the application from it if you can avoid it. Favor interfaces plus composition.

Good examples:
- `IMapLayerProvider`
- `IEntityResolver`
- `IAlertScorer`
- `IActionExecutor`
- `IUpdatePackageSource`
- `ILocalSnapshotStore`
- `IWorkspaceModule`
- `IApprovalGate`
- `IAuditWriter`

Then compose implementations.

*Effective Java* is strong on this: favor composition over inheritance because inheritance across unstable concrete implementations creates fragile software, while wrappers, forwarding, and interface-driven designs are more robust and flexible. It also emphasizes interfaces, dependency injection, immutability where practical, and careful API design. fileciteturn8file12 fileciteturn8file13

### Rule 14: Make the core model as immutable as you reasonably can

There are two reasons.

First, a lot of the OMNI model is “fact-like”:
- observations
- evidence references
- captured source records
- audit log entries
- version manifests
- signed snapshots
- timeline events

Those should usually be append-only or immutable after creation.

Second, concurrency and synchronization get easier when fewer things mutate.

Mutable things should be explicit:
- UI state
- selection state
- active filters
- staged edits
- draft actions
- local sync queues
- update staging area

This is not dogma. It is just practical. *Effective Java* argues that classes should be immutable unless there is a very good reason otherwise, and that reducing the number of states an object can inhabit makes reasoning and correctness easier. fileciteturn8file13

### Rule 15: Design public contracts like someone else will curse your name later

Because they will.

Every exposed interface, integration contract, plugin contract, update manifest, layout schema, export format, and local snapshot schema should be treated as if it will be used by somebody you do not control.

That means:
- clear naming
- strong validation
- good error messages
- stable versioning
- backward compatibility strategy
- explicit nullability
- documented thread assumptions
- documented failure modes
- documented security expectations

That is straight out of the “design APIs carefully / write doc comments / validate inputs / use appropriate exceptions” mindset from *Effective Java*. fileciteturn8file11

---

## 4.4 The C textbook translated into low-level engineering rules

This is the part people often skip, but it matters.

If OMNI uses C++ sidecars or native performance modules, the C/C++ mindset is still useful:

- do top-down decomposition
- keep functions and modules readable
- divide the program into manageable pieces
- document intent clearly
- separate interfaces from implementation
- be disciplined about memory and resource ownership
- treat low-level utility code as boring, predictable, and well-tested

The C textbook’s section on top-down programming makes the point well: high-level behavior should stay readable, while lower-level details should be pushed into functions/modules so the structure is easier to read, write, debug, and maintain. That is exactly the right mindset for native sidecars and performance-critical helpers in a mixed-language desktop system. fileciteturn8file5

---

# Part 5. The actual structure of the app

This section is what you specifically asked for: the actual planned layout of how the app would appear and be structured.

I am going to describe it like you are opening the application for the first time and moving through it.

## 5.1 The visual design stance

You asked for Palantir-like. So here is the sane interpretation.

The UI should feel like:

- dark, focused, operational
- dense but not cluttered
- panel-based, not page-hopping
- map and timeline forward
- object and action aware
- consistent typography and spacing
- deliberate use of hierarchy
- strong keyboard support
- obvious status at all times
- low-friction switching between read, analyze, and act

The design should not feel like a marketing SaaS app.
It should not feel like a plain BI dashboard.
It should not feel like a toy globe demo.

It should feel like a **serious operator workspace**.

That lines up with public Palantir Workshop design principles around consistent design and interactive operational workflows, and with the public Palantir map interface pattern of a central map framed by functional panels for layers, filters, selections, and time. citeturn397557view0turn397557view3

## 5.2 The high-level shell

The entire application should live inside a persistent shell.

### Top bar
From left to right:

- **OMNI logo / workspace icon**
- **workspace switcher**
  - Command Center
  - Map
  - Alerts
  - Cases
  - Entities
  - Sources
  - Actions
  - Admin
- **global search box**
- **time range picker**
- **environment badge**
  - Connected
  - Degraded
  - Offline
  - Break-Glass
- **sync status**
- **notifications bell**
- **approvals inbox**
- **user profile / role / clearance indicator**

Why this structure?

Because operators need persistent awareness of:
- where they are
- what timeframe they are looking at
- what environment they are in
- what actions need attention
- whether the system is in sync

Do not bury those in settings.

### Left rail
A vertical icon rail, always visible:

1. Home / COP
2. Map
3. Entities
4. Alerts
5. Cases
6. Workflows
7. Sources
8. Search / Query
9. Reports / Exports
10. Settings / Admin

Optional:
- Saved Views
- Watchlists
- Mission Boards

The left rail is for primary navigation.
The top bar is for state and global controls.

### Center workspace
This is the main canvas. It changes based on the workspace.

### Right inspector
This stays conceptually consistent across most workspaces. It shows:
- selected item summary
- metadata
- linked records
- recent activity
- actions
- notes / comments
- provenance
- confidence
- approvals needed

### Bottom strip
Use this for one or more of:
- timeline
- playback controls
- logs
- job progress
- query console
- output console
- sync queue
- diagnostics

Think of it as the “secondary temporal and system feedback zone.”

---

# Part 6. The actual screens

Now let’s walk through the actual screens one by one.

## 6.1 Login screen

You specifically asked for a secure login screen that still works in doomsday conditions.

So the login screen should not be a generic splash page. It should be treated like a serious entry checkpoint.

### Layout
Center card with:
- OMNI wordmark
- environment tag
- node name / local machine identity
- connection status
- auth method dropdown
- username
- password / secret input
- optional hardware-token / smart-card prompt
- “Use cached credential for offline mode” toggle
- “Emergency local authority mode” hidden or restricted entry point
- Sign In button
- View system trust status link
- Legal / monitoring banner
- Build version and signature fingerprint

### Secondary info zone
Small footer or side pane:
- current mode
- last successful sync time
- certificate status
- whether update is pending
- offline package validity date

### Why
Because the login screen is also a trust screen.

Users should know:
- what node they are on
- whether the node is trusted
- whether the system is connected
- what authentication path is active
- whether they are entering an exceptional continuity mode

### Build guidance
- auth UI is presentation only
- auth policy belongs to Identity and Access context
- credential validation path should support multiple adapters
- local cached credential path must be tightly scoped and audited
- break-glass entry, if it exists at all, must be separately governed, separately logged, and extremely constrained

No further operational auth bypass specifics are needed here.

---

## 6.2 Home / Common Operational Picture screen

This is the “I need to know what is happening right now” screen.

### Layout
Center:
- map or geographic operational pane
- current area-of-interest visualization
- event overlays
- key movement/activity markers
- mission zones / watch zones / notable areas

Left pane:
- saved views
- active filters
- layer toggles
- watchlists
- status category filters
- region selector

Right pane:
- active incidents summary
- high-priority alerts
- selected object/entity details
- top recommended next reviews
- pending approvals affecting the current view

Top center quick cards:
- total active alerts
- open cases
- tracked entities / monitored assets
- source health
- sync state
- pending actions

Bottom strip:
- timeline playback
- event density histogram
- key moments bookmarks
- ingest lag indicator

### Important buttons
- Save View
- Duplicate Workspace
- Bookmark Time Window
- Pin Selection
- Send to Case
- Escalate
- Request Review
- Export Snapshot
- Open in Map
- Open in Case

### Why
Public Palantir material openly describes common operational picture style workflows as shared situational displays with maps, statistics, charts, filters, and drill-down flows. That is exactly what the home screen should be: a mission posture overview, not just a dashboard. citeturn397557view0

### Design notes
- avoid overstuffing this screen
- think “macro awareness”
- anything detailed should click through into a specialized workspace
- keep the alert lane visible, but do not let it overwhelm the spatial picture

---

## 6.3 Map workspace

This is probably the flagship screen.

And there is no reason to be vague here, because the layout itself is a normal UI design topic.

### The map workspace should be organized like this

#### Left column
Tabs:
1. Layers
2. Find
3. Filters
4. Info
5. Saved Maps

Inside **Layers**
- base map selector
- object layers
- signal/sensor layers
- traffic layer
- camera/event layer
- overlay manager
- draw layer
- heatmap / density layer
- route/path layer
- label visibility settings
- per-layer styling options

Inside **Find**
- search entities
- search coordinates
- search places
- search saved markers
- jump to area

Inside **Filters**
- by entity type
- by time range
- by status
- by region
- by confidence
- by source
- by case linkage
- by watchlist membership

Inside **Info**
- map summary
- visible item counts
- active AOI
- scale
- current projection / mode
- data recency summary

#### Center pane
The map itself.

Supported view modes:
- 2D map
- 2.5D operational view
- optional 3D globe mode
- split compare mode
- timeline replay mode

#### Right column
Tabs:
1. Selection
2. Actions
3. Provenance
4. Related
5. Time

Inside **Selection**
- summary card
- key identifiers
- latest known location
- confidence
- status
- source count
- last updated
- linked case(s)
- evidence summary

Inside **Actions**
- Add to Case
- Create Watch
- Create Alert Rule
- Open Timeline
- Open Relationships
- Request Approval
- Export Snapshot
- Annotate
- Assign
- Deconflict / Merge Review

Inside **Provenance**
- source lineage
- observation trail
- quality score
- chain-of-custody style trace for system purposes

Inside **Related**
- linked entities
- nearby items
- overlapping events
- associated alerts
- cases touching this object

Inside **Time**
- current timestamp
- range start/end
- play
- pause
- scrub
- jump to last update
- compare to prior time window

#### Top toolbar
Buttons:
- Select
- Box Select
- Lasso Select
- Search Around
- Draw Point
- Draw Line
- Draw Polygon
- Draw Circle
- Measure
- Annotate
- Capture Snapshot
- Split View
- Playback
- Clear Selection

#### Bottom timeline strip
- scrubber
- play/pause
- speed selector
- time bookmarks
- event density graph
- lane-based event tracks
- source lag indicator

This layout is not arbitrary. It is very close to the public patterns Palantir documents for map-oriented applications: left-side layers/find/filter/info controls, right-side selection and time context, bottom temporal analysis, and a top toolbar centered on select/draw/capture/measure/annotate interactions. citeturn397557view3

### Why this layout works
Because map users do three things over and over:

1. decide what is visible
2. inspect what is selected
3. act on what they selected

So the layout should literally map to those three things:
- left = visibility
- center = spatial awareness
- right = interpretation and action

That is a strong design pattern because it matches human flow.

---

## 6.4 Entity explorer

This screen is for entity-first work, not map-first work.

### Layout
Left:
- entity type filter
- search facets
- source filters
- confidence filters
- state filters

Center:
- results table or card list
- columns configurable per entity type
- saved searches
- bulk-select support

Right:
- entity detail inspector
- aliases
- identifiers
- linked observations
- relationship graph preview
- linked alerts/cases
- recent actions
- approval history

Optional bottom:
- raw record viewer
- evidence timeline
- diff view between candidate matches

### Important buttons
- New Search
- Save Search
- Pin to Watchlist
- Open on Map
- Open Relationship Graph
- Compare
- Merge Review
- Send to Case
- Export

### Why
Not every workflow starts from geography. Some start from a person, object, organization, device, vehicle, site, document, or case identifier. This screen is the domain-model-first complement to the map screen.

And if you are serious about DDD, this screen should reflect the ontology/entity model directly instead of flattening everything into generic rows.

---

## 6.5 Alert triage screen

This is the “inbox” or work-queue surface.

Public Palantir Workshop docs explicitly call out inbox alert and task management as a common operational application pattern. That is worth copying. citeturn397557view0

### Layout
Top bar:
- queue selector
- severity filter
- ownership filter
- status filter
- SLA filter
- saved triage views

Center main table:
- alert ID
- summary
- severity
- type
- source
- confidence
- age
- assigned to
- linked case
- action required
- status

Right pane:
- full alert detail
- why this alert fired
- contributing signals
- linked entities
- recent similar alerts
- recommended review path
- action buttons

Bottom pane:
- analyst notes
- activity log
- assignment history
- related event timeline

### Buttons
- Acknowledge
- Assign to Me
- Reassign
- Create Case
- Link to Case
- Suppress
- Escalate
- Request Approval
- Open on Map
- View Source Trail
- Mark False Positive
- Create Rule Adjustment Proposal

### Why
An alert screen should reduce cognitive load. Operators should be able to do triage in a repeatable rhythm:
- scan
- sort
- inspect
- decide
- route
- act
- audit

If they have to jump three screens just to assign an alert, your design is wrong.

---

## 6.6 Case workspace

This is where multi-step work lives.

### Layout
Header:
- case title
- case status
- priority
- owner
- team
- tags
- created date
- last updated
- approvals state

Left pane:
- case navigation tabs
  - Summary
  - Entities
  - Evidence
  - Timeline
  - Tasks
  - Notes
  - Approvals
  - Exports

Center:
- tab-specific content

Right pane:
- case action panel
- quick links
- linked alerts
- linked workflows
- audit summary

### Tab details

#### Summary
- narrative summary
- current objective
- scope
- lead analyst / owner
- latest developments
- open questions

#### Entities
- linked entity list
- role in case
- confidence
- last updated
- relationship graph entry point

#### Evidence
- evidence table
- attachment preview
- source lineage
- quality markers
- notes

#### Timeline
- event chronology
- bookmarks
- significant moments
- playback launch

#### Tasks
- task board
- due dates
- assignees
- blockers
- task templates

#### Notes
- analyst notes
- structured notes
- embedded links to evidence and entities

#### Approvals
- pending approvals
- completed approvals
- required approvers
- reasons
- decision history

#### Exports
- snapshot export
- report generation
- package creation
- chain-of-custody style metadata bundle for system recordkeeping

### Why
Cases exist because real work is not just “look at the map.” It is collect, interpret, compare, document, escalate, coordinate, decide, and retain.

This screen should feel like the place where the spatial picture, the entity model, the evidence model, and the approval model come together.

---

## 6.7 Workflow / action center

This is one of the most important screens because it is where the system proves it is not just a dashboard.

Public Palantir documentation is very clear that operational applications matter because they let users capture decisions through governed writeback. That is the key lesson here. citeturn397557view2

### Layout
Left:
- action categories
- favorites
- recent actions
- environment availability
- approval-required filter

Center:
- selected action form
- parameter sections
- validation
- preview of affected objects
- side effects summary
- simulation/dry-run support where appropriate

Right:
- policy summary
- approval requirements
- capability restrictions by mode
- impacted systems
- rollback note
- audit preview

Bottom:
- execution log
- previous runs
- queued actions
- conflict warnings

### Example action categories
- Entity updates
- Case workflows
- Alert routing
- Watchlist operations
- Data curation
- Export jobs
- Notification and routing
- Sync / repair operations
- Update / rollback admin actions
- Environment continuity actions

### Buttons
- Validate
- Dry Run
- Submit
- Submit for Approval
- Save as Template
- Clone
- View Policy
- Open Related Case
- Roll Back (only if supported and allowed)
- View Audit Trail

### Why
If actions are not explicit, the system becomes mysterious and dangerous.
If actions are too frictionless, the system becomes reckless.
If actions are too hard, the system becomes shelfware.

So the action center should walk the line:
- clear
- governed
- explainable
- logged
- mode-aware

---

## 6.8 Source explorer

This is the screen for data understanding, not just data consumption.

### Layout
Left:
- source categories
- health status
- connector type
- retention
- legal/compliance tags
- freshness

Center:
- source cards or table
- feed name
- type
- latency
- freshness
- schema version
- connector health
- last ingest
- current backlog

Right:
- source detail
- schema summary
- normalization status
- provenance notes
- quality notes
- current incidents
- related entities/cases/alerts

Bottom:
- sample record viewer
- parser diagnostics
- ingest logs
- mapping preview into ontology/entity model

### Why
Because operators and admins need to know not just “what the system says,” but “why the system can say that.” This is part of provenance and trust.

### Important buttons
- Pause Connector
- Re-run Job
- View Mapping
- View Lineage
- Open Diagnostics
- Compare Schema Versions
- Request Connector Review
- Mark Source Degraded

---

## 6.9 Search / query workspace

This is for users who think in queries more than panels.

### Layout
Top:
- query bar
- search mode selector
  - natural language
  - entity search
  - structured filter
  - graph traversal
  - time-window query
- save query
- recent queries

Center split:
- left results
- right preview / detail

Bottom:
- generated query explanation
- cost / latency info
- diagnostics
- result export options

### Why
Because some people will always want to type and search rather than click through filters.

### Design note
If you include AI assistance here, it should be treated as a drafting and explanation layer, not a silent authority.

---

## 6.10 Settings / admin

This is where a lot of desktop maturity shows up.

### Layout
Left nav:
- General
- Identity
- Devices
- Data Sources
- Layout Defaults
- Notifications
- Update Management
- Offline Packages
- Audit
- Performance
- About

### Notable areas

#### General
- theme
- display density
- default workspace
- keyboard shortcuts
- accessibility

#### Identity
- auth methods
- local cache policy
- session controls
- role mapping
- approval routing defaults

#### Devices
- device trust
- encryption status
- local secure storage status
- external display settings

#### Update Management
- current version
- staged version
- update channel
- last check time
- manual check
- rollback points
- validation logs

#### Offline Packages
- package validity
- sync scope
- retention policy
- cache usage
- secure wipe tools

#### Audit
- local audit queue status
- upload status
- export reviewed logs
- tamper alerts

### Why
Because “serious desktop application” is partly about giving admins operational control without forcing them into a browser portal for every basic platform function.

---

## 6.11 System tray icon

You explicitly asked for this, so it should absolutely be included.

### Tray icon menu
- Open OMNI
- Current Environment: Connected / Degraded / Offline
- Sync Status
- Pending Alerts Count
- Pending Approvals Count
- Check for Updates
- View Staged Update
- Install Approved Update
- Revert to Previous Snapshot
- Diagnostics
- Connectivity Test
- Offline Package Status
- Settings
- Restart Services
- Quit

### Why the tray icon matters
Because native Windows software earns trust when it behaves like real desktop software.

The tray icon is the “small operational control surface” when the main window is minimized or when the operator just needs to see state quickly.

### What it should not do
It should not execute hidden privileged behavior in the background with no audit. Keep tray behavior visible and logged.

---

# Part 7. The actual domain model

This is where DDD does the most work.

## 7.1 Core domain nouns

These are the starting nouns I would model first.

### Entity
A real-world thing represented by the system.
Examples:
- person
- organization
- place
- device
- vehicle
- installation
- account
- document
- route
- event-cluster

### Observation
A time-bound, source-bound record that says something was seen, inferred, reported, or captured.

### Source
A feed, connector, repository, stream, dataset, or adapter from which observations arrive.

### Link
A meaningful relationship between entities or between entities and observations.

### Alert
A system-generated or analyst-generated signal that something deserves review.

### Case
A human-managed work object that groups evidence, entities, tasks, and decisions.

### Evidence
A selected, retained, and referenced artifact supporting a case, alert, or assessment.

### Action
A governed operation that changes system state, external state, or workflow state.

### Approval
A decision gate that must be satisfied before certain actions can proceed.

### WorkspaceView
A saved operational perspective, including filters, map state, timeline state, selected layers, and layout.

### Snapshot
A preserved application or data-state package used for restore or rollback in defined contexts.

### Mode
An environment capability profile, such as Connected, Degraded, Offline, or Emergency-Local.

## 7.2 Core value objects

These should usually be immutable.

- EntityId
- SourceId
- CaseId
- AlertId
- ApprovalId
- Geometry
- Coordinate
- TimeRange
- ConfidenceScore
- ProvenanceRef
- VersionId
- SnapshotId
- ClearanceLevel
- RoleCode
- CapabilitySet

## 7.3 Likely aggregates

You asked for textbooks as instructions, so here is the DDD move: identify aggregates where consistency matters.

### Case aggregate
Holds:
- case summary
- status
- linked evidence references
- linked entity references
- tasks
- notes
- approvals
- audit markers

Why aggregate?
Because you want consistent case state transitions and controlled updates.

### Alert aggregate
Holds:
- trigger metadata
- severity
- triage state
- assignment
- related entities
- case linkage
- suppression/escalation history

Why aggregate?
Because triage, assignment, and escalation rules need consistency.

### ActionSubmission aggregate
Holds:
- requested action
- parameters
- target object refs
- policy result
- approval chain
- execution result
- rollback marker if applicable

Why aggregate?
Because action lifecycle is one of the most sensitive operational paths in the system.

### UpdatePackage aggregate
Holds:
- version metadata
- signature info
- staged status
- validation results
- install outcome
- rollback relation

Why aggregate?
Because update integrity is a continuity-critical flow.

### Workspace aggregate
Holds:
- layout
- panels
- filters
- time window
- saved layer state
- bookmarks

Why aggregate?
Because users expect a workspace to behave like a durable personal or team object.

---

# Part 8. The architecture, for real

Now let’s move from domain model to software structure.

## 8.1 The outer shape

The simplest mental model is this:

### Core
- entities and business rules
- use cases
- policies
- action eligibility
- approvals
- mode restrictions
- conflict resolution rules
- update validation rules

### Application layer
- orchestration
- commands
- queries
- use-case handlers
- DTOs / request-response shapes
- transaction boundaries
- workflow coordination

### Interface adapters
- desktop UI presenters/view models
- map adapters
- persistence adapters
- source connector adapters
- auth adapters
- export adapters
- AI adapters
- update feed adapters

### Frameworks and drivers
- WinUI / WPF / whatever desktop shell
- database tech
- map SDK
- storage engine
- secure enclave provider
- network clients
- background job runtime
- telemetry stack
- installer/updater tech

This is classic Clean Architecture. The Dependency Rule says source dependencies should point inward toward the most stable, high-level rules. Frameworks and drivers are on the outside. Use cases and entities are toward the center. fileciteturn8file7

## 8.2 Recommended solution/package structure

Something like this:

```text
Omni.Desktop
Omni.Desktop.Shell
Omni.Desktop.Tray
Omni.Desktop.Map
Omni.Presentation.Common
Omni.Application
Omni.Application.Identity
Omni.Application.Entities
Omni.Application.Alerts
Omni.Application.Cases
Omni.Application.Actions
Omni.Application.Updates
Omni.Domain
Omni.Domain.Identity
Omni.Domain.Entities
Omni.Domain.Alerts
Omni.Domain.Cases
Omni.Domain.Actions
Omni.Domain.Updates
Omni.Domain.Shared
Omni.Infrastructure.Persistence
Omni.Infrastructure.Auth
Omni.Infrastructure.Connectors
Omni.Infrastructure.AI
Omni.Infrastructure.Map
Omni.Infrastructure.Updates
Omni.Infrastructure.Audit
Omni.Infrastructure.Offline
Omni.Contracts
Omni.Tests.Unit
Omni.Tests.Integration
Omni.Tests.Architecture
Omni.Tests.Offline
Omni.Tests.Security
```

Optional native sidecars:

```text
Omni.Native.Geo
Omni.Native.Index
Omni.Native.SignalAdapters
Omni.Native.MediaProcessing
```

Again, the key thing is: the domain and application layers do not depend on those native details. The native pieces are plugins.

## 8.3 Why a native Windows shell still makes sense

Your prompt wants a native Windows app first, and that is actually defensible.

Reasons:
- serious desktop window management
- multiple-monitor workflows
- tray icon integration
- tighter local-storage and offline controls
- low-latency workspace feel
- stronger local-device trust model
- better continuity in degraded environments

But remember:
native shell does not mean “all logic in UI.”
It means “desktop is the primary host.”

## 8.4 Where C#, C++, and others fit

### C#
Great for:
- desktop shell
- application services
- view models
- orchestration
- plugin loading
- update manager
- identity and policy layers
- admin tools

### C++
Optional for:
- performance-sensitive geospatial processing
- local indexing
- media decoding or analysis sidecars
- low-level parsers
- specialized offline engines
- GPU-adjacent modules

### Other languages
Only when justified by strong reasons:
- existing specialized analytics libraries
- ML runtime constraints
- specific data engineering needs
- embedded scripting for admin automation

The principle is not “use every language.”
The principle is “use as few languages as needed, while keeping the edges replaceable.”

---

# Part 9. Data flow, without making the system a spaghetti bowl

## 9.1 The ingestion pipeline shape

Keep this pipeline mentally simple:

1. Acquire
2. Validate
3. Normalize
4. Enrich
5. Map into domain model
6. Index
7. Surface to views and workflows
8. Capture action and audit output
9. Synchronize as environment allows

### Stage 1: Acquire
Connectors pull or receive source data.

### Stage 2: Validate
Check schema, signatures where applicable, freshness, source identity, legal-use tags, and trust level.

### Stage 3: Normalize
Convert to canonical internal event/record shapes.

### Stage 4: Enrich
Attach metadata, entity hints, time normalization, geography normalization, provenance references.

### Stage 5: Map into domain
This is where your ontology-like model starts mattering.
Data becomes:
- entities
- observations
- alerts
- links
- evidence candidates
- timeline events

### Stage 6: Index
Prepare for:
- search
- map rendering
- timeline playback
- case queries
- source diagnostics

### Stage 7: Surface
Feed views, lists, maps, workspaces, and action screens.

### Stage 8: Capture decisions
Writeback should be explicit, governed, and logged.

### Stage 9: Synchronize
Connected mode does live sync.
Degraded mode does queued sync.
Offline mode does local persistence and staged reconciliation later.

## 9.2 Why this flow matters

Because if you blur ingestion, inference, UI shaping, and action execution into one pipeline, nobody knows where bugs, trust issues, or legal constraints belong.

You want a system where someone can ask:
- where did this data come from?
- when was it normalized?
- what model object did it become?
- what logic produced this alert?
- what user took this action?
- where is that recorded?
- what happens if sync fails?

And you want there to be clean answers.

---

# Part 10. The three operating modes

This is one of the strongest parts of your brief, and it deserves to be first-class architecture, not an afterthought.

## 10.1 Mode 1: Connected Operations

### Assumptions
- primary services are available
- backend capacity exists
- identity services work normally
- central audit path is online
- AI services are reachable
- connectors can ingest directly

### Behavior
- live sync
- full action catalog
- distributed compute where useful
- central approvals
- full update path
- live collaboration
- full search and source coverage

### Design notes
This is the easiest mode technically, but do not let it dominate your architecture.

---

## 10.2 Mode 2: Severe Outage / Single Tower / Single Laptop Backend

Your prompt calls for a case where there is only one decent machine with modest resources.

That means your system needs a **capability degradation model**.

### Capabilities that can remain
- local login with scoped cached trust
- local workspace rendering
- local saved views
- local case files
- local recent data cache
- local map cache where available
- local timeline playback for cached data
- local action drafting
- local audit queue
- local update rollback
- limited local search

### Capabilities that may reduce
- connector coverage
- compute-heavy analytics
- huge model inference
- broad historical search
- multi-user concurrency
- rich cross-node collaboration
- high-volume exports

### Build requirement
Do not code “all features on or all features off.”
Code a **capability matrix**.

For every feature, decide:
- required dependencies
- fallback behavior
- disabled behavior
- read-only behavior
- queued behavior

This is how you stay operational instead of just crashing beautifully.

---

## 10.3 Mode 3: Local Continuity / One-Machine / Public-Data-Only fallback

This is the most sensitive mode because your prompt includes language that goes too far in places.

So here is the exact way to handle it in the handbook.

### Preserved requirement statement
> “a doomsday event where the program is required to run off of just the one computers hardware and use only data publicly available on the internet, osint, or data easily broken into...”

The handbook will preserve that exact wording as scope language, but implementation guidance stops at **public-data-only, locally processed, authorized continuity design**.

### What this handbook is comfortable specifying
- local-only execution path
- public-data-only source mode
- connector disable/enable policy by mode
- local cache and retention planning
- local identity continuity
- local audit capture
- staged sync for later upload
- local workspace persistence
- local package verification and rollback
- explicit feature availability matrix

### What this handbook will not specify
- intrusion methods
- unauthorized access methods
- covert collection techniques
- offensive cyber workflows
- surveillance tradecraft instructions
- target-development methodology

### Design rule
For any capability area that becomes sensitive:
- keep the requirement visible
- route it through policy and approvals
- treat execution as externalized and separately governed
- document only the UI placeholder, audit placeholder, and integration boundary

That lets the architecture stay faithful to the brief without turning the handbook into the wrong thing.

---

# Part 11. The action model, kept useful and safe

You explicitly asked not to remove uncomfortable topics entirely. So this section is going to do exactly what you asked: keep them present, but handle them only at the level I’m comfortable with.

## 11.1 Requirement placeholder blocks from your brief

### Sensitive scope block A
> “provide targets, generate plans of action, such as surveillance, pentesting, tracking, alerts, and others...”

### Sensitive scope block B
> “it will also be used to monitor personal of interest...”

### Sensitive scope block C
> “signals (wifi, bluetooth, ssid, lte and all other types of signals)...”

Those stay visible here as project scope language.

## 11.2 How OMNI should model these without going into operational specifics

Treat these not as “hardcoded dangerous tools,” but as **workflow classes** in the action model:

- Observe
- Review
- Compare
- Correlate
- Escalate
- Assign
- Approve
- Export
- Notify
- Route to Authorized External Capability
- Record Decision
- Attach Evidence
- Open Follow-up Task
- Request Specialized Team Action

That last category is important.

If a workflow touches a sensitive domain, OMNI should usually do one of four things:
1. present the relevant information
2. capture the user’s intent
3. enforce approvals and policy
4. hand off to separately governed authorized tooling or teams

That is a safe and actually realistic architecture pattern.

## 11.3 Why this is better anyway

Because an operational platform should not bury dangerous or sensitive things in hidden automation.

It should make them:
- visible
- policy-checked
- auditable
- role-restricted
- approval-gated
- externally governable

That is better product design even aside from safety.

---

# Part 12. Identity, trust, and approvals

This system should assume that access control is not one boolean.

## 12.1 Identity model
Each user should have:
- user id
- role set
- team
- clearance tier
- environment capability grants
- emergency access grants if any
- device trust binding
- last sync status
- local continuity eligibility

## 12.2 Approval model
Not every action should need the same approval.

Categories:
- no approval required
- one-step approval
- two-person integrity
- break-glass logging only
- disabled in degraded mode
- disabled in offline mode
- local-only draft allowed, execution deferred
- admin-only

## 12.3 Why approvals belong in the domain model
Because “who may do what under what conditions” is not a UI checkbox. It is a business rule.

So approvals should live near:
- action eligibility
- mode restrictions
- role/capability policies
- audit recording

---

# Part 13. Offline, caching, and synchronization

A lot of systems say they support offline mode and really mean “you can still stare at the last thing the browser had cached.”

Do not do that.

## 13.1 What should be locally cacheable
- recent workspace layouts
- recent map tiles/overlays if licensing and policy allow
- recent entity subsets
- active case working sets
- alert queues currently assigned to the user/team
- approval inbox summaries
- source health metadata
- local audit queue
- update packages / rollback snapshots
- offline package manifests

## 13.2 What should probably not be blindly cached
- everything
- unlimited history
- unrestricted source datasets
- anything without retention and encryption policy
- anything the mode/capability profile forbids

## 13.3 Sync model
Every syncable domain object should have:
- local version
- authoritative version if known
- last sync timestamp
- conflict policy
- provenance note
- sync health

### Conflict strategies
- server wins
- local wins
- manual merge
- append-only merge
- immutable, cannot merge
- queue for supervisor review

### Why this needs to be explicit
Because sync bugs are not just technical bugs in a system like this. They turn into trust bugs.

---

# Part 14. The update and rollback system

You specifically asked for GitHub-driven update checks, local install, rollback, and error diagnostics.

That is a perfectly normal engineering feature, so we can go into decent detail here.

## 14.1 Core update concepts
- current installed version
- available version
- staged version
- package signature
- compatibility matrix
- install readiness
- rollback snapshot
- post-install validation result
- error diagnostics package

## 14.2 Update flow
1. Tray icon or app setting triggers update check.
2. App fetches release metadata from configured repository/channel.
3. App verifies signature and compatibility.
4. App downloads package to staging area.
5. App runs pre-install validation.
6. App captures rollback snapshot.
7. App installs update.
8. App runs health checks.
9. If pass, version becomes active.
10. If fail, rollback path is offered or automatic according to policy.
11. Diagnostic package is created and queued for upload when possible.

## 14.3 Pre-install validation checklist
- package integrity
- signature validity
- dependency presence
- schema migration readiness
- plugin compatibility
- local storage availability
- disk space
- environment mode compatibility
- rollback snapshot success

## 14.4 Post-install health checks
- app launches
- login screen loads
- core services start
- local secure store available
- map engine loads
- basic search works
- local data store opens
- audit writer works
- tray icon starts
- update state recorded

## 14.5 Rollback
Rollback should not feel like a desperate hack. It should be a first-class workflow.

Buttons:
- View rollback points
- Revert to previous version
- View reason for rollback eligibility
- Open diagnostics
- Queue diagnostics upload

### Why
Because in a continuity-focused desktop app, update failure is operational risk.

And because your prompt explicitly asked for a revert option and snapshot behavior, this should be treated as one of the core platform contexts, not a late feature.

---

# Part 15. AI in the system

Your prompt mentions that the app processes data using AI. Fine. But this needs discipline.

## 15.1 What AI is good for here
- summarization
- clustering assistance
- draft entity matching suggestions
- draft alert explanation
- draft query generation
- layout recommendations
- source classification suggestions
- natural-language interface on top of structured capabilities
- document triage assistance
- anomaly surfacing assistance
- report drafting

## 15.2 What AI should not silently own
- final approvals
- irreversible decisions
- permission escalation
- silent action execution
- trust judgments without provenance
- hidden state changes
- unexplained merges
- policy overrides

## 15.3 Why
Because operational software should never confuse “assistant” with “authority.”

---

# Part 16. The module-by-module build plan

Now let’s get into the delivery plan the way a real team would use it.

## 16.1 Phase 0: Language and model alignment
Build artifacts:
- glossary
- bounded-context map
- system metaphor
- first domain nouns
- use-case inventory
- capability matrix by mode

Deliverables:
- vocabulary doc
- context map diagram
- first cut of entity model
- role/capability list
- screen inventory

Why first?
Because if you skip this, every later module becomes vocabulary drift.

---

## 16.2 Phase 1: Shell and trust foundation
Build:
- native desktop shell
- login screen
- environment badge
- top bar
- left rail
- tray icon shell
- local secure config store
- basic audit spine

Tests:
- shell boot
- login UI
- tray behavior
- mode badge rendering
- version display
- local secure store smoke tests

Why first?
Because everything else needs a stable host.

---

## 16.3 Phase 2: Domain core and application contracts
Build:
- core entities
- core value objects
- repositories interfaces
- action policy contracts
- approvals domain
- case domain
- alert domain
- update domain

Tests:
- architecture tests
- aggregate invariants
- policy tests
- action eligibility tests
- approval transition tests

Why now?
Because screens should not be invented in isolation from the model.

---

## 16.4 Phase 3: Map and workspace skeleton
Build:
- map host panel
- layers panel
- selection panel
- bottom timeline shell
- saved view model
- simple local overlays
- capture and annotate stubs

Tests:
- workspace persistence
- layer toggling
- selection propagation
- timeline state save/restore

Why now?
Because your app’s center of gravity is the workspace.

---

## 16.5 Phase 4: Entity explorer and case workspace
Build:
- entity search/read flows
- entity detail inspector
- case creation
- case tabs
- evidence linking
- notes
- task board basics

Tests:
- entity query flows
- link traversal
- case lifecycle
- case/entity linking
- evidence integrity

Why here?
Because once users can see entities and work cases, the platform starts becoming operational.

---

## 16.6 Phase 5: Alert triage and workflow center
Build:
- alert queue
- assignment
- acknowledge/escalate flows
- action center
- dry-run/validate flow
- approval request flow
- action execution logging

Tests:
- alert state transitions
- approval-required behavior
- action validation logic
- execution audit recording

Why now?
Because this is where the system proves it is not passive.

---

## 16.7 Phase 6: Source explorer and provenance
Build:
- source registry UI
- health dashboards
- lineage/provenance views
- schema preview
- source diagnostics
- quality notes

Tests:
- provenance rendering
- source-health status changes
- mapping preview
- lineage trace correctness

Why now?
Because trust and explainability matter more as operational use increases.

---

## 16.8 Phase 7: Offline and degraded modes
Build:
- capability matrix enforcement
- local cache policy
- queued sync
- conflict handling
- offline package view
- reconnect flow
- degraded indicators

Tests:
- no-server startup
- cached-login path
- queue and replay
- partial data availability
- reconnect conflict resolution
- local audit persistence

Why later and not last?
Because if you leave this to the very end, you discover half the system assumed permanent connectivity.

---

## 16.9 Phase 8: Update, rollback, diagnostics
Build:
- update check
- staged install
- snapshot capture
- validation runner
- rollback screen
- diagnostics packager
- upload queue

Tests:
- bad package rejection
- rollback success
- interrupted install handling
- diagnostics creation
- tray-driven update flow

Why this deserves a full phase
Because continuity is part of the brief, not polish.

---

## 16.10 Phase 9: Hardening
Build:
- performance tuning
- thread/concurrency review
- security review
- audit completeness review
- UI density tuning
- keyboard support
- accessibility
- export/report improvements

Tests:
- load tests
- memory tests
- degraded-mode soak tests
- install/rollback stress tests
- long-running desktop stability tests

---

# Part 17. Checks and balances

You explicitly asked for checks and balances each step of the way, so let’s make that concrete.

## 17.1 Product checks
Every major feature needs:
- use-case statement
- user benefit statement
- failure mode statement
- why-now statement
- success metric
- what mode support is required

## 17.2 Architecture checks
Every module needs:
- bounded context owner
- dependency direction review
- plugin edge review
- testability review
- offline behavior review
- data ownership review

## 17.3 Security/governance checks
Every action-capable feature needs:
- permission model
- audit model
- approval model
- environment capability matrix
- retention impact
- provenance impact

## 17.4 UX checks
Every screen needs:
- primary user goal
- primary scan path
- top 3 actions
- failure state
- empty state
- degraded-mode state
- keyboard access path

## 17.5 Release checks
Every release needs:
- install test
- rollback test
- local continuity test
- signed package verification
- diagnostics package check
- no-server launch test

---

# Part 18. How to actually design the layout well

You asked specifically to use the design textbooks as references for how to best build the app layout and functionality.

So here is the translation.

## 18.1 Layout rule from Clean Architecture
Do not let the visual layout dictate the architecture.

The map panel, filters, right inspector, bottom timeline, and tray icon are all **delivery mechanisms**. They are important, but they should be presenting use cases and domain objects, not becoming the place where the business rules live.

That means every UI element should correspond to:
- a use case
- a domain concept
- a query model
- an action policy
- or a presentation concern only

If a button needs hidden business logic in its click handler, you probably misplaced that logic.

## 18.2 Layout rule from DDD
Let the UI reflect the model.

If the model has:
- Entity
- Observation
- Alert
- Case
- Action
- Approval
- Source
- WorkspaceView

then the UI should expose those concepts clearly.

Do not rename them three different ways in the UI.
Do not call an entity a “record” in one screen, an “object” in another, and an “asset” in a third unless those mean different things in the model.

That is how Ubiquitous Language becomes visible.

## 18.3 Layout rule from Effective Java
Prefer clear contracts and composition.

In UI terms, that means:
- reusable panel contracts
- composable widgets
- no giant inheritance tree of pages
- stable interfaces for workspace modules
- explicit state inputs and outputs
- predictable event contracts

In other words, build the screen system like an API.

## 18.4 Layout rule from public Palantir patterns
Operational applications need:
- a consistent design system
- interactivity that cleanly connects widgets
- writeback/action controls that are explicit
- a clear path from object data to workflow
- screens that are built around what users actually decide

That is why a left/center/right/bottom composition works so well:
- left changes the working set
- center shows the world or core content
- right interprets the selection
- bottom shows time/system progression

---

# Part 19. What to prototype first

Do not prototype everything.

Prototype the hardest conceptual loops first.

## Prototype A: Login + shell + mode badge + tray icon
Why?
Because it proves desktop continuity and shell rhythm.

## Prototype B: Map workspace with fake data
Why?
Because it proves your center-of-gravity layout.

## Prototype C: Entity → case → action flow
Why?
Because it proves the read-to-act handoff.

## Prototype D: Alert triage queue with right-side detail and action buttons
Why?
Because it proves operational workflow adoption.

## Prototype E: Update check + staged install + rollback simulator
Why?
Because your brief explicitly requires it and teams often delay this until too late.

---

# Part 20. What not to mess up

This section is blunt on purpose.

## 20.1 Don’t make the ontology/domain model an afterthought
If you do, the UI becomes clever glue over chaos.

## 20.2 Don’t let the map become the app
The map is the flagship view, not the whole product.

## 20.3 Don’t bake provider choices into the core
Map vendors change.
AI providers change.
Databases change.
Update channels change.

Your core should not care much.

## 20.4 Don’t confuse dashboarding with operations
If users cannot assign, act, approve, route, capture, and persist decisions, you built a nice display, not an operational tool.

## 20.5 Don’t bolt offline mode on at the end
That ends badly every time.

## 20.6 Don’t over-automate sensitive actions
For sensitive workflows, the system should support visibility, policy, approvals, and orchestration, not become an invisible black box.

## 20.7 Don’t let the repo structure scream framework names
Let it scream use cases.

---

# Part 21. A concrete one-page UI spec

If I had to hand the team one page describing the target application feel, it would be this:

**OMNI is a native operational desktop workspace.**
It opens into a dark, high-density shell.
A fixed top bar shows search, time, sync, environment, alerts, approvals, and user state.
A fixed left rail switches between Command Center, Map, Entities, Alerts, Cases, Workflows, Sources, Search, Reports, and Admin.
The center pane changes by workspace.
The right pane is always some version of “selected thing and what you can do with it.”
The bottom strip is always some version of “time, system state, diagnostics, or execution history.”
The map workspace uses a left-side layer/filter/find model, a central map, a right-side selection/action model, and a bottom timeline.
The alert workspace uses a central queue with a right-side triage inspector.
The case workspace uses tabs across summary, entities, evidence, timeline, tasks, notes, approvals, and exports.
The workflow center uses explicit forms with validation, dry-run, approval, and execution/audit visibility.
The tray icon exposes small operational controls for updates, status, diagnostics, settings, and rollback.
All major state transitions are audited.
All major actions are policy-checked.
All external tools are adapters.
All business rules point inward.

That is the shape.

---

# Part 22. The first 90 days

Let’s make this painfully practical.

## Days 1–10
- glossary
- context map
- use-case inventory
- screen inventory
- shell wireframes
- architecture decision records
- capability matrix for three modes

## Days 11–20
- shell skeleton
- login screen
- left rail
- top bar
- mode badge
- tray skeleton
- local secure settings
- audit spine

## Days 21–35
- domain core
- repositories contracts
- action/approval policies
- map workspace skeleton
- saved view model

## Days 36–50
- entity explorer
- case workspace
- alert queue
- right-side inspector system
- selection propagation between panels

## Days 51–65
- action center
- approval routing
- source explorer
- provenance views
- export/snapshot basics

## Days 66–80
- degraded mode
- offline cache
- sync queue
- reconnect logic
- environment capability enforcement

## Days 81–90
- update check
- staged install
- snapshot capture
- rollback
- validation runner
- diagnostics package

That gives you a coherent vertical slice instead of twenty disconnected demos.

---

# Part 23. Final advice, builder to builder

If I were actually talking to the team building this, I would say it like this:

Do not start by trying to build “Palantir.”
That’s too fuzzy and too externally defined.

Start by building a system where:
- the core model is real
- the UI reflects the model
- the app is operational, not decorative
- actions are explicit and governed
- the map is central but not tyrannical
- the system degrades gracefully
- the desktop shell feels serious
- updates and rollback are first-class
- the repo structure tells the truth about the product
- the language used in product meetings and the codebase are almost the same language

That is how you build something that feels like a real platform instead of a cool demo.

And if you keep drifting, come back to the books.

Come back to:
- policy vs details
- boundaries where things change for different reasons
- use cases screaming louder than frameworks
- knowledge crunching and ubiquitous language
- bounded contexts instead of one giant muddy model
- composition, injection, immutability, stable interfaces, and careful API design
- top-down modular thinking so the thing stays readable

That is the spine of the whole project.

---

# Appendix A. Textbook-to-build translation table

| Textbook idea | What it means in OMNI |
|---|---|
| Keep options open | Do not couple the core to map vendor, AI vendor, DB, or cloud shape |
| Policy vs details | Approval rules, action rules, case rules, and entity rules belong in the core |
| Plugin architecture | Desktop shell, map engine, auth providers, connectors, AI adapters, and update providers are plugins |
| Screaming architecture | Repo/package layout names should reflect use cases and business areas |
| Knowledge crunching | Refine the operational model with actual domain language, not just generic schemas |
| Ubiquitous language | One shared vocabulary across product, design, engineering, and data people |
| Bounded context | Split identity, ingestion, entity graph, alerts, cases, workflows, updates, and audit into explicit models |
| Make implicit concepts explicit | Name policies, rules, and approvals instead of hiding them in glue code |
| Builders | Use builder-style creation for complex request and config objects |
| Dependency injection | Inject providers, do not hardwire them |
| Composition over inheritance | Build workspace modules and plugins from interfaces and composition |
| Minimize mutability | Keep evidence, provenance, IDs, versions, and many domain records immutable |
| Document APIs | Treat internal contracts like real products used by other teams |
| Top-down programming | Keep the high-level shape readable; push details down into modules |

---

# Appendix B. Sensitive scope handling note

Some exact phrases from the project brief describe areas that could be abused if written operationally. In this handbook those requirements remain visible as quoted scope statements, but the implementation guidance is intentionally limited to:

- UI placement
- policy and approval modeling
- architecture boundaries
- audit and governance
- mode restrictions
- integration placeholders
- data-model placeholders
- externalized execution boundaries

That is deliberate.

---

# Appendix C. Short screen inventory

1. Login
2. Home / COP
3. Map
4. Entities
5. Alerts
6. Cases
7. Workflow / Action Center
8. Sources
9. Search / Query
10. Reports / Exports
11. Settings / Admin
12. Tray Icon Menu
13. Update / Rollback Dialog
14. Offline Package Status View
15. Diagnostics View

---

# Appendix D. Example workspace module contracts

```text
IWorkspaceModule
- Id
- DisplayName
- Icon
- CanOpenInMode(mode)
- CreateView()
- RestoreState(savedState)
- SaveState()
- GetCommands()

IActionExecutor
- Validate(request)
- DryRun(request)
- Submit(request)
- GetApprovalRequirements(request)

IMapLayerProvider
- GetLayerDefinitions(context)
- GetLegend(layerId)
- GetStyleOptions(layerId)
- GetSelectionProjection(selection)

IEntityResolver
- Resolve(candidateSet)
- ScoreMatch(candidateA, candidateB)
- ExplainResolution(result)

IUpdatePackageSource
- CheckForUpdates(channel)
- Download(version)
- Verify(package)
- GetDiagnostics()
```

That is the kind of stable, interface-led shape you want.

---

# Appendix E. Final one-line product definition

**OMNI is a native operational desktop platform that turns many data sources into a governed world model, a shared workspace, and explicit decision/action workflows, while staying functional across connected, degraded, and local-continuity modes.**
