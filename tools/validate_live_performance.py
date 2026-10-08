#!/usr/bin/env python3
from pathlib import Path
import sys
root=Path(__file__).resolve().parents[1]
dm=(root/'device_monitor.go').read_text(encoding='utf-8')
win=(root/'win32.go').read_text(encoding='utf-8')
runtime=(root/'runtime.go').read_text(encoding='utf-8')
hist=(root/'history_export.go').read_text(encoding='utf-8')
checks={
 'native SetupAPI DLL':'setupapi = syscall.NewLazyDLL("setupapi.dll")' in win,
 'present USB enumerator':all(x in dm for x in ['procSetupDiGetClassDevsW.Call','utf16("USB")','digcfPresent|digcfAllClasses']),
 'instance IDs native':'procSetupDiGetDeviceInstanceIdW.Call' in dm,
 'bus descriptor native':'procSetupDiGetDevicePropertyW.Call' in dm and 'devpkeyDeviceBusReportedDeviceDesc' in dm,
 'no powershell live subprocess':'exec.Command("powershell.exe"' not in dm and 'setupLiveScriptPath' not in dm,
 'no active live ps1':not any((root/'setup').glob('setup-razer-live-*.ps1')),
 'known PID filtering before property probe':'if targetProductKey == "" && !knownSet[pid]' in dm,
 'native target discovery':'targetProductKey != ""' in dm and 'strings.EqualFold(productKey, targetProductKey)' in dm,
 'quiet-window generation debounce':'setupLiveRefreshGeneration++' in dm and 'generation != a.setupLiveRefreshGeneration' in dm,
 'only one active follow-up':'Preserve at most one follow-up' in dm and 'setupLiveRefreshQueued = true' in dm,
 'performance diagnostics':all(x in dm for x in ['requested=%v present=%v changed=%v','usbNodes=%d','matchedRoots=%d','elapsedMs=%d']),
 'native diagnostic JSON':'SetupLiveProbe-v1.1.0.json' in dm and 'SetupLiveProbe-v1.1.0.json' in hist,
 'runtime advertises native':'liveProbeImplementation=native-setupapi-usb' in runtime and 'setupLiveProbeImplementation' in runtime,
}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(('PASS' if v else 'FAIL')+': '+k)
print(f'live performance checks: {len(checks)-len(failed)}/{len(checks)}')
if failed: sys.exit(1)
