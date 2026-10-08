//go:build windows

package main

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strconv"
	"strings"
	"syscall"
	"time"
	"unsafe"
)

func isAdmin() bool {
	r, _, _ := procIsUserAnAdmin.Call()
	return r != 0
}

func hasArg(name string) bool {
	for _, v := range os.Args[1:] {
		if strings.EqualFold(v, name) {
			return true
		}
	}
	return false
}

func argValue(name string) string {
	for i := 1; i < len(os.Args); i++ {
		if strings.EqualFold(os.Args[i], name) && i+1 < len(os.Args) {
			return os.Args[i+1]
		}
		if strings.HasPrefix(strings.ToLower(os.Args[i]), strings.ToLower(name)+"=") {
			return os.Args[i][len(name)+1:]
		}
	}
	return ""
}

func quoteWindowsArg(v string) string {
	if !strings.ContainsAny(v, " \t\"") {
		return v
	}
	return `"` + strings.ReplaceAll(v, `"`, `\"`) + `"`
}

func quotePowerShellLiteral(v string) string {
	return "'" + strings.ReplaceAll(v, "'", "''") + "'"
}

func buildHealthEngineCommand(enginePath, inventoryPath, report, jsonPath, gatePath, progressPath string) string {
	// Windows PowerShell 5.1 otherwise emits redirected host output using the
	// legacy console code page. Force UTF-8 for stdout/stderr so EngineOutput is
	// valid UTF-8 while the BOM-normalized runtime script fixes source literals.
	return "$enc = New-Object System.Text.UTF8Encoding($false); " +
		"[Console]::OutputEncoding = $enc; $OutputEncoding = $enc; " +
		"& " + quotePowerShellLiteral(enginePath) +
		" -InventoryPath " + quotePowerShellLiteral(inventoryPath) +
		" -OutputPath " + quotePowerShellLiteral(report) +
		" -JsonOutputPath " + quotePowerShellLiteral(jsonPath) +
		" -GateOutputPath " + quotePowerShellLiteral(gatePath) +
		" -ProgressOutputPath " + quotePowerShellLiteral(progressPath) +
		" -ExitWithCode"
}

func launchElevatedHelper(params string) bool {
	exe, err := os.Executable()
	if err != nil {
		return false
	}
	r, _, _ := procShellExecuteW.Call(0,
		uintptr(unsafe.Pointer(utf16("runas"))), uintptr(unsafe.Pointer(utf16(exe))),
		uintptr(unsafe.Pointer(utf16(params))), 0, swShow)
	return r > 32
}

func runPowerShellEngine(enginePath, inventoryPath, report, jsonPath, gatePath, progressPath, engineOut string) (int, error, time.Duration) {
	started := time.Now()
	psCommand := buildHealthEngineCommand(enginePath, inventoryPath, report, jsonPath, gatePath, progressPath)
	cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
		"-Command", psCommand)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	var stdout, stderr bytes.Buffer
	cmd.Stdout = &stdout
	cmd.Stderr = &stderr
	err := cmd.Run()
	dur := time.Since(started)
	code := 0
	if err != nil {
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			code = ee.ExitCode()
		} else {
			code = -1
		}
	}

	// Golden v1.7.0 wraps the engine's stdout/stderr with stable metadata. This
	// metadata is also the canonical source for History duration reconstruction.
	var b strings.Builder
	fmt.Fprintf(&b, "ToolVersion: %s\r\n", referenceVersion)
	fmt.Fprintf(&b, "Started: %s\r\n", started.Format(time.RFC3339Nano))
	fmt.Fprintf(&b, "Duration: %s\r\n", dur)
	fmt.Fprintf(&b, "ExitCode: %d\r\n", code)
	if err == nil {
		fmt.Fprint(&b, "RunError: <nil>\r\n")
	} else {
		fmt.Fprintf(&b, "RunError: %v\r\n", err)
	}
	fmt.Fprint(&b, "Command: ")
	for i, arg := range cmd.Args {
		if i > 0 {
			b.WriteByte(' ')
		}
		b.WriteString(quoteWindowsArg(arg))
	}
	fmt.Fprint(&b, "\r\n\r\n=== STDOUT ===\r\n")
	b.WriteString(normalizeCRLF(stdout.String()))
	fmt.Fprint(&b, "\r\n=== STDERR ===\r\n")
	b.WriteString(normalizeCRLF(stderr.String()))
	_ = os.WriteFile(engineOut, []byte(b.String()), 0644)
	return code, err, dur
}

func normalizeCRLF(s string) string {
	s = strings.ReplaceAll(s, "\r\n", "\n")
	s = strings.ReplaceAll(s, "\r", "\n")
	return strings.ReplaceAll(s, "\n", "\r\n")
}

func (a *App) startCheck() {
	a.mu.Lock()
	ready := a.setupReady
	scanning := a.setupScanning
	hasActiveProduct := hasActiveHealthcheckProduct(a.inventory)
	a.mu.Unlock()
	if !ready {
		a.debugf("HEALTH blocked setupReady=false setupScanning=%t", scanning)
		a.mu.Lock()
		a.currentView = 0
		a.setupContinueHealth = true
		a.mu.Unlock()
		procInvalidateRect.Call(a.hwnd, 0, 0)
		if !scanning {
			a.startSetupScan()
		}
		return
	}
	if !hasActiveProduct {
		a.mu.Lock()
		a.currentView = 0
		a.setupContinueHealth = false
		a.setupNoticeVisible = true
		a.setupNoticeTitle = tr("setup.healthcheck.none.title")
		a.setupNoticeDetail = tr("setup.healthcheck.none.detail")
		a.hoverSetupNoticeButton = -1
		a.mu.Unlock()
		a.debugf("HEALTH blocked reason=no-active-healthcheck-product")
		procInvalidateRect.Call(a.hwnd, 0, 0)
		return
	}
	a.debugf("HEALTH start requested admin=false inventory=%q", a.inventoryPath)
	a.beginCheck(false)
}

func (a *App) beginCheck(admin bool) {
	a.mu.Lock()
	if a.checking || a.repairing {
		a.mu.Unlock()
		return
	}
	a.checking = true
	a.adminCheck = admin
	a.overall = overallChecking
	a.checkStarted = time.Now()
	a.completedGates = 0
	a.currentGate = trn("gate.progress.parallel", gateCount)
	a.detailGate = -1
	a.problemFindings = nil
	a.problemSnapshotPath = ""
	for i := 0; i < gateCount; i++ {
		a.states[i] = gateWaiting
		// Golden v1.7.0 closes into a single running state first: all gates
		// visibly enter PRÜFUNG before completed results replace them.
		a.liveGateDisplay[i] = gateChecking
		a.gateInspections[i] = GateInspection{}
	}
	a.mu.Unlock()
	procSetTimer.Call(a.hwnd, 1, 125, 0)
	a.setTray(nimModify, a.iconStatusPulse[0], tr("tray.tip.checking"))
	procInvalidateRect.Call(a.hwnd, 0, 0)
	go a.runHealthCheck(admin)
}

func (a *App) runHealthCheck(admin bool) {
	stamp := time.Now().Format("20060102-150405")
	report := filepath.Join(a.logsDir, "RazerHealth-"+stamp+".log")
	jsonPath := filepath.Join(a.diagDir, "RazerHealth-"+stamp+".json")
	gatePath := filepath.Join(a.diagDir, "GateResult-"+stamp+".txt")
	progressPath := filepath.Join(a.diagDir, "GateProgress-"+stamp+".txt")
	engineOut := filepath.Join(a.diagDir, "EngineOutput-"+stamp+".txt")
	assessmentPath := applicationAssessmentPath(a.diagDir, stamp)

	a.debugf("HEALTH worker start admin=%t report=%q json=%q gate=%q progress=%q engineOutput=%q", admin, report, jsonPath, gatePath, progressPath, engineOut)
	stop := make(chan struct{})
	done := make(chan struct{})
	go a.watchProgress(progressPath, stop, done)

	// Resolve the official Razer prod manifest in parallel with the base engine.
	// Version differences remain INFO-only; only the manifest-defined product
	// registration mapping can contribute an application-layer UNKNOWN result.
	versionCh := make(chan VersionStatus, 1)
	go func() { versionCh <- collectVersionStatus() }()

	code, runErr, dur := runPowerShellEngine(a.enginePath, a.inventoryPath, report, jsonPath, gatePath, progressPath, engineOut)
	a.debugf("HEALTH engine admin=%t exitCode=%d runErr=%v duration=%s", admin, code, runErr, dur)
	close(stop)
	<-done

	states, _, overall := parseGateFile(gatePath)
	inspections, inspectErr := loadGateInspections(jsonPath)
	versionStatus := <-versionCh
	a.persistVersionStatus(versionStatus)
	a.mu.Lock()
	a.versionStatus = versionStatus
	a.versionChecking = false
	a.mu.Unlock()

	appDiag, appDiagPath, appDiagErr := a.runAppEngineUserModeDiagnostic(stamp, "")
	assessmentFiles := []string{}
	if appDiagPath != "" {
		assessmentFiles = append(assessmentFiles, appDiagPath)
	}
	if appDiagErr != nil {
		a.debugf("HEALTH appengine diagnostic measurement=%s err=%v", stamp, appDiagErr)
	} else {
		a.debugf("HEALTH appengine diagnostic measurement=%s state=%s mainPid=%d systray=%t synapse=%t chroma=%t", stamp, appDiag.RuntimeState, appDiag.RuntimeMainPID, appDiag.SystrayPresent, appDiag.SynapsePresent, appDiag.ChromaPresent)
	}
	if inspectErr == nil {
		assessment := buildApplicationHealthAssessment(stamp, overall, states, versionStatus, appDiag, appDiagErr)
		applyApplicationHealthAssessment(&states, &inspections, assessment)
		if err := persistApplicationHealthComposition(jsonPath, gatePath, assessmentPath, assessment); err != nil {
			a.debugf("HEALTH application assessment persist failed measurement=%s err=%v", stamp, err)
		} else {
			assessmentFiles = append(assessmentFiles, assessmentPath)
		}
		a.debugf("HEALTH application assessment measurement=%s evaluated=%t impact=%t reason=%s synapseRegistration=%s chromaRegistration=%s", stamp, assessment.Evaluated, assessment.HealthImpact, assessment.ReasonCode, versionStatus.SynapseRegistrationState, versionStatus.ChromaRegistrationState)
	}
	states, display := finalGateSnapshot(states, inspections)

	needsDiagnostic := false
	for _, st := range display {
		if st == gateFailed || st == gateUnclear {
			needsDiagnostic = true
			break
		}
	}
	if needsDiagnostic {
		a.mu.Lock()
		a.currentGate = tr("diagnostic.running")
		a.mu.Unlock()
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	}
	findings, problemFiles := a.runDiagnosticOrchestrator(stamp, display, inspections, appDiag, appDiagPath, appDiagErr)

	a.mu.Lock()
	a.checking = false
	a.lastDuration = dur
	a.lastCheck = time.Now()
	a.states = states
	a.liveGateDisplay = display
	if inspectErr == nil {
		a.gateInspections = inspections
	}
	a.lastGateStates = states
	a.lastGateInspections = a.gateInspections
	a.problemFindings = append([]ProblemFinding(nil), findings...)
	a.problemSnapshotPath = filepath.Join(a.diagDir, "ProblemFindings-"+stamp+".json")
	measurementFiles := []string{report, jsonPath, gatePath, progressPath, engineOut}
	measurementFiles = append(measurementFiles, assessmentFiles...)
	measurementFiles = append(measurementFiles, problemFiles...)
	a.lastMeasurement = MeasurementExportState{Stamp: stamp, StartedAt: a.checkStarted, CompletedAt: a.lastCheck, Files: measurementFiles}
	failed := false
	unclear := false
	for _, st := range display {
		switch st {
		case gateFailed:
			failed = true
		case gateUnclear:
			unclear = true
		}
	}
	if overall == "FAILED" || failed || (runErr != nil && code != 4) {
		a.overall = overallFailed
	} else if unclear {
		a.overall = overallIncomplete
	} else {
		a.overall = overallHealthy
	}
	switch a.overall {
	case overallFailed:
		a.lastMeasurement.Overall = "FAILED"
	case overallIncomplete:
		a.lastMeasurement.Overall = "UNCLEAR"
	default:
		a.lastMeasurement.Overall = "PASS"
	}
	a.mu.Unlock()

	switch a.overall {
	case overallFailed:
		a.setTray(nimModify, a.iconFail, tr("tray.tip.failed"))
	case overallIncomplete:
		a.setTray(nimModify, a.iconIdle, tr("tray.tip.incomplete"))
	default:
		a.setTray(nimModify, a.iconPass, tr("tray.tip.healthy"))
	}
	a.debugf("HEALTH complete admin=%t overall=%s parsedGates=%d duration=%s", admin, exportOverall(a.lastMeasurement.Overall), gateCount, dur)
	procPostMessageW.Call(a.hwnd, wmEngineDone, 0, 0)
	a.refreshMeasurementsAsync()
}

func (a *App) watchProgress(path string, stop <-chan struct{}, done chan<- struct{}) {
	defer close(done)
	ticker := time.NewTicker(180 * time.Millisecond)
	defer ticker.Stop()
	last := ""
	for {
		select {
		case <-stop:
			a.applyProgressFile(path, &last)
			return
		case <-ticker.C:
			a.applyProgressFile(path, &last)
		}
	}
}

func (a *App) applyProgressFile(path string, lastSig *string) {
	b, err := os.ReadFile(path)
	if err != nil {
		return
	}
	sig := shaHex(b)
	if sig == *lastSig {
		return
	}
	*lastSig = sig
	states, display, current, done, ok := parseProgressFile(b)
	if !ok {
		return
	}
	a.mu.Lock()
	a.states = states
	a.liveGateDisplay = display
	a.currentGate = current
	a.completedGates = done
	a.mu.Unlock()
	a.debugf("HEALTH progress completed=%d current=%q states=%v display=%v", done, current, states, display)
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
}

func parseProgressFile(b []byte) (states [gateCount]string, display [gateCount]string, current string, done int, ok bool) {
	for i := range states {
		states[i] = "WARTET"
		// Golden keeps all not-yet-final gates in the visible PRÜFUNG state
		// for the complete run, rather than reverting them to idle grey.
		display[i] = gateChecking
	}
	sc := bufio.NewScanner(strings.NewReader(string(b)))
	first := true
	for sc.Scan() {
		line := strings.TrimSpace(sc.Text())
		if first {
			first = false
			if line != "RHM_PROGRESS_V2" {
				return states, display, "", 0, false
			}
			continue
		}
		p := strings.Split(line, "|")
		if len(p) >= 5 && p[0] == "GATE" {
			idx, _ := strconv.Atoi(p[1])
			if idx < 1 || idx > gateCount {
				continue
			}
			engineState := p[2]
			severity := p[3]
			states[idx-1] = engineState
			if engineState == "CHECKING" {
				display[idx-1] = gateChecking
			} else {
				display[idx-1] = severityToDisplay(severity)
				done++
			}
		}
	}
	remaining := gateCount - done
	if remaining > 1 {
		current = trn("gate.progress.parallel", remaining)
	} else if remaining == 1 {
		current = trn("gate.progress.parallel", 1)
	} else {
		current = ""
	}
	return states, display, current, done, true
}

func parseGateFile(path string) (states [gateCount]string, count int, overall string) {
	for i := range states {
		states[i] = "UNKNOWN"
	}
	f, err := os.Open(path)
	if err != nil {
		return states, 0, ""
	}
	defer f.Close()
	sc := bufio.NewScanner(f)
	first := true
	for sc.Scan() {
		p := strings.Split(strings.TrimSpace(sc.Text()), "|")
		if first {
			first = false
			if len(p) == 0 || p[0] != "RHM_GATE_RESULT_V1" {
				return states, 0, ""
			}
			continue
		}
		if len(p) >= 2 && p[0] == "OVERALL" {
			overall = p[1]
		}
		if len(p) >= 4 && p[0] == "GATE" {
			idx, _ := strconv.Atoi(p[1])
			if idx >= 1 && idx <= gateCount {
				states[idx-1] = p[2]
				count++
			}
		}
	}
	return
}

func gateInspectionsFromEngineResult(result EngineResult) [gateCount]GateInspection {
	var out [gateCount]GateInspection
	for i := 0; i < gateCount; i++ {
		out[i].Available = i < len(result.Gates)
		if i < len(result.Gates) {
			out[i].GateDetail = result.Gates[i].Detail
		}
		for _, c := range result.Checks {
			if gateCheckBelongs(i, c) {
				out[i].Checks = append(out[i].Checks, c)
			}
		}
	}
	return out
}

func loadGateInspections(path string) ([gateCount]GateInspection, error) {
	var out [gateCount]GateInspection
	b, err := os.ReadFile(path)
	if err != nil {
		return out, err
	}
	var result EngineResult
	if err := json.Unmarshal(b, &result); err != nil {
		return out, err
	}
	return gateInspectionsFromEngineResult(result), nil
}

func gateCheckBelongs(idx int, c EngineCheck) bool {
	section := strings.ToLower(strings.TrimSpace(c.Section))
	check := strings.ToLower(strings.TrimSpace(c.Check))
	switch idx {
	case 0:
		return section == "appengine"
	case 1:
		return section == "driverstore"
	case 2:
		return section == "kernel drivers"
	case 3:
		return section == "live pnp" && (strings.Contains(check, "produkt ") || strings.Contains(check, "physical nodes") || strings.Contains(check, "problemcode"))
	case 4:
		return section == "live pnp" && (strings.Contains(check, "rzvirtual") || strings.Contains(check, "rzcontrol") || strings.Contains(check, "razer-bound nodes"))
	case 5:
		return section == "device filters"
	case 6:
		return section == "chroma registry (32-bit)"
	case 7:
		return section == "services" && (strings.Contains(check, "chroma sdk") || strings.Contains(check, "chroma stream"))
	case 8:
		return section == "services" && (strings.Contains(check, "razerexperienceservice") || strings.Contains(check, "razer elevation service"))
	case 9:
		return section == "services" && strings.Contains(check, "game manager")
	case 10:
		return section == "rzcomdriver"
	case 11:
		return section == "power state"
	case 12:
		return section == "lamparray"
	}
	return false
}

func gateDisplayState(engineState string, inspection GateInspection) string {
	if engineState == "CHECKING" {
		return gateChecking
	}
	if engineState == "FAILED" {
		return gateFailed
	}
	if engineState == "ADMIN ERFORDERLICH" {
		return gateUnclear
	}
	rank := 0
	for _, c := range inspection.Checks {
		if strings.EqualFold(strings.TrimSpace(c.EvidenceRole), "SUPPORTING") {
			continue
		}
		switch strings.ToUpper(c.Status) {
		case "FAIL":
			if rank < 3 {
				rank = 3
			}
		case "UNKNOWN":
			if rank < 2 {
				rank = 2
			}
		case "WARN":
			if rank < 1 {
				rank = 1
			}
		}
	}
	switch rank {
	case 3:
		return gateFailed
	case 2:
		return gateUnclear
	case 1:
		return gateHint
	}
	if engineState == "PASS" {
		return gatePassed
	}
	return gateUnclear
}

func gateDisplayStates(states [gateCount]string, inspections [gateCount]GateInspection) (out [gateCount]string) {
	for i := 0; i < gateCount; i++ {
		out[i] = gateDisplayState(states[i], inspections[i])
	}
	return
}

// finalGateSnapshot is the lifecycle boundary between progress and result UI.
// A completed worker must never leave CHECKING in either the stored engine
// states or the user-facing display, even if a malformed/stale sidecar line
// were ever to contain that transient value.
func finalGateSnapshot(states [gateCount]string, inspections [gateCount]GateInspection) ([gateCount]string, [gateCount]string) {
	for i := 0; i < gateCount; i++ {
		if strings.EqualFold(strings.TrimSpace(states[i]), gateChecking) {
			states[i] = "UNKNOWN"
		}
	}
	display := gateDisplayStates(states, inspections)
	for i := 0; i < gateCount; i++ {
		if display[i] == gateChecking {
			display[i] = gateUnclear
		}
	}
	return states, display
}

func severityToDisplay(s string) string {
	switch strings.ToUpper(strings.TrimSpace(s)) {
	case "PASS", "BESTANDEN":
		return gatePassed
	case "HINWEIS", "WARN":
		return gateHint
	case "UNKLAR", "UNKNOWN":
		return gateUnclear
	case "FEHLER", "FAILED", "FAIL":
		return gateFailed
	case "CHECKING":
		return gateChecking
	case "INFO":
		return "INFO"
	}
	return gateWaiting
}

func formatElapsed(d time.Duration) string {
	if d < 0 {
		d = 0
	}
	if d < time.Minute {
		return fmt.Sprintf("%.1f s", d.Seconds())
	}
	m := int(d / time.Minute)
	s := int((d % time.Minute) / time.Second)
	return fmt.Sprintf("%d:%02d min", m, s)
}

func runAdminHelperMain() {
	// Recovery compatibility path. The normal v1.7.0 monitor remains unelevated.
	engine := argValue("--engine")
	inventory := argValue("--inventory")
	report := argValue("--report")
	jp := argValue("--json")
	gp := argValue("--gate")
	pp := argValue("--progress")
	op := argValue("--engine-out")
	if engine == "" {
		os.Exit(3)
	}
	code, _, _ := runPowerShellEngine(engine, inventory, report, jp, gp, pp, op)
	os.Exit(code)
}

func joinReason(a, b string) string {
	if a == "" {
		return b
	}
	if b == "" {
		return a
	}
	return a + "; " + b
}
