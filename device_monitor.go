//go:build windows

package main

import (
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

const setupLiveProbeVersion = "1.1.0"
const setupLiveRefreshTimerID = 2

const (
	setupWirelessFlowEventTransition = "event-transition"
	setupWirelessFlowUserConfirm     = "user-confirmation"
)

type SetupLiveProbeError struct {
	Stage   string `json:"stage"`
	Type    string `json:"type,omitempty"`
	Message string `json:"message,omitempty"`
}

type SetupLiveConnection struct {
	PID                string `json:"pid"`
	Present            bool   `json:"present"`
	ProductKey         string `json:"productKey,omitempty"`
	ProductName        string `json:"productName,omitempty"`
	DeviceClass        string `json:"deviceClass,omitempty"`
	IdentitySource     string `json:"identitySource,omitempty"`
	IdentityConfidence string `json:"identityConfidence,omitempty"`
	IdentityVerified   bool   `json:"identityVerified"`
	ExplicitRole       string `json:"explicitRole,omitempty"`
	RootInstanceID     string `json:"rootInstanceId,omitempty"`
}

type SetupLiveProbeResult struct {
	SchemaVersion      int                   `json:"schemaVersion"`
	ToolVersion        string                `json:"toolVersion"`
	ProbeVersion       string                `json:"probeVersion"`
	Implementation     string                `json:"implementation,omitempty"`
	CreatedAt          time.Time             `json:"createdAt"`
	ElapsedMS          int                   `json:"elapsedMs"`
	VendorID           string                `json:"vendorId"`
	Mode               string                `json:"mode"`
	TargetProductKey   string                `json:"targetProductKey,omitempty"`
	RequestedPIDs      []string              `json:"requestedPids,omitempty"`
	EnumeratedUSBNodes int                   `json:"enumeratedUsbNodes,omitempty"`
	MatchedRazerRoots  int                   `json:"matchedRazerRoots,omitempty"`
	Connections        []SetupLiveConnection `json:"connections"`
	Errors             []SetupLiveProbeError `json:"errors,omitempty"`
}

func (r SetupLiveProbeResult) valid() bool {
	if r.SchemaVersion != 1 || r.ProbeVersion != setupLiveProbeVersion || !strings.EqualFold(strings.TrimSpace(r.VendorID), "1532") {
		return false
	}
	for _, c := range r.Connections {
		if !validInventoryPID(c.PID) {
			return false
		}
		if c.DeviceClass != "" {
			switch strings.ToLower(strings.TrimSpace(c.DeviceClass)) {
			case "mouse", "keyboard", "device":
			default:
				return false
			}
		}
	}
	return true
}

func (a *App) knownSetupPIDsLocked() []string {
	set := map[string]bool{}
	for _, c := range a.inventory.Connections {
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		if validInventoryPID(pid) {
			set[pid] = true
		}
	}
	out := make([]string, 0, len(set))
	for pid := range set {
		out = append(out, pid)
	}
	sort.Strings(out)
	return out
}

var (
	liveGenericNameRE  = regexp.MustCompile(`(?i)^(USB Composite Device|USB Input Device|HID-compliant .+|HID Keyboard Device|Razer Control Device|\(Standard .+\)|Microsoft)$`)
	liveRazerWordRE    = regexp.MustCompile(`(?i)\brazer\b`)
	liveRoleTextRE     = regexp.MustCompile(`(?i)\b(?:wireless usb dongle|usb dongle|dongle|receiver|wired usb|wired|usb cable|cable)\b`)
	liveWirelessRoleRE = regexp.MustCompile(`(?i)\b(?:wireless usb dongle|usb dongle|dongle|receiver|wireless connection)\b`)
	liveWiredRoleRE    = regexp.MustCompile(`(?i)\b(?:wired usb|usb cable|cable connection|wired connection)\b`)
	liveNonAlphaNumRE  = regexp.MustCompile(`[^a-z0-9]+`)
	liveSpacesRE       = regexp.MustCompile(`\s+`)
)

func cleanLiveProductName(value string) string {
	s := strings.TrimSpace(value)
	if strings.HasPrefix(s, "@") {
		if i := strings.IndexByte(s, ';'); i >= 0 {
			s = s[i+1:]
		}
	}
	if strings.HasPrefix(strings.ToLower(s), "razer inc.") {
		s = "Razer " + strings.TrimSpace(s[len("Razer Inc."):])
	}
	return strings.TrimSpace(s)
}

func normalizeLiveProductIdentity(value string) string {
	s := cleanLiveProductName(value)
	if s == "" || liveGenericNameRE.MatchString(s) {
		return ""
	}
	s = strings.ToLower(s)
	// Keep this normalization aligned with the Setup Scanner's PID-free product
	// identity rules. Connection-role words are transport evidence, not identity.
	s = liveRazerWordRE.ReplaceAllString(s, "")
	s = liveRoleTextRE.ReplaceAllString(s, "")
	s = liveNonAlphaNumRE.ReplaceAllString(s, " ")
	return strings.TrimSpace(liveSpacesRE.ReplaceAllString(s, " "))
}

func liveExplicitRole(value string) string {
	s := strings.ToLower(cleanLiveProductName(value))
	if liveWirelessRoleRE.MatchString(s) {
		return "wireless-dongle"
	}
	if liveWiredRoleRE.MatchString(s) {
		return "wired-usb"
	}
	return ""
}

func utf16SliceString(buf []uint16) string {
	for i, v := range buf {
		if v == 0 {
			buf = buf[:i]
			break
		}
	}
	return string(syscall.UTF16ToString(buf))
}

func setupDiDeviceInstanceID(set uintptr, data *spDevinfoData) (string, error) {
	buf := make([]uint16, 512)
	var required uint32
	for attempt := 0; attempt < 2; attempt++ {
		r, _, callErr := procSetupDiGetDeviceInstanceIdW.Call(
			set,
			uintptr(unsafe.Pointer(data)),
			uintptr(unsafe.Pointer(&buf[0])),
			uintptr(len(buf)),
			uintptr(unsafe.Pointer(&required)),
		)
		if r != 0 {
			return utf16SliceString(buf), nil
		}
		errno, _ := callErr.(syscall.Errno)
		if errno == syscall.Errno(errorInsufficientBuffer) && required > uint32(len(buf)) {
			buf = make([]uint16, required+1)
			continue
		}
		return "", fmt.Errorf("SetupDiGetDeviceInstanceIdW: %v", callErr)
	}
	return "", errors.New("SetupDiGetDeviceInstanceIdW: buffer retry exhausted")
}

func setupDiStringProperty(set uintptr, data *spDevinfoData, key *devPropKey) (string, error) {
	buf := make([]uint16, 512)
	var propType uint32
	var required uint32
	for attempt := 0; attempt < 2; attempt++ {
		r, _, callErr := procSetupDiGetDevicePropertyW.Call(
			set,
			uintptr(unsafe.Pointer(data)),
			uintptr(unsafe.Pointer(key)),
			uintptr(unsafe.Pointer(&propType)),
			uintptr(unsafe.Pointer(&buf[0])),
			uintptr(len(buf)*2),
			uintptr(unsafe.Pointer(&required)),
			0,
		)
		if r != 0 {
			if propType != devpropTypeString {
				return "", fmt.Errorf("SetupDiGetDevicePropertyW: unexpected property type 0x%X", propType)
			}
			return utf16SliceString(buf), nil
		}
		errno, _ := callErr.(syscall.Errno)
		if errno == syscall.Errno(errorInsufficientBuffer) && required > uint32(len(buf)*2) {
			buf = make([]uint16, int(required/2)+2)
			continue
		}
		return "", fmt.Errorf("SetupDiGetDevicePropertyW: %v", callErr)
	}
	return "", errors.New("SetupDiGetDevicePropertyW: buffer retry exhausted")
}

func razerUSBRootPID(instanceID string) (string, bool) {
	id := strings.ToUpper(strings.TrimSpace(instanceID))
	const prefix = `USB\VID_1532&PID_`
	if !strings.HasPrefix(id, prefix) || len(id) < len(prefix)+5 {
		return "", false
	}
	pid := id[len(prefix) : len(prefix)+4]
	if !validInventoryPID(pid) || id[len(prefix)+4] != '\\' {
		// USB interface nodes include &MI_xx and are deliberately ignored. The
		// product identity belongs to the physical USB root connection.
		return "", false
	}
	return pid, true
}

func (a *App) persistSetupLiveProbeResult(result SetupLiveProbeResult) {
	b, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		a.debugf("SETUP live probe diagnostic marshal failed err=%v", err)
		return
	}
	latest := filepath.Join(a.setupDir, "SetupLiveProbe-v1.1.0.json")
	if err := os.WriteFile(latest, b, 0644); err != nil {
		a.debugf("SETUP live probe diagnostic write failed err=%v", err)
	}
}

func (a *App) runSetupLiveProbe(targetProductKey string, knownPIDs []string) (SetupLiveProbeResult, error) {
	a.setupProbeMu.Lock()
	defer a.setupProbeMu.Unlock()

	started := time.Now()
	targetProductKey = strings.TrimSpace(targetProductKey)
	knownSet := map[string]bool{}
	for _, raw := range knownPIDs {
		pid := strings.ToUpper(strings.TrimSpace(raw))
		if validInventoryPID(pid) {
			knownSet[pid] = true
		}
	}
	requested := make([]string, 0, len(knownSet))
	for pid := range knownSet {
		requested = append(requested, pid)
	}
	sort.Strings(requested)

	type expectedConnection struct {
		ProductKey  string
		ProductName string
		DeviceClass string
	}
	expectedByPID := map[string]expectedConnection{}
	a.mu.Lock()
	for _, c := range a.inventory.Connections {
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		if validInventoryPID(pid) {
			expectedByPID[pid] = expectedConnection{ProductKey: c.ProductKey, ProductName: c.ModelName, DeviceClass: c.DeviceClass}
		}
	}
	a.mu.Unlock()

	result := SetupLiveProbeResult{
		SchemaVersion:    1,
		ToolVersion:      appVersion,
		ProbeVersion:     setupLiveProbeVersion,
		Implementation:   "native-setupapi-usb",
		CreatedAt:        time.Now().UTC(),
		VendorID:         "1532",
		Mode:             "known-connections",
		TargetProductKey: targetProductKey,
		RequestedPIDs:    requested,
	}
	if targetProductKey != "" {
		result.Mode = "target-product"
	}

	h, _, callErr := procSetupDiGetClassDevsW.Call(
		0,
		uintptr(unsafe.Pointer(utf16("USB"))),
		0,
		digcfPresent|digcfAllClasses,
	)
	if h == 0 || h == ^uintptr(0) {
		return result, fmt.Errorf("SetupDiGetClassDevsW USB present: %v", callErr)
	}
	defer procSetupDiDestroyDeviceInfoList.Call(h)

	foundByPID := map[string]SetupLiveConnection{}
	seenRootByPID := map[string]int{}
	for index := uint32(0); ; index++ {
		data := spDevinfoData{CbSize: uint32(unsafe.Sizeof(spDevinfoData{}))}
		r, _, enumErr := procSetupDiEnumDeviceInfo.Call(h, uintptr(index), uintptr(unsafe.Pointer(&data)))
		if r == 0 {
			errno, _ := enumErr.(syscall.Errno)
			if errno == syscall.Errno(errorNoMoreItems) {
				break
			}
			result.Errors = append(result.Errors, SetupLiveProbeError{Stage: "SetupDiEnumDeviceInfo", Type: "win32", Message: enumErr.Error()})
			break
		}
		result.EnumeratedUSBNodes++
		instanceID, err := setupDiDeviceInstanceID(h, &data)
		if err != nil {
			result.Errors = append(result.Errors, SetupLiveProbeError{Stage: "SetupDiGetDeviceInstanceIdW", Type: "win32", Message: err.Error()})
			continue
		}
		pid, root := razerUSBRootPID(instanceID)
		if !root {
			continue
		}
		if targetProductKey == "" && !knownSet[pid] {
			continue
		}
		result.MatchedRazerRoots++
		seenRootByPID[pid]++
		busName, err := setupDiStringProperty(h, &data, &devpkeyDeviceBusReportedDeviceDesc)
		if err != nil {
			result.Errors = append(result.Errors, SetupLiveProbeError{Stage: "BusReportedDeviceDesc " + instanceID, Type: "win32", Message: err.Error()})
			continue
		}
		productName := cleanLiveProductName(busName)
		productKey := normalizeLiveProductIdentity(productName)
		if targetProductKey != "" && !strings.EqualFold(productKey, targetProductKey) {
			continue
		}
		expected := expectedByPID[pid]
		verified := productKey != ""
		if targetProductKey == "" {
			verified = verified && strings.EqualFold(strings.TrimSpace(productKey), strings.TrimSpace(expected.ProductKey))
		}
		deviceClass := normalizedDeviceClass(expected.DeviceClass)
		if deviceClass == "" {
			deviceClass = "device"
		}
		foundByPID[pid] = SetupLiveConnection{
			PID:                pid,
			Present:            true,
			ProductKey:         productKey,
			ProductName:        firstNonEmpty(productName, expected.ProductName),
			DeviceClass:        deviceClass,
			IdentitySource:     "bus-reported-device-description",
			IdentityConfidence: "high",
			IdentityVerified:   verified,
			ExplicitRole:       liveExplicitRole(productName),
			RootInstanceID:     instanceID,
		}
	}

	if targetProductKey != "" {
		pids := make([]string, 0, len(foundByPID))
		for pid := range foundByPID {
			pids = append(pids, pid)
		}
		sort.Strings(pids)
		for _, pid := range pids {
			result.Connections = append(result.Connections, foundByPID[pid])
		}
	} else {
		for _, pid := range requested {
			if c, ok := foundByPID[pid]; ok {
				result.Connections = append(result.Connections, c)
				continue
			}
			result.Connections = append(result.Connections, SetupLiveConnection{
				PID:                pid,
				Present:            false,
				DeviceClass:        "device",
				IdentitySource:     "not-present",
				IdentityConfidence: "none",
			})
		}
	}
	for pid, count := range seenRootByPID {
		if count > 1 {
			result.Errors = append(result.Errors, SetupLiveProbeError{Stage: "duplicate-root " + pid, Type: "ambiguous", Message: fmt.Sprintf("%d present physical USB roots share the same Razer PID", count)})
		}
	}
	result.ElapsedMS = int(time.Since(started).Milliseconds())
	result.CreatedAt = time.Now().UTC()
	a.persistSetupLiveProbeResult(result)
	present := sortedPIDSet(livePIDSet(result))
	a.debugf("SETUP native live probe complete mode=%s target=%q requested=%v present=%v usbNodes=%d matchedRoots=%d elapsedMs=%d errors=%d", result.Mode, targetProductKey, requested, present, result.EnumeratedUSBNodes, result.MatchedRazerRoots, result.ElapsedMS, len(result.Errors))
	if !result.valid() {
		return result, errors.New("native live probe returned an invalid result")
	}
	if len(result.Errors) > 0 {
		parts := make([]string, 0, len(result.Errors))
		for _, probeErr := range result.Errors {
			msg := strings.TrimSpace(probeErr.Message)
			if msg == "" {
				msg = strings.TrimSpace(probeErr.Stage)
			}
			if msg != "" {
				parts = append(parts, msg)
			}
		}
		return result, fmt.Errorf("live probe incomplete: %s", strings.Join(parts, "; "))
	}
	return result, nil
}

func (a *App) requestLivePresenceRefresh(reason string, delay time.Duration) {
	a.mu.Lock()
	if !a.setupReady || a.setupScanning || a.setupCalibrationVisible || len(a.inventory.Connections) == 0 {
		a.mu.Unlock()
		return
	}
	if a.setupLiveRefreshRunning {
		// A native probe is already executing. Preserve at most one follow-up
		// refresh for events that genuinely arrive during that short window.
		a.setupLiveRefreshQueued = true
		a.setupLiveRefreshReason = reason
		a.mu.Unlock()
		return
	}
	// Debounce before the probe starts. Every new PnP notification replaces the
	// pending generation, so a burst produces one probe after the quiet window
	// instead of one PowerShell process plus a queued second pass.
	a.setupLiveRefreshGeneration++
	generation := a.setupLiveRefreshGeneration
	a.setupLiveRefreshing = true
	a.setupLiveFresh = false
	a.setupLiveRefreshReason = reason
	a.mu.Unlock()
	procSetTimer.Call(a.hwnd, setupLiveRefreshTimerID, 125, 0)
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)

	go func() {
		if delay > 0 {
			time.Sleep(delay)
		}
		a.mu.Lock()
		if generation != a.setupLiveRefreshGeneration {
			a.mu.Unlock()
			return
		}
		if !a.setupReady || a.setupScanning || a.setupCalibrationVisible || len(a.inventory.Connections) == 0 {
			a.setupLiveRefreshing = false
			a.setupLiveFresh = false
			a.mu.Unlock()
			procKillTimer.Call(a.hwnd, setupLiveRefreshTimerID)
			procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
			return
		}
		a.setupLiveRefreshRunning = true
		known := a.knownSetupPIDsLocked()
		a.mu.Unlock()

		result, err := a.runSetupLiveProbe("", known)
		a.applyLivePresenceResult(result, err, reason)
	}()
}

func (a *App) applyLivePresenceResult(result SetupLiveProbeResult, err error, reason string) {
	a.mu.Lock()
	if err != nil {
		procKillTimer.Call(a.hwnd, setupLiveRefreshTimerID)
		a.setupLiveRefreshing = false
		a.setupLiveRefreshRunning = false
		a.setupLiveFresh = false
		a.setupLiveLastError = err.Error()
		queued := a.setupLiveRefreshQueued
		nextReason := a.setupLiveRefreshReason
		a.setupLiveRefreshQueued = false
		a.mu.Unlock()
		a.debugf("SETUP live presence refresh failed reason=%s implementation=%s requested=%v elapsedMs=%d err=%v", reason, result.Implementation, result.RequestedPIDs, result.ElapsedMS, err)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		if queued {
			a.requestLivePresenceRefresh(nextReason, 800*time.Millisecond)
		}
		return
	}
	byPID := make(map[string]SetupLiveConnection, len(result.Connections))
	for _, c := range result.Connections {
		byPID[strings.ToUpper(strings.TrimSpace(c.PID))] = c
	}
	verifiedPresent := 0
	presentPIDs := make([]string, 0, len(result.Connections))
	changed := make([]string, 0, len(result.Connections))
	for i := range a.inventory.Connections {
		c := &a.inventory.Connections[i]
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		wasPresent := c.PresentAtScan
		live, ok := byPID[pid]
		present := ok && live.Present && live.IdentityVerified && strings.EqualFold(strings.TrimSpace(live.ProductKey), strings.TrimSpace(c.ProductKey))
		c.PresentAtScan = present
		if wasPresent != present {
			changed = append(changed, fmt.Sprintf("%s:%t->%t", pid, wasPresent, present))
		}
		if present {
			verifiedPresent++
			presentPIDs = append(presentPIDs, pid)
			if k := strings.ToLower(strings.TrimSpace(live.DeviceClass)); k == "mouse" || k == "keyboard" {
				c.DeviceClass = k
			}
			if strings.TrimSpace(live.RootInstanceID) != "" {
				// Cache the current physical root in memory so subsequent diagnostics
				// know which concrete root was verified. Full Setup owns persistence.
				c.Topology.RootInstanceID = live.RootInstanceID
			}
		}
		if ok && live.Present && !present {
			a.debugf("SETUP live presence ignored PID=%s expectedProduct=%q observedProduct=%q verified=%t confidence=%s", pid, c.ProductKey, live.ProductKey, live.IdentityVerified, live.IdentityConfidence)
		}
	}
	sort.Strings(presentPIDs)
	sort.Strings(changed)
	for i := range a.inventory.Products {
		k := setupProductDeviceClass(a.inventory, a.inventory.Products[i])
		if k == "mouse" || k == "keyboard" {
			a.inventory.Products[i].DeviceClass = k
		}
	}
	a.setupLiveFresh = true
	a.setupLiveLast = time.Now()
	a.setupLiveLastError = ""
	procKillTimer.Call(a.hwnd, setupLiveRefreshTimerID)
	a.setupLiveRefreshing = false
	a.setupLiveRefreshRunning = false
	queued := a.setupLiveRefreshQueued
	nextReason := a.setupLiveRefreshReason
	a.setupLiveRefreshQueued = false
	a.mu.Unlock()
	a.debugf("SETUP live presence refreshed reason=%s implementation=%s requested=%v present=%v changed=%v verifiedPresent=%d usbNodes=%d matchedRoots=%d elapsedMs=%d errors=%d", reason, result.Implementation, result.RequestedPIDs, presentPIDs, changed, verifiedPresent, result.EnumeratedUSBNodes, result.MatchedRazerRoots, result.ElapsedMS, len(result.Errors))
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	if queued {
		a.requestLivePresenceRefresh(nextReason, 800*time.Millisecond)
	}
}

func (a *App) handleWindowsDeviceChange(event uint32) {
	a.debugf("DEVICE change event=0x%X", event)
	a.mu.Lock()
	visible := a.setupCalibrationVisible
	stage := a.setupCalibrationStage
	a.mu.Unlock()
	if visible && (stage == setupCalibrationWiredWaiting || stage == setupCalibrationWirelessWaiting || stage == setupCalibrationWiredVerifying || stage == setupCalibrationWirelessVerifying) {
		a.requestCalibrationVerification(800 * time.Millisecond)
		return
	}
	a.requestLivePresenceRefresh(fmt.Sprintf("device-change-0x%X", event), 800*time.Millisecond)
}

func livePIDSet(result SetupLiveProbeResult) map[string]bool {
	set := map[string]bool{}
	for _, c := range result.Connections {
		if c.Present && c.IdentityVerified {
			pid := strings.ToUpper(strings.TrimSpace(c.PID))
			if validInventoryPID(pid) {
				set[pid] = true
			}
		}
	}
	return set
}

func samePIDSet(aSet, bSet map[string]bool) bool {
	if len(aSet) != len(bSet) {
		return false
	}
	for k := range aSet {
		if !bSet[k] {
			return false
		}
	}
	return true
}

// calibrationWirelessFlowLocked derives the guided interaction model from the
// generic device profile, never from a product name or PID. A mouse can use
// cable removal itself as the intentional transition into wireless operation.
// Other/unknown device classes use an explicit user confirmation after the
// requested hardware steps; this avoids treating a permanently present dongle
// root as proof that the peripheral has already switched to wireless mode.
func (a *App) calibrationWirelessFlowLocked(product DeviceProductProfile) string {
	if setupProductDeviceClass(a.inventory, product) == "mouse" {
		return setupWirelessFlowEventTransition
	}
	return setupWirelessFlowUserConfirm
}

func (a *App) armCurrentCalibration(mode string) {
	mode = strings.ToLower(strings.TrimSpace(mode))
	if mode != "wired" && mode != "wireless" {
		return
	}
	a.mu.Lock()
	product, ok := a.calibrationCurrentProductLocked()
	if !ok || !a.setupCalibrationVisible || a.setupScanning || a.checking || a.repairing {
		a.mu.Unlock()
		return
	}
	if (mode == "wired" && a.setupCalibrationStage != setupCalibrationWiredPrompt) || (mode == "wireless" && a.setupCalibrationStage != setupCalibrationWirelessPrompt) {
		a.mu.Unlock()
		return
	}
	a.setupCalibrationGeneration++
	gen := a.setupCalibrationGeneration
	a.setupCalibrationMode = mode
	a.setupCalibrationProductKey = product.Key
	a.setupCalibrationBaseline = nil
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	a.setupCalibrationError = ""
	if mode == "wired" {
		a.setupCalibrationStage = setupCalibrationWiredPreparing
	} else {
		a.setupCalibrationStage = setupCalibrationWirelessPreparing
	}
	a.mu.Unlock()
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	go a.runCalibrationBaseline(gen, mode, product.Key)
}

func (a *App) runCalibrationBaseline(gen uint64, mode, productKey string) {
	result, err := a.runSetupLiveProbe(productKey, nil)
	a.mu.Lock()
	if gen != a.setupCalibrationGeneration || !a.setupCalibrationVisible || a.setupCalibrationMode != mode || a.setupCalibrationProductKey != productKey {
		a.mu.Unlock()
		return
	}
	if err != nil {
		a.setupCalibrationError = tr("setup.calibration.error.live_probe")
		a.restoreCalibrationPromptLocked(mode, a.setupCalibrationError)
		a.mu.Unlock()
		a.debugf("SETUP calibration baseline failed mode=%s product=%q err=%v", mode, productKey, err)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	a.setupCalibrationBaseline = livePIDSet(result)
	flow := setupWirelessFlowEventTransition
	if mode == "wired" {
		a.setupCalibrationStage = setupCalibrationWiredWaiting
	} else {
		product, ok := a.calibrationCurrentProductLocked()
		if !ok || !strings.EqualFold(strings.TrimSpace(product.Key), strings.TrimSpace(productKey)) {
			a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.target"))
			a.mu.Unlock()
			procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
			return
		}
		flow = a.calibrationWirelessFlowLocked(product)
		if flow == setupWirelessFlowUserConfirm {
			a.setupCalibrationStage = setupCalibrationWirelessConfirm
		} else {
			a.setupCalibrationStage = setupCalibrationWirelessWaiting
		}
	}
	a.mu.Unlock()
	a.debugf("SETUP calibration armed mode=%s product=%q flow=%s baseline=%v", mode, productKey, flow, sortedPIDSet(livePIDSet(result)))
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
}

func (a *App) requestCalibrationVerification(delay time.Duration) {
	a.mu.Lock()
	if !a.setupCalibrationVisible {
		a.mu.Unlock()
		return
	}
	waiting := a.setupCalibrationStage == setupCalibrationWiredWaiting || a.setupCalibrationStage == setupCalibrationWirelessWaiting
	verifying := a.setupCalibrationStage == setupCalibrationWiredVerifying || a.setupCalibrationStage == setupCalibrationWirelessVerifying
	if !waiting && !verifying {
		a.mu.Unlock()
		return
	}
	if a.setupCalibrationVerifyRunning {
		// Device arrival/removal commonly emits a short burst of WM_DEVICECHANGE
		// notifications while PnP settles. Preserve one follow-up verification so
		// an early probe cannot strand the wizard in a waiting state.
		a.setupCalibrationVerifyQueued = true
		a.mu.Unlock()
		return
	}
	if verifying {
		a.mu.Unlock()
		return
	}
	a.setupCalibrationVerifyRunning = true
	mode := a.setupCalibrationMode
	productKey := a.setupCalibrationProductKey
	gen := a.setupCalibrationGeneration
	if mode == "wired" {
		a.setupCalibrationStage = setupCalibrationWiredVerifying
	} else {
		a.setupCalibrationStage = setupCalibrationWirelessVerifying
	}
	a.mu.Unlock()
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	go func() {
		if delay > 0 {
			time.Sleep(delay)
		}
		a.runCalibrationVerification(gen, mode, productKey)
	}()
}

func (a *App) runCalibrationVerification(gen uint64, mode, productKey string) {
	result, err := a.runSetupLiveProbe(productKey, nil)
	a.mu.Lock()
	if gen != a.setupCalibrationGeneration || !a.setupCalibrationVisible || a.setupCalibrationMode != mode || a.setupCalibrationProductKey != productKey {
		a.setupCalibrationVerifyRunning = false
		a.mu.Unlock()
		return
	}
	baseline := copyPIDSet(a.setupCalibrationBaseline)
	queued := a.setupCalibrationVerifyQueued
	a.setupCalibrationVerifyQueued = false
	if err != nil {
		a.setupCalibrationVerifyRunning = false
		a.setupCalibrationError = tr("setup.calibration.error.live_probe")
		if mode == "wired" {
			a.setupCalibrationStage = setupCalibrationWiredWaiting
		} else {
			a.setupCalibrationStage = setupCalibrationWirelessWaiting
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration verify failed mode=%s product=%q err=%v", mode, productKey, err)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		if queued {
			a.requestCalibrationVerification(800 * time.Millisecond)
		}
		return
	}
	after := livePIDSet(result)
	if samePIDSet(baseline, after) {
		a.setupCalibrationVerifyRunning = false
		a.setupCalibrationError = ""
		if mode == "wired" {
			a.setupCalibrationStage = setupCalibrationWiredWaiting
		} else {
			a.setupCalibrationStage = setupCalibrationWirelessWaiting
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration device event unrelated/no target delta mode=%s product=%q state=%v", mode, productKey, sortedPIDSet(after))
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		if queued {
			a.requestCalibrationVerification(800 * time.Millisecond)
		}
		return
	}
	product, ok := a.calibrationCurrentProductLocked()
	if !ok || product.Key != productKey {
		a.setupCalibrationVerifyRunning = false
		a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.target"))
		a.mu.Unlock()
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	a.mu.Unlock()

	candidate, status := a.selectCalibrationCandidate(mode, productKey, baseline, after, result)
	if status != "success" {
		a.mu.Lock()
		if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
			a.setupCalibrationVerifyRunning = false
			if status == "no-change" {
				a.setupCalibrationError = tr("setup.calibration.error.no_change")
				if mode == "wired" {
					a.setupCalibrationStage = setupCalibrationWiredWaiting
				} else {
					a.setupCalibrationStage = setupCalibrationWirelessWaiting
				}
			} else {
				a.restoreCalibrationPromptLocked(mode, calibrationStatusText(status))
			}
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration delta rejected mode=%s product=%q status=%s before=%v after=%v", mode, productKey, status, sortedPIDSet(baseline), sortedPIDSet(after))
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}

	role := "wired-usb"
	source := "user-guided-wired-transition"
	if mode == "wireless" {
		role = "wireless-dongle"
		source = "user-guided-wireless-transition"
	}
	if candidate.ExplicitRole != "" && candidate.ExplicitRole != role {
		a.mu.Lock()
		if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
			a.setupCalibrationVerifyRunning = false
			a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.conflict"))
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration explicit role conflict mode=%s product=%q pid=%s explicit=%s desired=%s", mode, productKey, candidate.PID, candidate.ExplicitRole, role)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	materialized, err := a.commitGuidedConnectionRole(product, candidate, role, source)
	if err != nil {
		a.mu.Lock()
		if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
			a.setupCalibrationVerifyRunning = false
			a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.conflict"))
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration commit rejected mode=%s product=%q pid=%s err=%v", mode, productKey, candidate.PID, err)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}

	a.mu.Lock()
	if gen != a.setupCalibrationGeneration || !a.setupCalibrationVisible {
		a.setupCalibrationVerifyRunning = false
		a.mu.Unlock()
		return
	}
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationError = ""
	a.setupCalibrationLearned++
	if !materialized {
		a.setupCalibrationNeedsInventoryRefresh = true
	}
	a.applyTargetProbePresenceLocked(productKey, result)
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationSuccessPID = candidate.PID
	a.setupCalibrationSuccessRole = role
	if mode == "wired" {
		a.setupCalibrationStage = setupCalibrationWiredSuccess
	} else {
		a.setupCalibrationStage = setupCalibrationWirelessSuccess
	}
	needsInventoryRefresh := a.setupCalibrationNeedsInventoryRefresh
	a.mu.Unlock()
	a.debugf("SETUP calibration learned mode=%s product=%q pid=%s role=%s source=%s inventoryMaterialized=%t inventoryRefreshRecommended=%t", mode, productKey, candidate.PID, role, source, materialized, needsInventoryRefresh)
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
}

func (a *App) confirmCurrentWirelessCalibration() {
	a.mu.Lock()
	if !a.setupCalibrationVisible || a.setupScanning || a.checking || a.repairing || a.setupCalibrationStage != setupCalibrationWirelessConfirm {
		a.mu.Unlock()
		return
	}
	product, ok := a.calibrationCurrentProductLocked()
	if !ok || strings.TrimSpace(product.Key) == "" {
		a.restoreCalibrationPromptLocked("wireless", tr("setup.calibration.error.target"))
		a.mu.Unlock()
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	if a.calibrationWirelessFlowLocked(product) != setupWirelessFlowUserConfirm {
		a.mu.Unlock()
		return
	}
	a.setupCalibrationVerifyRunning = true
	a.setupCalibrationVerifyQueued = false
	a.setupCalibrationMode = "wireless"
	a.setupCalibrationProductKey = product.Key
	a.setupCalibrationError = ""
	a.setupCalibrationStage = setupCalibrationWirelessVerifying
	gen := a.setupCalibrationGeneration
	productKey := product.Key
	a.mu.Unlock()
	a.debugf("SETUP calibration wireless confirmation requested product=%q", productKey)
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	go a.runWirelessCalibrationConfirmation(gen, productKey)
}

func (a *App) runWirelessCalibrationConfirmation(gen uint64, productKey string) {
	result, err := a.runSetupLiveProbe(productKey, nil)
	a.mu.Lock()
	if gen != a.setupCalibrationGeneration || !a.setupCalibrationVisible || a.setupCalibrationMode != "wireless" || a.setupCalibrationProductKey != productKey {
		a.setupCalibrationVerifyRunning = false
		a.setupCalibrationVerifyQueued = false
		a.mu.Unlock()
		return
	}
	baseline := copyPIDSet(a.setupCalibrationBaseline)
	a.setupCalibrationVerifyQueued = false
	if err != nil {
		a.setupCalibrationVerifyRunning = false
		a.setupCalibrationError = tr("setup.calibration.error.live_probe")
		a.setupCalibrationStage = setupCalibrationWirelessConfirm
		a.mu.Unlock()
		a.debugf("SETUP calibration wireless confirmation failed product=%q err=%v", productKey, err)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	product, ok := a.calibrationCurrentProductLocked()
	if !ok || !strings.EqualFold(strings.TrimSpace(product.Key), strings.TrimSpace(productKey)) {
		a.setupCalibrationVerifyRunning = false
		a.restoreCalibrationPromptLocked("wireless", tr("setup.calibration.error.target"))
		a.mu.Unlock()
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	a.mu.Unlock()

	after := livePIDSet(result)
	for pid := range a.knownRolePIDs(productKey, "wired-usb") {
		if after[pid] {
			a.mu.Lock()
			if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
				a.setupCalibrationVerifyRunning = false
				a.setupCalibrationVerifyQueued = false
				a.setupCalibrationStage = setupCalibrationWirelessConfirm
				a.setupCalibrationError = tr("setup.calibration.error.wired_still_present")
			}
			a.mu.Unlock()
			a.debugf("SETUP calibration wireless confirmation rejected product=%q status=wired-still-present pid=%s current=%v", productKey, pid, sortedPIDSet(after))
			procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
			return
		}
	}
	candidate, status := a.selectCalibrationCandidate("wireless", productKey, baseline, after, result)
	if status != "success" {
		a.mu.Lock()
		if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
			a.setupCalibrationVerifyRunning = false
			a.setupCalibrationVerifyQueued = false
			a.setupCalibrationStage = setupCalibrationWirelessConfirm
			if status == "no-change" {
				a.setupCalibrationError = tr("setup.calibration.error.no_change")
			} else {
				a.setupCalibrationError = calibrationStatusText(status)
			}
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration wireless confirmation rejected product=%q status=%s baseline=%v current=%v", productKey, status, sortedPIDSet(baseline), sortedPIDSet(after))
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}

	role := "wireless-dongle"
	source := "user-guided-wireless-confirmation"
	if candidate.ExplicitRole != "" && candidate.ExplicitRole != role {
		a.mu.Lock()
		if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
			a.setupCalibrationVerifyRunning = false
			a.setupCalibrationVerifyQueued = false
			a.setupCalibrationStage = setupCalibrationWirelessConfirm
			a.setupCalibrationError = tr("setup.calibration.error.conflict")
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration wireless confirmation explicit role conflict product=%q pid=%s explicit=%s desired=%s", productKey, candidate.PID, candidate.ExplicitRole, role)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}
	materialized, err := a.commitGuidedConnectionRole(product, candidate, role, source)
	if err != nil {
		a.mu.Lock()
		if gen == a.setupCalibrationGeneration && a.setupCalibrationVisible {
			a.setupCalibrationVerifyRunning = false
			a.setupCalibrationVerifyQueued = false
			a.setupCalibrationStage = setupCalibrationWirelessConfirm
			a.setupCalibrationError = tr("setup.calibration.error.conflict")
		}
		a.mu.Unlock()
		a.debugf("SETUP calibration wireless confirmation commit rejected product=%q pid=%s err=%v", productKey, candidate.PID, err)
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
		return
	}

	a.mu.Lock()
	if gen != a.setupCalibrationGeneration || !a.setupCalibrationVisible {
		a.setupCalibrationVerifyRunning = false
		a.setupCalibrationVerifyQueued = false
		a.mu.Unlock()
		return
	}
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationVerifyQueued = false
	a.setupCalibrationError = ""
	a.setupCalibrationLearned++
	if !materialized {
		a.setupCalibrationNeedsInventoryRefresh = true
	}
	a.applyTargetProbePresenceLocked(productKey, result)
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationSuccessPID = candidate.PID
	a.setupCalibrationSuccessRole = role
	a.setupCalibrationStage = setupCalibrationWirelessSuccess
	needsInventoryRefresh := a.setupCalibrationNeedsInventoryRefresh
	a.mu.Unlock()
	a.debugf("SETUP calibration learned mode=wireless product=%q pid=%s role=%s source=%s inventoryMaterialized=%t inventoryRefreshRecommended=%t", productKey, candidate.PID, role, source, materialized, needsInventoryRefresh)
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
}

func (a *App) selectCalibrationCandidate(mode, productKey string, before, after map[string]bool, result SetupLiveProbeResult) (SetupLiveConnection, string) {
	byPID := map[string]SetupLiveConnection{}
	for _, c := range result.Connections {
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		if c.Present && c.IdentityVerified && strings.EqualFold(strings.TrimSpace(c.ProductKey), strings.TrimSpace(productKey)) {
			byPID[pid] = c
		}
	}
	if mode == "wired" {
		newPIDs := make([]string, 0, len(after))
		for pid := range after {
			if !before[pid] {
				newPIDs = append(newPIDs, pid)
			}
		}
		sort.Strings(newPIDs)
		if len(newPIDs) == 1 {
			return byPID[newPIDs[0]], "success"
		}
		if len(newPIDs) == 0 {
			return SetupLiveConnection{}, "no-change"
		}
		return SetupLiveConnection{}, "ambiguous"
	}

	wired := a.knownRolePIDs(productKey, "wired-usb")
	candidates := make([]string, 0, len(after))
	for pid := range after {
		if !wired[pid] {
			candidates = append(candidates, pid)
		}
	}
	sort.Strings(candidates)
	if len(candidates) == 1 {
		return byPID[candidates[0]], "success"
	}
	if len(candidates) == 0 {
		return SetupLiveConnection{}, "no-change"
	}
	return SetupLiveConnection{}, "ambiguous"
}

func (a *App) applyTargetProbePresenceLocked(productKey string, result SetupLiveProbeResult) {
	present := livePIDSet(result)
	byPID := map[string]SetupLiveConnection{}
	for _, c := range result.Connections {
		byPID[strings.ToUpper(strings.TrimSpace(c.PID))] = c
	}
	for i := range a.inventory.Connections {
		c := &a.inventory.Connections[i]
		if !strings.EqualFold(strings.TrimSpace(c.ProductKey), strings.TrimSpace(productKey)) {
			continue
		}
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		c.PresentAtScan = present[pid]
		if live, ok := byPID[pid]; ok {
			if k := strings.ToLower(strings.TrimSpace(live.DeviceClass)); k == "mouse" || k == "keyboard" {
				c.DeviceClass = k
			}
		}
	}
}

func sortedPIDSet(set map[string]bool) []string {
	out := make([]string, 0, len(set))
	for pid := range set {
		out = append(out, pid)
	}
	sort.Strings(out)
	return out
}

func copyPIDSet(src map[string]bool) map[string]bool {
	out := make(map[string]bool, len(src))
	for k, v := range src {
		if v {
			out[k] = true
		}
	}
	return out
}

type connectionHistoryFile struct {
	SchemaVersion  int                      `json:"schemaVersion"`
	ToolVersion    string                   `json:"toolVersion"`
	ScannerVersion string                   `json:"scannerVersion"`
	UpdatedAt      string                   `json:"updatedAt"`
	VendorID       string                   `json:"vendorId"`
	Connections    []connectionHistoryEntry `json:"connections"`
	LastSnapshot   json.RawMessage          `json:"lastSnapshot,omitempty"`
}

type connectionHistoryEntry struct {
	Key                       string          `json:"key"`
	VendorID                  string          `json:"vendorId"`
	PID                       string          `json:"pid"`
	ConnectionFingerprint     string          `json:"connectionFingerprint,omitempty"`
	ProductKey                string          `json:"productKey"`
	ProductName               string          `json:"productName"`
	DeviceClass               string          `json:"deviceClass,omitempty"`
	ProductIdentitySource     string          `json:"productIdentitySource,omitempty"`
	ProductIdentityConfidence string          `json:"productIdentityConfidence,omitempty"`
	ConnectionType            string          `json:"connectionType"`
	ConnectionTypeConfidence  string          `json:"connectionTypeConfidence,omitempty"`
	ConnectionTypeSource      string          `json:"connectionTypeSource,omitempty"`
	FirstSeenAt               string          `json:"firstSeenAt,omitempty"`
	LastSeenAt                string          `json:"lastSeenAt,omitempty"`
	SeenCount                 int             `json:"seenCount,omitempty"`
	PresentCount              int             `json:"presentCount,omitempty"`
	LastPresent               bool            `json:"lastPresent"`
	TransitionEvidenceCount   int             `json:"transitionEvidenceCount,omitempty"`
	Calibrated                bool            `json:"calibrated"`
	CalibratedAt              string          `json:"calibratedAt,omitempty"`
	Topology                  json.RawMessage `json:"topology,omitempty"`
}

func (a *App) readConnectionHistory() (connectionHistoryFile, error) {
	var h connectionHistoryFile
	b, err := os.ReadFile(a.connectionHistoryPath)
	if err != nil {
		if os.IsNotExist(err) {
			h = connectionHistoryFile{SchemaVersion: 2, ToolVersion: appVersion, ScannerVersion: setupScanVersion, VendorID: "1532", Connections: []connectionHistoryEntry{}}
			return h, nil
		}
		return h, err
	}
	if err := json.Unmarshal(b, &h); err != nil {
		return h, err
	}
	if h.SchemaVersion != 2 || !strings.EqualFold(strings.TrimSpace(h.VendorID), "1532") {
		return h, errors.New("unsupported connection history")
	}
	return h, nil
}

func (a *App) commitGuidedConnectionRole(product DeviceProductProfile, live SetupLiveConnection, role, source string) (bool, error) {
	pid := strings.ToUpper(strings.TrimSpace(live.PID))
	if !validInventoryPID(pid) || !live.IdentityVerified || !strings.EqualFold(strings.TrimSpace(live.ProductKey), strings.TrimSpace(product.Key)) {
		return false, errors.New("guided connection identity is not verified")
	}
	h, err := a.readConnectionHistory()
	if err != nil {
		return false, err
	}
	now := time.Now().UTC().Format(time.RFC3339Nano)
	idx := -1
	for i := range h.Connections {
		if strings.EqualFold(strings.TrimSpace(h.Connections[i].PID), pid) {
			idx = i
			break
		}
	}
	if idx < 0 {
		h.Connections = append(h.Connections, connectionHistoryEntry{
			Key:                       "1532:" + pid,
			VendorID:                  "1532",
			PID:                       pid,
			ConnectionFingerprint:     "1532:" + pid,
			ProductKey:                product.Key,
			ProductName:               firstNonEmpty(live.ProductName, product.Name),
			DeviceClass:               normalizedDeviceClass(live.DeviceClass),
			ProductIdentitySource:     live.IdentitySource,
			ProductIdentityConfidence: live.IdentityConfidence,
			FirstSeenAt:               now,
		})
		idx = len(h.Connections) - 1
	}
	e := &h.Connections[idx]
	if !strings.EqualFold(strings.TrimSpace(e.ProductKey), strings.TrimSpace(product.Key)) {
		return false, fmt.Errorf("PID %s belongs to a different productKey", pid)
	}
	if e.ConnectionTypeSource == "explicit-device-role-text" && e.ConnectionType != "" && e.ConnectionType != "usb-device" && e.ConnectionType != role {
		return false, fmt.Errorf("explicit role evidence conflicts for PID %s", pid)
	}
	e.ProductName = firstNonEmpty(live.ProductName, e.ProductName, product.Name)
	e.DeviceClass = firstNonEmpty(normalizedDeviceClass(live.DeviceClass), e.DeviceClass)
	e.ProductIdentitySource = firstNonEmpty(live.IdentitySource, e.ProductIdentitySource)
	e.ProductIdentityConfidence = firstNonEmpty(live.IdentityConfidence, e.ProductIdentityConfidence)
	e.ConnectionType = role
	e.ConnectionTypeConfidence = "high"
	e.ConnectionTypeSource = source
	e.LastSeenAt = now
	if e.FirstSeenAt == "" {
		e.FirstSeenAt = now
	}
	e.SeenCount++
	e.PresentCount++
	e.LastPresent = true
	e.Calibrated = true
	e.CalibratedAt = now
	h.ToolVersion = appVersion
	if h.ScannerVersion == "" {
		h.ScannerVersion = setupScanVersion
	}
	h.UpdatedAt = now
	b, err := json.MarshalIndent(h, "", "  ")
	if err != nil {
		return false, err
	}
	tmp := a.connectionHistoryPath + ".guided.tmp"
	if err := os.WriteFile(tmp, b, 0644); err != nil {
		return false, err
	}
	if err := os.Rename(tmp, a.connectionHistoryPath); err != nil {
		_ = os.Remove(tmp)
		return false, err
	}

	a.mu.Lock()
	materialized := false
	for i := range a.inventory.Connections {
		c := &a.inventory.Connections[i]
		if strings.EqualFold(strings.TrimSpace(c.PID), pid) && strings.EqualFold(strings.TrimSpace(c.ProductKey), strings.TrimSpace(product.Key)) {
			materialized = true
			c.ConnectionType = role
			c.ConnectionTypeConfidence = "high"
			c.ConnectionTypeSource = source
			if k := normalizedDeviceClass(live.DeviceClass); k == "mouse" || k == "keyboard" {
				c.DeviceClass = k
			}
		}
	}
	a.mu.Unlock()
	return materialized, nil
}

func (a *App) knownRolePIDs(productKey, role string) map[string]bool {
	out := map[string]bool{}
	a.mu.Lock()
	for _, c := range a.inventory.Connections {
		if strings.EqualFold(strings.TrimSpace(c.ProductKey), strings.TrimSpace(productKey)) && strings.EqualFold(strings.TrimSpace(c.ConnectionType), role) && strings.EqualFold(strings.TrimSpace(c.ConnectionTypeConfidence), "high") {
			out[strings.ToUpper(strings.TrimSpace(c.PID))] = true
		}
	}
	a.mu.Unlock()
	if h, err := a.readConnectionHistory(); err == nil {
		for _, e := range h.Connections {
			if strings.EqualFold(strings.TrimSpace(e.ProductKey), strings.TrimSpace(productKey)) && strings.EqualFold(strings.TrimSpace(e.ConnectionType), role) && strings.EqualFold(strings.TrimSpace(e.ConnectionTypeConfidence), "high") {
				out[strings.ToUpper(strings.TrimSpace(e.PID))] = true
			}
		}
	}
	return out
}

func normalizedDeviceClass(v string) string {
	switch strings.ToLower(strings.TrimSpace(v)) {
	case "mouse":
		return "mouse"
	case "keyboard":
		return "keyboard"
	default:
		return ""
	}
}

func firstNonEmpty(values ...string) string {
	for _, v := range values {
		if strings.TrimSpace(v) != "" {
			return v
		}
	}
	return ""
}
