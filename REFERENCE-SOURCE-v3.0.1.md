# Reference Source – v3.0.1

This directory is the complete canonical source snapshot for **Razer Synapse +
Chroma Health Center v3.0.1**.

Reference baseline: v3.0.0 diagnostic/problem/repair platform plus the v3.0.1
authoritative-version-evidence correction.

Key source contracts:

- `model.go`: app/reference version 3.0.1; Health Engine 1.4.6.
- `health-engine-v1.4.6.ps1`: read-only 13-gate engine with local Known-Good
  versions/hashes removed from normative Health semantics.
- `versioncheck.go`: VersionStatus schema 4; dynamic Razer Discovery `prod` hash,
  system-specific official product manifest, Razer-supplied registry mappings,
  and informational update semantics.
- `problem.go`: Diagnostic Orchestrator 1.0.0 / Problem Catalog 1.0.0 remain
  unchanged in safety semantics.
- `repair.go`: Repair Engine/Catalog 2.0.0; every repair still requires explicit
  in-app confirmation plus post-repair verification.
- `tools/validate_v301_manifest_authority.py`: v3.0.1 RED/GREEN authority
  regression.
- `SAFETY-MODEL.txt`: explicit prohibition of automatic repair.

Historical engine/source files remain in the source package for audit/history but
are not the v3.0.1 runtime payload. The runtime embeds
`health-engine-v1.4.6.ps1`.

Build with:

```bash
./build.sh <output-directory>
```

The Windows amd64 GUI release executable is `RazerHealthCenter.exe`.
