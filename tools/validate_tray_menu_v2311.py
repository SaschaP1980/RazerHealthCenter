#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
ui = (root / 'ui.go').read_text(encoding='utf-8')
win32 = (root / 'win32.go').read_text(encoding='utf-8')
checks = []

def add(name, ok):
    checks.append((name, bool(ok)))

add('owner-draw tray menu constants exist', 'mfOwnerDraw' in win32 and 'wmDrawItem' in win32 and 'wmMeasureItem' in win32 and 'tpmReturnCmd' in win32)
add('owner-draw menu ids exist', 'trayMenuHeaderID' in ui and 'trayMenuSeparatorID' in ui and 'trayMenuShowID' in ui)
add('wndproc handles tray menu measure/draw', 'case wmMeasureItem:' in ui and 'handleTrayMenuMeasure' in ui and 'case wmDrawItem:' in ui and 'handleTrayMenuDraw' in ui)
add('header row is added to tray menu', 'appendTrayOwnerDrawItem(menu, trayMenuHeaderID, mfGrayed)' in ui)
add('show-window row is added to tray menu', 'appendTrayOwnerDrawItem(menu, trayMenuShowID, 0)' in ui and 'case trayMenuShowID:' in ui and 'a.showWindow()' in ui)
add('all actionable rows are owner-drawn', 'appendTrayOwnerDrawItem(menu, 1001, flagsCheck)' in ui and 'appendTrayOwnerDrawItem(menu, 1002, flagsResult)' in ui and 'appendTrayOwnerDrawItem(menu, 1003, 0)' in ui and 'appendTrayOwnerDrawItem(menu, 1004, flagsExport)' in ui and 'appendTrayOwnerDrawItem(menu, 1099, flagsExit)' in ui)
add('header renders Synapse brand text', 'tr("app.brand.primary")' in ui and 'tr("app.brand.secondary")' in ui)
add('selected row uses green accent strip', 'fill(hdc, rect{r.Left, r.Top + 4, r.Left + 3, r.Bottom - 4}, colors.green)' in ui)
add('separator is custom-drawn', 'dis.ItemID == trayMenuSeparatorID' in ui and 'line(hdc, int(r.Left)+10, y, int(r.Right)-10, y, 1, colors.border)' in ui)
add('track popup menu uses return-cmd path', 'procTrackPopupMenu.Call(menu, tpmRightButton|tpmReturnCmd' in ui)
add('measure handler sizes header and action rows', 'mis.ItemWidth = uint32(scaleDPI(270, a.dpi))' in ui and 'mis.ItemHeight = uint32(scaleDPI(48, a.dpi))' in ui and 'mis.ItemHeight = uint32(scaleDPI(34, a.dpi))' in ui)
failed = [n for n, ok in checks if not ok]
for n, ok in checks:
    print(('PASS' if ok else 'FAIL') + ': ' + n)
print(f'v2.3.12 tray-menu styling regression: {len(checks)-len(failed)}/{len(checks)}')
if failed:
    sys.exit(1)
