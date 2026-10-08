//go:build windows

package main

import (
	"embed"
	"encoding/json"
	"fmt"
	"regexp"
	"strconv"
	"strings"
)

const activeLocale = "de-DE"

// de-DE is the single runtime presentation source in v2.0.1.
// Future languages must be added as additional catalogs; presentation text
// must never be reintroduced as Go string literals.
//
//go:embed locales/de-DE.json
var localeFS embed.FS

type localeDocument struct {
	Meta struct {
		Locale   string `json:"locale"`
		Language string `json:"language"`
		Version  string `json:"version"`
	} `json:"_meta"`
	Strings map[string]string `json:"strings"`
}

var (
	deStrings        map[string]string
	placeholderRegex = regexp.MustCompile(`\{([A-Za-z0-9_.-]+)\}`)
)

func init() {
	b, err := localeFS.ReadFile("locales/de-DE.json")
	if err != nil {
		panic(fmt.Errorf("load %s locale: %w", activeLocale, err))
	}
	var doc localeDocument
	if err := json.Unmarshal(b, &doc); err != nil {
		panic(fmt.Errorf("parse %s locale: %w", activeLocale, err))
	}
	if doc.Meta.Locale != activeLocale {
		panic(fmt.Errorf("locale mismatch: expected %s, got %s", activeLocale, doc.Meta.Locale))
	}
	if len(doc.Strings) == 0 {
		panic("de-DE locale has no strings")
	}
	deStrings = doc.Strings
}

func tr(key string) string {
	v, ok := deStrings[key]
	if !ok {
		panic("missing i18n key: " + key)
	}
	return v
}

func trf(key string, pairs ...any) string {
	if len(pairs)%2 != 0 {
		panic("i18n placeholders require name/value pairs for key: " + key)
	}
	v := tr(key)
	for i := 0; i < len(pairs); i += 2 {
		name, ok := pairs[i].(string)
		if !ok || name == "" {
			panic("invalid i18n placeholder name for key: " + key)
		}
		v = strings.ReplaceAll(v, "{"+name+"}", fmt.Sprint(pairs[i+1]))
	}
	if m := placeholderRegex.FindString(v); m != "" {
		panic("unresolved i18n placeholder " + m + " for key: " + key)
	}
	return v
}

func trn(base string, count int, pairs ...any) string {
	suffix := ".other"
	if count == 1 {
		suffix = ".one"
	}
	args := append([]any{"count", count}, pairs...)
	return trf(base+suffix, args...)
}

func trInt(key string, value int) string {
	return trf(key, "value", strconv.Itoa(value))
}

func displayVersion(raw string) string {
	raw = strings.TrimSpace(raw)
	raw = strings.TrimPrefix(strings.TrimPrefix(raw, "v"), "V")
	if raw == "" {
		return ""
	}
	return trf("app.version", "version", raw)
}

func overallText(code string) string {
	switch strings.ToUpper(strings.TrimSpace(code)) {
	case overallUnchecked:
		return tr("overall.unchecked")
	case overallChecking:
		return tr("overall.checking")
	case overallHealthy, "PASS", "PASSED", "GESUND":
		return tr("overall.healthy")
	case overallFailed, "FAIL", "FEHLER":
		return tr("overall.failed")
	default:
		return tr("overall.incomplete")
	}
}

func gateStatusText(code string) string {
	switch strings.ToUpper(strings.TrimSpace(code)) {
	case gateUnchecked, "NICHT GEPRÜFT":
		return tr("gate.lifecycle.unchecked")
	case gateWaiting, "WARTET":
		return tr("gate.lifecycle.waiting")
	case gateChecking, "PRÜFUNG", "PRÜFUNG …":
		return tr("gate.lifecycle.checking")
	case gatePassed, "PASSED", "BESTANDEN":
		return tr("gate.result.passed")
	case gateHint, "WARNING", "HINWEIS":
		return tr("gate.result.hint")
	case gateUnclear, "UNKLAR":
		return tr("gate.result.unclear")
	case gateFailed, "FEHLER":
		return tr("gate.result.failed")
	default:
		return tr("gate.result.not_evaluable")
	}
}

func measurementStatusText(code string) string {
	switch normalizeMeasurementStatus(code) {
	case measurementHealthy:
		return tr("measurement.result.healthy")
	case measurementHint:
		return tr("measurement.result.hint")
	case measurementUnclear:
		return tr("measurement.result.unclear")
	case measurementFailed:
		return tr("measurement.result.failed")
	default:
		return tr("measurement.result.unclear")
	}
}

func findingStatusText(code string) string {
	switch strings.ToUpper(strings.TrimSpace(code)) {
	case "PASS", "PASSED", "BESTANDEN":
		return tr("popover.finding.ok")
	case "WARN", "WARNING", "HINWEIS":
		return tr("popover.finding.hint")
	case "UNKNOWN", "UNKLAR":
		return tr("popover.finding.unclear")
	case "FAIL", "FAILED", "FEHLER":
		return tr("popover.finding.failed")
	case "INFO":
		return tr("popover.finding.info")
	default:
		return strings.ToUpper(strings.TrimSpace(code))
	}
}
