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
	"regexp"
	"strings"
	"syscall"
	"time"
)

const (
	repairVersionChromaServices = "1.1.0"
	repairGateChromaServices    = 7 // zero-based Gate 8

	repairDialogNone = iota
	repairDialogConfirm
	repairDialogRunning
	repairDialogResult
)

var chromaRepairServiceNames = []string{
	"Razer Chroma SDK Service",
	"Razer Chroma SDK Server",
}

type RepairServiceSnapshot struct {
	Name      string `json:"Name"`
	State     string `json:"State"`
	StartMode string `json:"StartMode"`
	ProcessID uint32 `json:"ProcessId"`
	ExitCode  uint32 `json:"ExitCode"`
	Path      string `json:"Path"`
}

type RepairActionResult struct {
	Name      string `json:"Name"`
	Attempted bool   `json:"Attempted"`
	Success   bool   `json:"Success"`
	Message   string `json:"Message"`
	HResult   string `json:"HResult"`
}

type RepairDependencySnapshot struct {
	Name       string   `json:"Name"`
	DependsOn  []string `json:"DependsOn"`
	Dependents []string `json:"Dependents"`
}

type RepairResult struct {
	SchemaVersion        int                        `json:"SchemaVersion"`
	RepairID             string                     `json:"RepairId"`
	ToolVersion          string                     `json:"ToolVersion"`
	RepairVersion        string                     `json:"RepairVersion"`
	ProblemID            string                     `json:"ProblemId"`
	RecipeID             string                     `json:"RecipeId"`
	ConfirmedByUser      bool                       `json:"ConfirmedByUser"`
	TargetGate           int                        `json:"TargetGate"`
	Started              string                     `json:"Started"`
	Completed            string                     `json:"Completed"`
	Elevated             bool                       `json:"Elevated"`
	Status               string                     `json:"Status"`
	Message              string                     `json:"Message"`
	Before               []RepairServiceSnapshot    `json:"Before"`
	Actions              []RepairActionResult       `json:"Actions"`
	After5Seconds        []RepairServiceSnapshot    `json:"After5Seconds"`
	Dependencies         []RepairDependencySnapshot `json:"Dependencies"`
	ExitCode             int                        `json:"ExitCode"`
	VerificationStatus   string                     `json:"VerificationStatus"`
	VerificationDetail   string                     `json:"VerificationDetail"`
	VerificationModuleID string                     `json:"VerificationModuleId"`
	VerificationVersion  string                     `json:"VerificationVersion"`
	VerifiedAt           string                     `json:"VerifiedAt"`
	ActionMode           string                     `json:"ActionMode,omitempty"`
	RuntimeBefore        any                        `json:"RuntimeBefore,omitempty"`
	RuntimeAfter         any                        `json:"RuntimeAfter,omitempty"`
}

func (r RepairResult) successful() bool {
	return strings.EqualFold(r.Status, "SUCCESS") && r.ExitCode == 0 && r.ConfirmedByUser && strings.EqualFold(r.VerificationStatus, "PASS")
}

// chromaServiceRepairTargets remains as a conservative compatibility detector for
// validators and technical diagnostics. Product repair availability in v3.0.0 is
// driven by the structured ProblemFinding produced by the diagnostic orchestrator.
func chromaServiceRepairTargets(state string, ins GateInspection) ([]string, bool) {
	if !strings.EqualFold(strings.TrimSpace(state), gateFailed) || !ins.Available {
		return nil, false
	}
	checks := make(map[string]EngineCheck)
	for _, c := range ins.Checks {
		if strings.EqualFold(strings.TrimSpace(c.Section), "Services") {
			checks[strings.TrimSpace(c.Check)] = c
		}
	}
	stateHas := func(name, state, mode string) bool {
		c, ok := checks[name]
		if !ok {
			return false
		}
		a := strings.ToLower(strings.TrimSpace(c.Actual))
		return strings.Contains(a, strings.ToLower(state)) && strings.Contains(a, strings.ToLower(mode))
	}
	if !stateHas("Razer Chroma SDK Diagnostic Service", "running", "auto") || !stateHas("Razer Chroma Stream Server", "stopped", "manual") {
		return nil, false
	}
	targets := []string{}
	for _, name := range chromaRepairServiceNames {
		if stateHas(name, "stopped", "auto") {
			targets = append(targets, name)
		} else if !stateHas(name, "running", "auto") {
			return nil, false
		}
	}
	return targets, len(targets) > 0
}

func (a *App) currentRepairTargets() ([]string, ProblemFinding, RepairDefinition, bool) {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.detailGate < 0 || a.checking || a.repairing {
		return nil, ProblemFinding{}, RepairDefinition{}, false
	}
	finding, ok := problemFindingForGate(a.problemFindings, a.detailGate)
	if !ok || finding.Classification != problemClassKnown || !finding.RepairAvailable || finding.RepairID == "" || !finding.ConfirmationRequired {
		return nil, ProblemFinding{}, RepairDefinition{}, false
	}
	def, ok := repairDefinitionByID(finding.RepairID)
	if !ok || !def.ConfirmationRequired {
		return nil, ProblemFinding{}, RepairDefinition{}, false
	}
	allowed := false
	for _, id := range def.ProblemIDs {
		if id == finding.ProblemID {
			allowed = true
			break
		}
	}
	if !allowed || len(finding.Targets) == 0 {
		return nil, ProblemFinding{}, RepairDefinition{}, false
	}
	return append([]string(nil), finding.Targets...), finding, def, true
}

func (a *App) openRepairConfirmation() {
	targets, finding, def, ok := a.currentRepairTargets()
	if !ok {
		return
	}
	a.mu.Lock()
	a.repairDialogVisible = true
	a.repairDialogStage = repairDialogConfirm
	a.repairTargets = append([]string(nil), targets...)
	a.repairProblemID = finding.ProblemID
	a.repairRecipeID = def.RepairID
	a.repairResult = RepairResult{}
	a.repairResultErr = ""
	a.hoverRepairButton = -1
	a.mu.Unlock()
	a.debugf("REPAIR confirmation required problemId=%s recipeId=%s gate=%d targets=%q", finding.ProblemID, def.RepairID, finding.Gate, strings.Join(targets, ";"))
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func (a *App) closeRepairDialog() bool {
	a.mu.Lock()
	if !a.repairDialogVisible {
		a.mu.Unlock()
		return false
	}
	if a.repairDialogStage == repairDialogRunning {
		a.mu.Unlock()
		return true
	}
	a.repairDialogVisible = false
	a.repairDialogStage = repairDialogNone
	a.hoverRepairButton = -1
	a.mu.Unlock()
	procInvalidateRect.Call(a.hwnd, 0, 0)
	return true
}

// startSelectedRepair is only reachable from the explicit confirmation
// button while repairDialogStage == repairDialogConfirm. There is intentionally
// no orchestrator path that can execute a repair automatically.
func (a *App) startSelectedRepair() {
	a.mu.Lock()
	if a.repairing || !a.repairDialogVisible || a.repairDialogStage != repairDialogConfirm {
		a.mu.Unlock()
		return
	}
	targets := append([]string(nil), a.repairTargets...)
	problemID := a.repairProblemID
	recipeID := a.repairRecipeID
	def, ok := repairDefinitionByID(recipeID)
	if !ok || !def.ConfirmationRequired || len(targets) == 0 || problemID == "" {
		a.mu.Unlock()
		return
	}
	allowed := false
	for _, id := range def.ProblemIDs {
		if id == problemID {
			allowed = true
			break
		}
	}
	if !allowed {
		a.mu.Unlock()
		return
	}
	repairID := time.Now().Format("20060102-150405.000") + fmt.Sprintf("-%d", os.Getpid())
	repairDir := filepath.Join(a.diagDir, "Repairs")
	_ = os.MkdirAll(repairDir, 0755)
	base := "Repair-" + a.session + "-" + repairID
	resultPath := filepath.Join(repairDir, base+".json")
	logPath := filepath.Join(repairDir, base+".log")
	script := filepath.Join(a.runtimeDir, "repair", def.RuntimeFile)
	a.repairing = true
	a.repairDialogStage = repairDialogRunning
	a.repairID = repairID
	a.repairResultPath = resultPath
	a.repairLogPath = logPath
	a.repairResult = RepairResult{}
	a.repairResultErr = ""
	a.hoverRepairButton = -1
	a.mu.Unlock()

	args := []string{
		"--repair-helper",
		"--script", script,
		"--result", resultPath,
		"--log", logPath,
		"--repair-id", repairID,
		"--problem-id", problemID,
		"--repair-recipe", recipeID,
	}
	a.debugf("REPAIR user-confirmed launch id=%s problemId=%s recipeId=%s targets=%q script=%q result=%q requiresElevation=%t", repairID, problemID, recipeID, strings.Join(targets, ";"), script, resultPath, def.RequiresElevation)
	if !launchRepairHelper(args, def.RequiresElevation) {
		a.mu.Lock()
		a.repairing = false
		a.repairDialogStage = repairDialogResult
		if def.RequiresElevation {
			a.repairResultErr = "UAC_CANCELLED"
		} else {
			a.repairResultErr = "LAUNCH_FAILED"
		}
		a.mu.Unlock()
		a.debugf("REPAIR launch failed/cancelled id=%s elevation=%t", repairID, def.RequiresElevation)
		procPostMessageW.Call(a.hwnd, wmRepairDone, 0, 0)
		return
	}
	go a.waitForRepairResult(resultPath, repairID)
	procInvalidateRect.Call(a.hwnd, 0, 0)
}

func launchRepairHelper(args []string, elevated bool) bool {
	if elevated {
		params := make([]string, 0, len(args))
		for _, arg := range args {
			params = append(params, quoteWindowsArg(arg))
		}
		return launchElevatedHelper(strings.Join(params, " "))
	}
	exe, err := os.Executable()
	if err != nil {
		return false
	}
	cmd := exec.Command(exe, args...)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	return cmd.Start() == nil
}

func (a *App) waitForRepairResult(path, repairID string) {
	a.mu.Lock()
	recipeID := a.repairRecipeID
	a.mu.Unlock()
	timeout := 90 * time.Second
	if recipeID == repairAppEngineControlledRecovery {
		timeout = 150 * time.Second
	}
	deadline := time.Now().Add(timeout)
	var result RepairResult
	var err error
	for time.Now().Before(deadline) {
		b, er := os.ReadFile(path)
		if er == nil && len(b) > 0 {
			if er = json.Unmarshal(bytes.TrimPrefix(b, []byte{0xEF, 0xBB, 0xBF}), &result); er == nil {
				err = nil
				break
			}
			err = er
		}
		time.Sleep(250 * time.Millisecond)
	}
	if result.RepairID == "" {
		if err == nil {
			err = errors.New("repair helper timeout")
		}
	}
	if err == nil {
		a.mu.Lock()
		expectedProblemID := a.repairProblemID
		expectedRecipeID := a.repairRecipeID
		a.mu.Unlock()
		if result.RepairID != repairID || result.ProblemID != expectedProblemID || result.RecipeID != expectedRecipeID || !result.ConfirmedByUser {
			err = errors.New("repair result identity/confirmation contract mismatch")
		}
	}
	if err == nil {
		result, err = a.verifyRepairOutcome(path, result)
	}
	a.mu.Lock()
	a.repairing = false
	a.repairDialogStage = repairDialogResult
	if err != nil {
		a.repairResultErr = err.Error()
	} else {
		a.repairResult = result
		a.repairResultErr = ""
	}
	a.mu.Unlock()
	if err != nil {
		a.debugf("REPAIR result/verification error id=%s err=%v", repairID, err)
	} else {
		a.debugf("REPAIR complete id=%s problemId=%s recipeId=%s status=%s exitCode=%d verification=%s", repairID, result.ProblemID, result.RecipeID, result.Status, result.ExitCode, result.VerificationStatus)
	}
	procPostMessageW.Call(a.hwnd, wmRepairDone, 0, 0)
}

func (a *App) verifyRepairOutcome(resultPath string, result RepairResult) (RepairResult, error) {
	switch result.RecipeID {
	case repairChromaStartStoppedAuto:
		return a.verifyChromaRepairOutcome(resultPath, result)
	case repairAppEngineControlledRecovery:
		return a.verifyAppEngineRepairOutcome(resultPath, result)
	default:
		result.VerificationStatus = "UNKNOWN"
		result.VerificationDetail = "Unknown repair recipe; post-repair verification unavailable."
		result.VerifiedAt = time.Now().Format(time.RFC3339Nano)
		_ = writeRepairResult(resultPath, result)
		return result, nil
	}
}

func (a *App) verifyChromaRepairOutcome(resultPath string, result RepairResult) (RepairResult, error) {
	result.VerifiedAt = time.Now().Format(time.RFC3339Nano)
	result.VerificationModuleID = chromaDiagnosticModuleID
	result.VerificationVersion = chromaDiagnosticModuleVersion
	if !strings.EqualFold(result.Status, "SUCCESS") || result.ExitCode != 0 {
		result.VerificationStatus = "NOT_RUN"
		result.VerificationDetail = "Repair action did not report SUCCESS; post-repair verification not accepted."
		_ = writeRepairResult(resultPath, result)
		return result, nil
	}
	stamp := "Repair-" + strings.NewReplacer(".", "_", ":", "_").Replace(result.RepairID)
	diag, _, err := a.runChromaServiceDiagnostic(stamp, "Verify")
	if err != nil {
		result.VerificationStatus = "UNKNOWN"
		result.VerificationDetail = err.Error()
		_ = writeRepairResult(resultPath, result)
		return result, nil
	}
	m := chromaDiagnosticServiceMap(diag)
	expected := map[string][2]string{
		"Razer Chroma SDK Diagnostic Service": {"Running", "Auto"},
		"Razer Chroma Stream Server":          {"Stopped", "Manual"},
		"Razer Chroma SDK Server":             {"Running", "Auto"},
		"Razer Chroma SDK Service":            {"Running", "Auto"},
	}
	failures := []string{}
	for name, want := range expected {
		svc, ok := m[strings.ToLower(name)]
		if !ok || !isServiceState(svc, want[0], want[1]) {
			actual := "NOT_FOUND"
			if ok {
				actual = strings.TrimSpace(svc.State) + " / " + strings.TrimSpace(svc.StartMode)
			}
			failures = append(failures, name+"="+actual)
		}
	}
	if len(failures) == 0 {
		result.VerificationStatus = "PASS"
		result.VerificationDetail = "Targeted Gate-8 service verification passed after repair."
	} else {
		result.VerificationStatus = "FAIL"
		result.VerificationDetail = strings.Join(failures, "; ")
	}
	if err := writeRepairResult(resultPath, result); err != nil {
		return result, err
	}
	return result, nil
}

func (a *App) verifyAppEngineRepairOutcome(resultPath string, result RepairResult) (RepairResult, error) {
	result.VerifiedAt = time.Now().Format(time.RFC3339Nano)
	result.VerificationModuleID = appEngineDiagnosticModuleID
	result.VerificationVersion = appEngineDiagnosticModuleVersion
	if !strings.EqualFold(result.Status, "SUCCESS") || result.ExitCode != 0 {
		result.VerificationStatus = "NOT_RUN"
		result.VerificationDetail = "Repair action did not report SUCCESS; post-repair verification not accepted."
		_ = writeRepairResult(resultPath, result)
		return result, nil
	}
	stamp := "Repair-" + strings.NewReplacer(".", "_", ":", "_").Replace(result.RepairID)
	diag, _, err := a.runAppEngineUserModeDiagnostic(stamp, "Verify")
	if err != nil {
		result.VerificationStatus = "UNKNOWN"
		result.VerificationDetail = err.Error()
		_ = writeRepairResult(resultPath, result)
		return result, nil
	}
	if strings.EqualFold(diag.RuntimeState, appEngineRuntimeHealthy) && diag.RunContractValid && diag.SystrayPresent && diag.SynapsePresent && diag.ChromaPresent {
		result.VerificationStatus = "PASS"
		result.VerificationDetail = "AppEngine user-mode runtime, Synapse, Chroma and systray contract verified read-only after repair."
	} else {
		result.VerificationStatus = "FAIL"
		result.VerificationDetail = fmt.Sprintf("RuntimeState=%s RunContractValid=%t Systray=%t Synapse=%t Chroma=%t", diag.RuntimeState, diag.RunContractValid, diag.SystrayPresent, diag.SynapsePresent, diag.ChromaPresent)
	}
	if err := writeRepairResult(resultPath, result); err != nil {
		return result, err
	}
	return result, nil
}

func writeRepairResult(path string, result RepairResult) error {
	b, err := json.MarshalIndent(result, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0644)
}

func runRepairHelperMain() {
	script := argValue("--script")
	result := argValue("--result")
	logPath := argValue("--log")
	repairID := argValue("--repair-id")
	problemID := argValue("--problem-id")
	recipeID := argValue("--repair-recipe")
	if !validateRepairHelperContract(script, result, logPath, repairID, problemID, recipeID) {
		os.Exit(3)
	}
	code, _ := runRepairPowerShell(script, result, logPath, repairID, problemID, recipeID)
	os.Exit(code)
}

func pathInside(base, candidate string) bool {
	b, err1 := filepath.Abs(filepath.Clean(base))
	c, err2 := filepath.Abs(filepath.Clean(candidate))
	if err1 != nil || err2 != nil {
		return false
	}
	rel, err := filepath.Rel(b, c)
	if err != nil || rel == "." {
		return false
	}
	return rel != ".." && !strings.HasPrefix(rel, ".."+string(os.PathSeparator))
}

func validateRepairHelperContract(script, result, logPath, repairID, problemID, recipeID string) bool {
	if script == "" || result == "" || logPath == "" || repairID == "" || problemID == "" || recipeID == "" {
		return false
	}
	if ok, _ := regexp.MatchString(`^[0-9]{8}-[0-9]{6}\.[0-9]{3}-[0-9]+$`, repairID); !ok {
		return false
	}
	def, ok := repairDefinitionByID(recipeID)
	if !ok || !def.ConfirmationRequired {
		return false
	}
	problemAllowed := false
	for _, id := range def.ProblemIDs {
		if id == problemID {
			problemAllowed = true
			break
		}
	}
	if !problemAllowed {
		return false
	}
	exe, err := os.Executable()
	if err != nil {
		return false
	}
	dataDir := filepath.Dir(exe)
	expectedScript := filepath.Join(dataDir, "Runtime", "repair", def.RuntimeFile)
	sp, _ := filepath.Abs(filepath.Clean(script))
	ep, _ := filepath.Abs(filepath.Clean(expectedScript))
	if !strings.EqualFold(sp, ep) {
		return false
	}
	disk, err := os.ReadFile(script)
	if err != nil {
		return false
	}
	emb, err := embedded.ReadFile(def.ScriptAsset)
	if err != nil || shaHex(disk) != shaHex(emb) {
		return false
	}
	repairDir := filepath.Join(dataDir, "Diagnostics", "Repairs")
	if !pathInside(repairDir, result) || !pathInside(repairDir, logPath) {
		return false
	}
	if !strings.HasSuffix(strings.ToLower(result), ".json") || !strings.HasSuffix(strings.ToLower(logPath), ".log") {
		return false
	}
	return true
}

func runRepairPowerShell(script, result, logPath, repairID, problemID, recipeID string) (int, error) {
	cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
		"-File", script,
		"-ResultPath", result,
		"-LogPath", logPath,
		"-RepairId", repairID,
		"-ToolVersion", referenceVersion,
		"-ProblemId", problemID,
		"-RecipeId", recipeID)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	var stderr bytes.Buffer
	cmd.Stdout = nil
	cmd.Stderr = &stderr
	err := cmd.Run()
	code := 0
	if err != nil {
		var ee *exec.ExitError
		if errors.As(err, &ee) {
			code = ee.ExitCode()
		} else {
			code = -1
		}
		if _, statErr := os.Stat(result); statErr != nil {
			def, _ := repairDefinitionByID(recipeID)
			gate := 0
			if len(def.ProblemIDs) > 0 {
				if pd, ok := problemDefinitionByID(def.ProblemIDs[0]); ok {
					gate = pd.Gate
				}
			}
			fallback := RepairResult{SchemaVersion: 2, RepairID: repairID, ToolVersion: referenceVersion, RepairVersion: def.Version, ProblemID: problemID, RecipeID: recipeID, ConfirmedByUser: true, TargetGate: gate, Started: time.Now().Format(time.RFC3339Nano), Completed: time.Now().Format(time.RFC3339Nano), Elevated: isAdmin(), Status: "FAILED", Message: strings.TrimSpace(stderr.String()), ExitCode: code, VerificationStatus: "NOT_RUN"}
			_ = writeRepairResult(result, fallback)
		}
	}
	return code, err
}

func repairServiceState(result RepairResult, name string) string {
	for _, s := range result.After5Seconds {
		if strings.EqualFold(s.Name, name) {
			if s.State == "" {
				return tr("repair.result.unknown")
			}
			return trf("repair.result.service_state", "name", s.Name, "state", s.State, "startMode", s.StartMode)
		}
	}
	return trf("repair.result.service_missing", "name", name)
}
