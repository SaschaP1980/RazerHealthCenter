//go:build windows

package main

import (
	"archive/zip"
	"encoding/json"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
	"unsafe"
)

func zipFileAs(zw *zip.Writer, src, archiveName string) error {
	f, err := os.Open(src)
	if err != nil {
		return err
	}
	defer f.Close()
	st, err := f.Stat()
	if err != nil {
		return err
	}
	h, err := zip.FileInfoHeader(st)
	if err != nil {
		return err
	}
	h.Name = filepath.ToSlash(archiveName)
	h.Method = zip.Deflate
	w, err := zw.CreateHeader(h)
	if err != nil {
		return err
	}
	_, err = io.Copy(w, f)
	return err
}

func parseMeasurementStampFromFile(name string) string {
	base := filepath.Base(name)
	for _, p := range []string{"RazerHealth-", "GateResult-", "GateProgress-", "Progress-", "EngineOutput-", "ProblemFindings-", "ApplicationHealthAssessment-", "Diagnostic-ChromaServices-"} {
		if strings.HasPrefix(base, p) {
			x := strings.TrimPrefix(base, p)
			if i := strings.LastIndexByte(x, '.'); i >= 0 {
				x = x[:i]
			}
			if len(x) >= 15 {
				return x[:15]
			}
		}
	}
	return ""
}

func parseMeasurementTime(stamp string) time.Time {
	t, _ := time.ParseInLocation("20060102-150405", stamp, time.Local)
	return t
}

func (a *App) collectMeasurementFileNames(stamp string) []string {
	var out []string
	for _, dir := range []string{a.logsDir, a.diagDir} {
		entries, _ := os.ReadDir(dir)
		for _, e := range entries {
			if e.IsDir() {
				continue
			}
			n := e.Name()
			if parseMeasurementStampFromFile(n) == stamp {
				out = append(out, filepath.Join(dir, n))
			}
		}
	}
	sort.Strings(out)
	return out
}

func parseDurationFromFiles(files []string) time.Duration {
	for _, path := range files {
		if !strings.HasPrefix(filepath.Base(path), "EngineOutput-") {
			continue
		}
		b, err := os.ReadFile(path)
		if err != nil {
			continue
		}
		for _, ln := range strings.Split(string(b), "\n") {
			ln = strings.TrimSpace(ln)
			if strings.HasPrefix(ln, "Duration:") {
				v := strings.TrimSpace(strings.TrimPrefix(ln, "Duration:"))
				if d, err := time.ParseDuration(v); err == nil {
					return d
				}
			}
		}
	}
	return 0
}

type appSessionEvidence struct {
	time    time.Time
	session string
	version string
}

func (a *App) scanAppSessions() []appSessionEvidence {
	entries, _ := os.ReadDir(a.diagDir)
	var out []appSessionEvidence
	for _, e := range entries {
		if e.IsDir() || !strings.HasPrefix(e.Name(), "AppDebug-") || !strings.HasSuffix(strings.ToLower(e.Name()), ".log") {
			continue
		}
		session := strings.TrimSuffix(strings.TrimPrefix(e.Name(), "AppDebug-"), filepath.Ext(e.Name()))
		parts := strings.Split(session, "-")
		if len(parts) < 3 {
			continue
		}
		stamp := parts[0] + "-" + parts[1]
		t, err := time.ParseInLocation("20060102-150405.000", stamp, time.Local)
		if err != nil {
			continue
		}
		version := legacyHistoryFallbackVersion
		if b, err := os.ReadFile(filepath.Join(a.diagDir, e.Name())); err == nil {
			first := string(b)
			if i := strings.Index(first, "version="); i >= 0 {
				v := first[i+len("version="):]
				if j := strings.IndexAny(v, " \r\n"); j >= 0 {
					v = v[:j]
				}
				v = strings.Trim(v, "\"")
				if v != "" {
					if i := strings.Index(strings.ToLower(v), "-recovered"); i > 0 {
						v = v[:i]
					}
					version = v
				}
			}
		}
		out = append(out, appSessionEvidence{time: t, session: session, version: version})
	}
	sort.Slice(out, func(i, j int) bool { return out[i].time.Before(out[j].time) })
	return out
}

func resolveAppSession(started time.Time, sessions []appSessionEvidence) (string, string, bool) {
	best := -1
	for i := range sessions {
		if sessions[i].time.After(started) {
			break
		}
		best = i
	}
	if best < 0 {
		return "", legacyHistoryFallbackVersion, false
	}
	return sessions[best].session, sessions[best].version, true
}

func historicalDetailSnapshot(r EngineResult) ([gateCount]string, [gateCount]GateInspection, bool, string) {
	var raw [gateCount]string
	var display [gateCount]string
	var inspections [gateCount]GateInspection
	if len(r.Gates) < gateCount {
		return display, inspections, false, trf("logs.detail_unavailable.gates", "count", len(r.Gates), "required", gateCount)
	}
	for i := 0; i < gateCount; i++ {
		state := strings.TrimSpace(r.Gates[i].Status)
		if state == "" {
			return display, inspections, false, trf("logs.detail_unavailable.gate_state", "gate", i+1)
		}
		raw[i] = state
	}
	inspections = gateInspectionsFromEngineResult(r)
	_, display = finalGateSnapshot(raw, inspections)
	for i := 0; i < gateCount; i++ {
		if strings.TrimSpace(display[i]) == "" || display[i] == gateChecking || display[i] == gateWaiting || display[i] == gateUnchecked {
			return [gateCount]string{}, [gateCount]GateInspection{}, false, trf("logs.detail_unavailable.gate_state", "gate", i+1)
		}
	}
	return display, inspections, true, ""
}

func (a *App) scanHistoricalMeasurements() []HistoricalMeasurement {
	entries, err := os.ReadDir(a.diagDir)
	if err != nil {
		return nil
	}
	var out []HistoricalMeasurement
	sessions := a.scanAppSessions()
	for _, e := range entries {
		if e.IsDir() || !strings.HasPrefix(e.Name(), "RazerHealth-") || !strings.HasSuffix(strings.ToLower(e.Name()), ".json") {
			continue
		}
		stamp := parseMeasurementStampFromFile(e.Name())
		if stamp == "" {
			continue
		}
		started := parseMeasurementTime(stamp)
		if started.IsZero() {
			continue
		}
		files := a.collectMeasurementFileNames(stamp)
		hm := HistoricalMeasurement{
			Stamp:                   stamp,
			StartedAt:               started,
			CompletedAt:             started,
			Overall:                 measurementUnclear,
			AppVersion:              legacyHistoryFallbackVersion,
			EngineVersion:           "—",
			Files:                   files,
			DetailAvailable:         false,
			DetailUnavailableReason: tr("logs.detail_unavailable.invalid"),
		}
		if sess, ver, ok := resolveAppSession(started, sessions); ok {
			hm.AppSession = sess
			hm.AppVersion = ver
			hm.SessionResolved = true
		}

		path := filepath.Join(a.diagDir, e.Name())
		b, readErr := os.ReadFile(path)
		if readErr == nil {
			var r EngineResult
			if json.Unmarshal(b, &r) == nil {
				if r.Timestamp != "" {
					if t, er := time.Parse(time.RFC3339Nano, r.Timestamp); er == nil {
						hm.CompletedAt = t
					}
				}
				hm.Overall = measurementOverallFromEngine(r)
				if strings.TrimSpace(r.EngineVersion) != "" {
					hm.EngineVersion = r.EngineVersion
				}
				states, inspections, ok, reason := historicalDetailSnapshot(r)
				hm.DetailAvailable = ok
				hm.DetailUnavailableReason = reason
				if ok {
					hm.GateStates = states
					hm.GateInspections = inspections
				}
			}
		}

		dur := parseDurationFromFiles(files)
		if dur <= 0 {
			dur = hm.CompletedAt.Sub(started)
		}
		if dur < 0 {
			dur = 0
		}
		hm.Duration = dur

		a.mu.Lock()
		currentStamp := a.lastMeasurement.Stamp
		session := a.session
		a.mu.Unlock()
		if stamp == currentStamp && currentStamp != "" {
			hm.AppSession = session
			hm.AppVersion = referenceVersion
			hm.SessionResolved = true
		}
		out = append(out, hm)
	}
	sort.Slice(out, func(i, j int) bool { return out[i].StartedAt.After(out[j].StartedAt) })
	return out
}

func normalizeMeasurementStatus(v string) string {
	switch strings.ToUpper(strings.TrimSpace(v)) {
	case "HEALTHY", "GESUND", "PASS", "PASSED", "BESTANDEN":
		return measurementHealthy
	case "HINT", "HINWEIS", "WARN", "WARNING":
		return measurementHint
	case "UNCLEAR", "UNKLAR", "UNKNOWN":
		return measurementUnclear
	case "FAILED", "FEHLER", "FAIL":
		return measurementFailed
	default:
		return ""
	}
}

func measurementOverallFromEngine(r EngineResult) string {
	if v := normalizeMeasurementStatus(r.OverallLabel); v != "" {
		return v
	}
	if v := normalizeMeasurementStatus(r.Overall); v != "" {
		return v
	}
	return measurementUnclear
}

func measurementDisplayStatus(v string) string {
	n := normalizeMeasurementStatus(v)
	if n == "" {
		n = measurementUnclear
	}
	return measurementStatusText(n)
}

func measurementIndexByStamp(ms []HistoricalMeasurement, stamp string) int {
	if stamp == "" {
		return -1
	}
	for i := range ms {
		if ms[i].Stamp == stamp {
			return i
		}
	}
	return -1
}

func (a *App) refreshMeasurementsAsync() {
	a.mu.Lock()
	if a.logsLoading {
		a.mu.Unlock()
		return
	}
	a.logsLoading = true
	selectedStamp := ""
	topStamp := ""
	if a.logSelected >= 0 && a.logSelected < len(a.logMeasurements) {
		selectedStamp = a.logMeasurements[a.logSelected].Stamp
	}
	if a.logScroll >= 0 && a.logScroll < len(a.logMeasurements) {
		topStamp = a.logMeasurements[a.logScroll].Stamp
	}
	restoreStamp := a.logHistoricalStamp
	restoreActive := a.logHistoricalActive
	a.mu.Unlock()
	go func() {
		m := a.scanHistoricalMeasurements()
		a.mu.Lock()
		a.logMeasurements = m
		if len(m) == 0 {
			a.logSelected = -1
			a.logScroll = 0
		} else {
			if idx := measurementIndexByStamp(m, selectedStamp); idx >= 0 {
				a.logSelected = idx
			} else if a.logSelected < 0 || a.logSelected >= len(m) {
				a.logSelected = 0
			}
			if idx := measurementIndexByStamp(m, topStamp); idx >= 0 {
				a.logScroll = idx
			}
			maxScroll := len(m) - 10
			if maxScroll < 0 {
				maxScroll = 0
			}
			if a.logScroll > maxScroll {
				a.logScroll = maxScroll
			}
			if a.logScroll < 0 {
				a.logScroll = 0
			}
		}
		if restoreStamp != "" {
			idx := measurementIndexByStamp(m, restoreStamp)
			if idx >= 0 && m[idx].DetailAvailable {
				a.logHistoricalStamp = restoreStamp
				a.logHistoricalOpen = true
				a.logHistoricalActive = restoreActive
			} else {
				a.logHistoricalStamp = ""
				a.logHistoricalOpen = false
				a.logHistoricalActive = false
			}
		}
		a.logsLoading = false
		a.logsLastScan = time.Now()
		a.mu.Unlock()
		procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	}()
}

func (a *App) exportDiagnostics() {
	a.debugf("UI diagnostics export requested")
	a.mu.Lock()
	if a.exporting || a.repairing {
		a.mu.Unlock()
		return
	}
	a.exporting = true
	a.mu.Unlock()
	procPostMessageW.Call(a.hwnd, wmRefresh, 0, 0)
	go a.exportDiagnosticsWorker()
}

func (a *App) exportDiagnosticsWorker() {
	now := time.Now()
	name := "RazerHealthDiagnostics-" + now.Format("20060102-150405") + ".zip"
	target := filepath.Join(a.exportsDir, name)
	err := os.MkdirAll(a.exportsDir, 0755)
	if err == nil {
		err = a.createDiagnosticZip(target, nil, "current")
	}
	a.finishExport(target, err)
}

func (a *App) exportSelectedMeasurement() {
	a.mu.Lock()
	if a.exporting || a.repairing || a.logSelected < 0 || a.logSelected >= len(a.logMeasurements) {
		a.mu.Unlock()
		return
	}
	sel := a.logMeasurements[a.logSelected]
	a.exporting = true
	a.mu.Unlock()
	go a.exportSelectedMeasurementWorker(sel)
}

func (a *App) exportHistoricalMeasurement() {
	a.mu.Lock()
	if a.exporting || a.repairing || !a.logHistoricalOpen || a.logHistoricalStamp == "" {
		a.mu.Unlock()
		return
	}
	idx := measurementIndexByStamp(a.logMeasurements, a.logHistoricalStamp)
	if idx < 0 {
		a.mu.Unlock()
		return
	}
	sel := a.logMeasurements[idx]
	a.exporting = true
	a.mu.Unlock()
	go a.exportSelectedMeasurementWorker(sel)
}

func (a *App) exportSelectedMeasurementWorker(selected HistoricalMeasurement) {
	target := filepath.Join(a.exportsDir, "RazerHealthDiagnostics-Measurement-"+selected.Stamp+"-"+time.Now().Format("150405")+".zip")
	err := os.MkdirAll(a.exportsDir, 0755)
	if err == nil {
		err = a.createDiagnosticZip(target, &selected, "measurement")
	}
	a.finishExport(target, err)
}

func exportOverall(v string) string {
	switch strings.ToUpper(strings.TrimSpace(v)) {
	case "GESUND", "PASS", "BESTANDEN":
		return "PASS"
	case "FEHLER", "FAILED", "FAIL":
		return "FAILED"
	default:
		return v
	}
}

func manifestMeasurementState(st MeasurementExportState) MeasurementExportState {
	cp := st
	cp.Overall = exportOverall(cp.Overall)
	cp.Files = make([]string, 0, len(st.Files))
	for _, f := range st.Files {
		cp.Files = append(cp.Files, filepath.Base(f))
	}
	return cp
}

func measurementArchivePath(prefix, src string) string {
	base := filepath.Base(src)
	if strings.HasPrefix(base, "RazerHealth-") && strings.HasSuffix(strings.ToLower(base), ".log") {
		return prefix + "/Logs/" + base
	}
	return prefix + "/Diagnostics/" + base
}

func (a *App) sessionDiagnosticSources(session string, includeCurrentMutableSetup bool) []struct{ src, arc string } {
	if session == "" {
		return nil
	}
	var out []struct{ src, arc string }
	entries, _ := os.ReadDir(a.diagDir)
	for _, e := range entries {
		if e.IsDir() {
			continue
		}
		n := e.Name()
		var arc string
		switch {
		case n == "AppDebug-"+session+".log":
			arc = "AppSession/Logs/" + n
		case strings.HasPrefix(n, "StartupDebug-"+session+"-") && strings.HasSuffix(strings.ToLower(n), ".json"):
			arc = "AppSession/Diagnostics/" + n
		case n == "UITrace-"+session+".log":
			arc = "AppSession/Diagnostics/" + n
		case n == "VersionStatus-"+session+".json":
			arc = "AppSession/Diagnostics/" + n
		case strings.HasPrefix(n, "SetupScan-"+session+"-") && strings.HasSuffix(strings.ToLower(n), ".json"):
			arc = "AppSession/Diagnostics/" + n
		case strings.HasPrefix(n, "SetupScannerDebug-"+session+"-") && (strings.HasSuffix(strings.ToLower(n), ".json") || strings.HasSuffix(strings.ToLower(n), ".txt")):
			arc = "AppSession/Diagnostics/" + n
		default:
			continue
		}
		out = append(out, struct{ src, arc string }{filepath.Join(a.diagDir, n), arc})
	}
	repairDir := filepath.Join(a.diagDir, "Repairs")
	if entries, err := os.ReadDir(repairDir); err == nil {
		prefix := "Repair-" + session + "-"
		for _, e := range entries {
			if e.IsDir() || !strings.HasPrefix(e.Name(), prefix) {
				continue
			}
			out = append(out, struct{ src, arc string }{filepath.Join(repairDir, e.Name()), "AppSession/Repairs/" + e.Name()})
		}
	}
	if includeCurrentMutableSetup {
		if a.inventoryPath != "" {
			if st, err := os.Stat(a.inventoryPath); err == nil && !st.IsDir() {
				out = append(out, struct{ src, arc string }{a.inventoryPath, "AppSession/Setup/" + filepath.Base(a.inventoryPath)})
			}
		}
		if a.connectionHistoryPath != "" {
			if st, err := os.Stat(a.connectionHistoryPath); err == nil && !st.IsDir() {
				out = append(out, struct{ src, arc string }{a.connectionHistoryPath, "AppSession/Setup/" + filepath.Base(a.connectionHistoryPath)})
			}
		}
		liveProbePath := filepath.Join(a.setupDir, "SetupLiveProbe-v1.1.0.json")
		if st, err := os.Stat(liveProbePath); err == nil && !st.IsDir() {
			out = append(out, struct{ src, arc string }{liveProbePath, "AppSession/Setup/" + filepath.Base(liveProbePath)})
		}
	}
	sort.Slice(out, func(i, j int) bool { return out[i].arc < out[j].arc })
	return out
}

func (a *App) createDiagnosticZip(target string, selected *HistoricalMeasurement, mode string) error {
	f, err := os.Create(target)
	if err != nil {
		return err
	}
	zw := zip.NewWriter(f)
	ok := false
	defer func() {
		if !ok {
			_ = zw.Close()
			_ = f.Close()
			_ = os.Remove(target)
		}
	}()

	a.mu.Lock()
	checking := a.checking
	session := a.session
	lm := a.lastMeasurement
	a.mu.Unlock()

	manifest := DiagnosticsExportManifest{
		SchemaVersion:         4,
		App:                   appName(),
		AppVersion:            referenceVersion,
		ExportedAt:            time.Now().Format(time.RFC3339Nano),
		ExportMode:            "currentSessionLastMeasurement",
		AppSession:            session,
		SessionResolved:       true,
		MeasurementInProgress: checking,
	}
	includedSession := []string{}
	includedMeasure := []string{}
	add := func(src, arc string) error {
		if src == "" {
			return nil
		}
		if _, er := os.Stat(src); er != nil {
			return nil
		}
		if er := zipFileAs(zw, src, arc); er != nil {
			return er
		}
		return nil
	}

	measurePrefix := "LastMeasurement"
	measureFiles := []string(nil)
	if selected != nil {
		manifest.ExportMode = "selectedMeasurement"
		manifest.AppSession = selected.AppSession
		manifest.SessionResolved = selected.SessionResolved
		measurePrefix = "SelectedMeasurement"
		st := MeasurementExportState{Stamp: selected.Stamp, StartedAt: selected.StartedAt, CompletedAt: selected.CompletedAt, Overall: selected.Overall, Files: selected.Files}
		cp := manifestMeasurementState(st)
		manifest.SelectedMeasurement = &cp
		measureFiles = selected.Files
		if selected.SessionResolved {
			for _, sf := range a.sessionDiagnosticSources(selected.AppSession, false) {
				if er := add(sf.src, sf.arc); er != nil {
					return er
				}
				includedSession = append(includedSession, sf.arc)
			}
		}
	} else {
		for _, sf := range a.sessionDiagnosticSources(session, true) {
			if er := add(sf.src, sf.arc); er != nil {
				return er
			}
			includedSession = append(includedSession, sf.arc)
		}
		if lm.Stamp != "" && !checking {
			cp := manifestMeasurementState(lm)
			manifest.LastMeasurement = &cp
			measureFiles = lm.Files
		}
	}

	for _, src := range measureFiles {
		arc := measurementArchivePath(measurePrefix, src)
		if er := add(src, arc); er != nil {
			return er
		}
		if _, er := os.Stat(src); er == nil {
			includedMeasure = append(includedMeasure, arc)
		}
	}
	manifest.IncludedSessionFiles = includedSession
	manifest.IncludedMeasureFiles = includedMeasure

	mb, _ := json.MarshalIndent(manifest, "", "  ")
	w, er := zw.Create("ExportManifest.json")
	if er != nil {
		return er
	}
	if _, er = w.Write(mb); er != nil {
		return er
	}
	if er = zw.Close(); er != nil {
		return er
	}
	if er = f.Close(); er != nil {
		return er
	}
	ok = true
	return nil
}

func (a *App) finishExport(path string, err error) {
	a.mu.Lock()
	a.exporting = false
	a.exportResultPath = path
	a.exportResultErr = err
	a.mu.Unlock()
	procPostMessageW.Call(a.hwnd, wmExportDone, 0, 0)
}

func (a *App) handleExportResult() {
	a.mu.Lock()
	p := a.exportResultPath
	err := a.exportResultErr
	a.exportResultPath = ""
	a.exportResultErr = nil
	if err == nil {
		a.exportDialogVisible = true
		a.exportDialogPath = p
	}
	a.mu.Unlock()
	if err != nil {
		messageBox(a.hwnd, tr("modal.export.error.title"), trf("error.export", "error", err.Error()), mbOK|mbIconError)
	}
}

func (a *App) openExports() {
	_ = os.MkdirAll(a.exportsDir, 0755)
	procShellExecuteW.Call(0, uintptr(unsafe.Pointer(utf16("open"))), uintptr(unsafe.Pointer(utf16("explorer.exe"))), uintptr(unsafe.Pointer(utf16(a.exportsDir))), 0, swShow)
}

func (a *App) selectedMeasurementSummary() string {
	a.mu.Lock()
	defer a.mu.Unlock()
	if a.logSelected < 0 || a.logSelected >= len(a.logMeasurements) {
		return ""
	}
	m := a.logMeasurements[a.logSelected]
	return trf("logs.selected.summary", "time", m.StartedAt.Format("02.01.2006 15:04:05"), "status", measurementDisplayStatus(m.Overall), "engineVersion", m.EngineVersion)
}
