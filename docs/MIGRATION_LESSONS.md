# RHC migration lessons ledger

This document captures observed problems from [RHC-1](https://github.com/SaschaP1980/RazerHealthCenter/issues/1). Reusable controls are generalized in `docs/templates/PROJECT_MIGRATION_TEMPLATE.md`.

| ID | Observed event | Evidence classification | Correction / prevention |
| --- | --- | --- | --- |
| RHC-M01 | `main` was a default branch name but had no commit; branch request 404, Git refs 409 | GitHub API response | First README commit initializes repository; do not invent parent/tree hash |
| RHC-M02 | CLI `git ls-remote` could not resolve GitHub from local container | Local environment / external access | Use authenticated connector for small documentation writes; separate from full byte-preserving source transfer |
| RHC-M03 | First all-in-one `build.sh` invocation timed out after validators/`go test`, at Go i18n guard | Interactive timeout, **not test FAIL** | Re-run guard and warm full build; report timeout and actual full PASS separately, plan explicit cold toolchain time |
| RHC-M04 | ZIP structures differ: 321 regular source files versus 7 portable files plus 12 empty directories | Source archive inspection | Keep separate source-byte manifest and portable-directory/package layout checks |
| RHC-M05 | Source includes historical logs/forensic artifacts and repository is public | Security review risk (not an observed leak) | Heuristic credential scan is insufficient; review sensitive history before public import |
| RHC-M06 | LBS builds PowerShell runtime; RHC builds Go Windows EXE and retains PS5.1 diagnostics | Source contract review | Reuse workflow *gates*, adapt binaries/versioning/repair policies; no blind workflow copy |

**Rule:** An item remains open if its corrective gate has not been independently verified; don't erase failure logs after later green results.
