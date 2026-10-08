# Reference Source – v3.0.0

This directory is the complete canonical source snapshot for **Razer Synapse +
Chroma Health Center v3.0.0**.

Reference baseline: natively accepted v2.4.0 plus the v3.0.0 diagnostic/problem/
repair platform and product rename.

Key source contracts:

- `model.go`: app/reference version 3.0.0.
- `health-engine-v1.4.5.ps1`: unchanged read-only Health Engine behavior.
- `problem.go`: Diagnostic Orchestrator 1.0.0, Problem Catalog 1.0.0, structured
  findings and exact known Gate-8 classifier.
- `diagnostics/diagnose-chroma-services-v1.0.0.ps1`: read-only deep diagnostic.
- `repair.go`: Repair Catalog / helper / mandatory confirmation / verification.
- `repair/repair-chroma-services-v1.1.0.ps1`: first catalogued repair recipe.
- `SAFETY-MODEL.txt`: explicit prohibition of automatic repair.
- `tools/validate_v300_diagnostic_repair_platform.py`: v3 RED/GREEN regression.

Build with:

```bash
./build.sh <output-directory>
```

The Windows amd64 GUI release executable is `RazerHealthCenter.exe`.
