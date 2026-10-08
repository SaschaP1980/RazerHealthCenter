# Razer Synapse + Chroma Health Monitor — Recovered Source v1.7.0

Status: **Recovered development source**, 2026-09-09.

This is **not the verbatim original `/mnt/data/rhm165src/main.go`**. That temporary
source tree was lost before the final handover. This repository was reconstructed
from the SHA-256 pinned v1.7.0 Windows binary/package, its Go DWARF/symbol metadata,
the embedded filesystem, and the canonical README/Runbook/Handover contracts.

## Golden reference

- Portable v1.7.0 SHA-256:
  `398d1a448e8b81ca738a1d132cded4a358cabaee2b59c77ab9ea57c4402f49fd`
- Golden EXE SHA-256:
  `6b37409c31cfd7431032d1c5f44e1cf9c75188c6d987965b2a289e7d1148d8d2`
- Go: 1.23.2, `GOOS=windows`, `GOARCH=amd64`, `CGO_ENABLED=0`
- Original linker flag: `-H windowsgui`
- Original source path recovered from DWARF: `/mnt/data/rhm165src/main.go`

The golden binary remains the behavioral reference. This recovered repository is
the new maintainable development source, subject to native Windows regression
checks before a later release is called stable. Recovery r3 passed native startup and a full Health Check; r4 passed native Windows functional/UI testing; r5 passed native comparison; r6 passed the next detail/progress/export comparison; RC1 passed a native follow-up UI test and exposed only the final Gate-detail scroll/interaction refinements addressed by RC2.

## What was recovered exactly

- Health Engine 1.3.5, byte-for-byte from `main.embedded.files`.
- All embedded app/status/sidebar/component ICO assets, byte-for-byte.
- All PE resource payloads (icons/manifest/version resources), byte-for-byte. The resource directory is relocated to a loader-safe RVA in the reconstructed image, so location-dependent RVA fields are intentionally different.
- Original Go module/build metadata.
- Main-package symbol table and DWARF source-line map.
- 19 named main-package type layouts, including the original `App` layout.
- 184 DWARF function records/signatures and the original source line numbers.
- Original gate names/details/icon naming tables.
- Exact v1.7.0 colors recovered from `main.init` machine code.
- v1.7.0 external i18n catalogs and manifest.

Forensic records are under `forensics/`.

## What was reconstructed, not recovered verbatim

The Go statements of the lost 4,900+ line `main.go` were not stored in DWARF.
The source implementation in this repository therefore reconstructs the app's
observable architecture and contracts rather than claiming original source text.
Some helper decomposition and pixel-level UI behavior may differ from the golden
binary until native Windows comparison is completed.

## Safety invariants

- Read-only toward Razer/Windows state.
- No service/driver/registry/PnP repair actions.
- Standard launch is unelevated.
- `runtime.LockOSThread()` is called before HWND/tray/message-queue initialization.
- Windows GUI subsystem; no console regression.
- Mutex: `Local\\RazerSynapseChromaHealthMonitor.SingleInstance`.
- Runtime directory is app-owned, flat and ephemeral.
- Diagnostic export uses conservative session association and does not mix an
  unrelated historical measurement with the current app session.
- Gate detail stays inside the main window, with raw findings/copy capability;
  there is no `In Diagnose aufnehmen` action.

## Build

On Linux with Go 1.23.x:

```bash
./build-recovered.sh
```

The script runs Windows cross-`go vet`, builds with `-H windowsgui`, then injects
the recovered v1.7.0 PE resource payloads into a relocated, loader-safe `.rsrc` section. It does **not** perform a native
Windows runtime test.

## Recovery revision note

The first recovered test build used the golden `.rsrc` section at its original RVA. A native Windows test rejected that image before startup. Recovery revision r2 therefore relocates `.rsrc` immediately after the reconstructed image and rewrites only `IMAGE_RESOURCE_DATA_ENTRY.OffsetToData` RVAs. The 11 resource payloads remain SHA-256-identical to the golden executable. The build now runs an explicit PE/resource-layout validator.

## Next release

Do not silently call this reconstructed build the original v1.7.0 release. Keep
v1.7.0 Golden as reference. After native Windows functional/UI regression testing,
future changes can branch from this recovered source and receive a new version.


## UI recovery revision r4

See `RECOVERY-UI-R4.md`. r4 reconstructs the Golden v1.7.0 layout and paint path from direct before/after screenshots and native Windows run videos. The recovery provenance is intentionally kept in source documentation rather than displayed in the end-user Golden-compatible UI.


## UI recovery revision r5

See `RECOVERY-UI-R5.md`. r5 refines the natively validated r4 UI using the follow-up Golden/recovery videos: larger navigation/action symbols and small typography, Golden ping-pong heartbeat animation, and control-specific hover states for sidebar views, action cards, rows, detail buttons, and export-modal actions.


## UI / diagnostics recovery revision r6

See `RECOVERY-UI-R6.md`. r6 adds the high-resolution Info heart, Golden progress-status wording, status-accented Gate detail panel with Golden raw-detail semantics, and the next diagnostic/history parity block (EngineOutput wrapper, GateProgress naming, schema-4 ExportManifest, StartupDebug/UITrace session artifacts).

## Recovery r7 / Release Candidate 1

See `RECOVERY-R7-RC1.md`. RC1 incorporates the final collected native r6
findings: wrapped/dynamic Gate raw-details, a larger Gate close control, strict
popover click ownership, overall-health terminology in Protocols, and crisp
vector action icons including the new package-folder/open-arrow design.


## Recovery r8 / Release Candidate 2

See `RECOVERY-R8-RC2.md`. RC2 keeps the RC1 functional baseline and refines the
Gate-detail interaction model: the whole middle content area scrolls as one document,
the scrollbar thumb supports captured live dragging during `WM_MOUSEMOVE`, the close
control is larger and more Golden-like, and ESC closes an open Gate detail panel.
