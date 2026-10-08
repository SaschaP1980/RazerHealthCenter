//go:build windows

package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
	"time"
)

const setupScanVersion = "1.0.6"
const inventorySchemaVersion = 2

const (
	setupCalibrationNone = iota
	setupCalibrationWiredPrompt
	setupCalibrationWiredPreparing
	setupCalibrationWiredWaiting
	setupCalibrationWiredVerifying
	setupCalibrationWiredSuccess
	setupCalibrationWirelessPrompt
	setupCalibrationWirelessPreparing
	setupCalibrationWirelessWaiting
	setupCalibrationWirelessConfirm
	setupCalibrationWirelessVerifying
	setupCalibrationWirelessSuccess
	setupCalibrationComplete
)

type SetupCalibrationResult struct {
	Requested    bool     `json:"requested"`
	Mode         string   `json:"mode,omitempty"`
	ProductKey   string   `json:"productKey,omitempty"`
	Status       string   `json:"status,omitempty"`
	Role         string   `json:"role,omitempty"`
	AssignedPIDs []string `json:"assignedPids,omitempty"`
	Source       string   `json:"source,omitempty"`
	Detail       string   `json:"detail,omitempty"`
}

type DeviceInventoryNode struct {
	InstanceID  string `json:"instanceId"`
	Name        string `json:"name,omitempty"`
	Service     string `json:"service,omitempty"`
	ProblemCode int    `json:"problemCode"`
	Present     bool   `json:"present"`
}

type DeviceConnectionCapabilities struct {
	RequiresRzVirtual       bool `json:"requiresRzVirtual"`
	RequiresRzControl       bool `json:"requiresRzControl"`
	RequiresRazerBoundNodes bool `json:"requiresRazerBoundNodes"`
	RequiresDeviceFilters   bool `json:"requiresDeviceFilters"`
}

type DeviceConnectionTopology struct {
	RootInstanceID     string   `json:"rootInstanceId,omitempty"`
	ContainerID        string   `json:"containerId,omitempty"`
	Parent             string   `json:"parent,omitempty"`
	LocationPaths      []string `json:"locationPaths,omitempty"`
	LastArrivalDate    string   `json:"lastArrivalDate,omitempty"`
	HIDCollectionCount int      `json:"hidCollectionCount,omitempty"`
	HIDInterfaceCount  int      `json:"hidInterfaceCount,omitempty"`
	USBInterfaceCount  int      `json:"usbInterfaceCount,omitempty"`
}

type DeviceConnectionProfile struct {
	DeviceClass               string                       `json:"deviceClass,omitempty"`
	PID                       string                       `json:"pid"`
	ModelName                 string                       `json:"modelName"`
	ProductKey                string                       `json:"productKey"`
	ProductIdentitySource     string                       `json:"productIdentitySource,omitempty"`
	ProductIdentityConfidence string                       `json:"productIdentityConfidence,omitempty"`
	ConnectionFingerprint     string                       `json:"connectionFingerprint,omitempty"`
	ConnectionType            string                       `json:"connectionType"`
	ConnectionTypeConfidence  string                       `json:"connectionTypeConfidence,omitempty"`
	ConnectionTypeSource      string                       `json:"connectionTypeSource,omitempty"`
	PresentAtScan             bool                         `json:"presentAtScan"`
	DriverStack               string                       `json:"driverStack"`
	DriverInfNames            []string                     `json:"driverInfNames"`
	RazerDriverInfNames       []string                     `json:"razerDriverInfNames,omitempty"`
	InboxDriverInfNames       []string                     `json:"inboxDriverInfNames,omitempty"`
	ServiceNames              []string                     `json:"serviceNames"`
	Topology                  DeviceConnectionTopology     `json:"topology,omitempty"`
	Capabilities              DeviceConnectionCapabilities `json:"capabilities"`
	Nodes                     []DeviceInventoryNode        `json:"nodes"`
}

type DeviceProductProfile struct {
	DeviceClass    string   `json:"deviceClass,omitempty"`
	Key            string   `json:"key"`
	Name           string   `json:"name"`
	Required       bool     `json:"required"`
	ConnectionPIDs []string `json:"connectionPids"`
}

type DeviceInventory struct {
	SchemaVersion     int                       `json:"schemaVersion"`
	ToolVersion       string                    `json:"toolVersion"`
	ScanVersion       string                    `json:"scanVersion"`
	CreatedAt         time.Time                 `json:"createdAt"`
	VendorID          string                    `json:"vendorId"`
	Computer          string                    `json:"computer,omitempty"`
	Products          []DeviceProductProfile    `json:"products"`
	Connections       []DeviceConnectionProfile `json:"connections"`
	LogicalProductIDs []string                  `json:"logicalProductIds,omitempty"`
	SourceSummary     []string                  `json:"sourceSummary,omitempty"`
	CalibrationResult SetupCalibrationResult    `json:"calibrationResult,omitempty"`
}

func validInventoryPID(pid string) bool {
	pid = strings.ToUpper(strings.TrimSpace(pid))
	if len(pid) != 4 {
		return false
	}
	for _, r := range pid {
		if !((r >= '0' && r <= '9') || (r >= 'A' && r <= 'F')) {
			return false
		}
	}
	return true
}

func (d DeviceInventory) valid() bool {
	if d.SchemaVersion != inventorySchemaVersion || !strings.EqualFold(strings.TrimSpace(d.VendorID), "1532") || len(d.Connections) == 0 || len(d.Products) == 0 {
		return false
	}
	known := make(map[string]bool, len(d.Connections))
	for _, c := range d.Connections {
		pid := strings.ToUpper(strings.TrimSpace(c.PID))
		if !validInventoryPID(pid) || strings.TrimSpace(c.ProductKey) == "" || strings.TrimSpace(c.ModelName) == "" || strings.TrimSpace(c.ConnectionType) == "" {
			return false
		}
		switch strings.ToLower(strings.TrimSpace(c.DriverStack)) {
		case "razer-filter", "windows-inbox":
		default:
			return false
		}
		known[pid] = true
	}
	// Healthcheck participation is a user preference, not an inventory-validity
	// prerequisite. Validate every product regardless of whether it currently
	// participates in the Healthcheck, and allow a valid inventory with zero
	// active products so the user can re-enable one after an app restart.
	for _, p := range d.Products {
		if p.DeviceClass != "" {
			switch strings.ToLower(strings.TrimSpace(p.DeviceClass)) {
			case "mouse", "keyboard", "device":
			default:
				return false
			}
		}
		if strings.TrimSpace(p.Key) == "" || strings.TrimSpace(p.Name) == "" || len(p.ConnectionPIDs) == 0 {
			return false
		}
		for _, raw := range p.ConnectionPIDs {
			pid := strings.ToUpper(strings.TrimSpace(raw))
			if !validInventoryPID(pid) || !known[pid] {
				return false
			}
		}
	}
	return true
}

func activeHealthcheckProductCount(inv DeviceInventory) int {
	count := 0
	for _, p := range inv.Products {
		if p.Required {
			count++
		}
	}
	return count
}

func hasActiveHealthcheckProduct(inv DeviceInventory) bool {
	return activeHealthcheckProductCount(inv) > 0
}

func mergeHealthcheckParticipation(next *DeviceInventory, previous DeviceInventory) {
	if next == nil || len(next.Products) == 0 || len(previous.Products) == 0 {
		return
	}
	byKey := make(map[string]bool, len(previous.Products))
	for _, p := range previous.Products {
		key := strings.ToLower(strings.TrimSpace(p.Key))
		if key != "" {
			byKey[key] = p.Required
		}
	}
	for i := range next.Products {
		key := strings.ToLower(strings.TrimSpace(next.Products[i].Key))
		if required, ok := byKey[key]; ok {
			next.Products[i].Required = required
		}
		// Products not present in the previous inventory retain the scanner's
		// default required=true and therefore enter the Healthcheck by default.
	}
}

func persistHealthcheckParticipation(path, productKey string, required bool) error {
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var inv DeviceInventory
	if err := json.Unmarshal(b, &inv); err != nil || !inv.valid() {
		if err != nil {
			return err
		}
		return errors.New("device inventory is invalid")
	}
	found := false
	for i := range inv.Products {
		if strings.EqualFold(strings.TrimSpace(inv.Products[i].Key), strings.TrimSpace(productKey)) {
			inv.Products[i].Required = required
			found = true
			break
		}
	}
	if !found {
		return fmt.Errorf("productKey %q not found in device inventory", productKey)
	}
	out, err := json.MarshalIndent(inv, "", "  ")
	if err != nil {
		return err
	}
	out = append(out, '\n')
	tmp := path + ".healthcheck.tmp"
	if err := os.WriteFile(tmp, out, 0644); err != nil {
		return err
	}
	if err := os.Rename(tmp, path); err != nil {
		_ = os.Remove(tmp)
		return err
	}
	return nil
}

func (a *App) loadDeviceInventory() {
	b, err := os.ReadFile(a.inventoryPath)
	if err != nil {
		a.mu.Lock()
		a.setupReady = false
		a.setupLastError = ""
		a.mu.Unlock()
		return
	}
	var inv DeviceInventory
	if err := json.Unmarshal(b, &inv); err != nil || !inv.valid() {
		a.mu.Lock()
		a.setupReady = false
		a.setupLastError = tr("setup.error.invalid_profile")
		a.mu.Unlock()
		return
	}
	a.mu.Lock()
	a.inventory = inv
	a.setupReady = true
	a.setupCalibrationNeedsInventoryRefresh = false
	a.setupLastError = ""
	a.setupLiveFresh = false
	a.setupLiveRefreshing = false
	a.setupLiveLastError = ""
	a.mu.Unlock()
}

func (a *App) startSetupScan() {
	a.mu.Lock()
	blocked := a.setupReady && len(a.inventory.Products) > 0 && !hasActiveHealthcheckProduct(a.inventory)
	if blocked {
		a.setupNoticeVisible = true
		a.setupNoticeTitle = tr("setup.healthcheck.none.title")
		a.setupNoticeDetail = tr("setup.healthcheck.none.detail")
		a.hoverSetupNoticeButton = -1
	}
	a.mu.Unlock()
	if blocked {
		a.debugf("SETUP scan blocked reason=no-active-healthcheck-product")
		procInvalidateRect.Call(a.hwnd, 0, 0)
		return
	}
	a.startSetupScanMode("none", "")
}

func (a *App) startSetupScanMode(mode, productKey string) {
	a.mu.Lock()
	if a.setupScanning || a.checking || a.repairing {
		a.mu.Unlock()
		return
	}
	baselinePath := ""
	if mode != "none" {
		if !a.setupCalibrationVisible || strings.TrimSpace(productKey) == "" {
			a.mu.Unlock()
			return
		}
		baselinePath = filepath.Join(a.setupDir, "SetupCalibrationBaseline-v2.tmp.json")
		baseline, err := json.MarshalIndent(a.inventory, "", "  ")
		if err != nil {
			a.setupCalibrationError = tr("setup.calibration.error.baseline")
			a.mu.Unlock()
			procInvalidateRect.Call(a.hwnd, 0, 0)
			return
		}
		if err := os.WriteFile(baselinePath, baseline, 0644); err != nil {
			a.setupCalibrationError = tr("setup.calibration.error.baseline")
			a.mu.Unlock()
			procInvalidateRect.Call(a.hwnd, 0, 0)
			return
		}
		if mode == "wired" {
			a.setupCalibrationStage = setupCalibrationWiredVerifying
		} else {
			a.setupCalibrationStage = setupCalibrationWirelessVerifying
		}
		a.setupCalibrationError = ""
	}
	a.setupScanning = true
	a.setupLastError = ""
	a.mu.Unlock()
	a.debugf("SETUP scan start mode=%s productKey=%q script=%q inventory=%q history=%q", mode, productKey, a.setupScriptPath, a.inventoryPath, a.connectionHistoryPath)
	procSetTimer.Call(a.hwnd, 1, 125, 0)
	procInvalidateRect.Call(a.hwnd, 0, 0)
	go a.runSetupScan(mode, productKey, baselinePath)
}

func (a *App) runSetupScan(mode, productKey, baselinePath string) {
	if baselinePath != "" {
		defer os.Remove(baselinePath)
	}
	stamp := time.Now().Format("20060102-150405")
	temp := filepath.Join(a.setupDir, "RazerDeviceInventory-v2.tmp.json")
	diag := filepath.Join(a.diagDir, "SetupScan-"+a.session+"-"+stamp+".json")
	setupDebugJSON := filepath.Join(a.setupDir, "SetupScannerDebug-v1.0.6.json")
	setupDebugText := filepath.Join(a.setupDir, "SetupScannerDebug-v1.0.6.txt")
	diagDebugJSON := filepath.Join(a.diagDir, "SetupScannerDebug-"+a.session+"-"+stamp+".json")
	diagDebugText := filepath.Join(a.diagDir, "SetupScannerDebug-"+a.session+"-"+stamp+".txt")
	_ = os.Remove(temp)
	psCommand := "$enc = New-Object System.Text.UTF8Encoding($false); " +
		"[Console]::OutputEncoding = $enc; $OutputEncoding = $enc; " +
		"& " + quotePowerShellLiteral(a.setupScriptPath) +
		" -OutputPath " + quotePowerShellLiteral(temp) +
		" -HistoryPath " + quotePowerShellLiteral(a.connectionHistoryPath) +
		" -ToolVersion " + quotePowerShellLiteral(appVersion) +
		" -CalibrationMode " + quotePowerShellLiteral(mode)
	if mode != "none" {
		psCommand += " -CalibrationProductKey " + quotePowerShellLiteral(productKey) +
			" -BaselinePath " + quotePowerShellLiteral(baselinePath)
	}
	cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", psCommand)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	var stdout, stderr bytes.Buffer
	cmd.Stdout, cmd.Stderr = &stdout, &stderr
	err := cmd.Run()
	copySetupDebugArtifact(setupDebugJSON, diagDebugJSON)
	copySetupDebugArtifact(setupDebugText, diagDebugText)
	if err != nil {
		msg := strings.TrimSpace(stderr.String())
		if msg == "" {
			msg = strings.TrimSpace(stdout.String())
		}
		if msg == "" {
			msg = err.Error()
		}
		a.mu.Lock()
		a.setupScanning = false
		a.setupLastError = msg
		if mode != "none" {
			a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.scan"))
		}
		a.mu.Unlock()
		a.debugf("SETUP scan failed err=%v stderr=%q stdout=%q", err, stderr.String(), stdout.String())
		procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
		return
	}
	b, readErr := os.ReadFile(temp)
	var inv DeviceInventory
	if readErr != nil || json.Unmarshal(b, &inv) != nil || !inv.valid() {
		msg := tr("setup.error.no_products")
		if readErr != nil {
			msg = readErr.Error()
		}
		a.mu.Lock()
		a.setupScanning = false
		a.setupLastError = msg
		if mode != "none" {
			a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.scan"))
		}
		a.mu.Unlock()
		a.debugf("SETUP scan invalid profile readErr=%v bytes=%d", readErr, len(b))
		procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
		return
	}
	// A full Setup scan rediscovers inventory facts, but it must not overwrite
	// the user's persistent Healthcheck include/exclude choices for products that
	// are recognized again. Newly discovered products keep scanner default=true.
	a.mu.Lock()
	previousInventory := a.inventory
	a.mu.Unlock()
	mergeHealthcheckParticipation(&inv, previousInventory)
	b, marshalErr := json.MarshalIndent(inv, "", "  ")
	if marshalErr != nil {
		a.mu.Lock()
		a.setupScanning = false
		a.setupLastError = marshalErr.Error()
		a.mu.Unlock()
		a.debugf("SETUP scan could not serialize merged Healthcheck participation err=%v", marshalErr)
		procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
		return
	}
	b = append(b, '\n')
	if err := os.WriteFile(temp, b, 0644); err != nil {
		a.mu.Lock()
		a.setupScanning = false
		a.setupLastError = err.Error()
		a.mu.Unlock()
		a.debugf("SETUP scan could not stage merged Healthcheck participation err=%v", err)
		procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
		return
	}

	if mode != "none" && !strings.EqualFold(inv.CalibrationResult.Status, "success") {
		_ = os.Remove(temp)
		a.mu.Lock()
		a.setupScanning = false
		a.setupLastError = ""
		a.restoreCalibrationPromptLocked(mode, calibrationStatusText(inv.CalibrationResult.Status))
		a.mu.Unlock()
		a.debugf("SETUP guided calibration rejected mode=%s productKey=%q status=%s detail=%q", mode, productKey, inv.CalibrationResult.Status, inv.CalibrationResult.Detail)
		procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
		return
	}

	if err := os.Rename(temp, a.inventoryPath); err != nil {
		if err := os.WriteFile(a.inventoryPath, b, 0644); err != nil {
			a.mu.Lock()
			a.setupScanning = false
			a.setupLastError = err.Error()
			if mode != "none" {
				a.restoreCalibrationPromptLocked(mode, tr("setup.calibration.error.scan"))
			}
			a.mu.Unlock()
			procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
			return
		}
		_ = os.Remove(temp)
	}
	_ = os.WriteFile(diag, b, 0644)
	a.mu.Lock()
	a.inventory = inv
	a.setupReady = true
	a.setupScanning = false
	a.setupCalibrationNeedsInventoryRefresh = false
	a.setupLastError = ""
	a.setupLiveFresh = true
	a.setupLiveLast = time.Now()
	a.setupLiveLastError = ""
	if mode != "none" {
		a.setupCalibrationError = ""
		a.setupCalibrationLearned += len(inv.CalibrationResult.AssignedPIDs)
		if mode == "wired" {
			a.setupCalibrationStage = setupCalibrationWirelessPrompt
		} else {
			a.advanceCalibrationProductLocked()
		}
	}
	a.mu.Unlock()
	a.debugf("SETUP scan complete mode=%s productKey=%q calibration=%s products=%d connections=%d logicalProducts=%d profile=%q history=%q", mode, productKey, inv.CalibrationResult.Status, len(inv.Products), len(inv.Connections), len(inv.LogicalProductIDs), a.inventoryPath, a.connectionHistoryPath)
	procPostMessageW.Call(a.hwnd, wmSetupDone, 0, 0)
}

func (a *App) openSetupCalibration() {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.setupScanning || a.checking || a.repairing || !a.setupReady || len(a.inventory.Products) == 0 {
		return
	}
	a.setupCalibrationVisible = true
	a.setupCalibrationGeneration++
	a.setupCalibrationStage = setupCalibrationWiredPrompt
	a.setupCalibrationProductIndex = 0
	a.setupCalibrationError = ""
	a.setupCalibrationLearned = 0
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationVerifyQueued = false
	a.setupCalibrationNeedsInventoryRefresh = false
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) closeSetupCalibration() bool {
	a.mu.Lock()
	if !a.setupCalibrationVisible || (a.setupScanning && a.setupCalibrationStage != setupCalibrationComplete) {
		a.mu.Unlock()
		return false
	}
	a.setupCalibrationGeneration++
	a.setupCalibrationVisible = false
	a.setupCalibrationStage = setupCalibrationNone
	a.setupCalibrationError = ""
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationVerifyQueued = false
	a.setupCalibrationNeedsInventoryRefresh = false
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
	return true
}

func (a *App) calibrationCurrentProductLocked() (DeviceProductProfile, bool) {
	if a.setupCalibrationProductIndex < 0 || a.setupCalibrationProductIndex >= len(a.inventory.Products) {
		return DeviceProductProfile{}, false
	}
	return a.inventory.Products[a.setupCalibrationProductIndex], true
}

func (a *App) startCurrentCalibration(mode string) {
	a.armCurrentCalibration(mode)
}

func (a *App) skipCurrentCalibrationStep() {
	a.mu.Lock()
	if !a.setupCalibrationVisible || a.setupScanning {
		a.mu.Unlock()
		return
	}
	a.setupCalibrationGeneration++
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationVerifyQueued = false
	stage := a.setupCalibrationStage
	if stage == setupCalibrationWiredPrompt || stage == setupCalibrationWiredWaiting {
		a.setupCalibrationStage = setupCalibrationWirelessPrompt
		a.setupCalibrationError = ""
	} else if stage == setupCalibrationWirelessPrompt || stage == setupCalibrationWirelessWaiting || stage == setupCalibrationWirelessConfirm {
		a.advanceCalibrationProductLocked()
	}
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) continueCalibrationSuccess() {
	a.mu.Lock()
	if !a.setupCalibrationVisible || a.setupScanning || a.checking || a.repairing {
		a.mu.Unlock()
		return
	}
	stage := a.setupCalibrationStage
	if stage != setupCalibrationWiredSuccess && stage != setupCalibrationWirelessSuccess {
		a.mu.Unlock()
		return
	}
	a.setupCalibrationGeneration++
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationVerifyQueued = false
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	a.setupCalibrationError = ""
	if stage == setupCalibrationWiredSuccess {
		a.setupCalibrationStage = setupCalibrationWirelessPrompt
	} else {
		a.advanceCalibrationProductLocked()
	}
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) advanceCalibrationProductLocked() {
	a.setupCalibrationProductIndex++
	a.setupCalibrationError = ""
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	if a.setupCalibrationProductIndex >= len(a.inventory.Products) {
		a.setupCalibrationStage = setupCalibrationComplete
	} else {
		a.setupCalibrationStage = setupCalibrationWiredPrompt
	}
}

func (a *App) restoreCalibrationPromptLocked(mode, message string) {
	a.setupCalibrationError = message
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	if mode == "wired" {
		a.setupCalibrationStage = setupCalibrationWiredPrompt
	} else {
		a.setupCalibrationStage = setupCalibrationWirelessPrompt
	}
}

func (a *App) skipCurrentCalibrationProduct() {
	a.mu.Lock()
	if !a.setupCalibrationVisible || a.setupScanning {
		a.mu.Unlock()
		return
	}
	stage := a.setupCalibrationStage
	if stage == setupCalibrationComplete || stage == setupCalibrationNone || stage == setupCalibrationWiredPreparing || stage == setupCalibrationWiredVerifying || stage == setupCalibrationWirelessPreparing || stage == setupCalibrationWirelessVerifying {
		a.mu.Unlock()
		return
	}
	product, ok := a.calibrationCurrentProductLocked()
	if !ok {
		a.mu.Unlock()
		return
	}
	a.setupCalibrationGeneration++
	a.setupCalibrationMode = ""
	a.setupCalibrationProductKey = ""
	a.setupCalibrationSuccessPID = ""
	a.setupCalibrationSuccessRole = ""
	a.setupCalibrationBaseline = nil
	a.setupCalibrationVerifyRunning = false
	a.setupCalibrationVerifyQueued = false
	a.setupCalibrationError = ""
	productKey := product.Key
	productName := product.Name
	a.advanceCalibrationProductLocked()
	a.mu.Unlock()
	a.debugf("SETUP calibration product skipped product=%q name=%q", productKey, productName)
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) closeSetupNotice() bool {
	a.mu.Lock()
	if !a.setupNoticeVisible {
		a.mu.Unlock()
		return false
	}
	a.setupNoticeVisible = false
	a.setupNoticeTitle = ""
	a.setupNoticeDetail = ""
	a.hoverSetupNoticeButton = -1
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
	return true
}

func (a *App) toggleHealthcheckProduct(index int) {
	a.mu.Lock()
	if !a.setupReady || a.setupScanning || a.checking || a.repairing || a.setupCalibrationVisible || index < 0 || index >= len(a.inventory.Products) {
		a.mu.Unlock()
		return
	}
	productKey := a.inventory.Products[index].Key
	productName := a.inventory.Products[index].Name
	oldRequired := a.inventory.Products[index].Required
	newRequired := !oldRequired
	a.inventory.Products[index].Required = newRequired
	a.mu.Unlock()

	if err := persistHealthcheckParticipation(a.inventoryPath, productKey, newRequired); err != nil {
		a.mu.Lock()
		if index >= 0 && index < len(a.inventory.Products) && strings.EqualFold(strings.TrimSpace(a.inventory.Products[index].Key), strings.TrimSpace(productKey)) {
			a.inventory.Products[index].Required = oldRequired
		}
		a.setupNoticeVisible = true
		a.setupNoticeTitle = tr("setup.healthcheck.persist_error.title")
		a.setupNoticeDetail = trf("setup.healthcheck.persist_error.detail", "error", err.Error())
		a.hoverSetupNoticeButton = -1
		a.mu.Unlock()
		a.debugf("SETUP Healthcheck participation persist failed product=%q required=%t err=%v", productKey, newRequired, err)
		procInvalidateRect.Call(a.hwnd, 0, 0)
		return
	}

	a.mu.Lock()
	// The previous Health result was calculated for a different set of products.
	// Keep measurement history intact, but invalidate the current dashboard result.
	a.overall = overallUnchecked
	a.lastCheck = time.Time{}
	a.lastDuration = 0
	a.completedGates = 0
	a.currentGate = ""
	a.detailGate = -1
	a.detailScroll = 0
	for i := 0; i < gateCount; i++ {
		a.states[i] = gateUnchecked
		a.liveGateDisplay[i] = gateUnchecked
		a.gateInspections[i] = GateInspection{}
	}
	active := activeHealthcheckProductCount(a.inventory)
	total := len(a.inventory.Products)
	a.mu.Unlock()
	a.setTray(nimModify, a.iconIdle, tr("tray.tip.unchecked"))
	a.debugf("SETUP Healthcheck participation changed product=%q name=%q required=%t active=%d total=%d healthStatus=%s", productKey, productName, newRequired, active, total, overallUnchecked)
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func calibrationStatusText(status string) string {
	switch strings.ToLower(strings.TrimSpace(status)) {
	case "ambiguous":
		return tr("setup.calibration.error.ambiguous")
	case "target-not-found":
		return tr("setup.calibration.error.target")
	case "baseline-missing":
		return tr("setup.calibration.error.baseline")
	case "evidence-conflict":
		return tr("setup.calibration.error.conflict")
	default:
		return tr("setup.calibration.error.scan")
	}
}

func copySetupDebugArtifact(src, dst string) {
	b, err := os.ReadFile(src)
	if err != nil || len(b) == 0 {
		return
	}
	_ = os.WriteFile(dst, b, 0644)
}

func setupConnectionRoleLabel(c DeviceConnectionProfile) string {
	if !(strings.EqualFold(c.ConnectionTypeConfidence, "medium") || strings.EqualFold(c.ConnectionTypeConfidence, "high")) {
		return ""
	}
	switch c.ConnectionType {
	case "wireless-dongle":
		return tr("setup.connection.wireless_dongle")
	case "wired-usb":
		return tr("setup.connection.wired_usb")
	default:
		return ""
	}
}

func setupConnectionSortPriority(c DeviceConnectionProfile, ok bool) int {
	if !ok || !(strings.EqualFold(c.ConnectionTypeConfidence, "medium") || strings.EqualFold(c.ConnectionTypeConfidence, "high")) {
		return 2
	}
	switch strings.ToLower(strings.TrimSpace(c.ConnectionType)) {
	case "wired-usb":
		return 0
	case "wireless-dongle":
		return 1
	default:
		return 2
	}
}

func setupSortedProductConnectionPIDs(inv DeviceInventory, product DeviceProductProfile) []string {
	byPID := make(map[string]DeviceConnectionProfile, len(inv.Connections))
	for _, c := range inv.Connections {
		byPID[strings.ToUpper(strings.TrimSpace(c.PID))] = c
	}
	pids := make([]string, 0, len(product.ConnectionPIDs))
	seen := make(map[string]bool, len(product.ConnectionPIDs))
	for _, raw := range product.ConnectionPIDs {
		pid := strings.ToUpper(strings.TrimSpace(raw))
		if pid == "" || seen[pid] {
			continue
		}
		seen[pid] = true
		pids = append(pids, pid)
	}
	sort.SliceStable(pids, func(i, j int) bool {
		ci, oki := byPID[pids[i]]
		cj, okj := byPID[pids[j]]
		pi := setupConnectionSortPriority(ci, oki)
		pj := setupConnectionSortPriority(cj, okj)
		if pi != pj {
			return pi < pj
		}
		return pids[i] < pids[j]
	})
	return pids
}

func setupConnectionSummary(inv DeviceInventory, product DeviceProductProfile) string {
	byPID := make(map[string]DeviceConnectionProfile, len(inv.Connections))
	for _, c := range inv.Connections {
		byPID[strings.ToUpper(strings.TrimSpace(c.PID))] = c
	}
	pids := setupSortedProductConnectionPIDs(inv, product)
	parts := make([]string, 0, len(pids))
	for _, pid := range pids {
		label := pid
		if c, ok := byPID[pid]; ok {
			if role := setupConnectionRoleLabel(c); role != "" {
				label = role + " · " + pid
			}
		}
		parts = append(parts, label)
	}
	return strings.Join(parts, ", ")
}

func setupPresentConnectionCount(inv DeviceInventory) int {
	count := 0
	for _, c := range inv.Connections {
		if c.PresentAtScan {
			count++
		}
	}
	return count
}

func storedConnectionDeviceClass(c DeviceConnectionProfile) string {
	if k := strings.ToLower(strings.TrimSpace(c.DeviceClass)); k == "mouse" || k == "keyboard" {
		return k
	}
	primary := map[string]bool{}
	fallback := map[string]bool{}
	for _, n := range c.Nodes {
		id := strings.ToUpper(strings.TrimSpace(n.InstanceID))
		name := strings.ToLower(strings.TrimSpace(n.Name))
		service := strings.ToLower(strings.TrimSpace(n.Service))
		kind := ""
		if service == "mouhid" || strings.Contains(name, "hid-compliant mouse") {
			kind = "mouse"
		} else if service == "kbdhid" || strings.Contains(name, "hid keyboard device") {
			kind = "keyboard"
		}
		if kind == "" {
			continue
		}
		fallback[kind] = true
		if strings.Contains(id, "&MI_00") {
			primary[kind] = true
		}
	}
	if len(primary) == 1 {
		for k := range primary {
			return k
		}
	}
	if len(primary) > 1 {
		return "device"
	}
	if len(fallback) == 1 {
		for k := range fallback {
			return k
		}
	}
	return "device"
}

func setupProductDeviceClass(inv DeviceInventory, product DeviceProductProfile) string {
	if k := strings.ToLower(strings.TrimSpace(product.DeviceClass)); k == "mouse" || k == "keyboard" {
		return k
	}
	pidSet := make(map[string]bool, len(product.ConnectionPIDs))
	for _, raw := range product.ConnectionPIDs {
		pidSet[strings.ToUpper(strings.TrimSpace(raw))] = true
	}
	classes := map[string]bool{}
	for _, c := range inv.Connections {
		if !pidSet[strings.ToUpper(strings.TrimSpace(c.PID))] {
			continue
		}
		if k := storedConnectionDeviceClass(c); k == "mouse" || k == "keyboard" {
			classes[k] = true
		}
	}
	if len(classes) == 1 {
		for k := range classes {
			return k
		}
	}
	return "device"
}

func inventorySummary(inv DeviceInventory) string {
	required := 0
	for _, p := range inv.Products {
		if p.Required {
			required++
		}
	}
	return fmt.Sprintf("%d/%d", required, len(inv.Connections))
}

var _ = errors.New
