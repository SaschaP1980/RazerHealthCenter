//go:build windows

package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"syscall"
)

const (
	appEngineDiagnosticModuleID      = "RHC.DIAG.APPENGINE.USERMODE"
	appEngineDiagnosticModuleVersion = "1.0.2"
	appEngineDiagnosticScriptName    = "diagnose-appengine-usermode-v1.0.2.ps1"

	appEngineRuntimeHealthy    = "HEALTHY"
	appEngineRuntimeIncomplete = "INCOMPLETE"
	appEngineRuntimeNotRunning = "NOT_RUNNING"
	appEngineRuntimeAmbiguous  = "AMBIGUOUS"
)

type AppEngineDiagnosticProcess struct {
	Name            string `json:"Name"`
	ProcessID       int    `json:"ProcessId"`
	ParentProcessID int    `json:"ParentProcessId"`
	ExecutablePath  string `json:"ExecutablePath"`
	CommandLine     string `json:"CommandLine"`
	CreationDate    string `json:"CreationDate"`
	Kind            string `json:"Kind"`
	PageName        string `json:"PageName"`
	IsHelper        bool   `json:"IsHelper"`
}

type AppEngineDiagnosticResult struct {
	SchemaVersion             int                          `json:"SchemaVersion"`
	ModuleID                  string                       `json:"ModuleId"`
	ModuleVersion             string                       `json:"ModuleVersion"`
	ToolVersion               string                       `json:"ToolVersion"`
	MeasurementStamp          string                       `json:"MeasurementStamp"`
	Started                   string                       `json:"Started"`
	Completed                 string                       `json:"Completed"`
	Elevated                  bool                         `json:"Elevated"`
	ReadOnly                  bool                         `json:"ReadOnly"`
	Status                    string                       `json:"Status"`
	Errors                    []string                     `json:"Errors"`
	RuntimeState              string                       `json:"RuntimeState"`
	RunContractValid          bool                         `json:"RunContractValid"`
	RunContract               string                       `json:"RunContract"`
	LauncherExecutable        string                       `json:"LauncherExecutable"`
	LauncherArguments         string                       `json:"LauncherArguments"`
	RuntimeExecutable         string                       `json:"RuntimeExecutable"`
	RuntimeMainPID            int                          `json:"RuntimeMainPid"`
	RuntimeMainArguments      string                       `json:"RuntimeMainArguments"`
	ProcessCount              int                          `json:"ProcessCount"`
	Pages                     []string                     `json:"Pages"`
	SystrayPresent            bool                         `json:"SystrayPresent"`
	BackgroundManagerPresent  bool                         `json:"BackgroundManagerPresent"`
	LightingEnginePresent     bool                         `json:"LightingEnginePresent"`
	DeviceMiddlewarePresent   bool                         `json:"DeviceMiddlewarePresent"`
	SynapsePresent            bool                         `json:"SynapsePresent"`
	ChromaPresent             bool                         `json:"ChromaPresent"`
	KeyboardMiddlewarePresent bool                         `json:"KeyboardMiddlewarePresent"`
	Processes                 []AppEngineDiagnosticProcess `json:"Processes"`
}

func (a *App) runAppEngineUserModeDiagnostic(stamp, suffix string) (AppEngineDiagnosticResult, string, error) {
	var out AppEngineDiagnosticResult
	script := a.diagnosticAppEnginePath
	if script == "" {
		return out, "", fmt.Errorf("appengine diagnostic runtime path missing")
	}
	disk, err := os.ReadFile(script)
	if err != nil {
		return out, "", err
	}
	emb, err := embedded.ReadFile("diagnostics/" + appEngineDiagnosticScriptName)
	if err != nil || shaHex(disk) != shaHex(windowsPowerShellUTF8ScriptBytes(emb)) {
		return out, "", fmt.Errorf("appengine diagnostic module integrity check failed")
	}
	name := "Diagnostic-AppEngineUserMode-" + stamp
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
	// Exit 2 represents a successfully captured but ambiguous runtime state.
	if err != nil {
		if ee, ok := err.(*exec.ExitError); !ok || ee.ExitCode() != 2 {
			return out, resultPath, fmt.Errorf("appengine diagnostic module: %w: %s", err, strings.TrimSpace(stderr.String()))
		}
	}
	b, err := os.ReadFile(resultPath)
	if err != nil {
		return out, resultPath, err
	}
	if err := json.Unmarshal(bytes.TrimPrefix(b, []byte{0xEF, 0xBB, 0xBF}), &out); err != nil {
		return out, resultPath, err
	}
	if out.ModuleID != appEngineDiagnosticModuleID || out.ModuleVersion != appEngineDiagnosticModuleVersion || !out.ReadOnly {
		return out, resultPath, fmt.Errorf("appengine diagnostic module contract mismatch")
	}
	return out, resultPath, nil
}

func appEngineHealthCheck(diag AppEngineDiagnosticResult, diagErr error) (EngineCheck, bool, string) {
	c := EngineCheck{
		Section:  "AppEngine",
		Check:    tr("health.appengine.runtime.check"),
		Expected: tr("health.appengine.runtime.expected"),
	}
	if diagErr != nil {
		c.Status = "UNKNOWN"
		c.Actual = tr("health.appengine.runtime.unreadable")
		c.Detail = trf("health.appengine.runtime.error", "error", diagErr.Error())
		return c, true, "APPENGINE_USERMODE_DIAGNOSTIC_UNREADABLE"
	}
	state := strings.ToUpper(strings.TrimSpace(diag.RuntimeState))
	switch state {
	case appEngineRuntimeHealthy:
		c.Status = "PASS"
		c.Actual = tr("health.appengine.runtime.healthy")
		c.Detail = trf("health.appengine.runtime.healthy_detail", "pid", diag.RuntimeMainPID)
		return c, false, ""
	case appEngineRuntimeNotRunning:
		c.Status = "UNKNOWN"
		c.Actual = tr("health.appengine.runtime.not_running")
		c.Detail = tr("health.appengine.runtime.not_running_detail")
		return c, true, "APPENGINE_USERMODE_RUNTIME_INCOMPLETE"
	case appEngineRuntimeIncomplete:
		c.Status = "UNKNOWN"
		c.Actual = tr("health.appengine.runtime.incomplete")
		c.Detail = trf("health.appengine.runtime.incomplete_detail", "args", strings.TrimSpace(diag.RuntimeMainArguments))
		return c, true, "APPENGINE_USERMODE_RUNTIME_INCOMPLETE"
	default:
		c.Status = "UNKNOWN"
		c.Actual = tr("health.appengine.runtime.ambiguous")
		c.Detail = tr("health.appengine.runtime.ambiguous_detail")
		return c, true, "APPENGINE_USERMODE_RUNTIME_AMBIGUOUS"
	}
}
