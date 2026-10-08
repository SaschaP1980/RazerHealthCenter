#!/usr/bin/env python3
from pathlib import Path
import json, sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]
checks=[]
def add(name, cond): checks.append((name, bool(cond)))
def read(rel): return (root/rel).read_text(encoding='utf-8')

model=read('model.go'); sg=read('setupscan.go'); ui=read('ui.go'); engine=read('engine.go')
health=read('health-engine-v1.4.6.ps1') if (root/'health-engine-v1.4.6.ps1').exists() else ''
locale=json.loads(read('locales/de-DE.json'))['strings']; build=read('build.sh')

add('app version 3.0.8', 'appVersion                   = "3.0.8"' in model)
add('health engine version 1.4.6', 'engineVersion                = "1.4.6"' in model)
add('active-product helpers', 'func activeHealthcheckProductCount(inv DeviceInventory) int' in sg and 'func hasActiveHealthcheckProduct(inv DeviceInventory) bool' in sg)
valid_block=sg[sg.find('func (d DeviceInventory) valid() bool'):sg.find('func activeHealthcheckProductCount')]
add('zero-active inventory remains valid', 'Healthcheck participation is a user preference' in valid_block and 'for _, p := range d.Products {' in valid_block and 'required > 0' not in valid_block)
add('participation persisted atomically', 'func persistHealthcheckParticipation(path, productKey string, required bool) error' in sg and '.healthcheck.tmp' in sg and 'os.Rename(tmp, path)' in sg)
add('setup rescan preserves known participation', 'func mergeHealthcheckParticipation(next *DeviceInventory, previous DeviceInventory)' in sg and 'next.Products[i].Required = required' in sg)
add('new products retain active default', 'default required=true' in sg)
merge_start=sg.find('mergeHealthcheckParticipation(&inv, previousInventory)'); rename_at=sg.find('if err := os.Rename(temp, a.inventoryPath)', merge_start)
add('merged preferences staged before inventory replacement', merge_start >= 0 and rename_at > merge_start and 'os.WriteFile(temp, b, 0644)' in sg[merge_start:rename_at])
add('whole-row toggle patches participation', 'func (a *App) toggleHealthcheckProduct(index int)' in sg and 'newRequired := !oldRequired' in sg and 'persistHealthcheckParticipation(a.inventoryPath, productKey, newRequired)' in sg)
add('toggle invalidates current health result', 'a.overall = overallUnchecked' in sg and 'a.states[i] = gateUnchecked' in sg and 'a.liveGateDisplay[i] = gateUnchecked' in sg and 'a.setTray(nimModify, a.iconIdle, tr("tray.tip.unchecked"))' in sg)
add('column renamed HEALTHCHECK', 'setup.table.state' in ui and locale.get('setup.table.state') == 'HEALTHCHECK')
add('status labels match active state', locale.get('setup.product.required') == 'AKTIV' and locale.get('setup.product.optional') == 'DEAKTIVIERT')
add('inactive icon/status grey and active Acid Green', 'iconColor = colors.muted' in ui and 'statusColor = colors.muted' in ui and 'iconColor := colors.green' in ui)
add('device rows have hover treatment', 'hoverSetupProductRow' in model and 'fill(hdc, row, colors.hover)' in ui and 'a.hoverSetupProductRow = idx' in ui)
add('device row click toggles participation', 'a.toggleHealthcheckProduct(idx)' in ui)
summary_start=ui.find('func drawSetupConnectionSummary'); summary_end=ui.find('func darkenRect', summary_start); summary_fn=ui[summary_start:summary_end]
add('connection presence rendering independent of Healthcheck participation', summary_start >= 0 and 'product.Required' not in summary_fn and 'entryColor = colors.green' in summary_fn)
add('setup scan blocked when all products inactive', 'blocked := a.setupReady && len(a.inventory.Products) > 0 && !hasActiveHealthcheckProduct(a.inventory)' in sg and 'SETUP scan blocked reason=no-active-healthcheck-product' in sg)
add('custom in-app setup notice modal', 'func (a *App) drawSetupNoticeModal' in ui and 'setupNoticeVisible' in model and 'MessageBox' not in sg)
add('no-active-device modal message', locale.get('setup.healthcheck.none.detail') == 'Mindestens ein Gerät muss für den Healthcheck aktiviert sein.')
add('health start blocked when no product active', 'hasActiveProduct := hasActiveHealthcheckProduct(a.inventory)' in engine and 'HEALTH blocked reason=no-active-healthcheck-product' in engine)
add('health engine filters products and connections by participation', '$RequiredProducts = @($DeviceProducts | Where-Object { $_.required })' in health and '$RelevantConnections = @($DeviceConnections | Where-Object { $DevicePids -contains' in health)
add('unattributed global logical product IDs cannot leak excluded products into Gate 12', '$PartialProductSelection' in health and 'if ($PartialProductSelection) { $LogicalProductIds = @() }' in health)
add('guided device skip function and UI', 'func (a *App) skipCurrentCalibrationProduct()' in sg and 'a.advanceCalibrationProductLocked()' in sg and 'action.skip_device' in ui)
add('device skip and step skip remain distinct', 'a.skipCurrentCalibrationProduct()' in ui and 'a.skipCurrentCalibrationStep()' in ui)
add('device skip localized', locale.get('action.skip_device') == 'Gerät überspringen')
add('lower setup action subtexts shortened', locale.get('action.setup_scan.sub') == 'Razer-Produkte neu inventarisieren' and locale.get('action.setup_calibrate.sub') == 'Wired/Wireless eindeutig zuordnen')
add('v3.0.8 regression validator is part of build gate', 'validate_healthcheck_selection_v237.py' in build)
production=(sg+'\n'+engine+'\n'+health).lower()
add('no product/PID-specific semantics added to Healthcheck selection', not any(t in production for t in ['00c0','00c1','02c9','02cc','viper v3 pro','blackwidow']))

failed=[name for name,ok in checks if not ok]
for name,ok in checks: print(('PASS' if ok else 'FAIL')+': '+name)
print(f'v3.0.8 Healthcheck/UI regression checks: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
