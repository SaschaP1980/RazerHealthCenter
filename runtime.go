//go:build windows

package main

import (
	"crypto/sha256"
	"embed"
	"encoding/hex"
	"fmt"
	"io/fs"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

// recovered verbatim from the v1.7.0 Go embed filesystem.
//
//go:embed health-engine-v1.4.6.ps1 diagnostics repair setup assets
var embedded embed.FS

func shaHex(b []byte) string {
	h := sha256.Sum256(b)
	return hex.EncodeToString(h[:])
}

// Windows PowerShell 5.1 interprets UTF-8 source files without a BOM using the
// active ANSI code page. The historical Health Engine asset intentionally stays
// byte-identical to the current 1.3.6 source, so the runtime execution copy is
// normalized instead: prepend a UTF-8 BOM only when one is not already present.
// This fixes non-ASCII literals (for example deutsche Umlaute) without changing
// the embedded/canonical Health Engine payload.
func windowsPowerShellUTF8ScriptBytes(src []byte) []byte {
	if len(src) >= 3 && src[0] == 0xEF && src[1] == 0xBB && src[2] == 0xBF {
		return src
	}
	out := make([]byte, 3+len(src))
	copy(out, []byte{0xEF, 0xBB, 0xBF})
	copy(out[3:], src)
	return out
}

func (a *App) debugf(format string, args ...any) {
	if a.debugPath == "" {
		return
	}
	line := time.Now().Format("2006-01-02 15:04:05.000") + " " + fmt.Sprintf(format, args...) + "\r\n"
	f, err := os.OpenFile(a.debugPath, os.O_CREATE|os.O_APPEND|os.O_WRONLY, 0644)
	if err == nil {
		_, _ = f.WriteString(line)
		_ = f.Close()
	}
}

func writeSnapshot(path string, v any) error {
	b, err := jsonMarshalIndent(v)
	if err != nil {
		return err
	}
	return os.WriteFile(path, b, 0644)
}

func (a *App) runtimeAssetPath(parts ...string) string {
	all := append([]string{a.runtimeDir, "assets"}, parts...)
	return filepath.Join(all...)
}

func (a *App) prepareRuntime() error {
	if err := os.MkdirAll(a.logsDir, 0755); err != nil {
		return err
	}
	if err := os.MkdirAll(a.diagDir, 0755); err != nil {
		return err
	}
	if err := os.MkdirAll(a.exportsDir, 0755); err != nil {
		return err
	}

	// Canonical invariant: Runtime is ephemeral and app-owned. The engine stays
	// directly under Runtime while UI/status assets preserve their source hierarchy
	// under Runtime/assets/{status,ui}. The entire tree is rebuilt at every start.
	_ = os.RemoveAll(a.runtimeDir)
	if err := os.MkdirAll(a.runtimeDir, 0755); err != nil {
		return err
	}

	engine, err := embedded.ReadFile("health-engine-v1.4.6.ps1")
	if err != nil {
		return err
	}
	a.enginePath = filepath.Join(a.runtimeDir, "health-engine-v1.4.6.ps1")
	engineRuntime := windowsPowerShellUTF8ScriptBytes(engine)
	if err := os.WriteFile(a.enginePath, engineRuntime, 0644); err != nil {
		return err
	}

	setupScript, err := embedded.ReadFile("setup/setup-razer-inventory-v1.0.6.ps1")
	if err != nil {
		return err
	}
	a.setupScriptPath = filepath.Join(a.runtimeDir, "setup", "setup-razer-inventory-v1.0.6.ps1")
	if err := os.MkdirAll(filepath.Dir(a.setupScriptPath), 0755); err != nil {
		return err
	}
	if err := os.WriteFile(a.setupScriptPath, windowsPowerShellUTF8ScriptBytes(setupScript), 0644); err != nil {
		return err
	}

	repairScript, err := embedded.ReadFile("repair/repair-chroma-services-v1.1.0.ps1")
	if err != nil {
		return err
	}
	a.repairScriptPath = filepath.Join(a.runtimeDir, "repair", "repair-chroma-services-v1.1.0.ps1")
	if err := os.MkdirAll(filepath.Dir(a.repairScriptPath), 0755); err != nil {
		return err
	}
	if err := os.WriteFile(a.repairScriptPath, repairScript, 0644); err != nil {
		return err
	}

	appEngineRepairScript, err := embedded.ReadFile("repair/repair-appengine-runtime-v1.0.0.ps1")
	if err != nil {
		return err
	}
	a.repairAppEngineScriptPath = filepath.Join(a.runtimeDir, "repair", "repair-appengine-runtime-v1.0.0.ps1")
	if err := os.WriteFile(a.repairAppEngineScriptPath, appEngineRepairScript, 0644); err != nil {
		return err
	}

	diagnosticScript, err := embedded.ReadFile("diagnostics/diagnose-chroma-services-v1.0.0.ps1")
	if err != nil {
		return err
	}
	a.diagnosticChromaServicesPath = filepath.Join(a.runtimeDir, "diagnostics", chromaDiagnosticScriptName)
	if err := os.MkdirAll(filepath.Dir(a.diagnosticChromaServicesPath), 0755); err != nil {
		return err
	}
	if err := os.WriteFile(a.diagnosticChromaServicesPath, windowsPowerShellUTF8ScriptBytes(diagnosticScript), 0644); err != nil {
		return err
	}

	appEngineDiagnosticScript, err := embedded.ReadFile("diagnostics/" + appEngineDiagnosticScriptName)
	if err != nil {
		return err
	}
	a.diagnosticAppEnginePath = filepath.Join(a.runtimeDir, "diagnostics", appEngineDiagnosticScriptName)
	if err := os.WriteFile(a.diagnosticAppEnginePath, windowsPowerShellUTF8ScriptBytes(appEngineDiagnosticScript), 0644); err != nil {
		return err
	}

	err = fs.WalkDir(embedded, "assets", func(path string, d fs.DirEntry, walkErr error) error {
		if walkErr != nil {
			return walkErr
		}
		rel := filepath.FromSlash(path)
		target := filepath.Join(a.runtimeDir, rel)
		if d.IsDir() {
			return os.MkdirAll(target, 0755)
		}
		b, er := embedded.ReadFile(path)
		if er != nil {
			return er
		}
		if er := os.MkdirAll(filepath.Dir(target), 0755); er != nil {
			return er
		}
		return os.WriteFile(target, b, 0644)
	})
	if err != nil {
		return err
	}

	a.debugf("runtime prepared engineSourceSHA256=%s engineRuntimeSHA256=%s engineRuntimeEncoding=UTF-8-BOM setupVersion=%s setupSHA256=%s liveProbeVersion=%s liveProbeImplementation=native-setupapi-usb idleSHA256=%s passedSHA256=%s failedSHA256=%s appIconSHA256=%s statusReadySHA256=%s statusPassSHA256=%s statusFailSHA256=%s pulseFrames=8 uiIcons=60 repairEngineVersion=%s repairVersion=%s repairSHA256=%s appEngineRepairVersion=%s appEngineRepairSHA256=%s diagnosticOrchestratorVersion=%s problemCatalogVersion=%s chromaDiagnosticVersion=%s chromaDiagnosticSHA256=%s appEngineDiagnosticVersion=%s appEngineDiagnosticSHA256=%s", strings.ToUpper(shaHex(engine)), strings.ToUpper(shaHex(engineRuntime)), setupScanVersion, shaFileUpper(a.setupScriptPath), setupLiveProbeVersion, shaFileUpper(a.runtimeAssetPath("idle.ico")), shaFileUpper(a.runtimeAssetPath("passed.ico")), shaFileUpper(a.runtimeAssetPath("failed.ico")), shaFileUpper(a.runtimeAssetPath("app-heart.ico")), shaFileUpper(a.runtimeAssetPath("status", "status-ready.ico")), shaFileUpper(a.runtimeAssetPath("status", "status-pass.ico")), shaFileUpper(a.runtimeAssetPath("status", "status-fail.ico")), repairEngineVersion, repairVersionChromaServices, shaFileUpper(a.repairScriptPath), repairVersionAppEngineRuntime, shaFileUpper(a.repairAppEngineScriptPath), diagnosticOrchestratorVersion, problemCatalogVersion, chromaDiagnosticModuleVersion, shaFileUpper(a.diagnosticChromaServicesPath), appEngineDiagnosticModuleVersion, shaFileUpper(a.diagnosticAppEnginePath))
	return nil
}

func mustEmbeddedHealthEngine() []byte {
	b, err := embedded.ReadFile("health-engine-v1.4.6.ps1")
	if err != nil {
		return nil
	}
	return b
}

func shaFileUpper(path string) string {
	b, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	return strings.ToUpper(shaHex(b))
}

func (a *App) writeStartupDebug(exe string) {
	mode := "unelevated-main"
	if a.elevated {
		mode = "elevated-main"
	}
	a.startupDebugPath = filepath.Join(a.diagDir, "StartupDebug-"+a.session+"-"+mode+".json")
	ready := a.runtimeAssetPath("status", "status-ready.ico")
	pass := a.runtimeAssetPath("status", "status-pass.ico")
	fail := a.runtimeAssetPath("status", "status-fail.ico")
	appIcon := a.runtimeAssetPath("app-heart.ico")
	obj := map[string]any{
		"app":                           appName(),
		"appIconSHA256":                 shaFileUpper(appIcon),
		"dataDir":                       a.dataDir,
		"elevated":                      a.elevated,
		"engineSHA256":                  shaFileUpper(a.enginePath),
		"engineSourceSHA256":            strings.ToUpper(shaHex(mustEmbeddedHealthEngine())),
		"engineEncoding":                "UTF-8-BOM runtime execution copy",
		"engineVersion":                 engineVersion,
		"repairEngineVersion":           repairEngineVersion,
		"repairVersion":                 repairVersionChromaServices,
		"repairSHA256":                  shaFileUpper(a.repairScriptPath),
		"appEngineRepairVersion":        repairVersionAppEngineRuntime,
		"appEngineRepairSHA256":         shaFileUpper(a.repairAppEngineScriptPath),
		"diagnosticOrchestratorVersion": diagnosticOrchestratorVersion,
		"problemCatalogVersion":         problemCatalogVersion,
		"chromaDiagnosticVersion":       chromaDiagnosticModuleVersion,
		"chromaDiagnosticSHA256":        shaFileUpper(a.diagnosticChromaServicesPath),
		"appEngineDiagnosticVersion":    appEngineDiagnosticModuleVersion,
		"appEngineDiagnosticSHA256":     shaFileUpper(a.diagnosticAppEnginePath),
		"setupScannerVersion":           setupScanVersion,
		"setupScannerSHA256":            shaFileUpper(a.setupScriptPath),
		"setupLiveProbeVersion":         setupLiveProbeVersion,
		"setupLiveProbeImplementation":  "native-setupapi-usb",
		"exe":                           exe,
		"failedSHA256":                  shaFileUpper(fail),
		"guiThreadId":                   a.traceGUIThreadID,
		"idleSHA256":                    shaFileUpper(ready),
		"osThreadLocked":                true,
		"passedSHA256":                  shaFileUpper(pass),
		"pid":                           os.Getpid(),
		"statusFailSHA256":              shaFileUpper(fail),
		"statusPassSHA256":              shaFileUpper(pass),
		"statusReadySHA256":             shaFileUpper(ready),
		"timestamp":                     time.Now().Format(time.RFC3339Nano),
		"uiTrace":                       a.tracePath,
		"version":                       referenceVersion,
		"go":                            runtime.Version(),
	}
	if err := writeSnapshot(a.startupDebugPath, obj); err != nil {
		a.debugf("startup debug snapshot failed: %v", err)
	} else {
		a.debugf("startup debug snapshot written: %s", a.startupDebugPath)
	}
}
