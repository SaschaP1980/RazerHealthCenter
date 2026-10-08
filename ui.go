//go:build windows

package main

import (
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"sync/atomic"
	"syscall"
	"time"
	"unsafe"
)

var app *App

// COLORREF values (0x00BBGGRR). These match the dark/green Golden-v1.7.0
// palette closely while keeping every surface readable on standard Windows 11.
var colors = struct {
	bg, sidebar, surface, surface2, archiveSurface, hover, selected, actionHover, sidebarHover, buttonHover, border, borderStrong uintptr
	green, greenDark, success, warning, unclear, failure, info                                                                    uintptr
	text, text2, muted                                                                                                            uintptr
}{
	0x090a07, 0x0c0e09, 0x12140f, 0x161a13, 0x001b1b0e, 0x18251a, 0x12311b, 0x173d16, 0x132c14, 0x172019, 0x2c3327, 0x3f4a37,
	0x41ff00, 0x123f19, 0x41ff00, 0x00b8ff, 0x0080ff, 0x552dff, 0x00ffc800,
	0xedefeb, 0xc5c9c1, 0x8a9184,
}

const (
	sidebarW      = 88
	headerH       = 72
	contentX      = 109
	pageTitleTop  = 76
	pageUnderline = 110
	statusTop     = 120
	statusBottom  = 238
	tableTop      = 252
	tableHeaderH  = 30
	gateRowH      = 31
	actionTop     = 714
	actionBottom  = 772
)

func maxInt(a, b int) int {
	if a > b {
		return a
	}
	return b
}

func (a *App) initFonts() {
	if a.dpi <= 0 {
		a.dpi = 96
	}
	a.fontTitle = createFont(a.dpi, 15, 700, "Segoe UI")
	a.fontSubtitle = createFont(a.dpi, 8, 600, "Segoe UI")
	a.fontH1 = createFont(a.dpi, 13, 700, "Segoe UI")
	a.fontBody = createFont(a.dpi, 10, 400, "Segoe UI")
	a.fontBodySemi = createFont(a.dpi, 10, 600, "Segoe UI")
	a.fontSmall = createFont(a.dpi, 9, 400, "Segoe UI")
	a.fontTiny = createFont(a.dpi, 8, 400, "Segoe UI")
	a.fontBrand = createFont(a.dpi, 15, 700, "Segoe UI")
	a.fontOverall = createFont(a.dpi, 28, 700, "Segoe UI")
	a.fontRuntime = createFont(a.dpi, 27, 700, "Segoe UI")
	a.fontAction = createFont(a.dpi, 11, 600, "Segoe UI")
	a.fontActionIcon = createFont(a.dpi, 20, 400, "Segoe UI Symbol")
	a.fontNav = createFont(a.dpi, 8, 600, "Segoe UI")
	a.fontDetailClose = createFont(a.dpi, 22, 400, "Segoe UI Symbol")
}

func (a *App) loadRuntimeIcons() {
	assetRoot := filepath.Join(a.runtimeDir, "assets")
	statusRoot := filepath.Join(assetRoot, "status")
	uiRoot := filepath.Join(assetRoot, "ui")
	a.iconIdle = loadIcon(filepath.Join(assetRoot, "idle.ico"), 32, 32)
	a.iconPass = loadIcon(filepath.Join(assetRoot, "passed.ico"), 32, 32)
	a.iconFail = loadIcon(filepath.Join(assetRoot, "failed.ico"), 32, 32)
	a.iconApp = loadIcon(filepath.Join(assetRoot, "app-heart.ico"), 48, 48)
	a.iconAppSmall = loadIcon(filepath.Join(assetRoot, "app-heart.ico"), 16, 16)
	// Golden info view uses a native high-resolution heart instead of scaling
	// the 48x48 header handle up to 88x88.
	a.iconAppInfo = loadIcon(filepath.Join(assetRoot, "app-heart.ico"), 96, 96)
	a.iconStatusReady = loadIcon(filepath.Join(statusRoot, "status-ready.ico"), 88, 88)
	a.iconStatusPass = loadIcon(filepath.Join(statusRoot, "status-pass.ico"), 88, 88)
	a.iconStatusFail = loadIcon(filepath.Join(statusRoot, "status-fail.ico"), 88, 88)
	for i := 0; i < 8; i++ {
		a.iconStatusPulse[i] = loadIcon(filepath.Join(statusRoot, fmt.Sprintf("status-check-%d.ico", i)), 88, 88)
	}
	sides := []string{"nav-setup", "nav-status", "nav-logs", "nav-info"}
	for i, n := range sides {
		a.sidebarIcons[i][0] = loadIcon(filepath.Join(uiRoot, n+"-muted.ico"), 28, 28)
		a.sidebarIcons[i][1] = loadIcon(filepath.Join(uiRoot, n+"-green.ico"), 28, 28)
	}
	vars := []string{"muted", "green", "warning", "red"}
	for i, n := range componentIconNames {
		for j, v := range vars {
			a.componentIcons[i][j] = loadIcon(filepath.Join(uiRoot, n+"-"+v+".ico"), 20, 20)
		}
	}
}

func (a *App) createWindow() error {
	hInst, _, _ := procGetModuleHandleWCompat()
	cursor, _, _ := procLoadCursorW.Call(0, 32512)
	className := utf16(mainWindowClass)
	modalClassName := utf16(modalWindowClass)
	trayMenuClassName := utf16(trayMenuWindowClass)

	cb := syscall.NewCallback(wndProc)
	wc := wndClassEx{
		CbSize:        uint32(unsafe.Sizeof(wndClassEx{})),
		Style:         csDblClks,
		LpfnWndProc:   cb,
		HInstance:     hInst,
		HIcon:         a.iconApp,
		HCursor:       cursor,
		LpszClassName: className,
		HIconSm:       a.iconAppSmall,
	}
	a.debugf("WINCLASS register main class=%q cbSize=%d structSize=%d hInst=0x%X wndProc=0x%X", mainWindowClass, wc.CbSize, unsafe.Sizeof(wndClassEx{}), hInst, cb)
	atom, _, e := procRegisterClassExW.Call(uintptr(unsafe.Pointer(&wc)))
	if atom == 0 {
		a.debugf("WINCLASS main FAILED class=%q err=%v", mainWindowClass, e)
		return fmt.Errorf("RegisterClassExW: %v", e)
	}
	a.debugf("WINCLASS main OK class=%q atom=0x%X", mainWindowClass, atom)

	modalCB := syscall.NewCallback(modalWndProc)
	mwc := wndClassEx{
		CbSize:        uint32(unsafe.Sizeof(wndClassEx{})),
		LpfnWndProc:   modalCB,
		HInstance:     hInst,
		HIcon:         a.iconApp,
		HCursor:       cursor,
		LpszClassName: modalClassName,
		HIconSm:       a.iconAppSmall,
	}
	modalAtom, _, me := procRegisterClassExW.Call(uintptr(unsafe.Pointer(&mwc)))
	if modalAtom == 0 {
		a.debugf("WINCLASS modal FAILED class=%q err=%v", modalWindowClass, me)
		return fmt.Errorf("Register modal class: %v", me)
	}
	a.debugf("WINCLASS modal OK class=%q atom=0x%X", modalWindowClass, modalAtom)

	trayMenuCB := syscall.NewCallback(trayMenuWndProc)
	twc := wndClassEx{
		CbSize:        uint32(unsafe.Sizeof(wndClassEx{})),
		LpfnWndProc:   trayMenuCB,
		HInstance:     hInst,
		HIcon:         a.iconApp,
		HCursor:       cursor,
		LpszClassName: trayMenuClassName,
		HIconSm:       a.iconAppSmall,
	}
	trayMenuAtom, _, te := procRegisterClassExW.Call(uintptr(unsafe.Pointer(&twc)))
	if trayMenuAtom == 0 {
		a.debugf("WINCLASS tray menu FAILED class=%q err=%v", trayMenuWindowClass, te)
		return fmt.Errorf("Register tray menu class: %v", te)
	}
	a.debugf("WINCLASS tray menu OK class=%q atom=0x%X", trayMenuWindowClass, trayMenuAtom)

	clientW := scaleDPI(1180, a.dpi)
	clientH := scaleDPI(800, a.dpi)
	rr := rect{Right: int32(clientW), Bottom: int32(clientH)}
	procAdjustWindowRectEx.Call(uintptr(unsafe.Pointer(&rr)), goldenWindowStyle, 0, 0)
	outerW := int(rr.Right - rr.Left)
	outerH := int(rr.Bottom - rr.Top)
	sw, _, _ := procGetSystemMetrics.Call(0)
	sh, _, _ := procGetSystemMetrics.Call(1)
	x := (int(sw) - outerW) / 2
	y := (int(sh) - outerH) / 2
	if x < 0 {
		x = 0
	}
	if y < 0 {
		y = 0
	}

	titleText := trf("app.window_title", "title", appName(), "version", appVersion)
	title := utf16(titleText)
	a.debugf("WINDOW create class=%q title=%q style=0x%X dpi=%d client=%dx%d outer=%dx%d pos=%d,%d", mainWindowClass, titleText, goldenWindowStyle, a.dpi, clientW, clientH, outerW, outerH, x, y)
	hwnd, _, e := procCreateWindowExW.Call(
		0,
		uintptr(unsafe.Pointer(className)),
		uintptr(unsafe.Pointer(title)),
		goldenWindowStyle,
		uintptr(int32(x)), uintptr(int32(y)), uintptr(int32(outerW)), uintptr(int32(outerH)),
		0, 0, hInst, 0,
	)
	if hwnd == 0 {
		a.debugf("WINDOW create FAILED err=%v", e)
		return fmt.Errorf("CreateWindowExW: %v", e)
	}
	a.hwnd = hwnd
	setDarkTitlebar(hwnd)
	procShowWindow.Call(hwnd, swShow)
	procUpdateWindow.Call(hwnd)
	a.debugf("WINDOW create OK hwnd=0x%X", hwnd)
	return nil
}

func modalWndProc(hwnd uintptr, m uint32, wParam, lParam uintptr) uintptr {
	r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), wParam, lParam)
	return r
}

func trayMenuWndProc(hwnd uintptr, m uint32, wParam, lParam uintptr) uintptr {
	if app == nil {
		r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), wParam, lParam)
		return r
	}
	return app.handleTrayPopupWndProc(hwnd, m, wParam, lParam)
}

func scaleDPI(v, dpi int) int {
	if dpi <= 0 {
		dpi = 96
	}
	return (v*dpi + 48) / 96
}

func procGetModuleHandleWCompat() (uintptr, uintptr, error) {
	p := kernel32.NewProc("GetModuleHandleW")
	r2, _, e := p.Call(0)
	return r2, 0, e
}

func wndProc(hwnd uintptr, m uint32, wParam, lParam uintptr) uintptr {
	if app != nil {
		atomic.StoreUint32(&app.traceLastMsg, m)
		atomic.StoreInt32(&app.traceInWndProc, 1)
		start := time.Now().UnixNano()
		atomic.StoreInt64(&app.traceWndStartNs, start)
		defer func() {
			now := time.Now().UnixNano()
			atomic.StoreInt64(&app.traceLastWndNs, now)
			updateAtomicMax(&app.traceMaxWndNs, now-start)
			atomic.StoreInt32(&app.traceInWndProc, 0)
			tid := currentThreadID()
			atomic.StoreUint32(&app.traceLastWndThreadID, tid)
			if app.traceGUIThreadID != 0 && tid != app.traceGUIThreadID {
				atomic.AddUint64(&app.traceThreadMismatches, 1)
			}
		}()
	}
	if app == nil {
		r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), wParam, lParam)
		return r
	}
	switch m {
	case wmTracePing:
		atomic.StoreInt64(&app.traceLastPongNs, time.Now().UnixNano())
		return 0
	case wmEraseBkgnd:
		// Golden paints the complete client area from an offscreen buffer. Avoid
		// a separate erase pass, which was the main source of r3 hover flicker.
		return 1
	case wmPaint:
		atomic.AddUint64(&app.tracePaints, 1)
		atomic.StoreInt32(&app.traceInPaint, 1)
		ps := time.Now().UnixNano()
		atomic.StoreInt64(&app.tracePaintStartNs, ps)
		app.paint()
		pe := time.Now().UnixNano()
		atomic.StoreInt64(&app.traceLastPaintNs, pe)
		updateAtomicMax(&app.traceMaxPaintNs, pe-ps)
		atomic.StoreInt32(&app.traceInPaint, 0)
		return 0
	case wmMouseMove:
		atomic.AddUint64(&app.traceMouseMoves, 1)
		app.ensureMouseLeaveTracking()
		if app.handleDetailScrollDrag(int(hiword(lParam))) {
			return 0
		}
		app.handleMouseMove(int(loword(lParam)), int(hiword(lParam)))
		return 0
	case wmMouseLeave:
		app.handleMouseLeave()
		return 0
	case wmLButtonDown:
		if app.handleDetailScrollMouseDown(int(loword(lParam)), int(hiword(lParam))) {
			return 0
		}
		return 0
	case wmLButtonUp:
		if app.endDetailScrollDrag() {
			return 0
		}
		app.handleClick(int(loword(lParam)), int(hiword(lParam)))
		return 0
	case wmLButtonDblClk:
		app.handleDoubleClick(int(loword(lParam)), int(hiword(lParam)))
		return 0
	case wmKeyDown:
		if wParam == vkEscape {
			if app.closeSetupNotice() {
				return 0
			}
			if app.closeSetupCalibration() {
				return 0
			}
			if app.closeRepairDialog() {
				return 0
			}
			if app.closeDetailPopover() {
				return 0
			}
		}
	case wmMouseWheel:
		app.handleMouseWheel(int(hiword(wParam)))
		return 0
	case wmTimer:
		app.mu.Lock()
		checking := app.checking
		setupScanning := app.setupScanning
		liveRefreshing := app.setupLiveRefreshing
		app.mu.Unlock()
		if checking || setupScanning || liveRefreshing {
			procInvalidateRect.Call(hwnd, 0, 0)
		}
		return 0
	case wmDeviceChange:
		event := uint32(wParam)
		if event == dbtDevNodesChanged || event == dbtDeviceArrival || event == dbtDeviceRemoveComplete {
			app.handleWindowsDeviceChange(event)
		}
		return 1
	case wmRefresh:
		procInvalidateRect.Call(hwnd, 0, 0)
		return 0
	case wmEngineDone:
		procKillTimer.Call(hwnd, 1)
		procInvalidateRect.Call(hwnd, 0, 0)
		return 0
	case wmExportDone:
		app.handleExportResult()
		procInvalidateRect.Call(hwnd, 0, 0)
		return 0
	case wmRepairDone:
		procInvalidateRect.Call(hwnd, 0, 0)
		return 0
	case wmSetupDone:
		procKillTimer.Call(hwnd, 1)
		app.mu.Lock()
		continueHealth := app.setupReady && app.setupContinueHealth
		app.setupContinueHealth = false
		if continueHealth {
			app.currentView = 1
		}
		app.mu.Unlock()
		procInvalidateRect.Call(hwnd, 0, 0)
		if continueHealth {
			app.startCheck()
		}
		return 0
	case wmTray:
		if uint32(lParam) == wmLButtonDblClk {
			app.showWindow()
			return 0
		}
		if uint32(lParam) == wmRButtonUp {
			app.showTrayMenu()
			return 0
		}
	case wmClose:
		procShowWindow.Call(hwnd, 0)
		return 0
	case wmDestroy:
		procPostQuitMessage.Call(0)
		return 0
	}
	r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), wParam, lParam)
	return r
}

func (a *App) ensureMouseLeaveTracking() {
	a.mu.Lock()
	if a.mouseTracking {
		a.mu.Unlock()
		return
	}
	a.mouseTracking = true
	a.mu.Unlock()
	tme := trackMouseEvent{CbSize: uint32(unsafe.Sizeof(trackMouseEvent{})), DwFlags: tmeLeave, HwndTrack: a.hwnd}
	procTrackMouseEvent.Call(uintptr(unsafe.Pointer(&tme)))
}

func (a *App) handleMouseLeave() {
	a.mu.Lock()
	changed := a.hoverGate != -1 || a.hoverAction != -1 || a.hoverSidebar != -1 || a.hoverDetailButton != -1 || a.hoverModalButton != -1 || a.hoverRepairButton != -1 || a.hoverSetupCalibrationButton != -1 || a.hoverSetupNoticeButton != -1 || a.hoverSetupProductRow != -1 || a.hoverLogRow != -1 || a.hoverDetailClose
	a.hoverGate = -1
	a.hoverAction = -1
	a.hoverSidebar = -1
	a.hoverDetailButton = -1
	a.hoverModalButton = -1
	a.hoverRepairButton = -1
	a.hoverSetupCalibrationButton = -1
	a.hoverSetupNoticeButton = -1
	a.hoverSetupProductRow = -1
	a.hoverLogRow = -1
	a.hoverDetailClose = false
	a.mouseTracking = false
	a.mu.Unlock()
	if changed {
		procInvalidateRect.Call(a.hwnd, 0, 0)
	}
}

// paint uses the Golden-v1.7.0 GDI strategy recovered from the binary symbols:
// render the complete client into a compatible memory bitmap, then publish one
// BitBlt. This removes the r3 blank/partial frames during hover and live updates.
func (a *App) paint() {
	var ps paintStruct
	hdc, _, _ := procBeginPaint.Call(a.hwnd, uintptr(unsafe.Pointer(&ps)))
	if hdc == 0 {
		return
	}
	defer procEndPaint.Call(a.hwnd, uintptr(unsafe.Pointer(&ps)))

	var cr rect
	procGetClientRect.Call(a.hwnd, uintptr(unsafe.Pointer(&cr)))
	w, h := int(cr.Right), int(cr.Bottom)
	mem, _, _ := procCreateCompatibleDC.Call(hdc)
	bmp, _, _ := procCreateCompatibleBitmap.Call(hdc, uintptr(w), uintptr(h))
	if mem == 0 || bmp == 0 {
		if mem != 0 {
			procDeleteDC.Call(mem)
		}
		if bmp != 0 {
			procDeleteObject.Call(bmp)
		}
		a.drawFrame(hdc, w, h)
		return
	}
	old, _, _ := procSelectObject.Call(mem, bmp)
	a.drawFrame(mem, w, h)
	procBitBlt.Call(hdc, 0, 0, uintptr(w), uintptr(h), mem, 0, 0, srccopy)
	procSelectObject.Call(mem, old)
	procDeleteObject.Call(bmp)
	procDeleteDC.Call(mem)
}

func (a *App) drawFrame(hdc uintptr, w, h int) {
	fill(hdc, rect{0, 0, int32(w), int32(h)}, colors.bg)
	a.mu.Lock()
	view := a.currentView
	modal := a.exportDialogVisible
	repairModal := a.repairDialogVisible
	setupCalibrationModal := a.setupCalibrationVisible
	setupNoticeModal := a.setupNoticeVisible
	a.mu.Unlock()
	a.drawShell(hdc, w, h, view)
	switch view {
	case 0:
		a.drawSetupView(hdc, w, h)
	case 1:
		a.drawDashboard(hdc, w, h)
	case 2:
		a.drawLogsView(hdc, w, h)
	case 3:
		a.drawInfoView(hdc, w, h)
	}
	if setupNoticeModal {
		a.drawSetupNoticeModal(hdc, w, h)
	} else if repairModal {
		a.drawRepairModal(hdc, w, h)
	} else if modal {
		a.drawExportModal(hdc, w, h)
	} else if setupCalibrationModal {
		a.drawSetupCalibrationModal(hdc, w, h)
	}
}

func (a *App) drawShell(hdc uintptr, w, h, view int) {
	fill(hdc, rect{0, 0, sidebarW, int32(h)}, colors.sidebar)
	line(hdc, sidebarW, 0, sidebarW, h, 1, colors.border)
	line(hdc, sidebarW, headerH, w, headerH, 1, colors.border)

	a.mu.Lock()
	archiveMode := view == 2 && a.logHistoricalOpen && a.logHistoricalActive
	a.mu.Unlock()
	tagline := tr("app.tagline")
	taglineColor := colors.green
	if archiveMode {
		tagline = tr("app.tagline.archive")
		taglineColor = colors.info
	}

	drawIcon(hdc, a.iconApp, 21, 16, 48, 48)
	text(hdc, a.fontBrand, tr("app.brand.primary"), rect{112, 14, 470, 39}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBody, tr("app.brand.secondary"), rect{112, 36, 270, 55}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, tagline, rect{int32(w - 300), 18, int32(w - 30), 45}, taglineColor, dtRight|dtVCenter|dtSingleLine|dtNoPrefix)

	items := []string{tr("nav.setup"), tr("nav.status"), tr("nav.logs"), tr("nav.info")}
	for i, label := range items {
		y := 91 + i*88
		active := i == view
		a.mu.Lock()
		hover := i == a.hoverSidebar
		a.mu.Unlock()
		if active {
			fill(hdc, rect{7, int32(y), 82, int32(y + 73)}, colors.greenDark)
			fill(hdc, rect{7, int32(y), 10, int32(y + 73)}, colors.green)
		} else if hover {
			fill(hdc, rect{7, int32(y), 82, int32(y + 73)}, colors.sidebarHover)
			fill(hdc, rect{7, int32(y), 9, int32(y + 73)}, colors.greenDark)
		}
		icon := a.sidebarIcons[i][0]
		col := colors.text2
		if active || hover {
			icon = a.sidebarIcons[i][1]
			col = colors.green
		}
		drawIcon(hdc, icon, 31, y+8, 28, 28)
		text(hdc, a.fontNav, label, rect{7, int32(y + 42), 83, int32(y + 68)}, col, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	}
	line(hdc, 21, h-56, 69, h-56, 1, colors.green)
	text(hdc, a.fontTiny, trf("app.version", "version", appVersion), rect{21, int32(h - 48), 69, int32(h - 25)}, colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
}

func (a *App) drawPageHeader(hdc uintptr, w int, title, right string) {
	text(hdc, a.fontBodySemi, title, rect{119, pageTitleTop, int32(w - 30), pageTitleTop + 27}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	fill(hdc, rect{contentX, pageUnderline, 248, pageUnderline + 3}, colors.green)
	if right != "" {
		text(hdc, a.fontTiny, right, rect{int32(w - 310), pageTitleTop, int32(w - 30), pageTitleTop + 27}, colors.muted, dtRight|dtVCenter|dtSingleLine|dtNoPrefix)
	}
}

func pulseFrameIndex(now time.Time) int {
	// Golden v1.7.0 uses a ping-pong heartbeat: 0→1→…→7→6→…→1→0.
	// A 14-step cycle avoids duplicating either endpoint while eliminating the
	// visible 7→0 jump of the recovery-r4 forward-only loop.
	step := int((now.UnixNano() / 125000000) % 14)
	if step <= 7 {
		return step
	}
	return 14 - step
}

func drawSetupDeviceClassIcon(hdc uintptr, kind string, x, y int, background uintptr) {
	drawSetupDeviceClassIconColor(hdc, kind, x, y, background, colors.green)
}

func drawSetupDeviceClassIconColor(hdc uintptr, kind string, x, y int, background, c uintptr) {
	kind = strings.ToLower(strings.TrimSpace(kind))
	switch kind {
	case "mouse":
		// Compact mouse outline with split buttons and wheel.
		roundBox(hdc, rect{int32(x + 5), int32(y + 1), int32(x + 17), int32(y + 20)}, 6, background, c, 1)
		line(hdc, x+11, y+2, x+11, y+8, 1, c)
		line(hdc, x+7, y+8, x+15, y+8, 1, c)
		line(hdc, x+11, y+4, x+11, y+6, 2, c)
	case "keyboard":
		// Keyboard silhouette; the key grid remains legible at 20 px.
		roundBox(hdc, rect{int32(x + 1), int32(y + 4), int32(x + 21), int32(y + 18)}, 3, background, c, 1)
		for row := 0; row < 2; row++ {
			for col := 0; col < 5; col++ {
				px := x + 4 + col*3
				py := y + 7 + row*4
				fill(hdc, rect{int32(px), int32(py), int32(px + 1), int32(py + 1)}, c)
			}
		}
		line(hdc, x+6, y+15, x+16, y+15, 1, c)
	default:
		// Generic device fallback when Windows evidence does not identify one
		// unambiguous primary HID class. Never guess the product category.
		roundBox(hdc, rect{int32(x + 3), int32(y + 3), int32(x + 19), int32(y + 18)}, 3, background, c, 1)
		line(hdc, x+7, y+7, x+15, y+7, 1, c)
		line(hdc, x+7, y+11, x+15, y+11, 1, c)
	}
}

func drawSetupLiveRefreshBar(hdc uintptr, r rect) {
	cellW := int(r.Right - r.Left)
	barW := cellW * 70 / 100
	if barW < 120 {
		barW = 120
	}
	if barW > cellW-18 {
		barW = cellW - 18
	}
	if barW <= 20 {
		return
	}
	left := int(r.Left) + (cellW-barW)/2
	// Keep the live-refresh indicator in the same vertical band as the PID/role
	// text. It is a true overlay, not a second line below the cell content.
	centerY := int(r.Top+r.Bottom) / 2
	track := rect{int32(left), int32(centerY - 3), int32(left + barW), int32(centerY + 3)}
	fill(hdc, track, colors.surface2)
	innerW := int(track.Right-track.Left) - 2
	if innerW <= 8 {
		return
	}
	segmentW := maxInt(12, innerW/4)
	travel := innerW - segmentW
	phase := int((time.Now().UnixMilli() / 20) % int64(maxInt(1, travel*2)))
	if phase > travel {
		phase = travel*2 - phase
	}
	fill(hdc, rect{track.Left + 1 + int32(phase), track.Top, track.Left + 1 + int32(phase+segmentW), track.Bottom}, colors.green)
}

func drawSetupConnectionSummary(hdc uintptr, a *App, inv DeviceInventory, product DeviceProductProfile, r rect, liveFresh, refreshing bool) {
	if refreshing {
		// During a live refresh the previous PID/role content is deliberately
		// hidden. Rendering stale glyphs beneath the animated sweep causes
		// visible flicker/bleed-through on native Windows GDI. Show only the
		// Acid-Green refresh indicator until the verified result is available.
		drawSetupLiveRefreshBar(hdc, r)
		return
	}

	byPID := make(map[string]DeviceConnectionProfile, len(inv.Connections))
	for _, c := range inv.Connections {
		byPID[strings.ToUpper(strings.TrimSpace(c.PID))] = c
	}
	x := int(r.Left)
	drawPart := func(value string, color uintptr) bool {
		if value == "" || x >= int(r.Right) {
			return x < int(r.Right)
		}
		w := measureSingleLineWidth(hdc, a.fontSmall, value)
		text(hdc, a.fontSmall, value, rect{int32(x), r.Top, r.Right, r.Bottom}, color, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		x += w
		return x < int(r.Right)
	}
	pids := setupSortedProductConnectionPIDs(inv, product)
	for i, pid := range pids {
		if i > 0 && !drawPart(", ", colors.muted) {
			break
		}
		c, ok := byPID[pid]
		entryColor := colors.muted
		if liveFresh && ok && c.PresentAtScan {
			// A live-present connection is one visual unit: learned role and PID
			// use the same Acid Green while the connection remains physically live.
			entryColor = colors.green
		}
		if ok {
			if role := setupConnectionRoleLabel(c); role != "" {
				if !drawPart(role+" · ", entryColor) {
					break
				}
			}
		}
		if !drawPart(pid, entryColor) {
			break
		}
	}
}

func darkenRect(hdc uintptr, r rect, alpha byte) {
	w := int(r.Right - r.Left)
	h := int(r.Bottom - r.Top)
	if w <= 0 || h <= 0 || alpha == 0 {
		return
	}
	mem, _, _ := procCreateCompatibleDC.Call(hdc)
	bmp, _, _ := procCreateCompatibleBitmap.Call(hdc, uintptr(w), uintptr(h))
	if mem == 0 || bmp == 0 {
		if mem != 0 {
			procDeleteDC.Call(mem)
		}
		if bmp != 0 {
			procDeleteObject.Call(bmp)
		}
		return
	}
	old, _, _ := procSelectObject.Call(mem, bmp)
	fill(mem, rect{0, 0, int32(w), int32(h)}, 0)
	procAlphaBlend.Call(hdc, uintptr(r.Left), uintptr(r.Top), uintptr(w), uintptr(h), mem, 0, 0, uintptr(w), uintptr(h), uintptr(alpha)<<16)
	procSelectObject.Call(mem, old)
	procDeleteObject.Call(bmp)
	procDeleteDC.Call(mem)
}

func drawSetupScanOverlay(hdc uintptr, table rect) {
	// Keep the current inventory visible as context, but make it clearly
	// inactive while the read-only inventory process is running.
	darkenRect(hdc, table, 128)
	tableW := int(table.Right - table.Left)
	barW := tableW * 70 / 100
	if barW < 240 {
		barW = 240
	}
	left := int(table.Left) + (tableW-barW)/2
	centerY := int(table.Top+table.Bottom) / 2
	track := rect{int32(left), int32(centerY - 5), int32(left + barW), int32(centerY + 5)}
	roundBox(hdc, track, 5, colors.surface2, colors.borderStrong, 1)
	innerLeft := int(track.Left + 2)
	innerWidth := int(track.Right-track.Left) - 4
	if innerWidth <= 12 {
		return
	}
	segmentWidth := innerWidth / 4
	travel := innerWidth - segmentWidth
	phase := int((time.Now().UnixMilli() / 24) % int64(maxInt(1, travel*2)))
	if phase > travel {
		phase = travel*2 - phase
	}
	fill(hdc, rect{int32(innerLeft + phase), track.Top + 2, int32(innerLeft + phase + segmentWidth), track.Bottom - 2}, colors.green)
}

func (a *App) drawSetupView(hdc uintptr, w, h int) {
	a.mu.Lock()
	ready := a.setupReady
	scanning := a.setupScanning
	liveFresh := a.setupLiveFresh
	liveRefreshing := a.setupLiveRefreshing
	errText := a.setupLastError
	inv := a.inventory
	hoverAction := a.hoverAction
	hoverProduct := a.hoverSetupProductRow
	checking := a.checking
	repairing := a.repairing
	a.mu.Unlock()

	a.drawPageHeader(hdc, w, tr("page.setup.title"), tr("page.setup.readonly"))
	right := w - 18
	card := rect{contentX, 128, int32(right), 244}
	roundBox(hdc, card, 8, colors.surface, colors.border, 1)
	state := tr("setup.state.required")
	stateCol := colors.warning
	detail := tr("setup.state.required.detail")
	if scanning {
		state = tr("setup.state.scanning")
		stateCol = colors.green
		detail = tr("setup.state.scanning.detail")
	} else if ready {
		state = tr("setup.state.ready")
		stateCol = colors.success
		if liveFresh {
			detail = trf("setup.state.ready.detail", "active", activeHealthcheckProductCount(inv), "products", len(inv.Products), "present", setupPresentConnectionCount(inv), "connections", len(inv.Connections))
		} else if liveRefreshing {
			detail = tr("setup.state.live_refreshing.detail")
		} else {
			detail = tr("setup.state.snapshot.detail")
		}
	} else if strings.TrimSpace(errText) != "" {
		state = tr("setup.state.failed")
		stateCol = colors.failure
		detail = errText
	}
	text(hdc, a.fontTiny, tr("setup.profile.label"), rect{132, 146, 320, 166}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontH1, state, rect{132, 168, 620, 198}, stateCol, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontSmall, detail, rect{132, 202, int32(right - 24), 230}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBodySemi, tr("setup.inventory.title"), rect{contentX, 266, 700, 292}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	table := rect{contentX, 300, int32(right), 650}
	roundBox(hdc, table, 6, colors.bg, colors.border, 1)
	fill(hdc, rect{table.Left + 1, table.Top + 1, table.Right - 1, table.Top + 32}, colors.surface)
	text(hdc, a.fontTiny, tr("setup.table.product"), rect{132, 300, 560, 332}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, tr("setup.table.connections"), rect{580, 300, 850, 332}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, tr("setup.table.state"), rect{880, 300, 1135, 332}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	if !ready {
		text(hdc, a.fontBody, tr("setup.inventory.empty"), rect{132, 350, int32(right - 24), 405}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
	} else {
		y := 334
		maxRows := 8
		for i, product := range inv.Products {
			if i >= maxRows {
				break
			}
			if i > 0 {
				line(hdc, int(table.Left+1), y, int(table.Right-1), y, 1, colors.border)
			}
			row := rect{table.Left + 1, int32(y), table.Right - 1, int32(y + 38)}
			rowBackground := colors.bg
			if hoverProduct == i && !scanning && !checking && !repairing {
				fill(hdc, row, colors.hover)
				rowBackground = colors.hover
			}
			iconColor := colors.green
			status := tr("setup.product.required")
			statusColor := colors.green
			if !product.Required {
				iconColor = colors.muted
				status = tr("setup.product.optional")
				statusColor = colors.muted
			}
			drawSetupDeviceClassIconColor(hdc, setupProductDeviceClass(inv, product), 132, y+8, rowBackground, iconColor)
			text(hdc, a.fontSmall, product.Name, rect{160, int32(y), 560, int32(y + 38)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
			drawSetupConnectionSummary(hdc, a, inv, product, rect{580, int32(y), 850, int32(y + 38)}, liveFresh, liveRefreshing)
			text(hdc, a.fontTiny, status, rect{880, int32(y), 1135, int32(y + 38)}, statusColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
			y += 38
		}
		if len(inv.Products) == 0 {
			text(hdc, a.fontSmall, tr("setup.inventory.no_required"), rect{132, 350, int32(right - 24), 395}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
		}
	}

	if scanning {
		drawSetupScanOverlay(hdc, table)
	}

	primary := rect{109, actionTop, 389, actionBottom}
	secondary := rect{406, actionTop, 686, actionBottom}
	scanTitle := tr("action.setup_scan")
	if scanning {
		scanTitle = tr("action.setup_scanning")
	}
	drawActionCard(hdc, a, primary, 4, "⌕", scanTitle, tr("action.setup_scan.sub"), hoverAction == 4, !scanning && !checking && !repairing)
	drawActionCard(hdc, a, secondary, 5, "↔", tr("action.setup_calibrate"), tr("action.setup_calibrate.sub"), hoverAction == 5, ready && !scanning && !checking && !repairing)
}

func (a *App) drawDashboard(hdc uintptr, w, h int) {
	a.mu.Lock()
	overall := a.overall
	checking := a.checking
	states := a.liveGateDisplay
	ins := a.gateInspections
	findings := append([]ProblemFinding(nil), a.problemFindings...)
	last := a.lastCheck
	dur := a.lastDuration
	started := a.checkStarted
	current := a.currentGate
	done := a.completedGates
	detail := a.detailGate
	exporting := a.exporting
	repairing := a.repairing
	hover := a.hoverGate
	hoverAction := a.hoverAction
	a.mu.Unlock()

	a.drawPageHeader(hdc, w, tr("page.status.title"), tr("page.status.live"))
	right := w - 18
	box := rect{contentX, statusTop, int32(right), statusBottom}
	roundBox(hdc, box, 8, colors.surface, colors.border, 1)

	icon := a.iconStatusReady
	if checking {
		icon = a.iconStatusPulse[pulseFrameIndex(time.Now())]
	} else if overall == overallHealthy {
		icon = a.iconStatusPass
	} else if overall == overallFailed {
		icon = a.iconStatusFail
	}
	drawIcon(hdc, icon, 130, 138, 82, 82)
	text(hdc, a.fontTiny, tr("status.system_label"), rect{240, 137, 460, 155}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontOverall, overallText(overall), rect{239, 151, 690, 199}, stateColor(overall), dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontSmall, overallSummary(overall, checking, states), rect{240, 198, 690, 224}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	line(hdc, 701, 137, 701, 220, 1, colors.borderStrong)
	text(hdc, a.fontTiny, tr("status.runtime_label"), rect{742, 137, 890, 156}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	elapsed := "--:--"
	if checking {
		elapsed = formatClock(time.Since(started))
	} else if !last.IsZero() {
		elapsed = formatClock(dur)
	}
	text(hdc, a.fontRuntime, elapsed, rect{742, 151, 910, 199}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBodySemi, trf("gate.progress.completed", "done", doneForOverall(checking, overall, done), "total", gateCount), rect{744, 198, 920, 220}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	progress := 0
	if checking {
		progress = done * 100 / gateCount
	} else if !last.IsZero() {
		progress = 100
	}
	bar := rect{946, 157, 1115, 170}
	roundBox(hdc, bar, 6, colors.bg, colors.borderStrong, 1)
	if progress > 0 {
		pw := (int(bar.Right-bar.Left) * progress) / 100
		roundBox(hdc, rect{bar.Left, bar.Top, bar.Left + int32(pw), bar.Bottom}, 6, colors.green, colors.green, 1)
	}
	text(hdc, a.fontTiny, trf("status.progress.percent", "percent", progress), rect{1121, 151, int32(right - 8), 175}, colors.text2, dtRight|dtVCenter|dtSingleLine|dtNoPrefix)
	statusLine := tr("measurement.not_run")
	if checking {
		remaining := gateCount - done
		if remaining < 0 {
			remaining = 0
		}
		if current != "" {
			// current is already generated through the canonical de-DE key in the
			// progress parser and represents not-yet-finalized groups.
			statusLine = current
		} else if remaining > 0 {
			statusLine = trn("gate.progress.parallel", remaining)
		} else {
			statusLine = trn("gate.progress.parallel", 0)
		}
	} else if !last.IsZero() {
		statusLine = trf("measurement.last_at", "time", last.Format("02.01.2006 15:04:05"))
	}
	text(hdc, a.fontSmall, statusLine, rect{946, 190, int32(right - 8), 221}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	// Golden four-column gate table.
	tableR := rect{contentX, tableTop, int32(right), int32(tableTop + tableHeaderH + gateCount*gateRowH)}
	roundBox(hdc, tableR, 6, colors.bg, colors.border, 1)
	fill(hdc, rect{tableR.Left + 1, tableR.Top + 1, tableR.Right - 1, tableR.Top + tableHeaderH}, colors.surface)
	text(hdc, a.fontTiny, tr("table.number"), rect{130, tableTop, 160, tableTop + tableHeaderH}, colors.text2, dtCenter|dtVCenter|dtSingleLine)
	text(hdc, a.fontTiny, tr("table.component"), rect{181, tableTop, 630, tableTop + tableHeaderH}, colors.text2, dtLeft|dtVCenter|dtSingleLine)
	text(hdc, a.fontTiny, tr("table.status"), rect{651, tableTop, 810, tableTop + tableHeaderH}, colors.text2, dtLeft|dtVCenter|dtSingleLine)
	text(hdc, a.fontTiny, tr("table.details"), rect{842, tableTop, int32(right - 10), tableTop + tableHeaderH}, colors.text2, dtLeft|dtVCenter|dtSingleLine)

	for i := 0; i < gateCount; i++ {
		y := tableTop + tableHeaderH + i*gateRowH
		row := rect{contentX + 1, int32(y), int32(right - 1), int32(y + gateRowH)}
		selected := detail == i
		if selected {
			fill(hdc, row, colors.selected)
			fill(hdc, rect{row.Left, row.Top, row.Left + 3, row.Bottom}, stateColor(states[i]))
		} else if hover == i {
			fill(hdc, row, colors.hover)
		}
		if i > 0 {
			line(hdc, contentX+1, y, right-1, y, 1, colors.border)
		}
		text(hdc, a.fontSmall, fmt.Sprintf("%d", i+1), rect{123, int32(y), 145, int32(y + gateRowH)}, colors.text2, dtCenter|dtVCenter|dtSingleLine)
		v := variantIndex(states[i])
		drawIcon(hdc, a.componentIcons[i][v], 182, y+5, 20, 20)
		text(hdc, a.fontBody, gateName(i), rect{216, int32(y), 635, int32(y + gateRowH)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		drawStatusBadge(hdc, a, states[i], rect{651, int32(y + 5), 801, int32(y + 27)})
		detailText, detailColor := gateRowDetail(states[i], gateDetail(i))
		if finding, ok := problemFindingForGate(findings, i); ok {
			if finding.Classification == problemClassKnown && repairAvailableForGateFindings(findings, i) {
				detailText = tr("problem.gate.repair_available")
				detailColor = colors.failure
			} else if finding.Classification == problemClassUnclassified {
				detailText = tr("problem.gate.unclassified")
				detailColor = colors.warning
			}
		}
		text(hdc, a.fontSmall, detailText, rect{842, int32(y), int32(right - 8), int32(y + gateRowH)}, detailColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	}

	primary := rect{109, actionTop, 389, actionBottom}
	secondary := rect{406, actionTop, 664, actionBottom}
	drawActionCard(hdc, a, primary, 0, "▶", func() string {
		if checking {
			return tr("action.check_running")
		}
		return tr("action.start_check")
	}(), tr("action.start_check.sub"), hoverAction == 0, !checking && !repairing)
	drawActionCard(hdc, a, secondary, 1, "⇧", func() string {
		if exporting {
			return tr("action.export_running")
		}
		return tr("action.export")
	}(), tr("action.export.sub"), hoverAction == 1, !exporting && !repairing)

	if detail >= 0 && detail < gateCount {
		a.drawGateDetailPopover(hdc, detail, states[detail], ins[detail], true, true)
	}
}

func doneForOverall(checking bool, overall string, done int) int {
	if checking {
		return done
	}
	if overall == overallHealthy || overall == overallIncomplete || overall == overallFailed {
		return gateCount
	}
	return 0
}

func overallSummary(overall string, checking bool, states [gateCount]string) string {
	if checking {
		return tr("overall.checking.detail")
	}
	if overall == overallUnchecked {
		return tr("overall.unchecked.detail")
	}
	if overall == overallFailed {
		return tr("overall.failed.detail")
	}
	if overall == overallIncomplete {
		return tr("overall.incomplete.detail")
	}
	unclear, hints := 0, 0
	for _, state := range states {
		switch strings.ToUpper(strings.TrimSpace(state)) {
		case "UNKNOWN", "UNKLAR":
			unclear++
		case "WARN", "HINWEIS":
			hints++
		}
	}
	if unclear == 0 && hints == 0 {
		return tr("overall.summary.clean")
	}
	parts := make([]string, 0, 2)
	if unclear > 0 {
		parts = append(parts, trn("status.finding.unclear", unclear))
	}
	if hints > 0 {
		parts = append(parts, trn("status.finding.hint", hints))
	}
	findings := ""
	if len(parts) == 2 {
		findings = trf("status.finding.join", "unclear", parts[0], "hints", parts[1])
	} else if len(parts) == 1 {
		findings = parts[0]
	}
	return trf("overall.summary.with_findings", "findings", findings)
}

func gateRowDetail(state, normal string) (string, uintptr) {
	switch strings.ToUpper(strings.TrimSpace(state)) {
	case "UNCHECKED", "WAITING", "NICHT GEPRÜFT", "WARTET":
		return tr("gate.row.unchecked"), colors.text2
	case "CHECKING", "PRÜFUNG", "PRÜFUNG …":
		return tr("gate.row.checking"), colors.warning
	case "WARN", "HINWEIS":
		return tr("gate.row.hint"), colors.warning
	case "UNKNOWN", "UNKLAR":
		return tr("gate.row.unclear"), colors.unclear
	case "FAIL", "FEHLER", "FAILED":
		return tr("gate.row.failed"), colors.failure
	default:
		return normal, colors.text2
	}
}

func statusBadgeText(state string) string {
	n := strings.ToUpper(strings.TrimSpace(state))
	switch n {
	case measurementHealthy, "GESUND":
		return tr("measurement.result.healthy")
	case measurementHint:
		return tr("measurement.result.hint")
	case measurementUnclear:
		return tr("measurement.result.unclear")
	case overallUnchecked:
		return tr("gate.lifecycle.unchecked")
	case overallChecking:
		return tr("gate.lifecycle.checking")
	default:
		return gateStatusText(state)
	}
}

func drawStatusBadge(hdc uintptr, a *App, state string, r rect) {
	label := statusBadgeText(state)
	col := stateColor(state)
	symbol := "○"
	n := strings.ToUpper(strings.TrimSpace(state))
	if n == gatePassed || n == measurementHealthy || n == overallHealthy || n == "BESTANDEN" || n == "GESUND" {
		symbol = "✓"
	} else if n == gateFailed || n == measurementFailed || n == overallFailed || n == "FEHLER" {
		symbol = "!"
	}
	roundBox(hdc, r, 7, colors.bg, col, 1)
	text(hdc, a.fontSmall, symbol, rect{r.Left + 8, r.Top, r.Left + 26, r.Bottom}, col, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, label, rect{r.Left + 28, r.Top, r.Right - 6, r.Bottom}, col, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
}

func drawActionCard(hdc uintptr, a *App, r rect, idx int, glyph, title, subtitle string, hover, enabled bool) {
	fc := colors.surface
	bc := colors.borderStrong
	borderW := 1
	if hover && enabled {
		fc = colors.actionHover
		bc = colors.green
		borderW = 2
	}
	if !enabled {
		fc = colors.bg
	}
	roundBox(hdc, r, 5, fc, bc, borderW)
	col := colors.text
	sub := colors.muted
	glyphCol := colors.text2
	if hover && enabled {
		glyphCol = colors.green
		sub = colors.text2
	}
	if !enabled {
		col = colors.muted
		glyphCol = colors.muted
	}
	iconR := rect{r.Left + 12, r.Top + 13, r.Left + 47, r.Bottom - 12}
	switch idx {
	case 1, 2:
		drawExportPackageIcon(hdc, iconR, glyphCol)
	case 3:
		// Vectorized from the approved generated folder/open-arrow concept so it
		// stays crisp at every DPI instead of depending on a raster glyph.
		drawOpenFolderIcon(hdc, iconR, glyphCol)
	default:
		text(hdc, a.fontActionIcon, glyph, rect{r.Left + 10, r.Top + 2, r.Left + 52, r.Bottom - 2}, glyphCol, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	}
	text(hdc, a.fontAction, title, rect{r.Left + 55, r.Top + 7, r.Right - 8, r.Top + 34}, col, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, subtitle, rect{r.Left + 55, r.Top + 32, r.Right - 8, r.Bottom - 4}, sub, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	_ = idx
}

func drawExportPackageIcon(hdc uintptr, r rect, color uintptr) {
	// Crisp tray + upward arrow. Shared by Diagnose exportieren and
	// Diagnosepaket erstellen, matching the product's intended semantics.
	xc := int((r.Left + r.Right) / 2)
	top := int(r.Top) + 1
	bottom := int(r.Bottom) - 1
	left := int(r.Left) + 3
	right := int(r.Right) - 3
	line(hdc, left, bottom-7, left, bottom, 2, color)
	line(hdc, left, bottom, right, bottom, 2, color)
	line(hdc, right, bottom, right, bottom-7, 2, color)
	line(hdc, xc, top+2, xc, bottom-9, 2, color)
	line(hdc, xc, top+2, xc-6, top+8, 2, color)
	line(hdc, xc, top+2, xc+6, top+8, 2, color)
}

func drawOpenFolderIcon(hdc uintptr, r rect, color uintptr) {
	// Folder + north-east/open arrow, based on the user-approved generated
	// symbol but rendered as GDI vectors for high-DPI clarity.
	left := int(r.Left) + 1
	top := int(r.Top) + 5
	right := int(r.Right) - 2
	bottom := int(r.Bottom) - 2
	// folder outline with tab
	line(hdc, left, top+5, left+8, top+5, 2, color)
	line(hdc, left+8, top+5, left+12, top+1, 2, color)
	line(hdc, left+12, top+1, left+20, top+1, 2, color)
	line(hdc, left+20, top+1, left+24, top+5, 2, color)
	line(hdc, left+24, top+5, right-2, top+5, 2, color)
	line(hdc, left, top+5, left, bottom, 2, color)
	line(hdc, left, bottom, right-7, bottom, 2, color)
	// external/open arrow
	ax := right - 13
	ay := top + 12
	line(hdc, ax, bottom-5, right, ay, 2, color)
	line(hdc, right, ay, right-9, ay, 2, color)
	line(hdc, right, ay, right, ay+9, 2, color)
}

func structuredFindingLines(c EngineCheck) []string {
	status := strings.ToUpper(strings.TrimSpace(c.Status))
	severe := status == "FAIL" || status == "UNKNOWN"
	if !severe {
		return []string{fallbackText(c.Actual, "—")}
	}
	lines := []string{trf("popover.finding.actual", "value", fallbackText(c.Actual, "—"))}
	if strings.TrimSpace(c.Expected) != "" {
		lines = append(lines, trf("popover.finding.expected", "value", c.Expected))
	}
	if strings.TrimSpace(c.Detail) != "" {
		lines = append(lines, trf("popover.finding.detail", "value", c.Detail))
	}
	if strings.TrimSpace(c.Section) != "" {
		lines = append(lines, trf("popover.finding.section", "value", c.Section))
	}
	return lines
}

func (a *App) drawGateDetailPopover(hdc uintptr, idx int, state string, inspection GateInspection, allowRepair, livePresentation bool) {
	a.mu.Lock()
	scroll := a.detailScroll
	raw := a.detailRawExpanded
	hoverDetail := a.hoverDetailButton
	hoverClose := a.hoverDetailClose
	a.mu.Unlock()

	p := rect{634, 291, 1149, 699}
	roundBox(hdc, p, 5, colors.surface2, colors.borderStrong, 1)
	col := stateColor(state)
	fill(hdc, rect{p.Left, p.Top + 1, p.Left + 4, p.Bottom - 1}, col)

	text(hdc, a.fontTiny, tr("popover.title"), rect{660, 305, 790, 326}, col, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBodySemi, gateName(idx), rect{660, 330, 940, 353}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	drawStatusBadge(hdc, a, state, rect{958, 324, 1108, 346})
	closeColor := colors.text2
	if hoverClose {
		closeColor = colors.green
	}
	// RC2: Golden-like larger close glyph, moved further into the top-right corner.
	text(hdc, a.fontDetailClose, "×", rect{1118, 286, 1149, 328}, closeColor, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	line(hdc, 660, 361, 1123, 361, 1, colors.borderStrong)

	checks := inspection.Checks
	if !raw && idx == 3 && livePresentation {
		a.mu.Lock()
		inv := a.inventory
		liveFresh := a.setupLiveFresh
		a.mu.Unlock()
		checks = gateDevicePresentationChecks(inv, liveFresh, checks)
	}
	const contentTop = 371
	const contentBottom = 646
	const contentLeft = 660
	const textLeft = 678
	const textRight = 1118
	const scrollbarTop = contentTop
	const scrollbarBottom = contentBottom
	viewportH := contentBottom - contentTop

	totalH := 0
	if raw {
		// Raw mode uses the full middle viewport and variable wrapped blocks.
		if !inspection.Available || len(checks) == 0 {
			msg := tr("popover.raw.none")
			totalH = measureWrappedTextHeight(hdc, a.fontSmall, msg, textRight-contentLeft) + 8
		} else {
			const blockGap = 12
			width := textRight - textLeft
			for _, c := range checks {
				expectedLine := trf("popover.raw.expected", "value", fallbackText(c.Expected, "—"))
				if strings.EqualFold(strings.TrimSpace(c.Status), "INFO") {
					expectedLine = tr("popover.raw.info_expected")
				}
				lines := [4]string{
					wrapTextToWidth(hdc, a.fontTiny, fallbackText(c.Actual, "—"), width),
					wrapTextToWidth(hdc, a.fontTiny, expectedLine, width),
					wrapTextToWidth(hdc, a.fontTiny, trf("popover.raw.detail", "value", fallbackText(c.Detail, "—")), width),
					wrapTextToWidth(hdc, a.fontTiny, trf("popover.raw.section", "value", fallbackText(c.Section, "—")), width),
				}
				blockH := 22
				for _, ln := range lines {
					blockH += measureWrappedTextHeight(hdc, a.fontTiny, ln, width) + 2
				}
				blockH += blockGap
				totalH += blockH
			}
		}
	} else {
		// RC2: the whole middle content (summary + assessment + findings) is one
		// continuous pixel-scroll document. Header and footer controls stay fixed.
		summary, assessment := gateDetailText(idx, state, inspection)
		bodyWidth := textRight - contentLeft
		summaryWrapped := wrapTextToWidth(hdc, a.fontSmall, summary, bodyWidth)
		assessmentWrapped := wrapTextToWidth(hdc, a.fontTiny, assessment, bodyWidth)
		summaryH := measureWrappedTextHeight(hdc, a.fontSmall, summaryWrapped, bodyWidth)
		assessmentH := measureWrappedTextHeight(hdc, a.fontTiny, assessmentWrapped, bodyWidth)
		totalH = 19 + 4 + summaryH + 10 + 19 + 3 + assessmentH + 10 + 1 + 8 + 19 + 5
		if !inspection.Available || len(checks) == 0 {
			msg := tr("popover.result.none")
			if inspection.Available {
				msg = tr("popover.result.no_structured")
			}
			totalH += measureWrappedTextHeight(hdc, a.fontSmall, msg, bodyWidth) + 8
		} else {
			for _, c := range checks {
				blockH := 20
				for _, findingLine := range structuredFindingLines(c) {
					wrapped := wrapTextToWidth(hdc, a.fontTiny, findingLine, textRight-textLeft)
					blockH += measureWrappedTextHeight(hdc, a.fontTiny, wrapped, textRight-textLeft) + 2
				}
				if strings.EqualFold(strings.TrimSpace(c.Status), "INFO") {
					blockH += 20
				}
				totalH += blockH + 10
			}
		}
	}

	// Reserve enough scrollable space below the last content line so the fixed
	// footer buttons can never visually crowd or cover the final finding. This
	// reserve is part of the scroll document in both normal and raw modes.
	const detailBottomScrollReserve = 52
	totalH += detailBottomScrollReserve

	maxScroll := totalH - viewportH
	if maxScroll < 0 {
		maxScroll = 0
	}
	if scroll > maxScroll {
		scroll = maxScroll
	}
	if scroll < 0 {
		scroll = 0
	}

	thumbTop, thumbBottom := detailScrollbarGeometry(totalH, viewportH, scroll, maxScroll, scrollbarTop, scrollbarBottom)
	a.mu.Lock()
	if a.detailGate == idx {
		a.detailScroll = scroll
		a.detailScrollMax = maxScroll
		a.detailScrollTrackTop = scrollbarTop
		a.detailScrollTrackBottom = scrollbarBottom
		a.detailScrollThumbTop = thumbTop
		a.detailScrollThumbBottom = thumbBottom
	}
	a.mu.Unlock()

	saved, _, _ := procSaveDC.Call(hdc)
	procIntersectClipRect.Call(hdc, 658, uintptr(contentTop), 1124, uintptr(contentBottom))
	y := contentTop - scroll

	if raw {
		if !inspection.Available || len(checks) == 0 {
			msg := tr("popover.raw.none")
			text(hdc, a.fontSmall, msg, rect{contentLeft, int32(y), textRight, int32(y + totalH)}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
		} else {
			const blockGap = 12
			width := textRight - textLeft
			for _, c := range checks {
				expectedLine := trf("popover.raw.expected", "value", fallbackText(c.Expected, "—"))
				if strings.EqualFold(strings.TrimSpace(c.Status), "INFO") {
					expectedLine = tr("popover.raw.info_expected")
				}
				lines := [4]string{
					wrapTextToWidth(hdc, a.fontTiny, fallbackText(c.Actual, "—"), width),
					wrapTextToWidth(hdc, a.fontTiny, expectedLine, width),
					wrapTextToWidth(hdc, a.fontTiny, trf("popover.raw.detail", "value", fallbackText(c.Detail, "—")), width),
					wrapTextToWidth(hdc, a.fontTiny, trf("popover.raw.section", "value", fallbackText(c.Section, "—")), width),
				}
				lineHeights := [4]int{}
				blockH := 22
				for i, ln := range lines {
					lineHeights[i] = measureWrappedTextHeight(hdc, a.fontTiny, ln, width)
					blockH += lineHeights[i] + 2
				}
				blockH += blockGap
				if y+blockH >= contentTop && y < contentBottom {
					label := findingLabel(c.Status)
					fc := stateColor(severityToDisplay(c.Status))
					symbol := "◆"
					if strings.EqualFold(strings.TrimSpace(c.Status), "INFO") {
						symbol = "ⓘ"
					}
					text(hdc, a.fontTiny, symbol+"  "+label+"  "+c.Check, rect{contentLeft, int32(y), textRight, int32(y + 20)}, fc, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
					ly := y + 22
					for i, ln := range lines {
						h := lineHeights[i]
						text(hdc, a.fontTiny, ln, rect{textLeft, int32(ly), textRight, int32(ly + h)}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
						ly += h + 2
					}
				}
				y += blockH
			}
		}
	} else {
		summary, assessment := gateDetailText(idx, state, inspection)
		bodyWidth := textRight - contentLeft
		summaryWrapped := wrapTextToWidth(hdc, a.fontSmall, summary, bodyWidth)
		assessmentWrapped := wrapTextToWidth(hdc, a.fontTiny, assessment, bodyWidth)
		summaryH := measureWrappedTextHeight(hdc, a.fontSmall, summaryWrapped, bodyWidth)
		assessmentH := measureWrappedTextHeight(hdc, a.fontTiny, assessmentWrapped, bodyWidth)

		text(hdc, a.fontTiny, tr("popover.summary"), rect{contentLeft, int32(y), 850, int32(y + 19)}, colors.muted, dtLeft|dtVCenter|dtSingleLine)
		y += 23
		text(hdc, a.fontSmall, summaryWrapped, rect{contentLeft, int32(y), textRight, int32(y + summaryH)}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
		y += summaryH + 10
		text(hdc, a.fontTiny, tr("popover.rating"), rect{contentLeft, int32(y), 850, int32(y + 19)}, colors.muted, dtLeft|dtVCenter|dtSingleLine)
		y += 22
		text(hdc, a.fontTiny, assessmentWrapped, rect{contentLeft, int32(y), textRight, int32(y + assessmentH)}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
		y += assessmentH + 10
		line(hdc, contentLeft, y, 1123, y, 1, colors.borderStrong)
		y += 9
		text(hdc, a.fontTiny, tr("popover.findings"), rect{contentLeft, int32(y), 850, int32(y + 19)}, colors.muted, dtLeft|dtVCenter|dtSingleLine)
		y += 24

		if !inspection.Available || len(checks) == 0 {
			msg := tr("popover.result.none")
			if inspection.Available {
				msg = tr("popover.result.no_structured")
			}
			h := measureWrappedTextHeight(hdc, a.fontSmall, msg, bodyWidth)
			text(hdc, a.fontSmall, msg, rect{contentLeft, int32(y), textRight, int32(y + h)}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
		} else {
			for _, c := range checks {
				findingLines := structuredFindingLines(c)
				wrappedLines := make([]string, 0, len(findingLines))
				lineHeights := make([]int, 0, len(findingLines))
				blockH := 20
				for _, findingLine := range findingLines {
					wrapped := wrapTextToWidth(hdc, a.fontTiny, findingLine, textRight-textLeft)
					wrappedLines = append(wrappedLines, wrapped)
					h := measureWrappedTextHeight(hdc, a.fontTiny, wrapped, textRight-textLeft)
					lineHeights = append(lineHeights, h)
					blockH += h + 2
				}
				isInfo := strings.EqualFold(strings.TrimSpace(c.Status), "INFO")
				if isInfo {
					blockH += 20
				}
				blockH += 10
				if y+blockH >= contentTop && y < contentBottom {
					label := findingLabel(c.Status)
					fc := stateColor(severityToDisplay(c.Status))
					symbol := "◆"
					if isInfo {
						symbol = "ⓘ"
					}
					text(hdc, a.fontTiny, symbol+"  "+label+"  "+c.Check, rect{contentLeft, int32(y), textRight, int32(y + 19)}, fc, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
					ly := y + 20
					for i, wrapped := range wrappedLines {
						h := lineHeights[i]
						text(hdc, a.fontTiny, wrapped, rect{textLeft, int32(ly), textRight, int32(ly + h)}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
						ly += h + 2
					}
					if isInfo {
						text(hdc, a.fontTiny, tr("popover.info.classification"), rect{textLeft, int32(ly), textRight, int32(ly + 18)}, colors.info, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
					}
				}
				y += blockH
			}
		}
	}

	if saved != 0 {
		procRestoreDC.Call(hdc, saved)
	}
	if maxScroll > 0 {
		drawDetailPixelScrollbar(hdc, totalH, viewportH, scroll, maxScroll, scrollbarTop, scrollbarBottom)
	}

	rawLabel := tr("action.raw_details")
	if raw {
		rawLabel = tr("action.raw_details.hide")
	}
	repairable := false
	if allowRepair {
		a.mu.Lock()
		repairable = repairAvailableForGateFindings(a.problemFindings, idx)
		a.mu.Unlock()
	}
	if repairable {
		repairBtn := rect{660, 659, 806, 687}
		rawBtn := rect{815, 659, 966, 687}
		copyBtn := rect{975, 659, 1122, 687}
		drawDetailButton(hdc, a, repairBtn, tr("action.repair"), hoverDetail == 2)
		drawDetailButton(hdc, a, rawBtn, rawLabel, hoverDetail == 0)
		drawDetailButton(hdc, a, copyBtn, tr("action.copy"), hoverDetail == 1)
	} else {
		rawBtn := rect{660, 659, 870, 687}
		copyBtn := rect{882, 659, 1122, 687}
		drawDetailButton(hdc, a, rawBtn, rawLabel, hoverDetail == 0)
		drawDetailButton(hdc, a, copyBtn, tr("action.copy"), hoverDetail == 1)
	}
}
func fallbackText(v, fallback string) string {
	if strings.TrimSpace(v) == "" {
		return fallback
	}
	return v
}

func minInt(a, b int) int {
	if a < b {
		return a
	}
	return b
}

func drawDetailScrollbar(hdc uintptr, count, visible, scroll, maxScroll, top, bottom int) {
	if count <= visible || bottom <= top {
		return
	}
	fill(hdc, rect{1131, int32(top), 1135, int32(bottom)}, colors.border)
	thumbH := (bottom - top) * visible / count
	if thumbH < 24 {
		thumbH = 24
	}
	if thumbH > bottom-top {
		thumbH = bottom - top
	}
	pos := 0
	if maxScroll > 0 {
		pos = (bottom - top - thumbH) * scroll / maxScroll
	}
	roundBox(hdc, rect{1130, int32(top + pos), 1136, int32(top + pos + thumbH)}, 4, colors.green, colors.green, 1)
}

func detailScrollbarGeometry(totalH, viewportH, scroll, maxScroll, top, bottom int) (int, int) {
	if bottom <= top {
		return top, top
	}
	trackH := bottom - top
	if totalH <= viewportH || totalH <= 0 || maxScroll <= 0 {
		return top, bottom
	}
	thumbH := trackH * viewportH / totalH
	if thumbH < 24 {
		thumbH = 24
	}
	if thumbH > trackH {
		thumbH = trackH
	}
	travel := trackH - thumbH
	pos := 0
	if travel > 0 {
		pos = travel * scroll / maxScroll
	}
	return top + pos, top + pos + thumbH
}

func drawDetailPixelScrollbar(hdc uintptr, totalH, viewportH, scroll, maxScroll, top, bottom int) {
	if totalH <= viewportH || bottom <= top || maxScroll <= 0 {
		return
	}
	fill(hdc, rect{1131, int32(top), 1135, int32(bottom)}, colors.border)
	thumbTop, thumbBottom := detailScrollbarGeometry(totalH, viewportH, scroll, maxScroll, top, bottom)
	roundBox(hdc, rect{1130, int32(thumbTop), 1136, int32(thumbBottom)}, 4, colors.green, colors.green, 1)
}

func drawDetailButton(hdc uintptr, a *App, r rect, label string, hover bool) {
	fc := colors.surface
	bc := colors.borderStrong
	tc := colors.text2
	if hover {
		fc = colors.buttonHover
		bc = colors.green
		tc = colors.green
	}
	roundBox(hdc, r, 5, fc, bc, 1)
	text(hdc, a.fontSmall, label, r, tc, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
}

func gateCheckPID(check string) string {
	upper := strings.ToUpper(strings.TrimSpace(check))
	pos := strings.Index(upper, "PID ")
	if pos < 0 {
		return ""
	}
	rest := strings.TrimSpace(upper[pos+4:])
	if len(rest) < 4 {
		return ""
	}
	pid := rest[:4]
	if !validInventoryPID(pid) {
		return ""
	}
	return pid
}

func gateConnectionModeNoun(c DeviceConnectionProfile) string {
	switch strings.ToLower(strings.TrimSpace(c.ConnectionType)) {
	case "wired-usb":
		return tr("gate.devices.connection.role.wired")
	case "wireless-dongle":
		return tr("gate.devices.connection.role.wireless")
	default:
		return tr("gate.devices.connection.role.generic")
	}
}

func gateDevicePresentationChecks(inv DeviceInventory, liveFresh bool, checks []EngineCheck) []EngineCheck {
	if !liveFresh || len(checks) == 0 {
		return checks
	}
	byPID := make(map[string]DeviceConnectionProfile, len(inv.Connections))
	productName := make(map[string]string, len(inv.Products))
	activeByProduct := make(map[string][]DeviceConnectionProfile)
	for _, p := range inv.Products {
		productName[strings.TrimSpace(p.Key)] = strings.TrimSpace(p.Name)
	}
	for _, c := range inv.Connections {
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		if validInventoryPID(pid) {
			byPID[pid] = c
		}
		if c.PresentAtScan && strings.TrimSpace(c.ProductKey) != "" {
			activeByProduct[strings.TrimSpace(c.ProductKey)] = append(activeByProduct[strings.TrimSpace(c.ProductKey)], c)
		}
	}
	for key := range activeByProduct {
		sort.Slice(activeByProduct[key], func(i, j int) bool {
			return strings.ToUpper(activeByProduct[key][i].PID) < strings.ToUpper(activeByProduct[key][j].PID)
		})
	}
	out := append([]EngineCheck(nil), checks...)
	for i := range out {
		c := &out[i]
		if !strings.Contains(strings.ToLower(c.Check), "physical nodes") {
			continue
		}
		pid := gateCheckPID(c.Check)
		conn, ok := byPID[pid]
		if !ok || strings.TrimSpace(conn.ProductKey) == "" {
			continue
		}
		name := productName[strings.TrimSpace(conn.ProductKey)]
		if name == "" {
			name = strings.TrimSpace(conn.ModelName)
		}
		if name == "" {
			continue
		}
		modeNoun := gateConnectionModeNoun(conn)
		role := setupConnectionRoleLabel(conn)
		if role == "" {
			role = modeNoun
		}
		if conn.PresentAtScan {
			c.Check = trf("gate.devices.connection.active", "connection", modeNoun, "product", name)
			c.Actual = trf("gate.devices.connection.active.detail", "role", role, "pid", pid)
			continue
		}
		var alternative *DeviceConnectionProfile
		for _, candidate := range activeByProduct[strings.TrimSpace(conn.ProductKey)] {
			candidatePID := strings.ToUpper(strings.TrimSpace(candidate.PID))
			if candidatePID != pid {
				copyCandidate := candidate
				alternative = &copyCandidate
				break
			}
		}
		if alternative == nil {
			continue
		}
		activePID := strings.ToUpper(strings.TrimSpace(alternative.PID))
		activeRole := setupConnectionRoleLabel(*alternative)
		if activeRole == "" {
			activeRole = gateConnectionModeNoun(*alternative)
		}
		c.Check = trf("gate.devices.connection.inactive", "connection", modeNoun, "product", name)
		c.Actual = trf("gate.devices.connection.inactive.alternative", "activeRole", activeRole, "activePid", activePID, "inactiveConnection", modeNoun)
	}
	return out
}

func gateDetailText(idx int, state string, inspection GateInspection) (string, string) {
	if idx == 0 {
		if strings.EqualFold(state, gateHint) || strings.EqualFold(state, "HINWEIS") {
			return tr("gate.appengine.summary.hint"), tr("gate.appengine.assessment")
		}
		return tr("gate.appengine.summary.default"), tr("gate.appengine.assessment")
	}
	if idx == 1 {
		return tr("gate.driverstore.summary"), tr("gate.driverstore.assessment")
	}
	if idx == 11 && (strings.EqualFold(state, gateUnclear) || strings.EqualFold(state, "UNKLAR")) {
		return tr("gate.power.summary.unclear"), tr("gate.power.assessment.unclear")
	}
	summary := tr(strings.Replace(gateNameKeys[idx], ".name", ".summary", 1))
	// Presentation assessment text is owned by de-DE. Engine GateDetail remains
	// available as technical evidence in raw/copy diagnostics, but is not the
	// source of UI prose.
	assessment := gateDetail(idx)
	return summary, assessment
}

func findingLabel(status string) string {
	return findingStatusText(status)
}

func logPrimaryTabRect() rect      { return rect{contentX, pageTitleTop, 232, pageUnderline + 3} }
func logHistoricalTabRect() rect   { return rect{246, pageTitleTop, 492, pageUnderline + 3} }
func logHistoricalCloseRect() rect { return rect{455, pageTitleTop + 1, 490, pageUnderline} }
func logDetailsButtonRect() rect   { return rect{930, 602, 1138, 642} }

func drawCompactLogButton(hdc uintptr, a *App, r rect, label string, hover, enabled bool) {
	fc := colors.bg
	bc := colors.borderStrong
	tc := colors.text2
	if !enabled {
		tc = colors.muted
		bc = colors.border
	} else if hover {
		fc = colors.buttonHover
		bc = colors.green
		tc = colors.green
	}
	roundBox(hdc, r, 5, fc, bc, 1)
	text(hdc, a.fontSmall, label, r, tc, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
}

func (a *App) drawLogsTabs(hdc uintptr, historical *HistoricalMeasurement, activeHistorical bool) {
	a.mu.Lock()
	hoverTab := a.hoverLogTab
	hoverClose := a.hoverLogClose
	a.mu.Unlock()
	primary := logPrimaryTabRect()
	primaryColor := colors.text2
	if !activeHistorical || historical == nil {
		primaryColor = colors.green
	} else if hoverTab == 0 {
		primaryColor = colors.green
	}
	text(hdc, a.fontBodySemi, tr("page.logs.title"), rect{119, pageTitleTop, primary.Right - 8, pageTitleTop + 27}, primaryColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	if !activeHistorical || historical == nil {
		fill(hdc, rect{primary.Left, pageUnderline, primary.Right, pageUnderline + 3}, colors.green)
	}
	if historical == nil {
		return
	}
	hist := logHistoricalTabRect()
	historicalTabColor := colors.info
	if hoverTab == 1 && !activeHistorical {
		fill(hdc, rect{hist.Left, hist.Top, hist.Right, hist.Bottom}, colors.hover)
	}
	text(hdc, a.fontBodySemi, historical.StartedAt.Format("02.01.2006 15:04:05"), rect{hist.Left + 9, pageTitleTop, hist.Right - 38, pageTitleTop + 27}, historicalTabColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	closeColor := colors.text2
	if hoverClose {
		closeColor = historicalTabColor
	}
	text(hdc, a.fontBodySemi, "×", logHistoricalCloseRect(), closeColor, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	if activeHistorical {
		fill(hdc, rect{hist.Left, pageUnderline, hist.Right, pageUnderline + 3}, historicalTabColor)
	}
}

func historicalSummary(m HistoricalMeasurement) string {
	return overallSummary(m.Overall, false, m.GateStates)
}

func (a *App) drawHistoricalMeasurementView(hdc uintptr, w, h int, m HistoricalMeasurement) {
	a.drawLogsTabs(hdc, &m, true)
	a.mu.Lock()
	detail := a.detailGate
	hover := a.hoverGate
	exporting := a.exporting
	repairing := a.repairing
	hoverAction := a.hoverAction
	a.mu.Unlock()

	right := w - 18
	box := rect{contentX, statusTop, int32(right), statusBottom}
	archiveModeColor := colors.info
	// archiveSurface is the visual equivalent of roughly 4% translucent cyan
	// over the normal status surface. Pre-blending preserves the rounded card
	// edges reliably with native GDI while keeping the tint intentionally quiet.
	roundBox(hdc, box, 8, colors.archiveSurface, colors.border, 1)

	// Historical mode is visually separated from LIVE without changing the
	// recorded health result itself. Cyan identifies only the archive context;
	// green/yellow/red remain reserved for the stored measurement. The timestamp
	// already lives in the historical tab, so the summary card avoids repeating it.

	icon := a.iconStatusReady
	if normalizeMeasurementStatus(m.Overall) == measurementHealthy {
		icon = a.iconStatusPass
	} else if normalizeMeasurementStatus(m.Overall) == measurementFailed {
		icon = a.iconStatusFail
	}
	drawIcon(hdc, icon, 130, 138, 82, 82)
	text(hdc, a.fontBodySemi, tr("logs.historical.system_label"), rect{240, 137, 560, 156}, archiveModeColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	overallLabel := measurementDisplayStatus(m.Overall)
	text(hdc, a.fontOverall, overallLabel, rect{239, 151, 690, 199}, stateColor(m.Overall), dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontSmall, historicalSummary(m), rect{240, 198, 690, 224}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	line(hdc, 701, 137, 701, 220, 1, colors.borderStrong)
	text(hdc, a.fontTiny, tr("logs.historical.duration"), rect{742, 137, 890, 156}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontRuntime, formatClock(m.Duration), rect{742, 151, 910, 199}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, tr("logs.historical.completed"), rect{946, 142, int32(right - 12), 161}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBodySemi, trf("logs.historical.gate_count", "done", gateCount, "total", gateCount), rect{946, 167, int32(right - 12), 193}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	tableR := rect{contentX, tableTop, int32(right), int32(tableTop + tableHeaderH + gateCount*gateRowH)}
	roundBox(hdc, tableR, 6, colors.bg, colors.border, 1)
	fill(hdc, rect{tableR.Left + 1, tableR.Top + 1, tableR.Right - 1, tableR.Top + tableHeaderH}, colors.surface)
	text(hdc, a.fontTiny, tr("table.number"), rect{130, tableTop, 160, tableTop + tableHeaderH}, colors.text2, dtCenter|dtVCenter|dtSingleLine)
	text(hdc, a.fontTiny, tr("table.component"), rect{181, tableTop, 630, tableTop + tableHeaderH}, colors.text2, dtLeft|dtVCenter|dtSingleLine)
	text(hdc, a.fontTiny, tr("table.status"), rect{651, tableTop, 810, tableTop + tableHeaderH}, colors.text2, dtLeft|dtVCenter|dtSingleLine)
	text(hdc, a.fontTiny, tr("table.details"), rect{842, tableTop, int32(right - 10), tableTop + tableHeaderH}, colors.text2, dtLeft|dtVCenter|dtSingleLine)

	for i := 0; i < gateCount; i++ {
		y := tableTop + tableHeaderH + i*gateRowH
		row := rect{contentX + 1, int32(y), int32(right - 1), int32(y + gateRowH)}
		if detail == i {
			fill(hdc, row, colors.selected)
			fill(hdc, rect{row.Left, row.Top, row.Left + 3, row.Bottom}, stateColor(m.GateStates[i]))
		} else if hover == i {
			fill(hdc, row, colors.hover)
		}
		if i > 0 {
			line(hdc, contentX+1, y, right-1, y, 1, colors.border)
		}
		text(hdc, a.fontSmall, fmt.Sprintf("%d", i+1), rect{123, int32(y), 145, int32(y + gateRowH)}, colors.text2, dtCenter|dtVCenter|dtSingleLine)
		v := variantIndex(m.GateStates[i])
		drawIcon(hdc, a.componentIcons[i][v], 182, y+5, 20, 20)
		text(hdc, a.fontBody, gateName(i), rect{216, int32(y), 635, int32(y + gateRowH)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		drawStatusBadge(hdc, a, m.GateStates[i], rect{651, int32(y + 5), 801, int32(y + 27)})
		detailText, detailColor := gateRowDetail(m.GateStates[i], gateDetail(i))
		text(hdc, a.fontSmall, detailText, rect{842, int32(y), int32(right - 8), int32(y + gateRowH)}, detailColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	}

	drawActionCard(hdc, a, rect{109, actionTop, 409, actionBottom}, 2, "⇧", func() string {
		if exporting {
			return tr("action.export_running")
		}
		return tr("action.create_package")
	}(), tr("action.create_package.sub.historical"), hoverAction == 2, !exporting && !repairing)
	drawActionCard(hdc, a, rect{426, actionTop, 705, actionBottom}, 3, "", tr("action.open_package_folder"), tr("action.open_package_folder.sub"), hoverAction == 3, true)

	if detail >= 0 && detail < gateCount {
		a.drawGateDetailPopover(hdc, detail, m.GateStates[detail], m.GateInspections[detail], false, false)
	}
}

func (a *App) drawLogsView(hdc uintptr, w, h int) {
	a.mu.Lock()
	histOpen := a.logHistoricalOpen
	histActive := a.logHistoricalActive
	histStamp := a.logHistoricalStamp
	a.mu.Unlock()
	var historical *HistoricalMeasurement
	if histOpen {
		a.mu.Lock()
		if idx := measurementIndexByStamp(a.logMeasurements, histStamp); idx >= 0 && a.logMeasurements[idx].DetailAvailable {
			m := a.logMeasurements[idx]
			historical = &m
		}
		a.mu.Unlock()
	}
	if historical != nil && histActive {
		a.drawHistoricalMeasurementView(hdc, w, h, *historical)
		return
	}
	a.drawLogsTabs(hdc, historical, false)
	a.mu.Lock()
	ms := append([]HistoricalMeasurement(nil), a.logMeasurements...)
	sel := a.logSelected
	scroll := a.logScroll
	hoverLog := a.hoverLogRow
	loading := a.logsLoading
	loadedAt := a.logsLastScan
	exporting := a.exporting
	repairing := a.repairing
	hoverAction := a.hoverAction
	a.mu.Unlock()

	if loading && len(ms) == 0 {
		text(hdc, a.fontBody, tr("logs.loading"), rect{contentX, 130, int32(w - 30), 170}, colors.muted, dtLeft|dtVCenter|dtSingleLine)
		return
	}
	if len(ms) == 0 {
		text(hdc, a.fontBody, tr("logs.empty"), rect{contentX, 130, int32(w - 30), 170}, colors.muted, dtLeft|dtVCenter|dtSingleLine)
		return
	}
	visible := 10
	maxScroll := len(ms) - visible
	if maxScroll < 0 {
		maxScroll = 0
	}
	if scroll > maxScroll {
		scroll = maxScroll
	}
	if scroll < 0 {
		scroll = 0
	}
	first, last := scroll+1, scroll+visible
	if last > len(ms) {
		last = len(ms)
	}
	text(hdc, a.fontTiny, trf("logs.range", "first", first, "last", last, "total", len(ms)), rect{820, pageTitleTop, int32(w - 40), pageTitleTop + 27}, colors.muted, dtRight|dtVCenter|dtSingleLine|dtNoPrefix)

	right := w - 18
	top := 120
	header := 36
	rowH := 35
	tableR := rect{contentX, int32(top), int32(right), int32(top + header + visible*rowH + 3)}
	roundBox(hdc, tableR, 5, colors.bg, colors.border, 1)
	fill(hdc, rect{tableR.Left + 1, tableR.Top + 1, tableR.Right - 1, tableR.Top + int32(header)}, colors.surface)
	cols := []int{131, 321, 501, 611, 710, 1035}
	headers := []string{tr("logs.column.time"), tr("logs.column.result"), tr("logs.column.duration"), tr("logs.column.app"), tr("logs.column.session"), tr("logs.column.files")}
	for i, t := range headers {
		r := rect{int32(cols[i]), int32(top), int32(func() int {
			if i+1 < len(cols) {
				return cols[i+1] - 8
			}
			return right - 8
		}()), int32(top + header)}
		flags := uint32(dtLeft | dtVCenter | dtSingleLine | dtNoPrefix)
		if i == 5 {
			flags = dtCenter | dtVCenter | dtSingleLine | dtNoPrefix
		}
		text(hdc, a.fontTiny, t, r, colors.text2, flags)
	}
	for vr := 0; vr < visible && scroll+vr < len(ms); vr++ {
		i := scroll + vr
		m := ms[i]
		y := top + header + vr*rowH
		row := rect{contentX + 1, int32(y), int32(right - 1), int32(y + rowH)}
		if i == sel {
			fill(hdc, row, colors.selected)
			fill(hdc, rect{row.Left, row.Top, row.Left + 3, row.Bottom}, stateColor(measurementDisplayStatus(m.Overall)))
		} else if i == hoverLog {
			fill(hdc, row, colors.hover)
		}
		if vr > 0 {
			line(hdc, contentX+1, y, right-1, y, 1, colors.border)
		}
		text(hdc, a.fontSmall, m.StartedAt.Format("02.01.2006 15:04:05"), rect{131, int32(y), 311, int32(y + rowH)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		result := measurementDisplayStatus(m.Overall)
		drawStatusBadge(hdc, a, result, rect{321, int32(y + 6), 475, int32(y + 28)})
		text(hdc, a.fontSmall, formatClock(m.Duration), rect{501, int32(y), 585, int32(y + rowH)}, colors.text2, dtLeft|dtVCenter|dtSingleLine)
		av := displayVersion(m.AppVersion)
		text(hdc, a.fontSmall, av, rect{611, int32(y), 690, int32(y + rowH)}, colors.text2, dtLeft|dtVCenter|dtSingleLine)
		session := m.AppSession
		if !m.SessionResolved || session == "" {
			session = "—"
		}
		text(hdc, a.fontTiny, session, rect{710, int32(y), 1025, int32(y + rowH)}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontSmall, fmt.Sprintf("%d", len(m.Files)), rect{1035, int32(y), 1122, int32(y + rowH)}, colors.text2, dtCenter|dtVCenter|dtSingleLine)
	}
	if len(ms) > visible {
		trackTop := top + header + 5
		trackBottom := top + header + visible*rowH - 5
		fill(hdc, rect{1149, int32(trackTop), 1154, int32(trackBottom)}, colors.border)
		thumbH := (trackBottom - trackTop) * visible / len(ms)
		if thumbH < 35 {
			thumbH = 35
		}
		pos := 0
		if maxScroll > 0 {
			pos = (trackBottom - trackTop - thumbH) * scroll / maxScroll
		}
		roundBox(hdc, rect{1148, int32(trackTop + pos), 1155, int32(trackTop + pos + thumbH)}, 4, colors.green, colors.green, 1)
	}

	if sel >= 0 && sel < len(ms) {
		m := ms[sel]
		p := rect{contentX, 526, int32(right), 676}
		roundBox(hdc, p, 5, colors.surface, colors.border, 1)
		text(hdc, a.fontTiny, tr("logs.selected"), rect{131, 538, 360, 558}, colors.green, dtLeft|dtVCenter|dtSingleLine)
		if !loadedAt.IsZero() {
			text(hdc, a.fontTiny, trf("logs.read_at", "time", loadedAt.Format("15:04:05")), rect{930, 538, int32(right - 30), 558}, colors.muted, dtRight|dtVCenter|dtSingleLine)
		}
		text(hdc, a.fontH1, m.StartedAt.Format("02.01.2006 15:04:05"), rect{131, 562, 395, 588}, colors.text, dtLeft|dtVCenter|dtSingleLine)
		result := measurementDisplayStatus(m.Overall)
		drawStatusBadge(hdc, a, result, rect{411, 566, 570, 590})
		session := m.AppSession
		if !m.SessionResolved || session == "" {
			session = tr("logs.session.unresolved")
		}
		text(hdc, a.fontSmall, trf("logs.session", "session", session), rect{131, 598, 900, 618}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		appV := displayVersion(m.AppVersion)
		text(hdc, a.fontSmall, trf("logs.meta", "appVersion", appV, "engineVersion", m.EngineVersion, "count", len(m.Files)), rect{131, 626, 900, 646}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		if m.DetailAvailable {
			packageText := tr("logs.package.resolved")
			if !m.SessionResolved {
				packageText = tr("logs.package.unresolved")
			}
			text(hdc, a.fontTiny, packageText, rect{131, 650, 900, 669}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		} else {
			reason := m.DetailUnavailableReason
			if strings.TrimSpace(reason) == "" {
				reason = tr("logs.detail_unavailable.invalid")
			}
			text(hdc, a.fontTiny, reason, rect{131, 650, 900, 669}, colors.warning, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		}
		drawCompactLogButton(hdc, a, logDetailsButtonRect(), tr("action.show_details"), a.hoverLogDetails, m.DetailAvailable)
	}

	drawActionCard(hdc, a, rect{109, actionTop, 409, actionBottom}, 2, "⇧", func() string {
		if exporting {
			return tr("action.export_running")
		}
		return tr("action.create_package")
	}(), tr("action.create_package.sub"), hoverAction == 2, !exporting && !repairing && sel >= 0)
	drawActionCard(hdc, a, rect{426, actionTop, 705, actionBottom}, 3, "", tr("action.open_package_folder"), tr("action.open_package_folder.sub"), hoverAction == 3, true)
}

func (a *App) drawInfoView(hdc uintptr, w, h int) {
	a.drawPageHeader(hdc, w, tr("page.info.title"), "")
	p := rect{109, 120, int32(w - 18), 686}
	roundBox(hdc, p, 5, colors.surface, colors.border, 1)
	drawIcon(hdc, a.iconAppInfo, 569, 143, 88, 88)
	text(hdc, a.fontH1, tr("info.app_title"), rect{300, 235, 971, 267}, colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBody, tr("info.description.line1"), rect{300, 278, 971, 302}, colors.text, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBody, tr("info.description.line2"), rect{210, 306, 1060, 331}, colors.text, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)

	a.mu.Lock()
	vs := a.versionStatus
	checking := a.versionChecking
	a.mu.Unlock()
	if checking && vs.CheckedAt.IsZero() {
		vs.SynapseStatus = versionStateChecking
		vs.ChromaStatus = versionStateChecking
	}
	na := tr("info.versioncheck.not_available")
	show := func(v string) string {
		if strings.TrimSpace(v) == "" {
			return na
		}
		return v
	}

	line(hdc, 300, 356, 971, 356, 1, colors.borderStrong)
	text(hdc, a.fontBodySemi, tr("info.versioncheck.title"), rect{300, 366, 971, 390}, colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)

	// Official Razer prod-manifest module versions are compared only with the
	// registry values mapped by that same manifest. AppEngine file/package
	// versions remain a separate informational domain.
	drawVersionInfoRow(hdc, a, 402,
		tr("info.versioncheck.synapse.installed"), show(vs.InstalledSynapse),
		tr("info.versioncheck.synapse.latest"), show(vs.LatestSynapse), vs.SynapseStatus)
	drawVersionInfoRow(hdc, a, 430,
		tr("info.versioncheck.chroma.installed"), show(vs.InstalledChroma),
		tr("info.versioncheck.chroma.latest"), show(vs.LatestChroma), vs.ChromaStatus)
	drawVersionInfoRow(hdc, a, 458,
		tr("info.versioncheck.appengine.package"), show(vs.AppEnginePackage),
		tr("info.versioncheck.appengine.file"), show(vs.AppEngineFileVersion), "")
	sourceText := tr("info.versioncheck.source")
	sourceColor := colors.muted
	if vs.OnlineError != "" {
		sourceText = tr("info.versioncheck.source.offline")
		sourceColor = colors.unclear
	}
	text(hdc, a.fontTiny, sourceText, rect{225, 488, 1048, 510}, sourceColor, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)

	line(hdc, 300, 522, 971, 522, 1, colors.borderStrong)
	text(hdc, a.fontBodySemi, tr("info.tool_label"), rect{300, 532, 971, 556}, colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, tr("info.disclaimer.independent"), rect{230, 558, 1040, 580}, colors.text2, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, tr("info.disclaimer.trademarks"), rect{205, 580, 1065, 602}, colors.text2, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)

	// Give the security model the widest footer column so its detail remains
	// on one line. Scope is shifted left and version right, as requested.
	footerTitleRects := []rect{{145, 615, 365, 637}, {380, 615, 890, 637}, {925, 615, 1110, 637}}
	footerValueRects := []rect{{145, 640, 365, 668}, {380, 640, 890, 668}, {925, 640, 1110, 668}}
	titles := []string{tr("info.scope.title"), tr("info.readonly.title"), tr("info.version.title")}
	values := []string{tr("info.scope.value"), tr("info.readonly.value"), trf("app.version", "version", appVersion)}
	for i := range footerTitleRects {
		text(hdc, a.fontTiny, titles[i], footerTitleRects[i], colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontTiny, values[i], footerValueRects[i], colors.text2, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	}
}

func drawVersionInfoRow(hdc uintptr, a *App, y int, leftLabel, leftValue, rightLabel, rightValue, state string) {
	text(hdc, a.fontTiny, leftLabel, rect{226, int32(y), 370, int32(y + 22)}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontSmall, leftValue, rect{372, int32(y), 555, int32(y + 22)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, rightLabel, rect{580, int32(y), 742, int32(y + 22)}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontSmall, rightValue, rect{744, int32(y), 915, int32(y + 22)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	if state != "" {
		label := tr(versionStatusTextKey(state))
		color := versionStateColor(state)
		text(hdc, a.fontTiny, label, rect{920, int32(y), 1118, int32(y + 22)}, color, dtRight|dtVCenter|dtSingleLine|dtNoPrefix)
	}
}

func versionStateColor(state string) uintptr {
	switch state {
	case versionStateCurrent:
		return colors.success
	case versionStateUpdateAvailable:
		return colors.info
	case versionStateAhead:
		return colors.info
	case versionStateChecking:
		return colors.muted
	default:
		return colors.unclear
	}
}

func (a *App) drawSetupCalibrationModal(hdc uintptr, w, h int) {
	a.mu.Lock()
	stage := a.setupCalibrationStage
	idx := a.setupCalibrationProductIndex
	learned := a.setupCalibrationLearned
	errText := a.setupCalibrationError
	hover := a.hoverSetupCalibrationButton
	needsInventoryRefresh := a.setupCalibrationNeedsInventoryRefresh
	successPID := a.setupCalibrationSuccessPID
	successRole := a.setupCalibrationSuccessRole
	products := append([]DeviceProductProfile(nil), a.inventory.Products...)
	wirelessFlow := ""
	if idx >= 0 && idx < len(a.inventory.Products) {
		wirelessFlow = a.calibrationWirelessFlowLocked(a.inventory.Products[idx])
	}
	a.mu.Unlock()

	darken(hdc, w, h)
	p := rect{280, 202, 900, 604}
	roundBox(hdc, p, 6, colors.surface2, colors.borderStrong, 1)
	drawIcon(hdc, a.iconAppSmall, 297, 216, 18, 18)
	text(hdc, a.fontSmall, tr("setup.calibration.title"), rect{324, 207, 790, 239}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	closeColor := colors.text2
	if hover == 9 {
		closeColor = colors.green
	}
	text(hdc, a.fontDetailClose, "×", rect{855, 202, 899, 246}, closeColor, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)

	if stage == setupCalibrationComplete {
		card := rect{303, 267, 877, 480}
		roundBox(hdc, card, 6, colors.surface, colors.borderStrong, 1)
		text(hdc, a.fontH1, "✓", rect{328, 300, 372, 350}, colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontBodySemi, tr("setup.calibration.complete.heading"), rect{390, 292, 840, 325}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontSmall, trf("setup.calibration.complete.detail", "count", learned), rect{390, 330, 840, 382}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
		if needsInventoryRefresh {
			text(hdc, a.fontTiny, tr("setup.calibration.complete.inventory_refresh"), rect{390, 387, 840, 445}, colors.info, dtLeft|dtWordBreak|dtNoPrefix)
		}
		closeBtn := rect{716, 535, 854, 575}
		drawDetailButton(hdc, a, closeBtn, tr("action.close"), hover == 1)
		return
	}

	if idx < 0 || idx >= len(products) {
		text(hdc, a.fontSmall, tr("setup.calibration.error.target"), rect{320, 285, 850, 360}, colors.failure, dtLeft|dtWordBreak|dtNoPrefix)
		return
	}
	product := products[idx]
	text(hdc, a.fontTiny, trf("setup.calibration.product_progress", "current", idx+1, "total", len(products)), rect{304, 253, 500, 276}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	drawSetupDeviceClassIcon(hdc, setupProductDeviceClass(a.inventory, product), 304, 282, colors.surface2)
	text(hdc, a.fontH1, product.Name, rect{334, 276, 852, 313}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	card := rect{303, 326, 877, 501}
	roundBox(hdc, card, 6, colors.surface, colors.borderStrong, 1)
	wireless := stage == setupCalibrationWirelessPrompt || stage == setupCalibrationWirelessPreparing || stage == setupCalibrationWirelessWaiting || stage == setupCalibrationWirelessConfirm || stage == setupCalibrationWirelessVerifying || stage == setupCalibrationWirelessSuccess
	stageTitle := tr("setup.calibration.wired.heading")
	stageDetail := tr("setup.calibration.wired.detail")
	if wireless {
		stageTitle = tr("setup.calibration.wireless.heading")
		stageDetail = tr("setup.calibration.wireless.detail")
	}
	waitingStatus := ""
	if stage == setupCalibrationWiredWaiting {
		stageDetail = tr("setup.calibration.waiting.wired.detail")
		waitingStatus = tr("setup.calibration.waiting.wired.status")
	}
	if stage == setupCalibrationWirelessWaiting {
		if wirelessFlow == setupWirelessFlowEventTransition {
			stageDetail = tr("setup.calibration.waiting.wireless.auto.detail")
		} else {
			stageDetail = tr("setup.calibration.waiting.wireless.detail")
		}
		waitingStatus = tr("setup.calibration.waiting.wireless.status")
	}
	if stage == setupCalibrationWirelessConfirm {
		stageDetail = tr("setup.calibration.confirm.wireless.detail")
		waitingStatus = tr("setup.calibration.waiting.wireless.status")
	}
	if stage == setupCalibrationWiredSuccess {
		stageDetail = tr("setup.calibration.success.wired")
	}
	if stage == setupCalibrationWirelessSuccess {
		stageDetail = tr("setup.calibration.success.wireless")
	}
	text(hdc, a.fontBodySemi, stageTitle, rect{326, 345, 845, 374}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)

	success := stage == setupCalibrationWiredSuccess || stage == setupCalibrationWirelessSuccess
	if success {
		text(hdc, a.fontBodySemi, stageDetail, rect{326, 388, 845, 418}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		roleLabel := setupConnectionRoleLabel(DeviceConnectionProfile{ConnectionType: successRole, ConnectionTypeConfidence: "high"})
		resultText := strings.TrimSpace(successPID)
		if roleLabel != "" && resultText != "" {
			resultText = roleLabel + " · " + resultText
		}
		if resultText != "" {
			text(hdc, a.fontSmall, resultText, rect{326, 428, 845, 458}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		}
		text(hdc, a.fontTiny, tr("setup.calibration.success.continue_hint"), rect{326, 462, 845, 490}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
	} else {
		text(hdc, a.fontSmall, stageDetail, rect{326, 382, 845, 449}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
	}

	busy := stage == setupCalibrationWiredPreparing || stage == setupCalibrationWirelessPreparing || stage == setupCalibrationWiredVerifying || stage == setupCalibrationWirelessVerifying
	waiting := stage == setupCalibrationWiredWaiting || stage == setupCalibrationWirelessWaiting
	if busy {
		label := tr("setup.calibration.preparing")
		if stage == setupCalibrationWiredVerifying || stage == setupCalibrationWirelessVerifying {
			label = tr("setup.calibration.verifying")
		}
		text(hdc, a.fontSmall, label, rect{326, 453, 845, 476}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		track := rect{326, 483, 845, 490}
		roundBox(hdc, track, 4, colors.bg, colors.borderStrong, 1)
		innerWidth := int(track.Right-track.Left) - 4
		if innerWidth > 12 {
			segmentWidth := innerWidth / 4
			travel := innerWidth - segmentWidth
			phase := int((time.Now().UnixMilli() / 24) % int64(maxInt(1, travel*2)))
			if phase > travel {
				phase = travel*2 - phase
			}
			fill(hdc, rect{track.Left + 2 + int32(phase), track.Top + 2, track.Left + 2 + int32(phase+segmentWidth), track.Bottom - 2}, colors.green)
		}
		return
	}
	if !success && strings.TrimSpace(errText) != "" {
		text(hdc, a.fontTiny, errText, rect{326, 454, 845, 493}, colors.failure, dtLeft|dtWordBreak|dtNoPrefix)
	} else if !success && waitingStatus != "" {
		text(hdc, a.fontTiny, waitingStatus, rect{326, 454, 845, 493}, colors.green, dtLeft|dtWordBreak|dtNoPrefix)
	}

	if success {
		deviceSkipBtn := rect{480, 535, 644, 575}
		continueBtn := rect{656, 535, 854, 575}
		drawDetailButton(hdc, a, deviceSkipBtn, tr("action.skip_device"), hover == 2)
		drawDetailButton(hdc, a, continueBtn, tr("action.continue"), hover == 1)
		return
	}

	if stage == setupCalibrationWiredPrompt || stage == setupCalibrationWirelessPrompt || stage == setupCalibrationWirelessConfirm || waiting {
		deviceSkipBtn := rect{304, 535, 468, 575}
		stepSkipBtn := rect{480, 535, 644, 575}
		drawDetailButton(hdc, a, deviceSkipBtn, tr("action.skip_device"), hover == 2)
		drawDetailButton(hdc, a, stepSkipBtn, tr("action.skip"), hover == 0)
		if stage == setupCalibrationWiredPrompt || stage == setupCalibrationWirelessPrompt || stage == setupCalibrationWirelessConfirm {
			actionBtn := rect{656, 535, 854, 575}
			if stage == setupCalibrationWiredPrompt {
				drawDetailButton(hdc, a, actionBtn, tr("setup.calibration.action.wired"), hover == 1)
			} else if stage == setupCalibrationWirelessConfirm {
				drawDetailButton(hdc, a, actionBtn, tr("setup.calibration.action.wireless_confirm"), hover == 1)
			} else {
				drawDetailButton(hdc, a, actionBtn, tr("setup.calibration.action.wireless"), hover == 1)
			}
		}
	}
}

func (a *App) drawSetupNoticeModal(hdc uintptr, w, h int) {
	a.mu.Lock()
	title := a.setupNoticeTitle
	detail := a.setupNoticeDetail
	hover := a.hoverSetupNoticeButton
	a.mu.Unlock()

	darken(hdc, w, h)
	p := rect{350, 285, 830, 500}
	roundBox(hdc, p, 6, colors.surface2, colors.borderStrong, 1)
	drawIcon(hdc, a.iconAppSmall, 368, 300, 18, 18)
	text(hdc, a.fontSmall, title, rect{398, 291, 760, 326}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	closeColor := colors.text2
	if hover == 9 {
		closeColor = colors.green
	}
	text(hdc, a.fontDetailClose, "×", rect{786, 285, 830, 329}, closeColor, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	card := rect{370, 340, 810, 421}
	roundBox(hdc, card, 5, colors.surface, colors.borderStrong, 1)
	fill(hdc, rect{370, 340, 374, 421}, colors.warning)
	text(hdc, a.fontSmall, detail, rect{392, 352, 790, 409}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
	drawDetailButton(hdc, a, rect{680, 440, 806, 480}, tr("action.close"), hover == 0)
}

func (a *App) drawExportModal(hdc uintptr, w, h int) {
	a.mu.Lock()
	path := a.exportDialogPath
	hoverModal := a.hoverModalButton
	a.mu.Unlock()
	darken(hdc, w, h)
	p := rect{315, 274, 867, 495}
	roundBox(hdc, p, 5, colors.surface2, colors.borderStrong, 1)
	drawIcon(hdc, a.iconAppSmall, 325, 280, 16, 16)
	text(hdc, a.fontSmall, tr("modal.export.success.title"), rect{344, 275, 700, 302}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontH1, "×", rect{835, 276, 863, 305}, colors.text2, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	card := rect{331, 321, 850, 425}
	roundBox(hdc, card, 5, colors.surface, colors.borderStrong, 1)
	fill(hdc, rect{331, 321, 335, 425}, colors.green)
	text(hdc, a.fontH1, "✓", rect{350, 337, 380, 374}, colors.green, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontBodySemi, tr("modal.export.success.heading"), rect{391, 336, 820, 365}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontSmall, tr("modal.export.path"), rect{391, 370, 820, 389}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	text(hdc, a.fontTiny, path, rect{391, 389, 826, 420}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
	openBtn := rect{560, 442, 706, 480}
	closeBtn := rect{718, 442, 837, 480}
	drawDetailButton(hdc, a, openBtn, tr("action.open_folder"), hoverModal == 0)
	drawDetailButton(hdc, a, closeBtn, tr("action.close"), hoverModal == 1)
}

func (a *App) drawRepairModal(hdc uintptr, w, h int) {
	a.mu.Lock()
	stage := a.repairDialogStage
	targets := append([]string(nil), a.repairTargets...)
	result := a.repairResult
	resultErr := a.repairResultErr
	problemID := a.repairProblemID
	recipeID := a.repairRecipeID
	hover := a.hoverRepairButton
	a.mu.Unlock()
	def, _ := repairDefinitionByID(recipeID)
	isAppEngineRepair := recipeID == repairAppEngineControlledRecovery

	darken(hdc, w, h)
	p := rect{300, 235, 882, 585}
	roundBox(hdc, p, 6, colors.surface2, colors.borderStrong, 1)
	drawIcon(hdc, a.iconAppSmall, 315, 246, 18, 18)
	titleKey := "repair.confirm.title"
	if isAppEngineRepair {
		titleKey = "repair.appengine.confirm.title"
	}
	if stage == repairDialogRunning {
		titleKey = "repair.running.title"
		if isAppEngineRepair {
			titleKey = "repair.appengine.running.title"
		}
	}
	if stage == repairDialogResult && result.successful() {
		titleKey = "repair.result.success.title"
		if isAppEngineRepair {
			titleKey = "repair.appengine.result.success.title"
		}
	}
	if stage == repairDialogResult && !result.successful() {
		titleKey = "repair.result.failed.title"
		if isAppEngineRepair {
			titleKey = "repair.appengine.result.failed.title"
		}
	}
	text(hdc, a.fontSmall, tr(titleKey), rect{342, 240, 760, 270}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
	if stage != repairDialogRunning {
		closeColor := colors.text2
		if hover == 9 {
			closeColor = colors.green
		}
		text(hdc, a.fontDetailClose, "×", rect{838, 234, 882, 278}, closeColor, dtCenter|dtVCenter|dtSingleLine|dtNoPrefix)
	}

	accent := colors.warning
	if stage == repairDialogResult {
		if result.successful() {
			accent = colors.success
		} else {
			accent = colors.failure
		}
	}
	card := rect{319, 286, 862, 493}
	roundBox(hdc, card, 5, colors.surface, colors.borderStrong, 1)
	fill(hdc, rect{319, 286, 323, 493}, accent)

	switch stage {
	case repairDialogConfirm:
		headingKey, bodyKey, targetsKey, elevationKey := "repair.confirm.heading", "repair.confirm.body", "repair.confirm.targets", "repair.confirm.uac"
		if isAppEngineRepair {
			headingKey, bodyKey, targetsKey = "repair.appengine.confirm.heading", "repair.appengine.confirm.body", "repair.appengine.confirm.targets"
			if def.RequiresElevation {
				elevationKey = "repair.confirm.uac"
			} else {
				elevationKey = "repair.appengine.confirm.no_uac"
			}
		}
		text(hdc, a.fontBodySemi, tr(headingKey), rect{344, 301, 830, 329}, accent, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontSmall, tr(bodyKey), rect{344, 332, 834, 372}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
		text(hdc, a.fontTiny, trf("repair.confirm.problem_id", "problemId", problemID), rect{344, 374, 830, 391}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontTiny, trf("repair.confirm.recipe_id", "recipeId", recipeID), rect{344, 392, 830, 409}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontTiny, tr(targetsKey), rect{344, 411, 520, 428}, colors.muted, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		y := 429
		for _, name := range targets {
			text(hdc, a.fontTiny, "• "+name, rect{358, int32(y), 830, int32(y + 18)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
			y += 18
		}
		text(hdc, a.fontTiny, tr(elevationKey), rect{344, 466, 830, 486}, colors.warning, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		drawDetailButton(hdc, a, rect{548, 515, 686, 555}, tr("action.cancel"), hover == 0)
		drawDetailButton(hdc, a, rect{698, 515, 850, 555}, tr("action.repair.start"), hover == 1)
	case repairDialogRunning:
		runningHeading, runningBody := "repair.running.heading", "repair.running.body"
		if isAppEngineRepair {
			runningHeading, runningBody = "repair.appengine.running.heading", "repair.appengine.running.body"
		}
		text(hdc, a.fontBodySemi, tr(runningHeading), rect{344, 314, 830, 344}, colors.warning, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontSmall, tr(runningBody), rect{344, 354, 830, 411}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
		text(hdc, a.fontTiny, tr("repair.audit.note"), rect{344, 434, 830, 477}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
	case repairDialogResult:
		success := result.successful() && resultErr == ""
		heading := tr("repair.result.failed.heading")
		body := tr("repair.result.failed.body")
		if isAppEngineRepair {
			heading, body = tr("repair.appengine.result.failed.heading"), tr("repair.appengine.result.failed.body")
		}
		if success {
			heading = tr("repair.result.success.heading")
			body = tr("repair.result.success.body")
			if isAppEngineRepair {
				heading, body = tr("repair.appengine.result.success.heading"), tr("repair.appengine.result.success.body")
			}
		}
		text(hdc, a.fontBodySemi, heading, rect{344, 300, 830, 329}, accent, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		text(hdc, a.fontSmall, body, rect{344, 334, 830, 382}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
		if resultErr != "" {
			errText := trf("repair.error.result", "error", resultErr)
			if resultErr == "UAC_CANCELLED" {
				errText = tr("repair.error.uac")
			}
			text(hdc, a.fontTiny, errText, rect{344, 389, 830, 428}, colors.failure, dtLeft|dtWordBreak|dtNoPrefix)
		} else {
			verificationColor := colors.failure
			if strings.EqualFold(result.VerificationStatus, "PASS") {
				verificationColor = colors.success
			}
			text(hdc, a.fontTiny, trf("repair.result.verification", "status", fallbackText(result.VerificationStatus, "—")), rect{344, 386, 830, 404}, verificationColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
			y := 405
			if isAppEngineRepair {
				text(hdc, a.fontTiny, trf("repair.appengine.result.mode", "mode", fallbackText(result.ActionMode, "—")), rect{344, int32(y), 830, int32(y + 20)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
				y += 22
				text(hdc, a.fontTiny, result.VerificationDetail, rect{344, int32(y), 830, int32(y + 42)}, colors.text2, dtLeft|dtWordBreak|dtNoPrefix)
			} else {
				for _, name := range chromaRepairServiceNames {
					text(hdc, a.fontTiny, repairServiceState(result, name), rect{344, int32(y), 830, int32(y + 20)}, colors.text, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
					y += 22
				}
			}
		}
		text(hdc, a.fontTiny, tr("repair.audit.note"), rect{344, 452, 830, 485}, colors.muted, dtLeft|dtWordBreak|dtNoPrefix)
		drawDetailButton(hdc, a, rect{521, 515, 704, 555}, tr("action.repair.recheck"), hover == 0)
		drawDetailButton(hdc, a, rect{716, 515, 850, 555}, tr("action.close"), hover == 1)
	}
}

func darken(hdc uintptr, w, h int) {
	// BLENDFUNCTION {AC_SRC_OVER,0,110,0}; constant-alpha black overlay.
	darkenRect(hdc, rect{0, 0, int32(w), int32(h)}, 110)
}

func stateColor(state string) uintptr {
	switch strings.ToUpper(strings.TrimSpace(state)) {
	case "HEALTHY", "GESUND", "BESTANDEN", "PASS", "PASSED":
		return colors.success
	case "HINT", "HINWEIS", "WARN", "WARNING", "CHECKING", "WAITING", "PRÜFUNG", "PRÜFUNG …", "WARTET":
		return colors.warning
	case "UNCLEAR", "UNKLAR", "UNKNOWN":
		return colors.unclear
	case "FAILED", "FEHLER", "FAIL":
		return colors.failure
	case "INFO":
		return colors.info
	}
	return colors.muted
}

func variantIndex(state string) int {
	switch strings.ToUpper(strings.TrimSpace(state)) {
	case "HEALTHY", "BESTANDEN", "GESUND", "PASS", "PASSED":
		return 1
	case "HINT", "UNCLEAR", "HINWEIS", "WARN", "WARNING", "UNKLAR", "UNKNOWN", "CHECKING", "WAITING", "PRÜFUNG", "PRÜFUNG …", "WARTET":
		return 2
	case "FAILED", "FEHLER", "FAIL":
		return 3
	}
	return 0
}

func formatClock(d time.Duration) string {
	if d < 0 {
		d = 0
	}
	sec := int(d.Round(time.Second) / time.Second)
	if sec < 0 {
		sec = 0
	}
	return fmt.Sprintf("%02d:%02d", sec/60, sec%60)
}

func (a *App) closeDetailPopover() bool {
	a.mu.Lock()
	if a.detailGate < 0 {
		a.mu.Unlock()
		return false
	}
	wasDragging := a.detailScrollDragging
	a.detailGate = -1
	a.detailScroll = 0
	a.detailScrollMax = 0
	a.detailScrollDragging = false
	a.detailRawExpanded = false
	a.hoverDetailButton = -1
	a.hoverDetailClose = false
	a.mu.Unlock()
	if wasDragging {
		procReleaseCapture.Call()
	}
	procInvalidateRect.Call(a.hwnd, 0, 0)
	return true
}

func (a *App) handleDetailScrollMouseDown(x, y int) bool {
	a.mu.Lock()
	if a.exportDialogVisible || a.repairDialogVisible || a.detailGate < 0 || a.detailScrollMax <= 0 || x < 1123 || x > 1144 || y < a.detailScrollTrackTop || y > a.detailScrollTrackBottom {
		a.mu.Unlock()
		return false
	}
	thumbH := a.detailScrollThumbBottom - a.detailScrollThumbTop
	if thumbH <= 0 {
		a.mu.Unlock()
		return false
	}
	if y >= a.detailScrollThumbTop && y <= a.detailScrollThumbBottom {
		a.detailScrollDragOffset = y - a.detailScrollThumbTop
	} else {
		// Track click: center the thumb beneath the pointer and immediately enter
		// drag mode. This mirrors normal Windows scrollbar behavior and makes the
		// enlarged hit target useful without requiring pixel-perfect thumb clicks.
		a.detailScrollDragOffset = thumbH / 2
	}
	a.detailScrollDragging = true
	trackTop := a.detailScrollTrackTop
	trackBottom := a.detailScrollTrackBottom
	maxScroll := a.detailScrollMax
	dragOffset := a.detailScrollDragOffset
	oldScroll := a.detailScroll
	travel := (trackBottom - trackTop) - thumbH
	if travel > 0 {
		thumbTop := y - dragOffset
		if thumbTop < trackTop {
			thumbTop = trackTop
		}
		if thumbTop > trackTop+travel {
			thumbTop = trackTop + travel
		}
		a.detailScroll = (thumbTop - trackTop) * maxScroll / travel
	}
	changed := oldScroll != a.detailScroll
	a.mu.Unlock()
	procSetCapture.Call(a.hwnd)
	if changed {
		procInvalidateRect.Call(a.hwnd, 0, 0)
		procUpdateWindow.Call(a.hwnd)
	}
	return true
}

func (a *App) handleDetailScrollDrag(y int) bool {
	a.mu.Lock()
	if !a.detailScrollDragging || a.detailGate < 0 {
		a.mu.Unlock()
		return false
	}
	trackTop := a.detailScrollTrackTop
	trackBottom := a.detailScrollTrackBottom
	thumbH := a.detailScrollThumbBottom - a.detailScrollThumbTop
	maxScroll := a.detailScrollMax
	dragOffset := a.detailScrollDragOffset
	oldScroll := a.detailScroll
	travel := (trackBottom - trackTop) - thumbH
	if travel > 0 && maxScroll > 0 {
		thumbTop := y - dragOffset
		if thumbTop < trackTop {
			thumbTop = trackTop
		}
		if thumbTop > trackTop+travel {
			thumbTop = trackTop + travel
		}
		// RC2 requirement: content follows the mouse continuously while the left
		// button is still held. Mouse-up only terminates the drag state.
		a.detailScroll = (thumbTop - trackTop) * maxScroll / travel
	}
	changed := oldScroll != a.detailScroll
	a.mu.Unlock()
	if changed {
		procInvalidateRect.Call(a.hwnd, 0, 0)
		// Force a paint while WM_MOUSEMOVE is still being processed so the
		// viewport visibly tracks the thumb before mouse-up.
		procUpdateWindow.Call(a.hwnd)
	}
	return true
}

func (a *App) endDetailScrollDrag() bool {
	a.mu.Lock()
	if !a.detailScrollDragging {
		a.mu.Unlock()
		return false
	}
	a.detailScrollDragging = false
	a.mu.Unlock()
	procReleaseCapture.Call()
	return true
}

func (a *App) handleMouseMove(x, y int) {
	a.mu.Lock()
	oldGate, oldAction, oldSidebar := a.hoverGate, a.hoverAction, a.hoverSidebar
	oldDetail, oldModal, oldRepair, oldSetupCalibration, oldSetupNotice, oldSetupProduct, oldLog := a.hoverDetailButton, a.hoverModalButton, a.hoverRepairButton, a.hoverSetupCalibrationButton, a.hoverSetupNoticeButton, a.hoverSetupProductRow, a.hoverLogRow
	oldDetailClose := a.hoverDetailClose
	oldLogTab, oldLogClose, oldLogDetails := a.hoverLogTab, a.hoverLogClose, a.hoverLogDetails
	a.hoverGate, a.hoverAction, a.hoverSidebar = -1, -1, -1
	a.hoverDetailButton, a.hoverModalButton, a.hoverRepairButton, a.hoverSetupCalibrationButton, a.hoverSetupNoticeButton, a.hoverSetupProductRow, a.hoverLogRow, a.hoverLogTab = -1, -1, -1, -1, -1, -1, -1, -1
	a.hoverDetailClose = false
	a.hoverLogClose = false
	a.hoverLogDetails = false

	if a.setupNoticeVisible {
		if x >= 786 && x <= 830 && y >= 285 && y <= 329 {
			a.hoverSetupNoticeButton = 9
		} else if x >= 680 && x <= 806 && y >= 440 && y <= 480 {
			a.hoverSetupNoticeButton = 0
		}
	} else if a.setupCalibrationVisible {
		stage := a.setupCalibrationStage
		if x >= 855 && x <= 899 && y >= 202 && y <= 246 {
			a.hoverSetupCalibrationButton = 9
		} else if stage == setupCalibrationComplete {
			if x >= 716 && x <= 854 && y >= 535 && y <= 575 {
				a.hoverSetupCalibrationButton = 1
			}
		} else if stage == setupCalibrationWiredSuccess || stage == setupCalibrationWirelessSuccess {
			if x >= 480 && x <= 644 && y >= 535 && y <= 575 {
				a.hoverSetupCalibrationButton = 2
			} else if x >= 656 && x <= 854 && y >= 535 && y <= 575 {
				a.hoverSetupCalibrationButton = 1
			}
		} else if stage == setupCalibrationWiredPrompt || stage == setupCalibrationWirelessPrompt || stage == setupCalibrationWirelessConfirm || stage == setupCalibrationWiredWaiting || stage == setupCalibrationWirelessWaiting {
			if x >= 304 && x <= 468 && y >= 535 && y <= 575 {
				a.hoverSetupCalibrationButton = 2
			} else if x >= 480 && x <= 644 && y >= 535 && y <= 575 {
				a.hoverSetupCalibrationButton = 0
			} else if (stage == setupCalibrationWiredPrompt || stage == setupCalibrationWirelessPrompt || stage == setupCalibrationWirelessConfirm) && x >= 656 && x <= 854 && y >= 535 && y <= 575 {
				a.hoverSetupCalibrationButton = 1
			}
		}
	} else if a.repairDialogVisible {
		stage := a.repairDialogStage
		if stage != repairDialogRunning && x >= 838 && x <= 882 && y >= 234 && y <= 278 {
			a.hoverRepairButton = 9
		} else if stage == repairDialogConfirm {
			if x >= 548 && x <= 686 && y >= 515 && y <= 555 {
				a.hoverRepairButton = 0
			} else if x >= 698 && x <= 850 && y >= 515 && y <= 555 {
				a.hoverRepairButton = 1
			}
		} else if stage == repairDialogResult {
			if x >= 521 && x <= 704 && y >= 515 && y <= 555 {
				a.hoverRepairButton = 0
			} else if x >= 716 && x <= 850 && y >= 515 && y <= 555 {
				a.hoverRepairButton = 1
			}
		}
	} else if a.exportDialogVisible {
		// A Golden modal suppresses background hover feedback. Only its own
		// action buttons stay interactive.
		if x >= 560 && x <= 706 && y >= 442 && y <= 480 {
			a.hoverModalButton = 0
		} else if x >= 718 && x <= 837 && y >= 442 && y <= 480 {
			a.hoverModalButton = 1
		}
	} else {
		if x >= 7 && x <= 82 {
			for i := 0; i < 4; i++ {
				ny := 91 + i*88
				if y >= ny && y < ny+73 {
					a.hoverSidebar = i
					break
				}
			}
		}

		if a.currentView == 1 {
			popoverHit := a.detailGate >= 0 && x >= 634 && x <= 1149 && y >= 291 && y <= 699
			if !popoverHit && x >= contentX && y >= tableTop+tableHeaderH && y < tableTop+tableHeaderH+gateCount*gateRowH {
				i := (y - (tableTop + tableHeaderH)) / gateRowH
				if i >= 0 && i < gateCount {
					a.hoverGate = i
				}
			}
			if a.detailGate >= 0 {
				if x >= 1107 && x <= 1149 && y >= 285 && y <= 334 {
					a.hoverDetailClose = true
				} else {
					repairable := repairAvailableForGateFindings(a.problemFindings, a.detailGate)
					if repairable {
						if x >= 660 && x <= 806 && y >= 659 && y <= 687 {
							a.hoverDetailButton = 2
						} else if x >= 815 && x <= 966 && y >= 659 && y <= 687 {
							a.hoverDetailButton = 0
						} else if x >= 975 && x <= 1122 && y >= 659 && y <= 687 {
							a.hoverDetailButton = 1
						}
					} else if x >= 660 && x <= 870 && y >= 659 && y <= 687 {
						a.hoverDetailButton = 0
					} else if x >= 882 && x <= 1122 && y >= 659 && y <= 687 {
						a.hoverDetailButton = 1
					}
				}
			}
		} else if a.currentView == 2 {
			if y >= pageTitleTop && y <= pageUnderline+3 {
				p := logPrimaryTabRect()
				if x >= int(p.Left) && x <= int(p.Right) {
					a.hoverLogTab = 0
				}
				if a.logHistoricalOpen {
					h := logHistoricalTabRect()
					c := logHistoricalCloseRect()
					if x >= int(c.Left) && x <= int(c.Right) && y >= int(c.Top) && y <= int(c.Bottom) {
						a.hoverLogClose = true
					} else if x >= int(h.Left) && x <= int(h.Right) {
						a.hoverLogTab = 1
					}
				}
			}
			if a.logHistoricalOpen && a.logHistoricalActive {
				popoverHit := a.detailGate >= 0 && x >= 634 && x <= 1149 && y >= 291 && y <= 699
				if !popoverHit && x >= contentX && y >= tableTop+tableHeaderH && y < tableTop+tableHeaderH+gateCount*gateRowH {
					i := (y - (tableTop + tableHeaderH)) / gateRowH
					if i >= 0 && i < gateCount {
						a.hoverGate = i
					}
				}
				if a.detailGate >= 0 {
					if x >= 1107 && x <= 1149 && y >= 285 && y <= 334 {
						a.hoverDetailClose = true
					} else if x >= 660 && x <= 870 && y >= 659 && y <= 687 {
						a.hoverDetailButton = 0
					} else if x >= 882 && x <= 1122 && y >= 659 && y <= 687 {
						a.hoverDetailButton = 1
					}
				}
			} else {
				if x >= contentX && x <= 1162 && y >= 156 && y < 156+10*35 {
					idx := a.logScroll + (y-156)/35
					if idx >= 0 && idx < len(a.logMeasurements) {
						a.hoverLogRow = idx
					}
				}
				if a.logSelected >= 0 && a.logSelected < len(a.logMeasurements) && a.logMeasurements[a.logSelected].DetailAvailable {
					r := logDetailsButtonRect()
					if x >= int(r.Left) && x <= int(r.Right) && y >= int(r.Top) && y <= int(r.Bottom) {
						a.hoverLogDetails = true
					}
				}
			}
		}

		if a.currentView == 0 && a.setupReady && !a.setupScanning && !a.checking && !a.repairing && x >= contentX && x <= 1162 && y >= 334 && y < 334+minInt(8, len(a.inventory.Products))*38 {
			idx := (y - 334) / 38
			if idx >= 0 && idx < len(a.inventory.Products) {
				a.hoverSetupProductRow = idx
			}
		}

		if y >= actionTop && y <= actionBottom {
			switch a.currentView {
			case 0:
				if x >= 109 && x <= 389 {
					a.hoverAction = 4
				} else if x >= 406 && x <= 686 {
					a.hoverAction = 5
				}
			case 1:
				if x >= 109 && x <= 389 {
					a.hoverAction = 0
				} else if x >= 406 && x <= 664 {
					a.hoverAction = 1
				}
			case 2:
				if x >= 109 && x <= 409 {
					a.hoverAction = 2
				} else if x >= 426 && x <= 705 {
					a.hoverAction = 3
				}
			}
		}
	}

	changed := oldGate != a.hoverGate || oldAction != a.hoverAction || oldSidebar != a.hoverSidebar ||
		oldDetail != a.hoverDetailButton || oldModal != a.hoverModalButton || oldRepair != a.hoverRepairButton || oldSetupCalibration != a.hoverSetupCalibrationButton || oldSetupNotice != a.hoverSetupNoticeButton || oldSetupProduct != a.hoverSetupProductRow || oldLog != a.hoverLogRow || oldDetailClose != a.hoverDetailClose || oldLogTab != a.hoverLogTab || oldLogClose != a.hoverLogClose || oldLogDetails != a.hoverLogDetails
	a.mu.Unlock()
	if changed {
		procInvalidateRect.Call(a.hwnd, 0, 0)
	}
}

func (a *App) handleMouseWheel(delta int) {
	a.mu.Lock()
	if a.exportDialogVisible || a.repairDialogVisible || a.setupCalibrationVisible || a.setupNoticeVisible {
		a.mu.Unlock()
		return
	}
	changed := false
	if a.detailGate >= 0 {
		// Both compact and raw Gate detail modes are a continuous pixel-scroll
		// document in RC2, so the entire Summary/Assessment/Findings region moves.
		step := 42
		old := a.detailScroll
		if delta < 0 {
			a.detailScroll += step
		} else if delta > 0 {
			a.detailScroll -= step
		}
		if a.detailScroll < 0 {
			a.detailScroll = 0
		}
		if a.detailScroll > a.detailScrollMax {
			a.detailScroll = a.detailScrollMax
		}
		changed = old != a.detailScroll
	} else if a.currentView == 2 && !(a.logHistoricalOpen && a.logHistoricalActive) {
		max := len(a.logMeasurements) - 10
		if max < 0 {
			max = 0
		}
		old := a.logScroll
		if delta < 0 && a.logScroll < max {
			a.logScroll++
		} else if delta > 0 && a.logScroll > 0 {
			a.logScroll--
		}
		changed = old != a.logScroll
	}
	a.mu.Unlock()
	if changed {
		procInvalidateRect.Call(a.hwnd, 0, 0)
	}
}

func (a *App) handleClick(x, y int) {
	a.mu.Lock()
	modal := a.exportDialogVisible
	view := a.currentView
	detail := a.detailGate
	checking := a.checking
	exporting := a.exporting
	repairing := a.repairing
	scroll := a.logScroll
	historicalOpen := a.logHistoricalOpen
	historicalActive := a.logHistoricalOpen && a.logHistoricalActive
	a.mu.Unlock()

	a.mu.Lock()
	calibrationModal := a.setupCalibrationVisible
	calibrationStage := a.setupCalibrationStage
	setupNoticeModal := a.setupNoticeVisible
	repairModal := a.repairDialogVisible
	repairStage := a.repairDialogStage
	a.mu.Unlock()
	if setupNoticeModal {
		if (x >= 786 && x <= 830 && y >= 285 && y <= 329) || (x >= 680 && x <= 806 && y >= 440 && y <= 480) {
			a.closeSetupNotice()
		}
		return
	}

	if calibrationModal {
		if x >= 855 && x <= 899 && y >= 202 && y <= 246 {
			a.closeSetupCalibration()
			return
		}
		if calibrationStage == setupCalibrationComplete {
			if x >= 716 && x <= 854 && y >= 535 && y <= 575 {
				a.closeSetupCalibration()
			}
			return
		}
		if calibrationStage == setupCalibrationWiredSuccess || calibrationStage == setupCalibrationWirelessSuccess {
			if x >= 480 && x <= 644 && y >= 535 && y <= 575 {
				a.skipCurrentCalibrationProduct()
				return
			}
			if x >= 656 && x <= 854 && y >= 535 && y <= 575 {
				a.continueCalibrationSuccess()
				return
			}
			return
		}
		waiting := calibrationStage == setupCalibrationWiredWaiting || calibrationStage == setupCalibrationWirelessWaiting
		if calibrationStage == setupCalibrationWiredPrompt || calibrationStage == setupCalibrationWirelessPrompt || calibrationStage == setupCalibrationWirelessConfirm || waiting {
			if x >= 304 && x <= 468 && y >= 535 && y <= 575 {
				a.skipCurrentCalibrationProduct()
				return
			}
			if x >= 480 && x <= 644 && y >= 535 && y <= 575 {
				a.skipCurrentCalibrationStep()
				return
			}
			if !waiting && x >= 656 && x <= 854 && y >= 535 && y <= 575 {
				if calibrationStage == setupCalibrationWiredPrompt {
					a.startCurrentCalibration("wired")
				} else if calibrationStage == setupCalibrationWirelessPrompt {
					a.startCurrentCalibration("wireless")
				} else {
					a.confirmCurrentWirelessCalibration()
				}
				return
			}
		}
		return
	}

	if repairModal {
		if repairStage != repairDialogRunning && x >= 838 && x <= 882 && y >= 234 && y <= 278 {
			a.closeRepairDialog()
			return
		}
		if repairStage == repairDialogConfirm {
			if x >= 548 && x <= 686 && y >= 515 && y <= 555 {
				a.closeRepairDialog()
				return
			}
			if x >= 698 && x <= 850 && y >= 515 && y <= 555 {
				a.startSelectedRepair()
				return
			}
		}
		if repairStage == repairDialogResult {
			if x >= 521 && x <= 704 && y >= 515 && y <= 555 {
				a.closeRepairDialog()
				a.startCheck()
				return
			}
			if x >= 716 && x <= 850 && y >= 515 && y <= 555 {
				a.closeRepairDialog()
				return
			}
		}
		return
	}

	if modal {
		if x >= 835 && x <= 863 && y >= 276 && y <= 305 || x >= 718 && x <= 837 && y >= 442 && y <= 480 {
			a.mu.Lock()
			a.exportDialogVisible = false
			a.exportDialogPath = ""
			a.mu.Unlock()
			procInvalidateRect.Call(a.hwnd, 0, 0)
			return
		}
		if x >= 560 && x <= 706 && y >= 442 && y <= 480 {
			a.mu.Lock()
			p := a.exportDialogPath
			a.mu.Unlock()
			openFolder(filepath.Dir(p))
			return
		}
		return
	}

	if x >= 7 && x <= 82 {
		for i := 0; i < 4; i++ {
			ny := 91 + i*88
			if y >= ny && y < ny+73 {
				a.mu.Lock()
				a.currentView = i
				a.detailGate = -1
				a.detailScroll = 0
				a.mu.Unlock()
				if i == 2 {
					a.refreshMeasurementsAsync()
				}
				procInvalidateRect.Call(a.hwnd, 0, 0)
				return
			}
		}
	}

	if detail >= 0 {
		if x >= 1107 && x <= 1149 && y >= 285 && y <= 334 {
			a.closeDetailPopover()
			return
		}
		allowRepair := view == 1
		repairable := false
		if allowRepair {
			a.mu.Lock()
			repairable = repairAvailableForGateFindings(a.problemFindings, detail)
			a.mu.Unlock()
		}
		if repairable {
			if x >= 660 && x <= 806 && y >= 659 && y <= 687 {
				a.openRepairConfirmation()
				return
			}
			if x >= 815 && x <= 966 && y >= 659 && y <= 687 {
				a.mu.Lock()
				a.detailRawExpanded = !a.detailRawExpanded
				a.detailScroll = 0
				a.mu.Unlock()
				procInvalidateRect.Call(a.hwnd, 0, 0)
				return
			}
			if x >= 975 && x <= 1122 && y >= 659 && y <= 687 {
				a.copyCurrentGateDetails()
				return
			}
		} else {
			if x >= 660 && x <= 870 && y >= 659 && y <= 687 {
				a.mu.Lock()
				a.detailRawExpanded = !a.detailRawExpanded
				a.detailScroll = 0
				a.mu.Unlock()
				procInvalidateRect.Call(a.hwnd, 0, 0)
				return
			}
			if x >= 882 && x <= 1122 && y >= 659 && y <= 687 {
				a.copyCurrentGateDetails()
				return
			}
		}
		// Modal-in-panel hit testing: every click inside the popover is owned by
		// the popover. Never fall through to the gate row behind it.
		if x >= 634 && x <= 1149 && y >= 291 && y <= 699 {
			return
		}
	}

	if view == 0 && x >= contentX && x <= 1162 && y >= 334 {
		a.mu.Lock()
		ready := a.setupReady
		busy := a.setupScanning || a.checking || a.repairing
		count := len(a.inventory.Products)
		a.mu.Unlock()
		if ready && !busy && y < 334+minInt(8, count)*38 {
			idx := (y - 334) / 38
			a.toggleHealthcheckProduct(idx)
			return
		}
	}

	if view == 0 && y >= actionTop && y <= actionBottom {
		a.mu.Lock()
		scanning := a.setupScanning
		ready := a.setupReady
		a.mu.Unlock()
		if x >= 109 && x <= 389 && !scanning && !checking && !repairing {
			a.startSetupScan()
			return
		}
		if x >= 406 && x <= 686 && ready && !scanning && !checking && !repairing {
			a.openSetupCalibration()
			return
		}
	}
	if view == 1 {
		if x >= contentX && y >= tableTop+tableHeaderH && y < tableTop+tableHeaderH+gateCount*gateRowH {
			i := (y - (tableTop + tableHeaderH)) / gateRowH
			if i >= 0 && i < gateCount {
				a.mu.Lock()
				a.detailGate = i
				a.detailScroll = 0
				a.detailRawExpanded = false
				a.mu.Unlock()
				procInvalidateRect.Call(a.hwnd, 0, 0)
				return
			}
		}
		if y >= actionTop && y <= actionBottom {
			if x >= 109 && x <= 389 && !checking && !repairing {
				a.startCheck()
				return
			}
			if x >= 406 && x <= 664 && !exporting && !repairing {
				a.exportDiagnostics()
				return
			}
		}
	}
	if view == 2 {
		if y >= pageTitleTop && y <= pageUnderline+3 {
			p := logPrimaryTabRect()
			if x >= int(p.Left) && x <= int(p.Right) {
				a.setHistoricalLogActive(false)
				return
			}
			if historicalOpen {
				c := logHistoricalCloseRect()
				if x >= int(c.Left) && x <= int(c.Right) && y >= int(c.Top) && y <= int(c.Bottom) {
					a.closeHistoricalMeasurement()
					return
				}
				h := logHistoricalTabRect()
				if x >= int(h.Left) && x <= int(h.Right) {
					a.setHistoricalLogActive(true)
					return
				}
			}
		}
		if historicalActive {
			if x >= contentX && y >= tableTop+tableHeaderH && y < tableTop+tableHeaderH+gateCount*gateRowH {
				i := (y - (tableTop + tableHeaderH)) / gateRowH
				if i >= 0 && i < gateCount {
					a.mu.Lock()
					a.detailGate = i
					a.detailScroll = 0
					a.detailRawExpanded = false
					a.mu.Unlock()
					procInvalidateRect.Call(a.hwnd, 0, 0)
					return
				}
			}
			if y >= actionTop && y <= actionBottom {
				if x >= 109 && x <= 409 && !exporting && !repairing {
					a.exportHistoricalMeasurement()
					return
				}
				if x >= 426 && x <= 705 {
					a.openExports()
					return
				}
			}
			return
		}
		if x >= contentX && x <= 1162 && y >= 156 && y < 156+10*35 {
			idx := scroll + (y-156)/35
			a.mu.Lock()
			if idx >= 0 && idx < len(a.logMeasurements) {
				a.logSelected = idx
			}
			a.mu.Unlock()
			procInvalidateRect.Call(a.hwnd, 0, 0)
			return
		}
		r := logDetailsButtonRect()
		if x >= int(r.Left) && x <= int(r.Right) && y >= int(r.Top) && y <= int(r.Bottom) {
			a.mu.Lock()
			idx := a.logSelected
			canOpen := idx >= 0 && idx < len(a.logMeasurements) && a.logMeasurements[idx].DetailAvailable
			a.mu.Unlock()
			if canOpen {
				a.openHistoricalMeasurement(idx)
			}
			return
		}
		if y >= actionTop && y <= actionBottom {
			if x >= 109 && x <= 409 && !exporting && !repairing {
				a.exportSelectedMeasurement()
				return
			}
			if x >= 426 && x <= 705 {
				a.openExports()
				return
			}
		}
	}
}

func (a *App) handleDoubleClick(x, y int) {
	a.mu.Lock()
	if a.currentView != 2 || a.logHistoricalActive || a.exportDialogVisible || a.repairDialogVisible || a.setupCalibrationVisible || a.setupNoticeVisible {
		a.mu.Unlock()
		return
	}
	scroll := a.logScroll
	count := len(a.logMeasurements)
	a.mu.Unlock()
	if x < contentX || x > 1162 || y < 156 || y >= 156+10*35 {
		return
	}
	idx := scroll + (y-156)/35
	if idx < 0 || idx >= count {
		return
	}
	a.mu.Lock()
	a.logSelected = idx
	available := idx < len(a.logMeasurements) && a.logMeasurements[idx].DetailAvailable
	a.mu.Unlock()
	if available {
		a.openHistoricalMeasurement(idx)
	} else {
		procInvalidateRect.Call(a.hwnd, 0, 0)
	}
}

func (a *App) copyCurrentGateDetails() {
	a.mu.Lock()
	idx := a.detailGate
	if idx < 0 || idx >= gateCount {
		a.mu.Unlock()
		return
	}
	state := a.liveGateDisplay[idx]
	ins := a.gateInspections[idx]
	if a.currentView == 2 && a.logHistoricalOpen && a.logHistoricalActive {
		if mi := measurementIndexByStamp(a.logMeasurements, a.logHistoricalStamp); mi >= 0 {
			state = a.logMeasurements[mi].GateStates[idx]
			ins = a.logMeasurements[mi].GateInspections[idx]
		}
	}
	a.mu.Unlock()
	var b strings.Builder
	fmt.Fprintf(&b, "%s\r\n%s\r\n%s\r\n", gateName(idx), trf("popover.copy.status", "status", gateStatusText(state)), ins.GateDetail)
	for _, c := range ins.Checks {
		fmt.Fprintf(&b, "[%s] %s\r\n%s\r\n", findingStatusText(c.Status), c.Check, trf("popover.copy.actual", "value", c.Actual))
		if c.Expected != "" {
			fmt.Fprintf(&b, "%s\r\n", trf("popover.copy.expected", "value", c.Expected))
		}
		if c.Detail != "" {
			fmt.Fprintf(&b, "%s\r\n", trf("popover.copy.detail", "value", c.Detail))
		}
		if c.Section != "" {
			fmt.Fprintf(&b, "%s\r\n", trf("popover.copy.section", "value", c.Section))
		}
	}
	if err := setClipboardText(a.hwnd, b.String()); err != nil {
		messageBox(a.hwnd, tr("clipboard.title"), trf("error.clipboard", "error", err.Error()), mbOK|mbIconError)
	}
}

func setClipboardText(owner uintptr, value string) error {
	open := user32.NewProc("OpenClipboard")
	closep := user32.NewProc("CloseClipboard")
	empty := user32.NewProc("EmptyClipboard")
	set := user32.NewProc("SetClipboardData")
	galloc := kernel32.NewProc("GlobalAlloc")
	glock := kernel32.NewProc("GlobalLock")
	gunlock := kernel32.NewProc("GlobalUnlock")
	if r, _, e := open.Call(owner); r == 0 {
		return fmt.Errorf("OpenClipboard: %v", e)
	}
	defer closep.Call()
	empty.Call()
	u, _ := syscall.UTF16FromString(value)
	bytes := uintptr(len(u) * 2)
	h, _, e := galloc.Call(0x0042, bytes)
	if h == 0 {
		return fmt.Errorf("GlobalAlloc: %v", e)
	}
	p, _, e := glock.Call(h)
	if p == 0 {
		return fmt.Errorf("GlobalLock: %v", e)
	}
	move := kernel32.NewProc("RtlMoveMemory")
	move.Call(p, uintptr(unsafe.Pointer(&u[0])), bytes)
	gunlock.Call(h)
	if r, _, e := set.Call(13, h); r == 0 {
		return fmt.Errorf("SetClipboardData: %v", e)
	}
	return nil
}

func (a *App) addTray() {
	a.setTray(nimAdd, a.iconIdle, tr("tray.tip.unchecked"))
}

func (a *App) removeTray() {
	var n notifyIconData
	n.CbSize = uint32(unsafe.Sizeof(n))
	n.HWnd = a.hwnd
	n.UID = 1
	procShellNotifyIconW.Call(nimDelete, uintptr(unsafe.Pointer(&n)))
}

func (a *App) setTray(op uint32, icon uintptr, tip string) bool {
	var n notifyIconData
	n.CbSize = uint32(unsafe.Sizeof(n))
	n.HWnd = a.hwnd
	n.UID = 1
	n.UFlags = nifMessage | nifIcon | nifTip
	n.UCallbackMessage = wmTray
	n.HIcon = icon
	u, _ := syscall.UTF16FromString(tip)
	copy(n.SzTip[:], u)
	r, _, _ := procShellNotifyIconW.Call(uintptr(op), uintptr(unsafe.Pointer(&n)))
	ok := r != 0
	a.debugf("tray update op=%d tip=%q ok=%t", op, tip, ok)
	return ok
}

func (a *App) showWindow() {
	procShowWindow.Call(a.hwnd, swRestore)
	procSetForegroundWindow.Call(a.hwnd)
}

const (
	trayMenuHeaderID    = 1900
	trayMenuSeparatorID = 1901
	trayMenuShowID      = 1005
)

const (
	trayMenuEntryHeader = iota
	trayMenuEntryAction
	trayMenuEntrySeparator
)

type trayMenuEntry struct {
	id      uint32
	kind    int
	enabled bool
}

func trayMenuLabel(id uint32) string {
	switch id {
	case trayMenuShowID:
		return tr("tray.menu.show")
	case 1001:
		return tr("tray.menu.check")
	case 1002:
		return tr("tray.menu.result")
	case 1003:
		return tr("tray.menu.logs")
	case 1004:
		return tr("tray.menu.export")
	case 1099:
		return tr("tray.menu.exit")
	default:
		return ""
	}
}

func (a *App) trayMenuEntries() []trayMenuEntry {
	a.mu.Lock()
	hasResult := !a.lastCheck.IsZero()
	checking := a.checking
	exporting := a.exporting
	repairing := a.repairing
	a.mu.Unlock()
	return []trayMenuEntry{
		{id: trayMenuHeaderID, kind: trayMenuEntryHeader, enabled: false},
		{id: trayMenuShowID, kind: trayMenuEntryAction, enabled: true},
		{id: 1001, kind: trayMenuEntryAction, enabled: !(checking || repairing)},
		{id: 1002, kind: trayMenuEntryAction, enabled: hasResult},
		{id: 1003, kind: trayMenuEntryAction, enabled: true},
		{id: 1004, kind: trayMenuEntryAction, enabled: !(exporting || repairing)},
		{id: trayMenuSeparatorID, kind: trayMenuEntrySeparator, enabled: false},
		{id: 1099, kind: trayMenuEntryAction, enabled: !repairing},
	}
}

func (a *App) trayMenuMetrics() (width, pad, headerH, rowH, sepH, totalH int) {
	width = scaleDPI(278, a.dpi)
	pad = scaleDPI(8, a.dpi)
	headerH = scaleDPI(52, a.dpi)
	rowH = scaleDPI(38, a.dpi)
	sepH = scaleDPI(12, a.dpi)
	totalH = pad
	for _, e := range a.trayMenuEntries() {
		switch e.kind {
		case trayMenuEntryHeader:
			totalH += headerH
		case trayMenuEntrySeparator:
			totalH += sepH
		default:
			totalH += rowH
		}
	}
	totalH += pad
	return
}

func (a *App) trayMenuEntryRect(index int) rect {
	width, pad, headerH, rowH, sepH, _ := a.trayMenuMetrics()
	entries := a.trayMenuEntries()
	y := int32(pad)
	for i, e := range entries {
		h := rowH
		if e.kind == trayMenuEntryHeader {
			h = headerH
		} else if e.kind == trayMenuEntrySeparator {
			h = sepH
		}
		r := rect{Left: int32(pad), Top: y, Right: int32(width - pad), Bottom: y + int32(h)}
		if i == index {
			return r
		}
		y += int32(h)
	}
	return rect{}
}

func (a *App) trayMenuActionAt(x, y int32) int {
	entries := a.trayMenuEntries()
	for i, e := range entries {
		if e.kind != trayMenuEntryAction || !e.enabled {
			continue
		}
		if pointInRect(a.trayMenuEntryRect(i), x, y) {
			return i
		}
	}
	return -1
}

func (a *App) drawTrayMenuActionIcon(hdc uintptr, id uint32, r rect, color uintptr, disabled bool) {
	drawIcon := func(icon uintptr) {
		if icon == 0 {
			return
		}
		procDrawIconEx.Call(hdc, uintptr(r.Left), uintptr(r.Top), icon, uintptr(int(r.Right-r.Left)), uintptr(int(r.Bottom-r.Top)), 0, 0, diNormal)
	}
	muted := disabled
	switch id {
	case trayMenuShowID:
		drawIcon(a.iconAppSmall)
	case 1001:
		if muted {
			drawIcon(a.sidebarIcons[1][0])
		} else {
			drawIcon(a.sidebarIcons[1][1])
		}
	case 1002:
		a.mu.Lock()
		hasResult := !a.lastCheck.IsZero()
		overall := a.overall
		a.mu.Unlock()
		if !hasResult {
			drawIcon(a.iconIdle)
			return
		}
		switch overall {
		case overallHealthy:
			drawIcon(a.iconPass)
		case overallFailed:
			drawIcon(a.iconFail)
		default:
			drawIcon(a.iconIdle)
		}
	case 1003:
		if muted {
			drawIcon(a.sidebarIcons[2][0])
		} else {
			drawIcon(a.sidebarIcons[2][1])
		}
	case 1004:
		drawExportPackageIcon(hdc, r, color)
	case 1099:
		line(hdc, int(r.Left)+3, int(r.Top)+3, int(r.Right)-3, int(r.Bottom)-3, 2, color)
		line(hdc, int(r.Left)+3, int(r.Bottom)-3, int(r.Right)-3, int(r.Top)+3, 2, color)
	}
}

func mousePointFromLParam(lParam uintptr) (int32, int32) {
	x := int32(int16(uint16(lParam & 0xFFFF)))
	y := int32(int16(uint16((lParam >> 16) & 0xFFFF)))
	return x, y
}

func (a *App) paintTrayMenuWindow(hwnd uintptr) {
	var ps paintStruct
	hdc, _, _ := procBeginPaint.Call(hwnd, uintptr(unsafe.Pointer(&ps)))
	if hdc == 0 {
		return
	}
	defer procEndPaint.Call(hwnd, uintptr(unsafe.Pointer(&ps)))
	var cr rect
	procGetClientRect.Call(hwnd, uintptr(unsafe.Pointer(&cr)))
	width, _, _, _, _, _ := a.trayMenuMetrics()
	_ = width
	radius := int32(scaleDPI(14, a.dpi))
	roundBox(hdc, rect{Left: 0, Top: 0, Right: cr.Right, Bottom: cr.Bottom}, radius, colors.surface, colors.border, 1)
	entries := a.trayMenuEntries()
	for i, e := range entries {
		r := a.trayMenuEntryRect(i)
		switch e.kind {
		case trayMenuEntrySeparator:
			y := int((r.Top + r.Bottom) / 2)
			line(hdc, int(r.Left)+10, y, int(r.Right)-10, y, 1, colors.border)
		case trayMenuEntryHeader:
			fill(hdc, r, colors.surface2)
			line(hdc, int(r.Left)+8, int(r.Bottom)-1, int(r.Right)-8, int(r.Bottom)-1, 1, colors.border)
			iconX := int(r.Left) + 12
			iconY := int(r.Top) + 12
			procDrawIconEx.Call(hdc, uintptr(iconX), uintptr(iconY), a.iconAppSmall, uintptr(scaleDPI(20, a.dpi)), uintptr(scaleDPI(20, a.dpi)), 0, 0, diNormal)
			text(hdc, a.fontBodySemi, tr("app.brand.primary"), rect{r.Left + 42, r.Top + 8, r.Right - 10, r.Top + 26}, colors.green, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
			text(hdc, a.fontTiny, tr("app.brand.secondary"), rect{r.Left + 42, r.Top + 24, r.Right - 10, r.Bottom - int32(7)}, colors.text2, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		case trayMenuEntryAction:
			hovered := i == a.trayMenuHover && e.enabled
			pressed := i == a.trayMenuPressed && e.enabled
			bg := colors.surface
			if hovered {
				bg = colors.hover
			}
			if pressed {
				bg = colors.selected
			}
			fill(hdc, r, bg)
			if hovered || pressed {
				fill(hdc, rect{r.Left, r.Top + 5, r.Left + 3, r.Bottom - 5}, colors.green)
			}
			line(hdc, int(r.Left)+8, int(r.Bottom)-1, int(r.Right)-8, int(r.Bottom)-1, 1, colors.border)
			iconColor := colors.text2
			textColor := colors.text
			if !e.enabled {
				iconColor = colors.muted
				textColor = colors.muted
			} else if hovered || pressed {
				iconColor = colors.green
			}
			iconR := rect{r.Left + 12, r.Top + 10, r.Left + 28, r.Top + 26}
			a.drawTrayMenuActionIcon(hdc, e.id, iconR, iconColor, !e.enabled)
			text(hdc, a.fontBody, trayMenuLabel(e.id), rect{r.Left + 38, r.Top + 1, r.Right - 10, r.Bottom - 1}, textColor, dtLeft|dtVCenter|dtSingleLine|dtNoPrefix)
		}
	}
}

func (a *App) executeTrayMenuCommand(cmd uint32) {
	switch cmd {
	case trayMenuShowID:
		a.showWindow()
	case 1001:
		a.startCheck()
	case 1002:
		a.mu.Lock()
		a.currentView = 0
		a.mu.Unlock()
		a.showWindow()
		procInvalidateRect.Call(a.hwnd, 0, 0)
	case 1003:
		a.mu.Lock()
		a.currentView = 1
		a.mu.Unlock()
		a.refreshMeasurementsAsync()
		a.showWindow()
	case 1004:
		a.exportDiagnostics()
	case 1099:
		a.quit()
	}
}

func (a *App) closeTrayMenuWindow() {
	if a.trayMenuHwnd == 0 {
		return
	}
	procDestroyWindow.Call(a.trayMenuHwnd)
}

func (a *App) handleTrayPopupWndProc(hwnd uintptr, m uint32, wParam, lParam uintptr) uintptr {
	switch m {
	case wmEraseBkgnd:
		return 1
	case wmPaint:
		a.paintTrayMenuWindow(hwnd)
		return 0
	case wmMouseMove:
		x, y := mousePointFromLParam(lParam)
		hover := a.trayMenuActionAt(x, y)
		if hover != a.trayMenuHover {
			a.trayMenuHover = hover
			procInvalidateRect.Call(hwnd, 0, 0)
		}
		return 0
	case wmLButtonDown:
		x, y := mousePointFromLParam(lParam)
		a.trayMenuPressed = a.trayMenuActionAt(x, y)
		if a.trayMenuPressed >= 0 {
			a.trayMenuHover = a.trayMenuPressed
			procInvalidateRect.Call(hwnd, 0, 0)
		}
		return 0
	case wmLButtonUp:
		x, y := mousePointFromLParam(lParam)
		hit := a.trayMenuActionAt(x, y)
		pressed := a.trayMenuPressed
		a.trayMenuPressed = -1
		procInvalidateRect.Call(hwnd, 0, 0)
		if pressed >= 0 && pressed == hit {
			entries := a.trayMenuEntries()
			if pressed < len(entries) {
				cmd := entries[pressed].id
				a.closeTrayMenuWindow()
				a.executeTrayMenuCommand(cmd)
			}
		}
		return 0
	case wmRButtonDown, wmRButtonUp, wmClose:
		a.closeTrayMenuWindow()
		return 0
	case wmKillFocus:
		a.closeTrayMenuWindow()
		return 0
	case wmActivate:
		if uint32(wParam&0xFFFF) == waInactive {
			a.closeTrayMenuWindow()
			return 0
		}
	case wmKeyDown:
		if wParam == vkEscape {
			a.closeTrayMenuWindow()
			return 0
		}
	case wmDestroy:
		if a.trayMenuHwnd == hwnd {
			a.trayMenuHwnd = 0
		}
		a.trayMenuHover = -1
		a.trayMenuPressed = -1
		return 0
	}
	r, _, _ := procDefWindowProcW.Call(hwnd, uintptr(m), wParam, lParam)
	return r
}

func (a *App) showTrayMenu() {
	if a.trayMenuHwnd != 0 {
		a.closeTrayMenuWindow()
		return
	}
	width, _, _, _, _, totalH := a.trayMenuMetrics()
	var p point
	procGetCursorPos.Call(uintptr(unsafe.Pointer(&p)))
	sw, _, _ := procGetSystemMetrics.Call(0)
	sh, _, _ := procGetSystemMetrics.Call(1)
	x := int(p.X) - width/2
	y := int(p.Y) - totalH + scaleDPI(4, a.dpi)
	margin := scaleDPI(6, a.dpi)
	if x+width+margin > int(sw) {
		x = int(sw) - width - margin
	}
	if x < margin {
		x = margin
	}
	if y+totalH+margin > int(sh) {
		y = int(sh) - totalH - margin
	}
	if y < margin {
		y = margin
	}
	hInst, _, _ := procGetModuleHandleWCompat()
	a.trayMenuHover = -1
	a.trayMenuPressed = -1
	hwnd, _, _ := procCreateWindowExW.Call(
		wsExToolWindow|wsExTopmost,
		uintptr(unsafe.Pointer(utf16(trayMenuWindowClass))),
		0,
		wsPopup|wsVisible,
		uintptr(int32(x)), uintptr(int32(y)), uintptr(int32(width)), uintptr(int32(totalH)),
		a.hwnd, 0, hInst, 0,
	)
	if hwnd == 0 {
		return
	}
	a.trayMenuHwnd = hwnd
	radius := scaleDPI(16, a.dpi)
	rgn, _, _ := procCreateRoundRectRgn.Call(0, 0, uintptr(width+1), uintptr(totalH+1), uintptr(radius), uintptr(radius))
	if rgn != 0 {
		procSetWindowRgn.Call(hwnd, rgn, 1)
	}
	procSetForegroundWindow.Call(hwnd)
	procShowWindow.Call(hwnd, swShow)
	procUpdateWindow.Call(hwnd)
}

func (a *App) quit() {
	a.mu.Lock()
	if a.quitting {
		a.mu.Unlock()
		return
	}
	a.quitting = true
	a.mu.Unlock()
	a.removeTray()
	user32.NewProc("DestroyWindow").Call(a.hwnd)
}

func (a *App) cleanupGDI() {
	for _, h := range []uintptr{
		a.fontTitle, a.fontSubtitle, a.fontH1, a.fontBody, a.fontBodySemi, a.fontSmall, a.fontTiny,
		a.fontBrand, a.fontOverall, a.fontRuntime, a.fontAction, a.fontActionIcon, a.fontNav, a.fontDetailClose,
	} {
		if h != 0 {
			procDeleteObject.Call(h)
		}
	}
}

func openFolder(path string) {
	if path == "" {
		return
	}
	procShellExecuteW.Call(0, uintptr(unsafe.Pointer(utf16("open"))), uintptr(unsafe.Pointer(utf16("explorer.exe"))), uintptr(unsafe.Pointer(utf16(path))), 0, swShow)
}

func ensureDir(path string) error { return os.MkdirAll(path, 0755) }
