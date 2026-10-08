# RHC v3.0.8 — GitHub source-import handover

Target: https://github.com/SaschaP1980/RazerHealthCenter
Draft PR: https://github.com/SaschaP1980/RazerHealthCenter/pull/2
Target branch: `import/RHC-1-v3.0.8`

**Status**: PR contains source verification and CI workflow only. Full product source (321 files) has **NOT** been uploaded. Release/publishing is not authorized. This kit provides the exact source and vetted helper needed for the remaining byte-preserving transfer.

**Important privacy gate:** GitHub repository is public. Before the commands below that contain `--public-source-reviewed`, review the original source ZIP's three `BUILD-FULL-*.log` files, `forensics/*`, historic validation files, assets and third-party/license material for private information or content you do not wish to publish. The preceding automated heuristic scan reported no credentials or personal-user paths, but is not a substitute for your review. Omitting the flag correctly prevents import.

## Verified inputs

- Original Source ZIP SHA-256: `f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495`
- File count: 321 regular files, no case-insensitive filename collisions
- Exact source byte-inventory fingerprint: `adbfc9de536bd0ca8a1b69163ffdf080fe0b46b083b42ca498b8fafeb18703db`
- Existing v3.0.8 golden Windows EXE: `6b48359e6388ee20a0b4974ce1c75ba7c2cd537dc58512e62ed9e6d263529f0a`
- GitHub import branch has new `tools/verify_source_intake.py` and `tools/import_source_archive.py` with the `--expected-branch` parameter. Prefer the current GitHub copy of these helpers, not the copy in the kit, if the branch has since changed.

## Commands (from a computer with GitHub network access and Git/Python 3.9+)

In a terminal (Git Bash/macOS/Linux; substitute paths as needed):

```bash
git clone https://github.com/SaschaP1980/RazerHealthCenter.git
cd RazerHealthCenter
git fetch origin
git switch --track origin/import/RHC-1-v3.0.8
git status --porcelain
# Status MUST be clean; record exact HEAD:
git rev-parse HEAD
```

The ZIP path must refer to `Razer-Synapse-Chroma-Health-Center-Source-v3.0.8.zip` inside the import kit **after extraction**. Run the dry-run first, with your recorded `HEAD`:

```bash
python tools/import_source_archive.py \
  --repo . --archive "<ABSOLUTE_PATH_TO_SOURCE_ZIP>" \
  --expected-archive-sha256 f2f973acf587b4334f6b90b4418a0d953641fb706188bd354e0577a97a86d495 \
  --expected-file-count 321 \
  --expected-branch import/RHC-1-v3.0.8 \
  --expected-head "<EXACT_CURRENT_BRANCH_HEAD_SHA>" \
  --replace-bootstrap-readme
```

Expected: `SOURCE_INTAKE_MODE=DRY_RUN; no files written`. This command must not upload, commit or push any files.

**Only after you have reviewed and approved the public source content**, repeat the **same** command and append both flags:

```bash
  --apply --public-source-reviewed
```

Then verify:

```bash
python -B tools/verify_source_intake.py --root .
# Expected: RHC_SOURCE_INTAKE_MANIFEST=PASS files=321 fingerprint=adbfc9de...
git diff --check
git status --short
git add -A
git diff --cached --check
git diff --cached --stat
git diff --cached --name-status
```

Inspect this *entire* staged scope: 321 original source entries including replacement source `README.md`, plus the generated `docs/migration/RHC-v3.0.8-source-file-manifest.json`. Do not commit sensitive files. The source import should not alter the product version or create an EXE/source ZIP in Git.

Once the staged scope has passed review, commit and push the import branch:

```bash
git commit -m 'migration: import exact canonical RHC v3.0.8 source'
git push -u origin import/RHC-1-v3.0.8
```

The existing Draft PR #2 automatically triggers GitHub Actions: the Linux gate must reproduce the golden EXE checksum; the Windows gate must run Windows PowerShell 5.1 parsing and the safety validators. Do **not** mark PR ready/merge until both jobs PASS, exact 321-file manifest equality and public-source review are confirmed. GitHub checks failing because the source is still absent are expected fail-closed staging signals, not a successful build.

## Automation evidence already measured

- Local exact source verifier: original source PASS, file tampering rejected, manifest tampering rejected, missing file rejected — 4/4 expected outcomes.
- Branch-specific importer: dry-run PASS, unreviewed apply rejected, reviewed apply preserved all 321 source bytes; generated source manifest validated PASS.
- GitHub Draft PR #2 initially failed on missing `go.mod` (Linux) / missing manifest (Windows), as expected. No product build or safety tests ran. The CI workflow is a no-publish intake gate; it does not automatically merge or release.

Only after import is complete and PR is verified should RHC's Single Source of Truth status advance from "migration in progress" to "source imported". Separate release automation and physical hardware acceptance remain future phases.
