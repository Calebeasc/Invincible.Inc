# Codex Omni Native Scan and Planning Addendum

Date: `2026-04-04`
Scope: `Omni-repo/Invincible.Native/Invincible.App`
Purpose: capture the actual current state of the Claude-tracked native app and convert that scan into updated Codex planning guidance.

## Sources Scanned
- `Omni-repo/CLAUDE.md`
- `Omni-repo/AGENTS.md`
- `Omni-repo/SOVEREIGN_MANDATE.md`
- `C:\Users\eckel\.claude\plans\peaceful-waddling-deer.md`
- `Omni-repo/Invincible.Native/Invincible.App/App.xaml.cs`
- `Omni-repo/Invincible.Native/Invincible.App/Styles/OmniColors.xaml`
- `Omni-repo/Invincible.Native/Invincible.App/Services/*.cs`
- `Omni-repo/Invincible.Native/Invincible.App/Pages/Omni/*.xaml`
- `Omni-repo/Invincible.Native/Invincible.App/Pages/Omni/*.xaml.cs`

## Build Truth
- `dotnet build -c Omni-Debug` succeeds
- Result: `0 errors`, `0 warnings`

This means the native app is currently in a compilable state and planning should target controlled architectural change, not emergency stabilization.

## High-Confidence Current-State Findings

### 1. Claude's active Phase 35 plan is partially stale
The external Claude plan correctly identified the native-only mandate, but its implementation target list is no longer fully current.

Already completed:
- `GeospatialPage` is now fully native XAML/C#
- `TemporalPage` is now fully native XAML/C#
- `DownloadPage` manual download no longer opens a browser and now uses a native `FileSavePicker` plus `OmniApiService.DownloadFileAsync`

Implication:
- Future Codex planning must treat those three items as implemented baseline, not pending work.

### 2. Remaining browser-era remnants still exist inside `Invincible.App`
The operator shell pages under `Pages/Omni/` are mostly native, but browser-era remnants still exist elsewhere in the app project:
- `Pages/MapPage.xaml` still contains `WebView2`
- `Pages/ReplayPage.xaml` still contains `WebView2`
- `ViewModels/MapViewModel.cs` still defaults to `http://localhost:8742`

Implication:
- The native-only transition is incomplete even if the Omni shell pages look mostly compliant.
- Phase 35 needs to be re-scoped from "replace three shell pages" to "remove every browser-era surface still living inside the native app project."

### 3. The shell is still module navigation, not the target workstation model
`OmniShellPage.xaml.cs` still drives a route-like module shell:
- one current `ContentFrame`
- one active module label
- one search index of modules
- one nav map by string tag
- static `download` module still present

Useful native foundations already exist:
- drawer pattern
- activity strip pattern
- module search pattern
- tier/classification bar pattern

Implication:
- The shell should be evolved, not thrown away.
- It is a viable base for the larger workspace / UTT / WorldView redesign.

### 4. Download is technically native now but strategically obsolete
The current `DownloadPage` is no longer browser-launched for manual artifact save, but the broader architecture plan still requires removing download/distribution from the operator shell.

Current reality:
- native ticket generation exists
- native save-to-disk flow exists
- native update/apply/rollback exists
- shell still exposes `Downloads`

Implication:
- This is no longer a browser-compliance issue.
- It is now a product-boundary issue.

### 5. The app startup profile still contains temporary operational compromises
`App.xaml.cs` currently disables several startup paths:
- `EnableSignalBridgeOnStartup = false`
- `EnableGpsOnStartup = false`
- `EnablePipeClientOnStartup = true`
- `EnableUpdateServiceOnStartup = true`

Implication:
- The app compiles and opens, but not all native subsystems are considered safe for default startup.
- Any broader native rebuild plan must include a service-readiness matrix and staged re-enable criteria.

### 6. The design system is present but not fully normalized
`OmniColors.xaml` contains a real Omni token set and several shared button/module styles.

Strengths:
- clear brush taxonomy
- reusable tab/button/module styles
- Gotham-like dense dark palette

Notable mismatch with stated design doctrine:
- `OmniNavButtonStyle` uses `FontFamily="Inter"` while the repo rules emphasize `Courier New` for labels and dense tactical typography

Implication:
- The style system is real enough to become the base design system.
- It still needs normalization during the full workstation redesign.

### 7. Module implementation maturity is uneven
Current module patterns break into three rough categories:

Dense native operational pages:
- `LeGoliathPage`
- `GeospatialPage`
- `TemporalPage`
- `DeFlockPage`

Native functional workbench pages:
- `SigintPage`
- `IdentityPage`
- `SurveillancePage`
- `BlockchainPage`
- `EasmPage`
- `TriagePage`
- `AipTerminalPage`
- `HealthPage`

Utility / lifecycle pages:
- `OmniAuthPage`
- `OmniOverviewPage`
- `DownloadPage`

Implication:
- The rebuild should not treat all modules equally.
- The richer pages should be used as reference patterns for density, orchestration, and cross-panel behavior.

### 8. There is still at least one likely broken module contract
`LeGoliathPage.xaml.cs` calls `/api/le-goliath/status`.
This endpoint has previously not been found in the backend scan.

Implication:
- The planning docs should explicitly separate:
  - architecture modernization
  - module parity
  - broken contract repair

## Updated Planning Direction

### 1. Immediate planning truth
The app is no longer at the stage of "replace obvious WebView pages in the shell."
It is now at the stage of:
- remove remaining browser remnants outside the shell
- remove or re-home download from the operator shell
- convert module navigation into persistent workspaces
- formalize UTT as the primary post-selection action surface
- formalize WorldView as the spatial command theater

### 2. Execution order for the next implementation phase
Recommended order:
1. Remove all remaining browser-era pages and localhost UI dependencies in `Invincible.App`
2. Delete `Downloads` from the operator shell and re-home any retained installer/update functions
3. Introduce workspace primitives inside the current shell rather than replacing the whole shell at once
4. Build UTT as the first flagship workspace
5. Build WorldView as the second flagship workspace
6. Migrate thin module pages into shared panel/workspace patterns
7. Re-enable currently disabled native services only behind explicit stability criteria

### 3. Planning assumptions now locked
- The Claude scan is treated as valuable but not authoritative where the code now differs
- `Pages/Omni/` is the main production operator surface
- `MapPage` and `ReplayPage` are still relevant debt until removed or formally quarantined
- `DownloadPage` is compliant with native file saving, but not compliant with the final product boundary
- `OmniShellPage` is the upgrade path for the workstation shell

## Planning Deltas To Carry Into OMNI_ENCYCLOPEDIA
- Note that Claude's three-page WebView replacement plan is partially completed already
- Note that browser-era debt still exists in non-shell native pages
- Note that download has shifted from a browser problem to a shell-boundary problem
- Note that the app is build-clean today
- Note that service startup is intentionally constrained and should be treated as part of the rebuild plan
