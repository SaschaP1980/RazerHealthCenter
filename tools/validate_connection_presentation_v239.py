#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
ui=(root/'ui.go').read_text(encoding='utf-8')
setup=(root/'setupscan.go').read_text(encoding='utf-8')
checks=[]
def add(name, ok): checks.append((name,bool(ok)))
add('typed display uses role before PID in summary', 'label = role + " · " + pid' in setup)
add('typed display uses role before PID in table', 'drawPart(role+" · ", entryColor)' in ui)
add('table no longer draws PID before learned role', 'drawPart(pid, pidColor)' not in ui and 'drawPart(" · "+role, roleColor)' not in ui)
add('connection sort helper exists', 'func setupConnectionSortPriority' in setup and 'func setupSortedProductConnectionPIDs' in setup)
add('wired sorts before wireless', 'case "wired-usb":\n\t\treturn 0' in setup and 'case "wireless-dongle":\n\t\treturn 1' in setup)
add('unknown or untyped connections sort last', 'return 2' in setup)
add('table uses sorted product connections', 'pids := setupSortedProductConnectionPIDs(inv, product)' in ui)
add('text summary uses sorted product connections', 'pids := setupSortedProductConnectionPIDs(inv, product)' in setup)
add('stable tie break by PID', 'return pids[i] < pids[j]' in setup)
add('live present still colors entire typed entry green', 'entryColor = colors.green' in ui and 'drawPart(role+" · ", entryColor)' in ui and 'drawPart(pid, entryColor)' in ui)
failed=[n for n,ok in checks if not ok]
for n,ok in checks: print(('PASS' if ok else 'FAIL')+': '+n)
print(f'v2.3.9 connection presentation regression: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
