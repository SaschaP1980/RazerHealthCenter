//go:build windows

package main

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"
)

const (
	applicationHealthAssessmentSchema        = 1
	applicationHealthGate                    = 1
	applicationHealthReasonUnconfirmed       = "RAZER_PRODUCT_REGISTRATION_UNCONFIRMED"
	applicationHealthReasonRuntimeIncomplete = "APPENGINE_USERMODE_RUNTIME_INCOMPLETE"
)

type ApplicationHealthAssessment struct {
	SchemaVersion               int           `json:"schemaVersion"`
	ToolVersion                 string        `json:"toolVersion"`
	MeasurementStamp            string        `json:"measurementStamp"`
	Timestamp                   string        `json:"timestamp"`
	Source                      string        `json:"source"`
	DiscoveryURL                string        `json:"discoveryUrl,omitempty"`
	ManifestURL                 string        `json:"manifestUrl,omitempty"`
	ManifestChannel             string        `json:"manifestChannel,omitempty"`
	ManifestProdHash            string        `json:"manifestProdHash,omitempty"`
	Evaluated                   bool          `json:"evaluated"`
	HealthImpact                bool          `json:"healthImpact"`
	ReasonCode                  string        `json:"reasonCode,omitempty"`
	Gate                        int           `json:"gate"`
	GateName                    string        `json:"gateName"`
	BaseGateState               string        `json:"baseGateState"`
	FinalGateState              string        `json:"finalGateState"`
	BaseOverall                 string        `json:"baseOverall"`
	FinalOverall                string        `json:"finalOverall"`
	GateDetail                  string        `json:"gateDetail,omitempty"`
	Checks                      []EngineCheck `json:"checks,omitempty"`
	AppEngineRuntimeState       string        `json:"appEngineRuntimeState,omitempty"`
	AppEngineDiagnosticModuleID string        `json:"appEngineDiagnosticModuleId,omitempty"`
	AppEngineDiagnosticVersion  string        `json:"appEngineDiagnosticVersion,omitempty"`
	Note                        string        `json:"note,omitempty"`
}

func productRegistrationCheck(name, installed, state, regKey, regValue, regView, regErr string) (EngineCheck, bool) {
	regKey = strings.TrimSpace(regKey)
	regValue = strings.TrimSpace(regValue)
	if regKey == "" || regValue == "" || state == registrationStateNotEvaluated {
		return EngineCheck{}, false
	}

	checkName := tr("health.registration.synapse.check")
	if strings.EqualFold(name, "Chroma") {
		checkName = tr("health.registration.chroma.check")
	}
	mapping := regKey + " [" + regValue + "]"
	if strings.TrimSpace(regView) != "" {
		mapping += " / " + strings.TrimSpace(regView)
	}
	c := EngineCheck{
		Section:  "AppEngine",
		Check:    checkName,
		Expected: tr("health.registration.expected"),
	}
	if state == registrationStatePresent && strings.TrimSpace(installed) != "" {
		c.Status = "PASS"
		c.Actual = strings.TrimSpace(installed)
		c.Detail = trf("health.registration.present.detail", "mapping", mapping)
		return c, true
	}

	c.Status = "UNKNOWN"
	c.Actual = tr("health.registration.unreadable.actual")
	if strings.TrimSpace(regErr) == "" {
		regErr = "Registry-Wert konnte nicht bestätigt werden"
	}
	c.Detail = trf("health.registration.unreadable.detail", "error", regErr)
	return c, true
}

func buildApplicationHealthAssessment(stamp string, baseOverall string, baseStates [gateCount]string, st VersionStatus, appDiag AppEngineDiagnosticResult, appDiagErr error) ApplicationHealthAssessment {
	a := ApplicationHealthAssessment{
		SchemaVersion:               applicationHealthAssessmentSchema,
		ToolVersion:                 referenceVersion,
		MeasurementStamp:            stamp,
		Timestamp:                   time.Now().Format(time.RFC3339Nano),
		Source:                      "appengine-usermode+official-razer-prod-manifest-registration",
		DiscoveryURL:                st.DiscoveryURL,
		ManifestURL:                 st.ManifestURL,
		ManifestChannel:             st.ManifestChannel,
		ManifestProdHash:            st.ManifestProdHash,
		Gate:                        applicationHealthGate,
		GateName:                    gateName(applicationHealthGate - 1),
		BaseGateState:               strings.TrimSpace(baseStates[applicationHealthGate-1]),
		FinalGateState:              strings.TrimSpace(baseStates[applicationHealthGate-1]),
		BaseOverall:                 strings.TrimSpace(baseOverall),
		FinalOverall:                strings.TrimSpace(baseOverall),
		AppEngineRuntimeState:       strings.TrimSpace(appDiag.RuntimeState),
		AppEngineDiagnosticModuleID: appEngineDiagnosticModuleID,
		AppEngineDiagnosticVersion:  appEngineDiagnosticModuleVersion,
	}

	checks := make([]EngineCheck, 0, 3)
	appCheck, appImpact, appReason := appEngineHealthCheck(appDiag, appDiagErr)
	checks = append(checks, appCheck)
	a.Evaluated = true

	manifestEvaluated := strings.TrimSpace(st.OnlineError) == "" && strings.TrimSpace(st.ManifestURL) != ""
	if manifestEvaluated {
		if c, ok := productRegistrationCheck("Synapse", st.InstalledSynapse, st.SynapseRegistrationState, st.SynapseRegistryKey, st.SynapseRegistryValue, st.SynapseRegistryView, st.SynapseRegistrationError); ok {
			checks = append(checks, c)
		}
		if c, ok := productRegistrationCheck("Chroma", st.InstalledChroma, st.ChromaRegistrationState, st.ChromaRegistryKey, st.ChromaRegistryValue, st.ChromaRegistryView, st.ChromaRegistrationError); ok {
			checks = append(checks, c)
		}
	} else {
		a.Note = "Offizielles Razer prod-Manifest war für diese Messung nicht auswertbar; AppEngine-User-Mode-Prüfung bleibt davon unabhängig aktiv."
	}
	a.Checks = checks

	unknown := false
	registrationUnknown := false
	for i, c := range checks {
		if strings.EqualFold(strings.TrimSpace(c.Status), "UNKNOWN") {
			unknown = true
			if i > 0 {
				registrationUnknown = true
			}
		}
	}

	if unknown && strings.EqualFold(a.BaseGateState, "PASS") {
		a.HealthImpact = true
		a.FinalGateState = "UNKNOWN"
		a.FinalOverall = "UNKNOWN"
		if appImpact {
			a.ReasonCode = appReason
			a.GateDetail = tr("health.appengine.runtime.gate_detail")
		} else if registrationUnknown {
			a.ReasonCode = applicationHealthReasonUnconfirmed
			a.GateDetail = tr("health.registration.gate.detail")
		}
	}
	return a
}

func applyApplicationHealthAssessment(states *[gateCount]string, inspections *[gateCount]GateInspection, a ApplicationHealthAssessment) {
	if !a.Evaluated || len(a.Checks) == 0 {
		return
	}
	idx := applicationHealthGate - 1
	ins := &inspections[idx]
	ins.Available = true
	ins.Checks = append(ins.Checks, a.Checks...)
	if a.HealthImpact {
		states[idx] = gateUnclear
		ins.GateDetail = a.GateDetail
	}
}

func writeApplicationHealthAssessment(path string, a ApplicationHealthAssessment) error {
	b, err := json.MarshalIndent(a, "", "  ")
	if err != nil {
		return err
	}
	b = append(b, '\n')
	return os.WriteFile(path, b, 0644)
}

func engineCheckAsAny(c EngineCheck) any {
	b, _ := json.Marshal(c)
	var v any
	_ = json.Unmarshal(b, &v)
	return v
}

func bumpJSONCount(counts map[string]any, key string, n int) {
	if n == 0 {
		return
	}
	cur := 0
	switch v := counts[key].(type) {
	case float64:
		cur = int(v)
	case int:
		cur = v
	case json.Number:
		cur, _ = strconv.Atoi(v.String())
	}
	counts[key] = cur + n
}

func patchRazerHealthJSON(path string, a ApplicationHealthAssessment) error {
	if !a.Evaluated {
		return nil
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	var root map[string]any
	if err := json.Unmarshal(b, &root); err != nil {
		return err
	}
	root["healthCenterAssessment"] = a

	passAdded, unknownAdded := 0, 0
	checks, _ := root["checks"].([]any)
	for _, c := range a.Checks {
		checks = append(checks, engineCheckAsAny(c))
		switch strings.ToUpper(strings.TrimSpace(c.Status)) {
		case "PASS":
			passAdded++
		case "UNKNOWN":
			unknownAdded++
		}
	}
	root["checks"] = checks
	if counts, ok := root["counts"].(map[string]any); ok {
		bumpJSONCount(counts, "pass", passAdded)
		bumpJSONCount(counts, "unknown", unknownAdded)
	}

	if a.HealthImpact {
		if gates, ok := root["gates"].([]any); ok && len(gates) >= applicationHealthGate {
			if g, ok := gates[applicationHealthGate-1].(map[string]any); ok {
				g["Status"] = "UNKNOWN"
				g["Label"] = "UNKLAR"
				g["Detail"] = a.GateDetail
			}
		}
		root["overall"] = "UNKNOWN"
		root["overallLabel"] = "UNKLAR"
		root["rawDiagnostic"] = "UNKNOWN"
	}

	out, err := json.MarshalIndent(root, "", "  ")
	if err != nil {
		return err
	}
	out = append(out, '\n')
	return os.WriteFile(path, out, 0644)
}

func patchGateResult(path string, a ApplicationHealthAssessment) error {
	if !a.HealthImpact {
		return nil
	}
	b, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	lines := strings.Split(strings.ReplaceAll(string(b), "\r\n", "\n"), "\n")
	for i, line := range lines {
		if strings.HasPrefix(line, "OVERALL|") {
			lines[i] = "OVERALL|UNKNOWN"
			continue
		}
		if strings.HasPrefix(line, fmt.Sprintf("GATE|%d|", applicationHealthGate)) {
			parts := strings.Split(line, "|")
			if len(parts) >= 4 {
				parts[2] = "UNKNOWN"
				lines[i] = strings.Join(parts, "|")
			}
		}
	}
	out := strings.Join(lines, "\r\n")
	return os.WriteFile(path, []byte(out), 0644)
}

func persistApplicationHealthComposition(jsonPath, gatePath, assessmentPath string, a ApplicationHealthAssessment) error {
	if err := writeApplicationHealthAssessment(assessmentPath, a); err != nil {
		return err
	}
	if err := patchRazerHealthJSON(jsonPath, a); err != nil {
		return err
	}
	if err := patchGateResult(gatePath, a); err != nil {
		return err
	}
	return nil
}

func applicationAssessmentPath(diagDir, stamp string) string {
	return filepath.Join(diagDir, "ApplicationHealthAssessment-"+stamp+".json")
}
