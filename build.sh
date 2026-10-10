#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
OUT="${1:-$ROOT/dist}"
mkdir -p "$OUT"
cd "$ROOT"
# RHC-131: optional, read-only phase timestamps; no validation command or gate changes.
# GNU date is available on the hosted Ubuntu build runners.
rhc131_phase() {
  printf 'RHC131_PHASE %s=%s label=%s\n' "$1" "$(date -u +'%Y-%m-%dT%H:%M:%S.%3NZ')" "$2"
}
rhc131_phase start validation
python3 "$ROOT/tools/test_powershell_reserved_pid.py"
python3 "$ROOT/tools/validate_i18n.py"
python3 "$ROOT/tools/validate_repair_safety.py"
python3 "$ROOT/tools/validate_setup_inventory.py"
python3 "$ROOT/tools/validate_guided_calibration.py"
python3 "$ROOT/tools/validate_guided_flow_v236.py"
python3 "$ROOT/tools/validate_guided_ux_v2310.py"
python3 "$ROOT/tools/validate_tray_menu_v2312.py"
python3 "$ROOT/tools/validate_historical_details_v240.py"
python3 "$ROOT/tools/validate_v302_historical_session_archive.py"
python3 "$ROOT/tools/validate_v303_archive_header_polish.py"
python3 "$ROOT/tools/validate_v304_archive_surface_tint.py"
python3 "$ROOT/tools/validate_v300_diagnostic_repair_platform.py"
python3 "$ROOT/tools/validate_v301_manifest_authority.py"
python3 "$ROOT/tools/validate_v305_false_green_guard.py"
python3 "$ROOT/tools/validate_v306_appengine_recovery.py"
python3 "$ROOT/tools/validate_v307_ps51_appengine_diagnostic.py"
python3 "$ROOT/tools/validate_v308_background_runtime_semantics.py"
python3 "$ROOT/tools/validate_healthcheck_selection_v237.py"
python3 "$ROOT/tools/validate_connection_presentation_v239.py"
python3 "$ROOT/tools/test_structured_failure_details_v238.py"
python3 "$ROOT/tools/validate_gate_finalization_v238.py"
python3 "$ROOT/tools/validate_live_performance.py"
python3 "$ROOT/tools/validate_powershell_encoding.py"
python3 "$ROOT/tools/validate_version_check.py"
python3 "$ROOT/tools/validate_log_evidence.py"
rhc131_phase end validation
rhc131_phase start go_test
go test .
rhc131_phase end go_test
rhc131_phase start i18n_guard
go run ./tools/i18n_guard .
rhc131_phase end i18n_guard
rhc131_phase start go_vet
GOOS=windows GOARCH=amd64 go vet ./...
rhc131_phase end go_vet
rhc131_phase start go_build
GOOS=windows GOARCH=amd64 CGO_ENABLED=0 go build -trimpath -ldflags='-H windowsgui' -o "$OUT/RazerHealthCenter-unresourced.exe" .
rhc131_phase end go_build
rhc131_phase start resource_patch
python3 "$ROOT/tools/patch_rsrc.py" "$OUT/RazerHealthCenter-unresourced.exe" "$ROOT/resources/app_rsrc.bin" "$ROOT/resources/app_rsrc.json" "$OUT/RazerHealthCenter.exe"
rhc131_phase end resource_patch
rhc131_phase start pe_validation
python3 "$ROOT/tools/validate_pe.py" "$OUT/RazerHealthCenter.exe"
rhc131_phase end pe_validation
rhc131_phase start ui_validation
python3 "$ROOT/tools/validate_ui_recovery.py"
rhc131_phase end ui_validation
rhc131_phase start checksum
sha256sum "$OUT/RazerHealthCenter.exe" > "$OUT/RazerHealthCenter.exe.sha256"
rhc131_phase end checksum
