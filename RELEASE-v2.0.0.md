# v2.0.0 — Diagnose + gezielte Reparatur

Major release: the Health Monitor can now perform one narrowly scoped repair in
addition to read-only diagnostics.

- Adds repair eligibility detection for Gate 8 `Chroma Dienste`.
- Adds an in-popover `Reparieren` action only when the exact safe repair pattern
  is present.
- Adds custom confirmation, UAC execution, 5-second stability verification and
  result UI.
- Adds a `Systemprüfung erneut starten` action after repair.
- Adds Repair Engine 1.0.0 with a strict two-service Start-Service allowlist.
- Adds repair JSON/text audit artifacts and diagnostic-export inclusion.
- Diagnostic Health Engine 1.3.5 and all 13 gates remain unchanged/read-only.
- Runtime now includes `Runtime/repair/` for the ephemeral repair engine.
- de-DE remains the only runtime locale; all new repair UI text is i18n-owned.
