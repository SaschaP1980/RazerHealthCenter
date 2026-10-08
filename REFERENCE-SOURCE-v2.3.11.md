# Reference Source v2.3.11

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.11.

v2.3.11 is based on v2.3.10 and changes only the tray icon context menu plus
version/release/validation metadata. The tray menu is now built as a custom
owner-drawn popup so it visually matches the Synapse product language much more
closely than the default Windows menu.

The new menu adds a branded header row using the product icon and the
`RAZER SYNAPSE + CHROMA / HEALTH MONITOR` wordmark, a dedicated `Fenster anzeigen`
command, custom-drawn row backgrounds, a green hover accent strip, muted disabled
states, and a custom separator. Existing commands keep their prior behaviors and
state gating.

The implementation is integrated through `WM_MEASUREITEM` / `WM_DRAWITEM`,
owner-draw menu flags, and a dedicated `validate_tray_menu_v2311.py` build gate.
Guided Connection Learning UX from v2.3.10 and all engine / setup / repair
components remain unchanged.
