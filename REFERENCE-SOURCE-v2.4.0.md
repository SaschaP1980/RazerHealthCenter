# Reference Source v2.4.0

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.4.0.

v2.4.0 is based strictly on the canonical v2.3.12 source and adds a historical
measurement detail view inside PROTOKOLLE. The permanent PROTOKOLLE tab can open
exactly one reusable timestamp tab. The historical view consumes only the stored
measurement JSON/check evidence, reuses the 13-gate status/detail rendering and
is read-only: it does not expose Gate-8 repair and does not enrich Gate 4 with
current live device data.

The historical tab can be opened by `Details anzeigen` or double-clicking a
measurement row, switched against PROTOKOLLE, and closed with an X hover control.
Its opened measurement stamp and active subview persist in `UIState-v1.json` only
when the referenced measurement remains present and detail-capable. Table
selection and scroll position remain session-only and reset after full app exit.

Old/incomplete measurement files remain listable whenever their timestamp can be
reconstructed, but detail opening is disabled and the selected-measurement panel
explains the reason.

Historical `Diagnosepaket erstellen` exports the opened measurement and resolved
historical app-session evidence. Current mutable Setup inventory/history/live-
probe snapshots are deliberately excluded from historical packages. The existing
`Paketordner öffnen` action remains unchanged.

The live status page heading and small system-status label are now
`AKTUELLER SYSTEMSTATUS`; the historical view uses `HISTORISCHER SYSTEMSTATUS`.

Health Engine 1.4.5, Setup Scanner 1.0.6, native SetupAPI Live Probe 1.1.0,
Repair Engine 1.0.0 and the v2.3.12 rounded tray-menu architecture are unchanged.
