# Release v2.3.4

- App: 2.3.4
- Health Engine: 1.4.3 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.0.1 (unchanged)
- Repair Engine: 1.0.0 (unchanged)

## Change

During Setup live refresh, the connection PID/role cell now hides stale text completely and renders only the Acid-Green sweep. This removes the native GDI bleed-through/flicker seen when the sweep overlapped dimmed text in v2.3.3. The text reappears only after the current live result has completed.
