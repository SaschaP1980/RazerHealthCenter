# RHC v3.0.8 — Safe source import playbook

**Historical playbook — completed via PR #2.** All 321 original sources were verified and merged at `daf3e4994f108299c9ed9aa47bbaf48b2ae720d9`; both hosted Linux and Windows passed in [run #37737410046](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37737410046). Retain the procedures below as reproducible migration history; they are **not** an instruction to repeat the already-completed import or authorize a release/repair. Current state: [migration status](MIGRATION_STATUS.md).

## Preconditions

- An environment with authorized GitHub git push/PR access, Python 3.9+ and Git. The migration preparation container could use the GitHub connector for small source-text commits, but local git transport failed DNS; that path is not a verified bulk/binary upload method.
- The **original** v3.0.8 Source ZIP, SHA-256: `f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495`; exactly **321 regular files**. Do not use the Portable ZIP here.
- User or owner has reviewed historical build logs, forensics, diagnostic data and source for publication in a **public** GitHub repository. A heuristic secret scan with zero hits is not sufficient consent/safety evidence.
- Re-read current remote `main` before intake; **do not hardcode the SHA recorded in an earlier chat**. Use a freshly cloned clean checkout. Import deliberately replaces the provisional bootstrap `README.md` with the byte-identical source-provided `README.md`. GitHub governance remains under `docs/`.

## 1. Clone or refresh an exact clean main

~~~bash
git clone https://github.com/SaschaP1980/RazerHealthCenter.git
cd RazerHealthCenter
git fetch origin
git switch main
git pull --ff-only origin main
git status --short
git rev-parse HEAD
~~~

The status **must** be empty. Save the current SHA as the `--expected-head` lease. The migration PR branch may also be used if it exists: run `git switch import/RHC-1-v3.0.8`, verify its clean status and exact HEAD, and add `--expected-branch import/RHC-1-v3.0.8` to the intake commands below. Do not reuse an old SHA after switching branches.

## 2. Preview source intake; no mutation

Run this exact reviewed helper on the **clean** `main` checkout, replacing `<SOURCE_ZIP_PATH>` and `<CURRENT_MAIN_SHA>`:

~~~bash
python3 tools/import_source_archive.py \
  --repo . \
  --archive "<SOURCE_ZIP_PATH>" \
  --expected-archive-sha256 f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495 \
  --expected-file-count 321 \
  --expected-head <CURRENT_MAIN_SHA> \
  --replace-bootstrap-readme
~~~

Expected: `SOURCE_INTAKE_CHECK=PASS`, `SOURCE_INTAKE_MODE=DRY_RUN`. A missing/incorrect README replacement flag, archive hash, file count, source path or clean repo **must fail closed**.

## 3. After public-source review, apply to working tree (not remote)

Repeat command with `--apply --public-source-reviewed`. This is an explicit human public-upload acknowledgement; the script itself does **not** upload, commit or create any tag/release. It writes a SHA-256 entry for every imported file to `docs/migration/RHC-v3.0.8-source-file-manifest.json`, preserves bytes/line endings and checks every written hash.

**Important:** `--public-source-reviewed` must be true based on an actual review, not supplied merely to bypass the gate.

## 4. Stage a reviewed import on a dedicated PR branch

~~~bash
git switch -c import/RHC-1-v3.0.8  # omit if already on this existing PR branch
git status --short
git add -A
git diff --cached --stat
git diff --cached --check
git diff --cached --name-status
~~~

Expect exactly the reviewed baseline files plus the generated manifest, and the intended one-file `README.md` replacement. Check for unwanted private data, binaries, local logs, secrets, token files and unexpected modifications. Confirm the original `go.mod`, `model.go`, `build.sh`, `resources/`, `assets/` and safety scripts exist as root-relative build inputs.

No product version bump, repair logic change or manual release tag is part of this source-import PR.

Commit and push only **after** reviewing the full diff. Open a PR into `main`; do not merge on an unverified local-only PASS.

## 5. Hosted source-intake validation

Once GitHub source is available and checked out at the import branch SHA, request the manual-only [RHC v3.0.8 Source Intake](../.github/workflows/rhc-source-intake.yml) workflow **against the import SHA/ref**. It performs:
- Linux Go 1.23.2 original `build.sh`, Go+Python tests, Windows cross-build and **exact reference EXE SHA**.
- Hosted Windows 2025 runner using genuine Windows PowerShell 5.1 parser, native Go test/vet and relevant read-only diagnostic/repair source validators.
- No GitHub Release or public pointer mutation.

If GitHub refuses to display the manual workflow before the source ref is merged, **do not merge untested source**: add an explicitly PR-triggered intake gate on the import branch as a reviewed documentation/workflow correction, run it and require GREEN before merging. Record the actual limitation and fix in `docs/MIGRATION_LESSONS.md` and the generic template. Workflow-dispatch discoverability and required checks have **not** yet been tested end-to-end.

## 6. Finalize authority transition

After verified PR and hosted gate PASS, update `docs/MIGRATION_STATUS.md` and Issue RHC-1 with the actual source-import commit, SHA manifest, runner versions/validator counts, failed attempts, branch/ruleset statuses and real RHC acceptance requirements. Only declare GitHub the complete source of truth when all required approved files and build inputs are retrievable and reproduce the baseline.

**Do not start v3.0.9 or implement production Candidate/Release orchestration implicitly.** Those are separate gates in RHC-1.
