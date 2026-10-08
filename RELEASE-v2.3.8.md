# Release v2.3.8

- App: 2.3.8
- Health Engine: 1.4.5
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- VersionStatus schema: 3
- ExportManifest schema: 4
- Runtime locale: de-DE, 342 UI keys

## Gate 3 applicability

Gate 3 `Kernel-Treiber RzDev / RzCommon` is now applicability-aware. If the
currently Healthcheck-enabled products have no inventory requirement for
RzDev/RzCommon, zero binary/service checks is a valid not-applicable state rather
than a failure. Health Engine 1.4.5 emits a structured `Kernel drivers` INFO
finding explaining that no RzDev/RzCommon filter stack is required. Existing
FAIL/UNKNOWN results for actual relevant driver/service checks remain decisive.

## Structured failure details

The normal `PRÜFDETAILS` view now expands structured FAIL/UNKNOWN checks using the
JSON fields for actual state, expected state, diagnostic detail and section. The
generic `Keine strukturierten Einzelbefunde ...` fallback remains limited to a
truly empty mapped check list. Raw details and clipboard export remain technical
and unchanged in ownership.

A dedicated regression validator was executed RED→GREEN against the exact
canonical v2.3.7 source and v2.3.8 source.

## Final lifecycle guard

After the Health worker completes, transient `CHECKING` values are normalized out
of the final gate snapshot before it is published to table rows and an open detail
popover. Final UI state is therefore PASS/HINWEIS/UNKLAR/FEHLER (or informational
content attached to a passed/not-applicable gate), never `PRÜFUNG LÄUFT`.
