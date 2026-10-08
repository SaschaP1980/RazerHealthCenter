# Razer Synapse + Chroma Health Center v3.0.0

v3.0.0 is the first Health Center release and the architectural transition from
a health monitor with one special-case repair to a versioned diagnostic/problem/
repair platform.

## New platform

- Product renamed to **Razer Synapse + Chroma Health Center**.
- Executable renamed to `RazerHealthCenter.exe`.
- Diagnostic Orchestrator 1.0.0.
- Problem Catalog 1.0.0 with structured KNOWN / UNCLASSIFIED findings.
- Repair Engine / Repair Catalog 2.0.0.
- Read-only Chroma service deep-diagnostic module 1.0.0.
- Problem evidence persisted per measurement and included in measurement-specific
  diagnostic packages.
- Unknown causes are recorded explicitly and never mapped heuristically to a
  repair.

## First catalogued reference problem

- Problem ID: `RHC.CHROMA.SDK_SERVICES.STOPPED_AUTO`
- Repair ID: `RHC.REPAIR.CHROMA.START_STOPPED_AUTO`
- Repair payload: `repair-chroma-services-v1.1.0.ps1`
- Exact service-state eligibility is preserved.
- Repair mutation remains limited to starting the eligible stopped/automatic
  Chroma SDK service(s).

## Mandatory repair safety

**No repair is ever automatic.** Every repair must be explicitly confirmed in the
Health Center before execution. UAC is additional when required and is never a
substitute for the in-app confirmation. Post-repair read-only verification is
mandatory; exit code 0 alone is insufficient for success.

## Preserved v2.4 functionality

- Health Engine 1.4.5 and 13-gate model.
- Setup Scanner 1.0.6 and schema-2 device inventory.
- Native SetupAPI Live Probe 1.1.0.
- Guided connection learning and PID-free identity semantics.
- Historical measurement tab/details and historical diagnostic packaging.
- Version monitor and read-only evidence-role architecture.

## Validation

The release build is gated by the existing regression suite plus the new
`tools/validate_v300_diagnostic_repair_platform.py`. A pristine v2.4.0 source
serves as the RED baseline for the new platform regression.
