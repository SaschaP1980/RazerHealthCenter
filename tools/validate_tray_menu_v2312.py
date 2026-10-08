#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
ui = (root / 'ui.go').read_text(encoding='utf-8')
win32 = (root / 'win32.go').read_text(encoding='utf-8')
checks = []

def add(name, ok):
    checks.append((name, bool(ok)))

add('dedicated tray menu popup window class exists', 'trayMenuWindowClass' in win32 and 'trayMenuWndProc' in ui and 'handleTrayPopupWndProc' in ui)
add('app tracks tray popup state', 'trayMenuHwnd' in (root/'model.go').read_text(encoding='utf-8') and 'trayMenuHover' in (root/'model.go').read_text(encoding='utf-8') and 'trayMenuPressed' in (root/'model.go').read_text(encoding='utf-8'))
add('tray menu uses popup window creation', 'procCreateWindowExW.Call(' in ui and 'trayMenuWindowClass' in ui and 'wsPopup|wsVisible' in ui)
add('tray menu window is rounded and borderless', 'procCreateRoundRectRgn.Call' in ui and 'procSetWindowRgn.Call' in ui and 'wsExToolWindow|wsExTopmost' in ui)
add('tray menu paints its own rounded surface', 'paintTrayMenuWindow' in ui and 'roundBox(hdc, rect{Left: 0, Top: 0, Right: cr.Right, Bottom: cr.Bottom}' in ui)
add('tray menu still renders branded header', 'tr("app.brand.primary")' in ui and 'tr("app.brand.secondary")' in ui)
add('tray menu still has direct show-window action', 'trayMenuShowID' in ui and 'tr("tray.menu.show")' in ui and 'case trayMenuShowID:' in ui and 'a.showWindow()' in ui)
add('tray menu keeps green hover accent strip', 'fill(hdc, rect{r.Left, r.Top + 5, r.Left + 3, r.Bottom - 5}, colors.green)' in ui)
add('tray menu closes on focus loss or escape', 'case wmKillFocus:' in ui and 'case wmActivate:' in ui and 'case wmKeyDown:' in ui and 'vkEscape' in ui)
add('new validator is build-gated', 'validate_tray_menu_v2312.py' in (root/'build.sh').read_text(encoding='utf-8'))
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(('PASS' if ok else 'FAIL') + ': ' + n)
print(f'v2.3.12 tray-menu rounding regression: {len(checks)-len(failed)}/{len(checks)}')
if failed:
    sys.exit(1)
