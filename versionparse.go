package main

import (
	"regexp"
	"strings"
)

var (
	publicRazerReleaseVersionRE = regexp.MustCompile(`^[1-9][0-9]*\.[0-9]+\.[0-9]+\.[0-9]{8,}$`)
	metadataVersionRE           = regexp.MustCompile(`(?i)\bversion\s*:\s*([0-9]+(?:\.[0-9]+){2,3})\b`)
	metadataBuildVersionRE      = regexp.MustCompile(`(?i)\bbuildVersion\s*:\s*([0-9]{8,})\b`)
	appEnginePackageVersionRE   = regexp.MustCompile(`^([0-9]+)\.([0-9]+)\.([0-9]+)$`)
	topLevelRawProductVersionRE = regexp.MustCompile(`^0\.0\.([0-9]+)$`)
	buildVersionRE              = regexp.MustCompile(`^[0-9]{8,}$`)
)

type razerProductVersionMetadata struct {
	ReleaseVersion string
	RawVersion     string
	BuildVersion   string
	Derivation     string
}

func isPublicRazerReleaseVersion(v string) bool {
	v = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(v), "V"))
	return publicRazerReleaseVersionRE.MatchString(v)
}

func appEnginePackageMajor(appEnginePackage string) string {
	appEnginePackage = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(appEnginePackage), "V"))
	m := appEnginePackageVersionRE.FindStringSubmatch(appEnginePackage)
	if len(m) != 4 || m[1] == "0" {
		return ""
	}
	return m[1]
}

// deriveRazerTopLevelReleaseVersion keeps all local version sources separate:
// - the product-specific dashboard metadata supplies the raw product tail and build;
// - the active local AppEngine package supplies only the leading product major.
// No online value is used to construct the local release version.
func deriveRazerTopLevelReleaseVersion(rawVersion, buildVersion, appEnginePackage string) razerProductVersionMetadata {
	rawVersion = strings.TrimSpace(strings.TrimPrefix(strings.TrimSpace(rawVersion), "V"))
	buildVersion = strings.TrimSpace(buildVersion)
	out := razerProductVersionMetadata{RawVersion: rawVersion, BuildVersion: buildVersion}

	// If Razer ever starts storing an already-public full release in the local
	// top-level metadata, accept it directly and do not rewrite it.
	if isPublicRazerReleaseVersion(rawVersion) {
		out.ReleaseVersion = rawVersion
		out.Derivation = "local-product-release"
		return out
	}
	if !buildVersionRE.MatchString(buildVersion) {
		return out
	}
	raw := topLevelRawProductVersionRE.FindStringSubmatch(rawVersion)
	if len(raw) != 2 {
		return out
	}
	major := appEnginePackageMajor(appEnginePackage)
	if major == "" {
		return out
	}
	// For the observed top-level Razer metadata, raw 0.0.<product> carries the
	// product release tail while the active AppEngine package identifies the
	// installed platform major (for example app-4.0.699 -> major 4).
	release := major + ".0." + raw[1] + "." + buildVersion
	if !isPublicRazerReleaseVersion(release) {
		return out
	}
	out.ReleaseVersion = release
	out.Derivation = "appengine-major+top-level-product-tail+build"
	return out
}

// parseRazerBuildMetadata extracts only top-level Synapse/Chroma dashboard build
// metadata. Module URLs such as /synapse/chroma-connect/ are intentionally not
// accepted, because they belong to a different version domain.
func parseRazerBuildMetadata(data []byte, appEnginePackage string) (synapse, chroma razerProductVersionMetadata) {
	text := strings.ReplaceAll(string(data), "\r\n", "\n")
	lines := strings.Split(text, "\n")
	for i, line := range lines {
		lower := strings.ToLower(line)
		product := ""
		switch {
		case strings.Contains(lower, "https://apps.razer.com/synapse/dashboard"):
			product = "synapse"
		case strings.Contains(lower, "https://apps.razer.com/chroma-app/dashboard"):
			product = "chroma"
		default:
			continue
		}

		version, build := "", ""
		limit := i + 28
		if limit > len(lines) {
			limit = len(lines)
		}
		for j := i + 1; j < limit; j++ {
			candidate := lines[j]
			candidateLower := strings.ToLower(candidate)
			if strings.Contains(candidateLower, "https://apps.razer.com/") {
				break
			}
			if version == "" {
				if m := metadataVersionRE.FindStringSubmatch(candidate); len(m) == 2 {
					version = m[1]
				}
			}
			if build == "" {
				if m := metadataBuildVersionRE.FindStringSubmatch(candidate); len(m) == 2 {
					build = m[1]
				}
			}
			if version != "" && build != "" {
				break
			}
		}
		derived := deriveRazerTopLevelReleaseVersion(version, build, appEnginePackage)
		if derived.ReleaseVersion == "" {
			continue
		}
		if product == "synapse" {
			synapse = derived
		} else {
			chroma = derived
		}
	}
	return synapse, chroma
}
