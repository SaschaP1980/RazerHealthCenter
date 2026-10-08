# UI Recovery revision r4 — Golden v1.7.0 parity pass

Date: 2026-09-09

This revision is based on direct before/after screenshots and native Windows videos
of Golden v1.7.0 versus recovered r3. It is not a claim that the lost original Go
source was recovered verbatim.

## Reconstructed Golden UI contracts

- 88 px icon sidebar with Golden heart branding, compact nav cells and `v1.7.0` footer.
- Global `RAZER SYNAPSE + CHROMA / HEALTH MONITOR` header and live-diagnose label.
- Status page in UNGEPRÜFT, PRÜFUNG and GESUND/FEHLER states.
- Three-part overall card: system state, runtime/progress count, progress bar/last check.
- 13-row table with `# / KOMPONENTE / STATUS / DETAILS` columns and status badges.
- Golden run-state semantics: all gates first enter PRÜFUNG; final states replace them incrementally.
- Golden action-card layout for Systemprüfung and Diagnoseexport.
- Protokolle: 10-row history viewport, six columns, selection, scrollbar, selected-measurement card,
  Diagnosepaket erstellen and Paketordner öffnen actions.
- Historical duration recovery from EngineOutput and best-effort AppDebug session/version association.
- Info view restored to the centered Golden panel; recovery provenance remains in source docs, not end-user UI.
- Gate detail panel restored to Golden docking/section order: ZUSAMMENFASSUNG, BEWERTUNG, BEFUNDE,
  status badge, close, scroll viewport, Rohdetails and Kopieren.
- Technical PASS/WARN/UNKNOWN labels are mapped to user-facing OK/HINWEIS/UNKLAR inside the detail UI.
- Tray menu order restored to Golden: Systemprüfung starten, Ergebnis öffnen, Protokolle anzeigen,
  Diagnose exportieren, separator, Beenden.
- Successful export uses a dark in-app Golden-style dialog with Ordner öffnen / Schließen.

## Flicker recovery

Recovered r3 painted directly into the BeginPaint DC and invalidated the full window on hover.
Golden v1.7.0 binary symbols and native video prove a compatible-DC/bitmap/BitBlt and
TrackMouseEvent style paint path. r4 restores:

- CreateCompatibleDC / CreateCompatibleBitmap offscreen frame,
- one BitBlt publication per WM_PAINT,
- WM_ERASEBKGND suppression,
- TrackMouseEvent / WM_MOUSELEAVE hover lifecycle,
- periodic run repaint only while a health check is active.

Native Windows verification of r4 is still required. r3 remains the last natively proven
recovery revision for startup + complete Health Engine execution; r4 is the UI parity candidate.
