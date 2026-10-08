//go:build windows

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"syscall"
	"time"
)

const (
	diagnosticOrchestratorVersion = "1.1.0"
	problemCatalogVersion         = "1.1.0"
	repairEngineVersion           = "2.1.0"

	chromaDiagnosticModuleID      = "RHC.DIAG.CHROMA.SERVICES"
	chromaDiagnosticModuleVersion = "1.0.0"
	chromaDiagnosticScriptName    = "diagnose-chroma-services-v1.0.0.ps1"

	problemChromaServicesStoppedAuto  = "RHC.CHROMA.SDK_SERVICES.STOPPED_AUTO"
	repairChromaStartStoppedAuto      = "RHC.REPAIR.CHROMA.START_STOPPED_AUTO"
	problemAppEngineRuntimeIncomplete = "RHC.APPENGINE.USERMODE.RUNTIME_INCOMPLETE"
	repairAppEngineControlledRecovery = "RHC.REPAIR.APPENGINE.CONTROLLED_RUNTIME_RECOVERY"
	repairVersionAppEngineRuntime     = "1.0.0"

	problemClassKnown        = "KNOWN"
	problemClassUnclassified = "UNCLASSIFIED"
	problemConfidenceExact   = "EXACT"
	problemConfidenceUnknown = "UNKNOWN"
)

type ProblemEvidence struct {
	Section      string `json:"section"`
	Check        string `json:"check"`
	Status       string `json:"status"`
	Actual       string `json:"actual"`
	Expected     string `json:"expected"`
	Detail       string `json:"detail"`
	EvidenceRole string `json:"evidenceRole,omitempty"`
}

type ProblemFinding struct {
	SchemaVersion        int               `json:"schemaVersion"`
	FindingID            string            `json:"findingId"`
	MeasurementStamp     string            `json:"measurementStamp"`
	Gate                 int               `json:"gate"`
	GateName             string            `json:"gateName"`
	GateState            string            `json:"gateState"`
	Classification       string            `json:"classification"`
	ProblemID            string            `json:"problemId,omitempty"`
	Title                string            `json:"title"`
	Detail               string            `json:"detail"`
	Confidence           string            `json:"confidence"`
	DiagnosticModuleID   string            `json:"diagnosticModuleId,omitempty"`
	DiagnosticVersion    string            `json:"diagnosticVersion,omitempty"`
	RepairID             string            `json:"repairId,omitempty"`
	RepairAvailable      bool              `json:"repairAvailable"`
	ConfirmationRequired bool              `json:"confirmationRequired"`
	RequiresElevation    bool              `json:"requiresElevation"`
	Targets              []string          `json:"targets,omitempty"`
	Evidence             []ProblemEvidence `json:"evidence,omitempty"`
}

type ProblemSnapshot struct {
	SchemaVersion       int              `json:"schemaVersion"`
	ToolVersion         string           `json:"toolVersion"`
	CatalogVersion      string           `json:"catalogVersion"`
	OrchestratorVersion string           `json:"orchestratorVersion"`
	MeasurementStamp    string           `json:"measurementStamp"`
	Timestamp           string           `json:"timestamp"`
	Findings            []ProblemFinding `json:"findings"`
}

type ProblemDefinition struct {
	ProblemID          string
	Gate               int
	TitleKey           string
	DetailKey          string
	DiagnosticModuleID string
	RepairID           string
}

type RepairDefinition struct {
	RepairID             string
	Version              string
	ProblemIDs           []string
	SafetyClass          string
	RequiresElevation    bool
	ConfirmationRequired bool
	ScriptAsset          string
	RuntimeFile          string
}

type ChromaDiagnosticService struct {
	Name        string `json:"Name"`
	ServiceName string `json:"ServiceName"`
	DisplayName string `json:"DisplayName"`
	State       string `json:"State"`
	StartMode   string `json:"StartMode"`
	ProcessID   uint32 `json:"ProcessId"`
	ExitCode    uint32 `json:"ExitCode"`
	Path        string `json:"Path"`
}

type ChromaDiagnosticResult struct {
	SchemaVersion    int                       `json:"SchemaVersion"`
	ModuleID         string                    `json:"ModuleId"`
	ModuleVersion    string                    `json:"ModuleVersion"`
	ToolVersion      string                    `json:"ToolVersion"`
	MeasurementStamp string                    `json:"MeasurementStamp"`
	Started          string                    `json:"Started"`
	Completed        string                    `json:"Completed"`
	Elevated         bool                      `json:"Elevated"`
	ReadOnly         bool                      `json:"ReadOnly"`
	Status           string                    `json:"Status"`
	Errors           []string                  `json:"Errors"`
	Services         []ChromaDiagnosticService `json:"Services"`
}

func problemCatalog() []ProblemDefinition {
	return []ProblemDefinition{
		{
			ProblemID:          problemChromaServicesStoppedAuto,
			Gate:               8,
			TitleKey:           "problem.chroma.stopped_auto.title",
			DetailKey:          "problem.chroma.stopped_auto.detail",
			DiagnosticModuleID: chromaDiagnosticModuleID,
			RepairID:           repairChromaStartStoppedAuto,
		},
		{
			ProblemID:          problemAppEngineRuntimeIncomplete,
			Gate:               1,
			TitleKey:           "problem.appengine.runtime_incomplete.title",
			DetailKey:          "problem.appengine.runtime_incomplete.detail",
			DiagnosticModuleID: appEngineDiagnosticModuleID,
			RepairID:           repairAppEngineControlledRecovery,
		},
	}
}

func repairCatalog() []RepairDefinition {
	return []RepairDefinition{
		{
			RepairID:             repairChromaStartStoppedAuto,
			Version:              repairVersionChromaServices,
			ProblemIDs:           []string{problemChromaServicesStoppedAuto},
			SafetyClass:          "CONFIRM",
			RequiresElevation:    true,
			ConfirmationRequired: true,
			ScriptAsset:          "repair/repair-chroma-services-v1.1.0.ps1",
			RuntimeFile:          "repair-chroma-services-v1.1.0.ps1",
		},
		{
			RepairID:             repairAppEngineControlledRecovery,
			Version:              repairVersionAppEngineRuntime,
			ProblemIDs:           []string{problemAppEngineRuntimeIncomplete},
			SafetyClass:          "CONFIRM",
			RequiresElevation:    false,
			ConfirmationRequired: true,
			ScriptAsset:          "repair/repair-appengine-runtime-v1.0.0.ps1",
			RuntimeFile:          "repair-appengine-runtime-v1.0.0.ps1",
		},
	}
}

func repairDefinitionByID(id string) (RepairDefinition, bool) {
	for _, d := range repairCatalog() {
		if d.RepairID == id {
			return d, true
		}
	}
	return RepairDefinition{}, false
}

func problemDefinitionByID(id string) (ProblemDefinition, bool) {
	for _, d := range problemCatalog() {
		if d.ProblemID == id {
			return d, true
		}
	}
	return ProblemDefinition{}, false
}

func problemEvidenceFromInspection(ins GateInspection) []ProblemEvidence {
	out := make([]ProblemEvidence, 0, len(ins.Checks))
	for _, c := range ins.Checks {
		s := strings.ToUpper(strings.TrimSpace(c.Status))
		if s == "PASS" || s == "PASSED" || s == "BESTANDEN" || s == "INFO" {
			continue
		}
		out = append(out, ProblemEvidence{
			Section: c.Section, Check: c.Check, Status: c.Status, Actual: c.Actual,
			Expected: c.Expected, Detail: c.Detail, EvidenceRole: c.EvidenceRole,
		})
	}
	return out
}

func (a *App) runChromaServiceDiagnostic(stamp, suffix string) (ChromaDiagnosticResult, string, error) {
	var out ChromaDiagnosticResult
	script := a.diagnosticChromaServicesPath
	if script == "" {
		return out, "", fmt.Errorf("chroma diagnostic runtime path missing")
	}
	disk, err := os.ReadFile(script)
	if err != nil {
		return out, "", err
	}
	emb, err := embedded.ReadFile("diagnostics/diagnose-chroma-services-v1.0.0.ps1")
	if err != nil || shaHex(disk) != shaHex(windowsPowerShellUTF8ScriptBytes(emb)) {
		return out, "", fmt.Errorf("diagnostic module integrity check failed")
	}
	name := "Diagnostic-ChromaServices-" + stamp
	if suffix != "" {
		name += "-" + suffix
	}
	resultPath := filepath.Join(a.diagDir, name+".json")
	cmd := exec.Command("powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass",
		"-File", script,
		"-ResultPath", resultPath,
		"-ToolVersion", referenceVersion,
		"-MeasurementStamp", stamp)
	cmd.SysProcAttr = &syscall.SysProcAttr{HideWindow: true}
	var stderr bytes.Buffer
	cmd.Stderr = &stderr
	err = cmd.Run()
	if err != nil {
		return out, resultPath, fmt.Errorf("diagnostic module: %w: %s", err, strings.TrimSpace(stderr.String()))
	}
	b, err := os.ReadFile(resultPath)
	if err != nil {
		return out, resultPath, err
	}
	if err := json.Unmarshal(bytes.TrimPrefix(b, []byte{0xEF, 0xBB, 0xBF}), &out); err != nil {
		return out, resultPath, err
	}
	if out.ModuleID != chromaDiagnosticModuleID || out.ModuleVersion != chromaDiagnosticModuleVersion || !out.ReadOnly {
		return out, resultPath, fmt.Errorf("diagnostic module contract mismatch")
	}
	return out, resultPath, nil
}

func chromaDiagnosticServiceMap(r ChromaDiagnosticResult) map[string]ChromaDiagnosticService {
	m := make(map[string]ChromaDiagnosticService, len(r.Services))
	for _, s := range r.Services {
		m[strings.ToLower(strings.TrimSpace(s.Name))] = s
	}
	return m
}

func isServiceState(s ChromaDiagnosticService, state, startMode string) bool {
	return strings.EqualFold(strings.TrimSpace(s.State), state) && strings.EqualFold(strings.TrimSpace(s.StartMode), startMode)
}

func classifyChromaStoppedAuto(stamp, gateState string, ins GateInspection, diag ChromaDiagnosticResult) (ProblemFinding, []string, bool) {
	if !strings.EqualFold(strings.TrimSpace(gateState), gateFailed) || !ins.Available {
		return ProblemFinding{}, nil, false
	}
	m := chromaDiagnosticServiceMap(diag)
	diagSvc, ok1 := m[strings.ToLower("Razer Chroma SDK Diagnostic Service")]
	streamSvc, ok2 := m[strings.ToLower("Razer Chroma Stream Server")]
	serverSvc, ok3 := m[strings.ToLower("Razer Chroma SDK Server")]
	sdkSvc, ok4 := m[strings.ToLower("Razer Chroma SDK Service")]
	if !(ok1 && ok2 && ok3 && ok4) {
		return ProblemFinding{}, nil, false
	}
	if !isServiceState(diagSvc, "Running", "Auto") || !isServiceState(streamSvc, "Stopped", "Manual") {
		return ProblemFinding{}, nil, false
	}
	targets := make([]string, 0, 2)
	for _, s := range []ChromaDiagnosticService{sdkSvc, serverSvc} {
		if isServiceState(s, "Stopped", "Auto") {
			targets = append(targets, s.Name)
			continue
		}
		if !isServiceState(s, "Running", "Auto") {
			return ProblemFinding{}, nil, false
		}
	}
	if len(targets) == 0 {
		return ProblemFinding{}, nil, false
	}
	sort.Strings(targets)
	d, _ := problemDefinitionByID(problemChromaServicesStoppedAuto)
	r, _ := repairDefinitionByID(d.RepairID)
	f := ProblemFinding{
		SchemaVersion: 1, FindingID: stamp + "-G08-KNOWN-001", MeasurementStamp: stamp,
		Gate: 8, GateName: gateName(7), GateState: gateState, Classification: problemClassKnown,
		ProblemID: d.ProblemID, Title: tr(d.TitleKey), Detail: trf(d.DetailKey, "targets", strings.Join(targets, ", ")),
		Confidence: problemConfidenceExact, DiagnosticModuleID: diag.ModuleID, DiagnosticVersion: diag.ModuleVersion,
		RepairID: d.RepairID, RepairAvailable: true, ConfirmationRequired: r.ConfirmationRequired,
		RequiresElevation: r.RequiresElevation, Targets: append([]string(nil), targets...), Evidence: problemEvidenceFromInspection(ins),
	}
	return f, targets, true
}

func classifyAppEngineRuntimeIncomplete(stamp, gateState string, ins GateInspection, diag AppEngineDiagnosticResult) (ProblemFinding, bool) {
	state := strings.ToUpper(strings.TrimSpace(diag.RuntimeState))
	if state != appEngineRuntimeIncomplete && state != appEngineRuntimeNotRunning {
		return ProblemFinding{}, false
	}
	d, _ := problemDefinitionByID(problemAppEngineRuntimeIncomplete)
	r, _ := repairDefinitionByID(d.RepairID)
	target := "RazerAppEngine User-Mode Runtime"
	mode := state
	f := ProblemFinding{
		SchemaVersion: 1, FindingID: stamp + "-G01-KNOWN-001", MeasurementStamp: stamp,
		Gate: 1, GateName: gateName(0), GateState: gateState, Classification: problemClassKnown,
		ProblemID: d.ProblemID, Title: tr(d.TitleKey), Detail: trf(d.DetailKey, "state", mode),
		Confidence: problemConfidenceExact, DiagnosticModuleID: diag.ModuleID, DiagnosticVersion: diag.ModuleVersion,
		RepairID: d.RepairID, RepairAvailable: true, ConfirmationRequired: r.ConfirmationRequired,
		RequiresElevation: r.RequiresElevation, Targets: []string{target}, Evidence: problemEvidenceFromInspection(ins),
	}
	return f, true
}

func unclassifiedProblemFinding(stamp string, gate int, state string, ins GateInspection, moduleID, moduleVersion string, moduleErr error) ProblemFinding {
	detail := tr("problem.unclassified.detail")
	if moduleErr != nil {
		detail = trf("problem.unclassified.detail_module_error", "error", moduleErr.Error())
	}
	return ProblemFinding{
		SchemaVersion: 1, FindingID: fmt.Sprintf("%s-G%02d-UNCLASSIFIED", stamp, gate), MeasurementStamp: stamp,
		Gate: gate, GateName: gateName(gate - 1), GateState: state, Classification: problemClassUnclassified,
		Title: tr("problem.unclassified.title"), Detail: detail, Confidence: problemConfidenceUnknown,
		DiagnosticModuleID: moduleID, DiagnosticVersion: moduleVersion,
		RepairAvailable: false, ConfirmationRequired: false, RequiresElevation: false,
		Evidence: problemEvidenceFromInspection(ins),
	}
}

func writeProblemSnapshot(path, stamp string, findings []ProblemFinding) error {
	snap := ProblemSnapshot{
		SchemaVersion: 1, ToolVersion: referenceVersion, CatalogVersion: problemCatalogVersion,
		OrchestratorVersion: diagnosticOrchestratorVersion, MeasurementStamp: stamp,
		Timestamp: time.Now().Format(time.RFC3339Nano), Findings: findings,
	}
	b, err := json.MarshalIndent(snap, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0644)
}

func (a *App) runDiagnosticOrchestrator(stamp string, states [gateCount]string, inspections [gateCount]GateInspection, appDiag AppEngineDiagnosticResult, _ string, appDiagErr error) ([]ProblemFinding, []string) {
	findings := make([]ProblemFinding, 0)
	files := make([]string, 0, 3)
	var chromaDiag ChromaDiagnosticResult
	var chromaErr error
	chromaRan := false
	chromaPath := ""

	for i, state := range states {
		if state != gateFailed && state != gateUnclear {
			continue
		}
		gate := i + 1
		if gate == 1 {
			if appDiagErr == nil {
				if f, ok := classifyAppEngineRuntimeIncomplete(stamp, state, inspections[i], appDiag); ok {
					findings = append(findings, f)
					continue
				}
			}
			findings = append(findings, unclassifiedProblemFinding(stamp, gate, state, inspections[i], appEngineDiagnosticModuleID, appEngineDiagnosticModuleVersion, appDiagErr))
			continue
		}
		if gate == 8 {
			chromaDiag, chromaPath, chromaErr = a.runChromaServiceDiagnostic(stamp, "")
			chromaRan = true
			if chromaPath != "" {
				files = append(files, chromaPath)
			}
			if chromaErr == nil {
				if f, _, ok := classifyChromaStoppedAuto(stamp, state, inspections[i], chromaDiag); ok {
					findings = append(findings, f)
					continue
				}
			}
			findings = append(findings, unclassifiedProblemFinding(stamp, gate, state, inspections[i], chromaDiagnosticModuleID, chromaDiagnosticModuleVersion, chromaErr))
			continue
		}
		findings = append(findings, unclassifiedProblemFinding(stamp, gate, state, inspections[i], "", "", nil))
	}

	if chromaRan {
		if chromaErr != nil {
			a.debugf("DIAGNOSTIC module=%s version=%s measurement=%s err=%v", chromaDiagnosticModuleID, chromaDiagnosticModuleVersion, stamp, chromaErr)
		} else {
			a.debugf("DIAGNOSTIC module=%s version=%s measurement=%s status=%s services=%d", chromaDiag.ModuleID, chromaDiag.ModuleVersion, stamp, chromaDiag.Status, len(chromaDiag.Services))
		}
	}
	path := filepath.Join(a.diagDir, "ProblemFindings-"+stamp+".json")
	if err := writeProblemSnapshot(path, stamp, findings); err != nil {
		a.debugf("PROBLEM snapshot failed measurement=%s err=%v", stamp, err)
	} else {
		files = append(files, path)
	}
	for _, f := range findings {
		a.debugf("PROBLEM finding gate=%d classification=%s problemId=%s repairId=%s confidence=%s", f.Gate, f.Classification, f.ProblemID, f.RepairID, f.Confidence)
	}
	return findings, files
}

func problemFindingForGate(findings []ProblemFinding, gateIndex int) (ProblemFinding, bool) {
	gate := gateIndex + 1
	for _, f := range findings {
		if f.Gate == gate {
			return f, true
		}
	}
	return ProblemFinding{}, false
}

func (a *App) currentProblemForGate(gateIndex int) (ProblemFinding, bool) {
	a.mu.Lock()
	defer a.mu.Unlock()
	return problemFindingForGate(a.problemFindings, gateIndex)
}

func repairAvailableForGateFindings(findings []ProblemFinding, gateIndex int) bool {
	f, ok := problemFindingForGate(findings, gateIndex)
	if !ok || f.Classification != problemClassKnown || !f.RepairAvailable || !f.ConfirmationRequired || f.RepairID == "" {
		return false
	}
	d, ok := repairDefinitionByID(f.RepairID)
	return ok && d.ConfirmationRequired
}
