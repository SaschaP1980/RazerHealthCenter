Razer Synapse + Chroma Health Center v3.0.8.0

Portable Windows x64 build.

Start:
  RazerHealthCenter.exe

Health Center architecture (v3.0.8):
  - Health Engine 1.4.6: read-only 13-gate first-level assessment.
  - Diagnostic Orchestrator 1.1.0: targeted read-only deep diagnostics for
    relevant FAIL/UNKNOWN conditions.
  - Problem Catalog 1.1.0: known signatures become stable problem IDs; unknown
    causes remain UNCLASSIFIED and are never guessed.
  - Repair Engine / Catalog 2.1.0: only versioned known repair recipes.

Version evidence (v3.0.8):
  Local Known-Good versions/hashes are not normative Soll values. The online
  version monitor resolves Razer's current prod manifest through Discovery and
  compares Synapse/Chroma using Razer-supplied registry mappings. A newer offered
  version is cyan INFO "NEUE VERSION VERFÜGBAR" and never degrades Health.
  Internal Chroma SDK component versions are inventory/supporting evidence unless
  Razer explicitly publishes a normative requirement.

Safety rule:
  NO repair is automatic. Every repair requires explicit in-app confirmation.
  UAC, where required, is an additional authorization step and never replaces
  the in-app confirmation. Repair success additionally requires read-only
  post-repair verification.

Current known repair reference case:
  RHC.CHROMA.SDK_SERVICES.STOPPED_AUTO
    -> RHC.REPAIR.CHROMA.START_STOPPED_AUTO
  The recipe can only start the documented Chroma SDK service(s) when the exact
  catalogued service-state signature matches. It does not change service start
  types, registry, drivers, PnP, installation files or unrelated processes.

Current AppEngine user-mode recovery:
  RHC.APPENGINE.USERMODE.RUNTIME_INCOMPLETE
    -> RHC.REPAIR.APPENGINE.CONTROLLED_RUNTIME_RECOVERY
  This recipe requires explicit confirmation, does not request automatic UAC,
  and only starts/restarts the uniquely validated RazerAppEngine runtime through
  the existing HKCU Synapse+Chroma launch contract. It changes no services,
  drivers, registry values, installed packages or Razer files. Success requires
  a separate read-only AppEngine user-mode verification.

Setup and device inventory:
  A read-only schema-2 Razer device inventory is required before the 13-gate
  Healthcheck can run. It is stored under Setup\RazerDeviceInventory-v2.json.
  HEALTHCHECK participation is persisted per product; newly discovered products
  default to active. Live connection presence is independent from participation.

Fast live connection state:
  Startup and WM_DEVICECHANGE refreshes use native Windows SetupAPI. Current
  roots are identity-verified before a known observed PID is considered present.
  Endpoint PIDs carry no compiled product/device-class/wired/wireless meaning.

Guided connection learning:
  Connection roles are learned only from explicit/current evidence and user-
  guided transitions. Ambiguous cases remain uncalibrated.
  Persistent role evidence is stored in Setup\RazerConnectionHistory-v2.json.

Historical measurements:
  PROTOKOLLE supports one reusable historical measurement tab with stored 13-gate
  details and measurement-specific diagnostic packaging. The historical tab is
  session-only: after a full app restart only the permanent PROTOKOLLE tab is
  open. Active archive mode is marked in cyan as "ARCHIVANSICHT • NICHT LIVE"
  with a simplified archive summary: cyan HISTORISCHER SYSTEMSTATUS, DAUER,
  static completion information and a very subtle cyan-tinted dark background.
  The timestamp stays in the tab; duplicate archive copy and the cyan separator
  are removed. The heart and stored green/yellow/red result semantics remain unchanged.
  Historical views are read-only and never expose repair actions.

Runtime directories are created/used below this portable folder. Runtime payloads
are ephemeral and app-owned.

Language:
  de-DE only; 413 presentation keys. No runtime language switch.

Canonical source:
  Every release includes a complete independently buildable Source ZIP.
