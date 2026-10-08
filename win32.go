//go:build windows

package main

import (
	"fmt"
	"strings"
	"syscall"
	"unsafe"
)

var (
	user32   = syscall.NewLazyDLL("user32.dll")
	gdi32    = syscall.NewLazyDLL("gdi32.dll")
	shell32  = syscall.NewLazyDLL("shell32.dll")
	kernel32 = syscall.NewLazyDLL("kernel32.dll")
	setupapi = syscall.NewLazyDLL("setupapi.dll")
	dwmapi   = syscall.NewLazyDLL("dwmapi.dll")
	msimg32  = syscall.NewLazyDLL("msimg32.dll")

	procRegisterClassExW             = user32.NewProc("RegisterClassExW")
	procCreateWindowExW              = user32.NewProc("CreateWindowExW")
	procDefWindowProcW               = user32.NewProc("DefWindowProcW")
	procShowWindow                   = user32.NewProc("ShowWindow")
	procUpdateWindow                 = user32.NewProc("UpdateWindow")
	procDestroyWindow                = user32.NewProc("DestroyWindow")
	procSetWindowRgn                 = user32.NewProc("SetWindowRgn")
	procGetMessageW                  = user32.NewProc("GetMessageW")
	procTranslateMessage             = user32.NewProc("TranslateMessage")
	procDispatchMessageW             = user32.NewProc("DispatchMessageW")
	procPostQuitMessage              = user32.NewProc("PostQuitMessage")
	procBeginPaint                   = user32.NewProc("BeginPaint")
	procEndPaint                     = user32.NewProc("EndPaint")
	procGetClientRect                = user32.NewProc("GetClientRect")
	procInvalidateRect               = user32.NewProc("InvalidateRect")
	procLoadCursorW                  = user32.NewProc("LoadCursorW")
	procLoadImageW                   = user32.NewProc("LoadImageW")
	procSetForegroundWindow          = user32.NewProc("SetForegroundWindow")
	procFindWindowW                  = user32.NewProc("FindWindowW")
	procPostMessageW                 = user32.NewProc("PostMessageW")
	procMessageBoxW                  = user32.NewProc("MessageBoxW")
	procGetDpiForSystem              = user32.NewProc("GetDpiForSystem")
	procSetProcessDPIAware           = user32.NewProc("SetProcessDPIAware")
	procGetCursorPos                 = user32.NewProc("GetCursorPos")
	procAdjustWindowRectEx           = user32.NewProc("AdjustWindowRectEx")
	procGetSystemMetrics             = user32.NewProc("GetSystemMetrics")
	procScreenToClient               = user32.NewProc("ScreenToClient")
	procTrackPopupMenu               = user32.NewProc("TrackPopupMenu")
	procCreatePopupMenu              = user32.NewProc("CreatePopupMenu")
	procAppendMenuW                  = user32.NewProc("AppendMenuW")
	procDestroyMenu                  = user32.NewProc("DestroyMenu")
	procTrackMouseEvent              = user32.NewProc("TrackMouseEvent")
	procSetCapture                   = user32.NewProc("SetCapture")
	procReleaseCapture               = user32.NewProc("ReleaseCapture")
	procSetTimer                     = user32.NewProc("SetTimer")
	procKillTimer                    = user32.NewProc("KillTimer")
	procRegisterDeviceNotificationW  = user32.NewProc("RegisterDeviceNotificationW")
	procUnregisterDeviceNotification = user32.NewProc("UnregisterDeviceNotification")

	procCreateSolidBrush       = gdi32.NewProc("CreateSolidBrush")
	procDeleteObject           = gdi32.NewProc("DeleteObject")
	procCreateRoundRectRgn     = gdi32.NewProc("CreateRoundRectRgn")
	procFillRect               = user32.NewProc("FillRect")
	procCreatePen              = gdi32.NewProc("CreatePen")
	procSelectObject           = gdi32.NewProc("SelectObject")
	procRectangle              = gdi32.NewProc("Rectangle")
	procRoundRect              = gdi32.NewProc("RoundRect")
	procMoveToEx               = gdi32.NewProc("MoveToEx")
	procLineTo                 = gdi32.NewProc("LineTo")
	procSetBkMode              = gdi32.NewProc("SetBkMode")
	procSetTextColor           = gdi32.NewProc("SetTextColor")
	procDrawTextW              = user32.NewProc("DrawTextW")
	procCreateFontW            = gdi32.NewProc("CreateFontW")
	procDrawIconEx             = user32.NewProc("DrawIconEx")
	procCreateCompatibleDC     = gdi32.NewProc("CreateCompatibleDC")
	procCreateCompatibleBitmap = gdi32.NewProc("CreateCompatibleBitmap")
	procDeleteDC               = gdi32.NewProc("DeleteDC")
	procBitBlt                 = gdi32.NewProc("BitBlt")
	procAlphaBlend             = msimg32.NewProc("AlphaBlend")
	procSaveDC                 = gdi32.NewProc("SaveDC")
	procRestoreDC              = gdi32.NewProc("RestoreDC")
	procIntersectClipRect      = gdi32.NewProc("IntersectClipRect")

	procShellNotifyIconW      = shell32.NewProc("Shell_NotifyIconW")
	procShellExecuteW         = shell32.NewProc("ShellExecuteW")
	procIsUserAnAdmin         = shell32.NewProc("IsUserAnAdmin")
	procDwmSetWindowAttribute = dwmapi.NewProc("DwmSetWindowAttribute")

	procCreateMutexW       = kernel32.NewProc("CreateMutexW")
	procCloseHandle        = kernel32.NewProc("CloseHandle")
	procGetCurrentThreadId = kernel32.NewProc("GetCurrentThreadId")
	procRtlMoveMemory      = kernel32.NewProc("RtlMoveMemory")

	procSetupDiGetClassDevsW         = setupapi.NewProc("SetupDiGetClassDevsW")
	procSetupDiEnumDeviceInfo        = setupapi.NewProc("SetupDiEnumDeviceInfo")
	procSetupDiGetDeviceInstanceIdW  = setupapi.NewProc("SetupDiGetDeviceInstanceIdW")
	procSetupDiGetDevicePropertyW    = setupapi.NewProc("SetupDiGetDevicePropertyW")
	procSetupDiDestroyDeviceInfoList = setupapi.NewProc("SetupDiDestroyDeviceInfoList")
)

const (
	mainWindowClass     = "RazerHealthMonitorMainWindow"
	modalWindowClass    = "RazerHealthMonitorModalWindow"
	trayMenuWindowClass = "RazerHealthMonitorTrayMenuWindow"
	goldenWindowStyle   = 0x00CA0000

	csHRedraw          = 0x0002
	csVRedraw          = 0x0001
	csDblClks          = 0x0008
	wsOverlappedWindow = 0x00CF0000
	wsVisible          = 0x10000000
	wsPopup            = 0x80000000
	wsExToolWindow     = 0x00000080
	wsExTopmost        = 0x00000008
	swShow             = 5
	swRestore          = 9

	wmDestroy       = 0x0002
	wmActivate      = 0x0006
	wmPaint         = 0x000F
	wmKillFocus     = 0x0008
	wmEraseBkgnd    = 0x0014
	wmClose         = 0x0010
	wmDrawItem      = 0x002B
	wmMeasureItem   = 0x002C
	wmKeyDown       = 0x0100
	wmCommand       = 0x0111
	wmTimer         = 0x0113
	wmMouseMove     = 0x0200
	wmLButtonDown   = 0x0201
	wmLButtonUp     = 0x0202
	wmLButtonDblClk = 0x0203
	wmRButtonDown   = 0x0204
	wmRButtonUp     = 0x0205
	wmMouseWheel    = 0x020A
	wmDeviceChange  = 0x0219
	wmMouseLeave    = 0x02A3
	wmApp           = 0x8000
	wmTray          = wmApp + 1
	wmRefresh       = wmApp + 2
	wmEngineDone    = wmApp + 3
	wmExportDone    = wmApp + 4
	wmRepairDone    = wmApp + 5
	wmSetupDone     = wmApp + 6

	dbtDevNodesChanged        = 0x0007
	dbtDeviceArrival          = 0x8000
	dbtDeviceRemoveComplete   = 0x8004
	dbtDevtypDeviceInterface  = 0x00000005
	deviceNotifyWindowHandle  = 0x00000000
	deviceNotifyAllInterfaces = 0x00000004

	imageIcon      = 1
	lrLoadFromFile = 0x0010
	diNormal       = 0x0003

	dtLeft       = 0x0000
	dtCenter     = 0x0001
	dtRight      = 0x0002
	dtVCenter    = 0x0004
	dtSingleLine = 0x0020
	dtWordBreak  = 0x0010
	dtNoPrefix   = 0x0800
	dtCalcRect   = 0x0400

	transparent = 1
	psSolid     = 0
	srccopy     = 0x00CC0020
	tmeLeave    = 0x00000002

	nifMessage = 0x1
	nifIcon    = 0x2
	nifTip     = 0x4
	nimAdd     = 0
	nimModify  = 1
	nimDelete  = 2

	mfString       = 0x0000
	mfGrayed       = 0x0001
	mfOwnerDraw    = 0x0100
	mfSeparator    = 0x0800
	tpmRightButton = 0x0002
	tpmReturnCmd   = 0x0100

	mbOK        = 0x00000000
	mbIconError = 0x00000010
	mbIconInfo  = 0x00000040

	vkEscape   = 0x1B
	waInactive = 0

	odtMenu     = 1
	odsSelected = 0x0001
	odsGrayed   = 0x0002
	odsDisabled = 0x0004

	errorAlreadyExists      = 183
	errorNoMoreItems        = 259
	errorInsufficientBuffer = 122

	digcfPresent      = 0x00000002
	digcfAllClasses   = 0x00000004
	devpropTypeString = 0x00000012
)

type winGUID struct {
	Data1 uint32
	Data2 uint16
	Data3 uint16
	Data4 [8]byte
}

type spDevinfoData struct {
	CbSize    uint32
	ClassGUID winGUID
	DevInst   uint32
	Reserved  uintptr
}

type devPropKey struct {
	FmtID winGUID
	PID   uint32
}

var devpkeyDeviceBusReportedDeviceDesc = devPropKey{
	FmtID: winGUID{Data1: 0x540B947E, Data2: 0x8B40, Data3: 0x45BC, Data4: [8]byte{0xA8, 0xA2, 0x6A, 0x0B, 0x89, 0x4C, 0xBD, 0xA2}},
	PID:   4,
}

type devBroadcastDeviceInterface struct {
	Size       uint32
	DeviceType uint32
	Reserved   uint32
	ClassGUID  winGUID
	Name       [1]uint16
}

func (a *App) registerDeviceNotifications() error {
	filter := devBroadcastDeviceInterface{}
	filter.Size = uint32(unsafe.Sizeof(filter))
	filter.DeviceType = dbtDevtypDeviceInterface
	h, _, err := procRegisterDeviceNotificationW.Call(
		a.hwnd,
		uintptr(unsafe.Pointer(&filter)),
		deviceNotifyWindowHandle|deviceNotifyAllInterfaces,
	)
	if h == 0 {
		return fmt.Errorf("RegisterDeviceNotificationW: %v", err)
	}
	a.deviceNotifyHandle = h
	a.debugf("DEVICE notification registered handle=0x%X allInterfaceClasses=true", h)
	return nil
}

func (a *App) unregisterDeviceNotifications() {
	if a.deviceNotifyHandle == 0 {
		return
	}
	procUnregisterDeviceNotification.Call(a.deviceNotifyHandle)
	a.debugf("DEVICE notification unregistered handle=0x%X", a.deviceNotifyHandle)
	a.deviceNotifyHandle = 0
}

func utf16(s string) *uint16 {
	p, _ := syscall.UTF16PtrFromString(s)
	return p
}

func rgb(r, g, b uint8) uintptr { return uintptr(r) | uintptr(g)<<8 | uintptr(b)<<16 }

func currentThreadID() uint32 {
	r, _, _ := procGetCurrentThreadId.Call()
	return uint32(r)
}

func loadIcon(path string, w, h int) uintptr {
	r, _, _ := procLoadImageW.Call(0, uintptr(unsafe.Pointer(utf16(path))), imageIcon, uintptr(w), uintptr(h), lrLoadFromFile)
	return r
}

func createFont(dpi, pt, weight int, face string) uintptr {
	h := -int32((pt*dpi + 36) / 72)
	r, _, _ := procCreateFontW.Call(
		uintptr(h), 0, 0, 0, uintptr(weight), 0, 0, 0,
		1, 0, 0, 5, 0, uintptr(unsafe.Pointer(utf16(face))),
	)
	return r
}

func setDarkTitlebar(hwnd uintptr) {
	value := int32(1)
	procDwmSetWindowAttribute.Call(hwnd, 20, uintptr(unsafe.Pointer(&value)), unsafe.Sizeof(value))
}

func fill(hdc uintptr, r rect, color uintptr) {
	brush, _, _ := procCreateSolidBrush.Call(color)
	if brush == 0 {
		return
	}
	defer procDeleteObject.Call(brush)
	procFillRect.Call(hdc, uintptr(unsafe.Pointer(&r)), brush)
}

func roundBox(hdc uintptr, r rect, radius int32, fillColor, borderColor uintptr, borderWidth int) {
	brush, _, _ := procCreateSolidBrush.Call(fillColor)
	pen, _, _ := procCreatePen.Call(psSolid, uintptr(borderWidth), borderColor)
	oldB, _, _ := procSelectObject.Call(hdc, brush)
	oldP, _, _ := procSelectObject.Call(hdc, pen)
	procRoundRect.Call(hdc, uintptr(r.Left), uintptr(r.Top), uintptr(r.Right), uintptr(r.Bottom), uintptr(radius), uintptr(radius))
	procSelectObject.Call(hdc, oldB)
	procSelectObject.Call(hdc, oldP)
	procDeleteObject.Call(brush)
	procDeleteObject.Call(pen)
}

func line(hdc uintptr, x1, y1, x2, y2, width int, color uintptr) {
	pen, _, _ := procCreatePen.Call(psSolid, uintptr(width), color)
	old, _, _ := procSelectObject.Call(hdc, pen)
	procMoveToEx.Call(hdc, uintptr(x1), uintptr(y1), 0)
	procLineTo.Call(hdc, uintptr(x2), uintptr(y2))
	procSelectObject.Call(hdc, old)
	procDeleteObject.Call(pen)
}

func text(hdc, font uintptr, s string, r rect, color uintptr, flags uint32) {
	if s == "" {
		return
	}
	procSetBkMode.Call(hdc, transparent)
	procSetTextColor.Call(hdc, color)
	old, _, _ := procSelectObject.Call(hdc, font)
	u, _ := syscall.UTF16FromString(s)
	procDrawTextW.Call(hdc, uintptr(unsafe.Pointer(&u[0])), uintptr(len(u)-1), uintptr(unsafe.Pointer(&r)), uintptr(flags))
	procSelectObject.Call(hdc, old)
}

func pointInRect(r rect, x, y int32) bool {
	return x >= r.Left && x < r.Right && y >= r.Top && y < r.Bottom
}

func measureSingleLineWidth(hdc, font uintptr, s string) int {
	if s == "" {
		return 0
	}
	r := rect{Left: 0, Top: 0, Right: 0, Bottom: 0}
	old, _, _ := procSelectObject.Call(hdc, font)
	u, _ := syscall.UTF16FromString(s)
	procDrawTextW.Call(hdc, uintptr(unsafe.Pointer(&u[0])), uintptr(len(u)-1), uintptr(unsafe.Pointer(&r)), uintptr(dtLeft|dtSingleLine|dtNoPrefix|dtCalcRect))
	procSelectObject.Call(hdc, old)
	return int(r.Right - r.Left)
}

func wrapTextToWidth(hdc, font uintptr, s string, width int) string {
	if width <= 0 || s == "" || measureSingleLineWidth(hdc, font, s) <= width {
		return s
	}
	runes := []rune(s)
	var out []string
	for len(runes) > 0 {
		lo, hi, best := 1, len(runes), 1
		for lo <= hi {
			mid := (lo + hi) / 2
			if measureSingleLineWidth(hdc, font, string(runes[:mid])) <= width {
				best = mid
				lo = mid + 1
			} else {
				hi = mid - 1
			}
		}
		if best >= len(runes) {
			out = append(out, string(runes))
			break
		}
		cut := best
		// Prefer a semantic separator near the measured boundary, but fall back
		// to a hard visual wrap for long unbroken paths/identifiers.
		for i := best - 1; i >= best/2; i-- {
			switch runes[i] {
			case ' ', '\\', '/', ';', '|', ',', '=':
				cut = i + 1
				i = -1
			}
		}
		part := strings.TrimRight(string(runes[:cut]), " ")
		if part == "" {
			part = string(runes[:cut])
		}
		out = append(out, part)
		runes = runes[cut:]
		for len(runes) > 0 && runes[0] == ' ' {
			runes = runes[1:]
		}
	}
	return strings.Join(out, "\n")
}

func measureWrappedTextHeight(hdc, font uintptr, s string, width int) int {
	if strings.TrimSpace(s) == "" || width <= 0 {
		return 0
	}
	r := rect{Left: 0, Top: 0, Right: int32(width), Bottom: 0}
	procSetBkMode.Call(hdc, transparent)
	old, _, _ := procSelectObject.Call(hdc, font)
	u, _ := syscall.UTF16FromString(s)
	procDrawTextW.Call(hdc, uintptr(unsafe.Pointer(&u[0])), uintptr(len(u)-1), uintptr(unsafe.Pointer(&r)), uintptr(dtLeft|dtWordBreak|dtNoPrefix|dtCalcRect))
	procSelectObject.Call(hdc, old)
	h := int(r.Bottom - r.Top)
	if h < 16 {
		h = 16
	}
	return h
}

func drawIcon(hdc, icon uintptr, x, y, w, h int) {
	if icon == 0 {
		return
	}
	procDrawIconEx.Call(hdc, uintptr(x), uintptr(y), icon, uintptr(w), uintptr(h), 0, 0, diNormal)
}

func messageBox(hwnd uintptr, title, body string, flags uintptr) {
	procMessageBoxW.Call(hwnd, uintptr(unsafe.Pointer(utf16(body))), uintptr(unsafe.Pointer(utf16(title))), flags)
}

func activateExistingInstance() {
	hwnd, _, _ := procFindWindowW.Call(uintptr(unsafe.Pointer(utf16(mainWindowClass))), 0)
	if hwnd != 0 {
		procShowWindow.Call(hwnd, swRestore)
		procSetForegroundWindow.Call(hwnd)
	}
}

func acquireSingleInstance() (uintptr, bool, error) {
	name := utf16(`Local\RazerSynapseChromaHealthMonitor.SingleInstance`)
	h, _, e := procCreateMutexW.Call(0, 0, uintptr(unsafe.Pointer(name)))
	if h == 0 {
		return 0, false, fmt.Errorf("CreateMutexW: %v", e)
	}
	already := e == syscall.Errno(errorAlreadyExists)
	return h, already, nil
}

func hiword(v uintptr) int16 { return int16((v >> 16) & 0xffff) }
func loword(v uintptr) int16 { return int16(v & 0xffff) }
