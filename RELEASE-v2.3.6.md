# Release v2.3.6

- App: 2.3.6
- Health Engine: 1.4.3 (unchanged)
- Setup Scanner: 1.0.6 (unchanged)
- Fast Setup Live Probe: 1.1.0 native SetupAPI (unchanged)
- Repair Engine: 1.0.0 (unchanged)
- Device Inventory schema: 2
- Connection History schema: 2
- Runtime locale: de-DE, 333 UI keys

## Guided Connection Learning correction

Wireless learning no longer assumes that cable removal is sufficient evidence for every device profile.

- The interaction flow is selected from the generic device profile (`mouse`, `keyboard`, `device`) and contains no product-name or endpoint-PID rules.
- Mouse profiles keep event-driven Wireless learning. Cable removal can itself be the intentional transition into wireless operation, so no nonexistent mode switch is requested.
- Keyboard and conservative unknown-device profiles enter an explicit confirmation state after the Wireless baseline. `WM_DEVICECHANGE` cannot complete this state automatically. The user establishes the complete wireless operating state and then presses `Wireless prüfen`.
- If a HIGH learned wired path is still present, explicit Wireless confirmation is rejected instead of accepting the receiver root prematurely.
- Successful explicit confirmation is persisted as `wireless-dongle`, HIGH, source `user-guided-wireless-confirmation`; mouse event transitions keep `user-guided-wireless-transition`.
- The final automatic full Setup scan has been removed from Guided Learning. Existing inventory entries are updated immediately and history is persisted directly. If a newly discovered PID is not yet materialized in the full inventory, the completion dialog recommends a later manual Setup scan for complete metadata without blocking SETUP.

The v2.3.5 native live-presence path, 800 ms PnP debounce, product-key verification, full Setup scanner, Health Engine and Repair semantics are otherwise unchanged.
