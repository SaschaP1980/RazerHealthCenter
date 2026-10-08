# Reference Source v2.3.12

Canonical source baseline for Razer Synapse + Chroma Health Monitor v2.3.12.

v2.3.12 is based on v2.3.11 and changes only the tray icon context menu plus
version/release/validation metadata. The menu is no longer hosted in the native
Windows popup menu container. Instead, it is rendered as a dedicated custom
popup window with rounded corners and a dark Synapse-style surface, which removes
the previously visible white system outline.

The branded header, hover accent strip, command icons, direct `Fenster anzeigen`
action and the existing command gating rules remain unchanged.

The implementation introduces a dedicated tray-menu window class, popup-window
painting, rounded region handling and a dedicated `validate_tray_menu_v2312.py`
build gate. Guided Connection Learning UX from v2.3.10 and all engine / setup /
repair components remain unchanged.
