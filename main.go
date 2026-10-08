//go:build windows

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"syscall"
	"time"
	"unsafe"
)

func main() {
	if hasArg("--repair-helper") {
		runRepairHelperMain()
		return
	}
	if hasArg("--admin-helper") {
		runAdminHelperMain()
		return
	}

	// Canonical v1.7.0 invariant recovered from main.go:4785 and the binary:
	// lock the goroutine to one OS thread before any HWND, tray or message-queue init.
	runtime.LockOSThread()
	defer runtime.UnlockOSThread()

	mutex, already, err := acquireSingleInstance()
	if err != nil {
		messageBox(0, appName(), trf("error.single_instance", "error", err.Error()), mbOK|mbIconError)
		return
	}
	if mutex != 0 {
		defer procCloseHandle.Call(mutex)
	}
	if already {
		activateExistingInstance()
		return
	}

	procSetProcessDPIAware.Call()
	exe, err := os.Executable()
	if err != nil {
		return
	}
	dataDir := filepath.Dir(exe)
	session := time.Now().Format("20060102-150405.000") + fmt.Sprintf("-%d", os.Getpid())
	a := &App{hoverRepairButton: -1, hoverSetupNoticeButton: -1, hoverSetupProductRow: -1, dataDir: dataDir, logsDir: filepath.Join(dataDir, "Logs"), diagDir: filepath.Join(dataDir, "Diagnostics"), runtimeDir: filepath.Join(dataDir, "Runtime"), exportsDir: filepath.Join(dataDir, "Exports"), setupDir: filepath.Join(dataDir, "Setup"), session: session, overall: overallUnchecked, detailGate: -1, hoverGate: -1, hoverAction: -1, hoverSidebar: -1, hoverDetailButton: -1, hoverModalButton: -1, hoverLogRow: -1, hoverLogTab: -1, logSelected: -1, currentView: 0, elevated: isAdmin()}
	a.inventoryPath = filepath.Join(a.setupDir, "RazerDeviceInventory-v2.json")
	a.connectionHistoryPath = filepath.Join(a.setupDir, "RazerConnectionHistory-v2.json")
	a.loadUIState()
	_ = ensureDir(a.setupDir)
	a.loadDeviceInventory()
	if a.setupReady {
		a.currentView = 1
	}
	app = a
	_ = ensureDir(a.diagDir)
	a.debugPath = filepath.Join(a.diagDir, "AppDebug-"+session+".log")
	a.debugf("BOOTSTRAP app=%s version=%s recovered=true pid=%d exe=%q guiThread=%d osThreadLocked=true", appName(), appVersion, os.Getpid(), exe, currentThreadID())
	a.debugf("START app=%s version=%s pid=%d elevated=%t exe=%q dataDir=%q go=%s guiThread=%d osThreadLocked=true", appName(), appVersion, os.Getpid(), a.elevated, exe, dataDir, runtime.Version(), currentThreadID())
	a.debugf("START diagnostic mode=standard-unelevated; repair elevation only after explicit confirmation")

	if err := a.prepareRuntime(); err != nil {
		messageBox(0, appName(), trf("error.runtime_prepare", "error", err.Error()), mbOK|mbIconError)
		return
	}
	defer os.RemoveAll(a.runtimeDir)

	if r, _, _ := procGetDpiForSystem.Call(); r != 0 {
		a.dpi = int(r)
	} else {
		a.dpi = 96
	}
	a.loadRuntimeIcons()
	a.initFonts()
	defer a.cleanupGDI()
	for i := 0; i < gateCount; i++ {
		a.states[i] = "UNKNOWN"
		a.liveGateDisplay[i] = gateUnchecked
	}

	if err := a.createWindow(); err != nil {
		messageBox(0, appName(), trf("error.window_create", "error", err.Error()), mbOK|mbIconError)
		return
	}
	if err := a.registerDeviceNotifications(); err != nil {
		a.debugf("DEVICE notification registration failed err=%v", err)
	} else {
		defer a.unregisterDeviceNotifications()
	}
	if a.setupReady {
		a.requestLivePresenceRefresh("startup", 150*time.Millisecond)
	}
	a.traceGUIThreadID = currentThreadID()
	a.tracePath = filepath.Join(a.diagDir, "UITrace-"+a.session+".log")
	a.writeStartupDebug(exe)
	a.startUITrace()
	defer a.stopUITrace()
	a.addTray()
	defer a.removeTray()
	a.refreshMeasurementsAsync()
	a.refreshVersionStatusAsync()
	a.debugf("UI initialized recovered dashboard; startup state=IDLE dpi=%d guiThread=%d", a.dpi, a.traceGUIThreadID)
	a.debugf("GUI thread invariant established guiThread=%d loopThread=%d hwnd=0x%X", a.traceGUIThreadID, currentThreadID(), a.hwnd)

	var m msg
	for {
		r, _, e := procGetMessageW.Call(uintptr(unsafe.Pointer(&m)), 0, 0, 0)
		if int32(r) == -1 {
			a.debugf("GetMessageW failed: %v", e)
			break
		}
		if r == 0 {
			break
		}
		procTranslateMessage.Call(uintptr(unsafe.Pointer(&m)))
		procDispatchMessageW.Call(uintptr(unsafe.Pointer(&m)))
	}
	a.debugf("EXIT")
}

var _ = syscall.Errno(0)
