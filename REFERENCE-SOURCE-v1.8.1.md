# Canonical Reference Source — v1.8.1

Effective with v1.8.1, this complete source snapshot is the authoritative
reference for future development of Razer Synapse + Chroma Health Monitor.

The recovered Golden-v1.7.0 executable is no longer the active development
reference. It remains historical recovery evidence only.

Canonical invariants carried into v1.8.1 include the natively validated RC2 UI,
read-only Health Engine 1.3.5, session/diagnostic export model, double-buffered
Win32 rendering, Gate detail interaction model, tray lifecycle and single-instance
behavior.

New source invariant in v1.8.1:

- All presentation-owned visible UI wording is maintained only in
  `locales/de-DE.json`.
- No language switch is implemented.
- Build guards reject direct presentation literals in rendering, tray and modal
  sinks.

## Runtime layout refinement — v1.8.1

The ephemeral Runtime tree is structured again:

- `Runtime/health-engine-v1.3.5.ps1`
- `Runtime/assets/` for top-level app/status assets
- `Runtime/assets/status/` for overall/pulse status icons
- `Runtime/assets/ui/` for navigation and gate/component icons

The application rebuilds this hierarchy on every start. Embedded asset payloads
remain byte-identical; only their extracted runtime paths changed.
