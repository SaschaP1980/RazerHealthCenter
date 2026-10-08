package main

import "testing"

func TestParseObservedTopLevelRazerBuildMetadataWithAppEngineMajor(t *testing.T) {
	sample := []byte(`[2026/09/09 12:00:00.000] info: build
            url: https://apps.razer.com/synapse/dashboard/
            version: 0.0.86
            buildVersion: 2608311115
[2026/09/09 12:00:01.000] info: build
            url: https://apps.razer.com/chroma-app/dashboard/
            version: 0.0.63
            buildVersion: 2608271424
`)
	syn, chr := parseRazerBuildMetadata(sample, "4.0.699")
	if syn.ReleaseVersion != "4.0.86.2608311115" {
		t.Fatalf("unexpected Synapse version: %#v", syn)
	}
	if chr.ReleaseVersion != "4.0.63.2608271424" {
		t.Fatalf("unexpected Chroma version: %#v", chr)
	}
	if syn.RawVersion != "0.0.86" || syn.BuildVersion != "2608311115" {
		t.Fatalf("Synapse raw metadata not preserved: %#v", syn)
	}
	if chr.RawVersion != "0.0.63" || chr.BuildVersion != "2608271424" {
		t.Fatalf("Chroma raw metadata not preserved: %#v", chr)
	}
	if syn.Derivation != "appengine-major+top-level-product-tail+build" || chr.Derivation != syn.Derivation {
		t.Fatalf("unexpected derivation: syn=%q chr=%q", syn.Derivation, chr.Derivation)
	}
}

func TestAlreadyPublicLocalProductReleaseRemainsUnchanged(t *testing.T) {
	sample := []byte(`url: https://apps.razer.com/synapse/dashboard/
version: 4.0.86.2608311115
buildVersion: 2608311115
`)
	syn, _ := parseRazerBuildMetadata(sample, "4.0.699")
	if syn.ReleaseVersion != "4.0.86.2608311115" || syn.Derivation != "local-product-release" {
		t.Fatalf("already-public version must remain unchanged: %#v", syn)
	}
}

func TestRejectsMissingOrInvalidAppEngineMajorForRawTopLevelVersion(t *testing.T) {
	sample := []byte(`url: https://apps.razer.com/synapse/dashboard/
version: 0.0.86
buildVersion: 2608311115
`)
	for _, pkg := range []string{"", "0.0.699", "4.0.699.99", "garbage"} {
		syn, _ := parseRazerBuildMetadata(sample, pkg)
		if syn.ReleaseVersion != "" {
			t.Fatalf("must reject AppEngine package %q: %#v", pkg, syn)
		}
	}
}

func TestRejectsUnexpectedRawProductVersionShape(t *testing.T) {
	sample := []byte(`url: https://apps.razer.com/synapse/dashboard/
version: 1.0.86
buildVersion: 2608311115
`)
	syn, _ := parseRazerBuildMetadata(sample, "4.0.699")
	if syn.ReleaseVersion != "" {
		t.Fatalf("unexpected raw product domain must be rejected: %#v", syn)
	}
}

func TestRejectsModuleVersionDomain(t *testing.T) {
	sample := []byte(`url: https://apps.razer.com/synapse/chroma-connect/
version: 0.0.86
buildVersion: 2608311115
`)
	syn, chr := parseRazerBuildMetadata(sample, "4.0.699")
	if syn.ReleaseVersion != "" || chr.ReleaseVersion != "" {
		t.Fatalf("module build must not become product version: syn=%#v chr=%#v", syn, chr)
	}
}

func TestPublicVersionShape(t *testing.T) {
	for _, v := range []string{"4.0.86.2608311115", "4.0.63.2608271424"} {
		if !isPublicRazerReleaseVersion(v) {
			t.Fatalf("expected public release version: %s", v)
		}
	}
	for _, v := range []string{"4.0.699", "4.0.699.99", "1.0.0.1234", "0.0.86.2608311115", ""} {
		if isPublicRazerReleaseVersion(v) {
			t.Fatalf("must reject incompatible version domain: %s", v)
		}
	}
}

func TestAppEnginePackageMajor(t *testing.T) {
	if got := appEnginePackageMajor("4.0.699"); got != "4" {
		t.Fatalf("expected AppEngine major 4, got %q", got)
	}
	for _, bad := range []string{"", "0.0.699", "4.0.699.99", "app-4.0.699"} {
		if got := appEnginePackageMajor(bad); got != "" {
			t.Fatalf("invalid package %q produced major %q", bad, got)
		}
	}
}
