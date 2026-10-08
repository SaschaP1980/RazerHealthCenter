# Recovery validation — r8 / Release Candidate 2 — 2026-09-09

RC2 is built on the natively exercised RC1 recovery line. It is a focused Gate-detail
interaction/layout refinement and intentionally leaves the Health Engine, Gate semantics,
history/export model, vector action icons and read-only contract unchanged.

Static/build acceptance before packaging:
- Windows amd64 GUI cross-build and `go vet`.
- PE/resource layout validation.
- UI/diagnostics recovery contract checks, including RC2 whole-content scrolling,
  live scrollbar dragging, mouse capture/release and ESC close semantics.
- Health Engine 1.3.5 SHA-256 invariant.
- 80/80 Golden-recovered embedded payload hash invariants.
- Golden recovered `.rsrc` payload invariant.
- Read-only mutation primitive scan.
- `runtime.LockOSThread()` source ordering and single-instance mutex contract.
- ZIP integrity.
- Clean rebuild from the final source ZIP; rebuilt EXE must be byte-identical to
  the packaged RC2 EXE.

Native Windows acceptance is still required before RC2 can be called stable.
