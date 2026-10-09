## Manual one-time GitHub Actions repository setup — project bootstrap checklist

Complete this **manually when creating a new GitHub repository that will use Actions to create pull requests**. It is **not** automatically transferred by a repository template, migration script, checkout or workflow YAML.

- [ ] Have a repository administrator open **Settings > Actions > General** in the **new target repository**, then scroll to **Workflow permissions**.
- [ ] For an explicitly owner-authorized PR-writing Actions pipeline, select **Read and write permissions**.
- [ ] Check **Allow GitHub Actions to create and approve pull requests** (this permits PR creation; automation must not self-approve PRs).
- [ ] Click **Save**, reopen the settings page and confirm both choices persisted.
- [ ] Verify required per-job least-privilege `GITHUB_TOKEN` YAML scopes separately, and respect any restrictive organization policy.
- [ ] Execute a real, scoped **nonpublishing** GitHub Actions PR-creation smoke test; independently verify the PR's actor/base/head and clean up only test-owned refs. A screenshot and Save alone are not an effective-permission test.
- [ ] Record administrator confirmation and exact successful CI/PR evidence in the new project's setup Issue. On denial, stop and choose a narrowly authorized GitHub App rather than bypassing protections.

This checklist applies **only for repositories requiring GitHub Actions to create PRs**; normal read-only repositories should keep minimal permissions. See [the operator guide](../GITHUB_HOWTO.md) for steps, security constraints and the RHC-43 real permission finding.

---
## Reusable interim release and English GitHub documentation pattern (RHC-43)

For all future GitHub development tasks, use **English** in Issues, comments, commits, source code comments, tests, workflow names, documentation and release notes; owner-facing chat may remain German with English technical terms.

Never assume that a single successful, specifically versioned interim publisher automatically extends to a following HOTFIX. A user request for a *complete* Development → Build → Release cycle must be treated as end-to-end: version/source/main consistency, exact native Linux+Windows evidence, two independent deterministic PE/ZIP builds, bounded PR/merge/source tag, immutable prior ZIP/history, public latest pointer, independently reread remote results, and verifiable cleanup. A Work/Candidate GREEN is **not** a released artifact. A mode that is approved conceptually but not implemented is **NOT READY**, not PASS.

Preserve production policy and hardware/rollback/signing evidence as separately observed states; a specific interim unsigned mode may defer only external approval categories, and must disclose unsigned/SmartScreen trust limitations. Never fake owner approval, disable repair safety or claim missing GitHub PR creation/branch cleanup permissions are present. Keep old release-workflow historical RED evidence and isolate old prepublication fixtures from future-version PR CI. Prefer scoped test-first counterexamples plus exact SHA hosted readback.

See [Git provenance](../GIT_PROVENANCE_CONTRACT.md), [Interim Contract](../REUSABLE_INTERIM_RELEASE_CONTRACT.md), [Development Guidelines](../DEVELOPMENT_GUIDELINES.md) and [Release Process](../RELEASE_PROCESS.md). For RHC and any adopting repository, future changed-file work—including documentation-only changes—must use a responsible Issue plus an explicit Issue-linked PR, verified exact-merge readback and Issue completion evidence. No routine direct-main edits; do not presume branch ruleset enforcement. Historical version-specific source and release proof belongs in the responsible Issues/Rolling Comments, not this reusable template.

---
# Reusable GitHub project migration template (v0.1)

**Purpose:** establish product source/build/safety/release authority on GitHub **without silent publication**. Product-neutral template; the [RHC migration ledger](../MIGRATION_STATUS.md) is the **historical** first case. Its original v3.0.8 ZIP with 12 empty directories, three-part source version and Draft-release proposal do **not** override RHC-16 `3.0.8.0` or RHC-12 `repo-downloads` (new lean seven-file ZIP, GitHub source, no separate Source ZIP). Check [current release rules](../RELEASE_PROCESS.md).

## Mandatory intake variables

| Field | Record verified value or `unknown` |
| --- | --- |
| Repository URL, visibility, owner permissions | <repo; visibility; access evidence> |
| Short project code and issue numbering rule | <e.g. RHC; actual GitHub Issue #N> |
| Product version(s) and actual source of version authority | <path, exact semantics> |
| Source/archive locations, SHA-256, file manifest and historical proof | <bytes/hash/count> |
| Language/toolchain version/dependencies | <names/versions; clean rebuild> |
| Native target OS/arch, signing, updater, installer/portable format | <grounded> |
| Product safety boundaries and prohibited CI side effects | <contracts> |
| Required hosted operating systems and validation matrix | <test names and counts> |
| Release and source package retention/distribution | <target, immutable assets> |
| Repository initialization, branch policy, token scopes, secrets | <observed configuration> |
| Previous exact baseline hashes, PR/Issue, recovery state | <evidence> |

## Stage 0 — Preserve provenance, authorize migration

- Obtain **complete** canonical source and release archives, build logs, regression reports and handover. Verify hashes against declared manifests. Distinguish supplied reports from newly rerun tests.
- Confirm whether the GitHub repository is public. Scan source and historical logs for secrets/PII; document scan limits and inspect relevant files. Do not upload sensitive material into public history; removing it later does not erase history.
- Freeze product-version and behavior scope. Initial repository bootstrap is not permission for an application update, firmware/service modification, signing decision or production release.
- Create one migration Issue with acceptance gates and known limitations. Use actual GitHub Issue #N, rename to `[<CODE>-N]`, and document path decisions and unresolved questions.

### Recovery bootstrap — mandatory before the first Work-Path mutation

For each later **Issue-backed Work-Path**, establish its single persistent Rolling Comment **before** creating a Work branch, opening a Work PR, making the first code/workflow commit or dispatching related CI:

1. Verify the Issue, owner authorization, current main SHA, product version, permitted diff and forbidden safety/release changes. If the repository is unborn, a minimal initial README/bootstrap commit may first establish a real main SHA, but must not start product Work.
2. Create the Issue comment with `Current phase: BOOTSTRAP`, the planned Work branch marked `NOT CREATED`, verified main SHA as last checkpoint, scope, risks, and the precise next recovery action. Mark a Work-Chat-ID `not issued` unless it was actually shown in the execution chat.
3. **Re-read** the comment through GitHub. Verify comment ID, stored body, independently sourced ISO 8601 UTC millisecond heartbeat and GitHub `created_at`/`updated_at`. If this bootstrap write or readback fails or is ambiguous: **STOP** before branch creation.
4. Re-verify main, create the Work branch from its pinned SHA, read back the branch head, update the **same** comment and verify that edit **before the first code commit**. A stale ref or missing checkpoint **BLOCKS** further work.
5. Before consequential transitions and after each significant commit/CI checkpoint, reconcile the live Issue, comment, refs, PR and CI; update SHA, failures and next action. After timeout/stream interruption, never guess or blindly retry an uncertain external write.

An initial comment added *after* code commits does not retrospectively establish resume safety and must be recorded as a **process nonconformance**, separately from technical test results. This rule does **not** require a Rolling Comment for routine one-commit documentation Fast-Paths. RHC-5 [incident evidence](https://github.com/SaschaP1980/RazerHealthCenter/issues/5#issuecomment-6056455848).

## Stage 1 — Safely initialize GitHub

- Check whether `main` has a commit. If unborn, use a simple first README commit; do not call `compare`/`update_ref` with fabricated base SHA. Read new head/tree after initialization.
- Create new-chat entry point, current status, development path guidelines, release target design and this migration template. Do not label bootstrap docs as the complete source of truth.
- Track file/checksum inventory, source tree and release-binary hash separately. Prevent Git storage of local build outputs, private logs, caches, secrets and platform-specific generated intermediates unless deliberately canonical.
- **Protect the default branch as an explicit setup gate:** the owner should configure an ACTIVE GitHub branch ruleset targeting `~DEFAULT_BRANCH` (or the exact intended branch); block deletions and non-fast-forward/force pushes, with no bypass actors by default. Re-query the full ruleset detail and `branches/<default>` to confirm effective enforcement. A UI screenshot of selected unsaved checkboxes or a missing warning is **not** proof of activation. If an integration cannot read the legacy branch-protection endpoint (403), use the readable ruleset and effective `protected` branch flag instead; record residual visibility limitations.
- **Split baseline protection from merge-gate enforcement:** do not turn on mandatory PRs/required status contexts until the target project's release workflow and required checks are implemented and tested. Stage 1 protects history/deletion only; ordinary direct fast-forward pushes remain possible and must not be described as blocked.


### Provision missing Issue labels automatically (idempotent)

Before assigning Issue priority or a development path, **reconcile the target repository's Issue-label catalog**. Use the live canonical definitions in [LenovoBootSelector](https://github.com/SaschaP1980/LenovoBootSelector) (its [Issue-label taxonomy](https://github.com/SaschaP1980/LenovoBootSelector/blob/main/docs/GITHUB_HOWTO.md)). Copy each missing canonical label's **name, description and hexadecimal color**, not just its name. For target-specific text, replace only the source's `work/LBS-<issue>` reference with `work/<PROJECT_CODE>-<issue>`.

The following nine labels were confirmed in LenovoBootSelector's actual labeled Issues and remain the donor-canonical migration baseline. The owner has additionally defined `dev-ops` as a tenth default label for new project migrations, with metadata verified in RazerHealthCenter; this **does not** assert that `dev-ops` exists in LenovoBootSelector. The final provisioner fetches the nine donor labels' live metadata and adds the separately owner-defined label from the verified values below. This table is an auditable reference, not a claim that the donor has no additional labels.

| Name | Color (hex) | Description (donor except owner-defined `dev-ops`) |
| --- | --- | --- |
| `bug` | `d73a4a` | Something isn't working |
| `enhancement` | `a2eeef` | New feature or request |
| `priority: critical` | `b60205` | Requires immediate attention / blocks important functionality |
| `priority: high` | `FFA500` | High priority; should be addressed soon |
| `priority: medium` | `fbca04` | Normal priority |
| `priority: low` | `c5def5` | Low priority; can be addressed later |
| `dev-path: fast` | `2DA44E` | Branchless atomic path for small, well-bounded Patch/Hotfix work. |
| `dev-path: work-branch` | `8250DF` | Uses `work/LBS-<issue>` for Major/Minor or complex Patch/Hotfix work. |
| `wontfix` | `ffffff` | This will not be worked on |
| `dev-ops` | `c4907e` | Development Operations or CI/CD related |

`dev-ops` is an **optional supplementary work-area label** for CI/CD, GitHub Actions, build/release automation, developer tooling and development operations. It may coexist with the appropriate `bug` or `enhancement` type, exactly one `priority:*` on open Issues and, when applicable, a single `dev-path:*`. It never substitutes for those dimensions or grants production/release authorization. Including it in a new repository's label catalog does **not** automatically assign it to any Issue.

**Executable bootstrap:** Authenticate GitHub CLI `gh` with read access to the donor and label-management write access to the target. Set `TARGET_REPO` and `PROJECT_CODE` for the **new project**, then run this block. It reads both catalogs completely before any write, creates **only missing** labels, and verifies the saved state. No issue labels are assigned automatically, no existing definitions are edited/deleted, and foreign labels are retained. Re-running it is a no-op when complete.

~~~bash
TARGET_REPO=OWNER/NEW_REPOSITORY PROJECT_CODE=NEW python3 - <<'PY'
import json
import os
import re
import subprocess
import sys

source = "SaschaP1980/LenovoBootSelector"
target = os.environ["TARGET_REPO"]
code = os.environ["PROJECT_CODE"]
required = (
    "bug", "enhancement", "priority: critical", "priority: high",
    "priority: medium", "priority: low", "dev-path: fast",
    "dev-path: work-branch", "wontfix",
)
owner_defined = (
    dict(name="dev-ops", color="c4907e",
         description="Development Operations or CI/CD related"),
)

if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", target):
    raise SystemExit("BLOCKED: invalid TARGET_REPO")
if not re.fullmatch(r"[A-Z][A-Z0-9]{1,15}", code):
    raise SystemExit("BLOCKED: invalid PROJECT_CODE")
if source.casefold() == target.casefold():
    raise SystemExit("BLOCKED: source and target must differ")

def gh(*args):
    return subprocess.check_output(["gh", "api", *args], text=True)

def read_catalog(repository):
    labels = []
    for page in range(1, 101):
        payload = json.loads(gh(
            f"repos/{repository}/labels?per_page=100&page={page}"
        ))
        if not isinstance(payload, list):
            raise ValueError("GitHub labels response was not a list")
        labels.extend(payload)
        if len(payload) < 100:
            break
    else:
        raise ValueError("Label pagination limit reached; no writes")
    by_name = {}
    for row in labels:
        if not isinstance(row, dict) or not isinstance(row.get("name"), str):
            raise ValueError("Invalid label record")
        key = row["name"].casefold()
        if key in by_name:
            raise ValueError("Ambiguous case-insensitive label duplicate")
        by_name[key] = row
    return by_name

donor = read_catalog(source)
existing = read_catalog(target)
if any(name.casefold() not in donor for name in required):
    raise SystemExit("BLOCKED: incomplete canonical source label catalog")

wanted = {}
for name in required:
    row = donor[name.casefold()]
    if row["name"] != name:
        raise SystemExit("BLOCKED: donor label name changed")
    color = row.get("color")
    description = row.get("description")
    if not isinstance(color, str) or not re.fullmatch(r"[0-9A-Fa-f]{6}", color):
        raise SystemExit("BLOCKED: missing or invalid donor label color")
    if not isinstance(description, str):
        raise SystemExit("BLOCKED: missing donor label description")
    description = description.replace(
        "work/LBS-<issue>", f"work/{code}-<issue>"
    )
    wanted[name.casefold()] = dict(
        name=name, color=color, description=description
    )

for row in owner_defined:
    key = row["name"].casefold()
    if key in wanted:
        raise SystemExit("BLOCKED: duplicate owner-defined label name")
    wanted[key] = row

# Fail closed on ALL pre-existing name/metadata drift BEFORE the first POST.
# This is deliberately earlier than the post-write verification below:
# otherwise other missing labels might already have been created.
drift = [
    row["name"] for key, row in wanted.items()
    if key in existing and (
        str(existing[key].get("color") or "").casefold() != row["color"].casefold()
        or existing[key].get("description") != row["description"]
    )
]
if drift:
    raise SystemExit(
        "BLOCKED: existing label definition(s) differ; zero changes made: "
        + ", ".join(drift)
    )

missing = [row for key, row in wanted.items() if key not in existing]
print(json.dumps({"target": target, "missing": missing}, ensure_ascii=False, indent=2))
for row in missing:
    gh("repos/" + target + "/labels", "--method", "POST",
       "-f", "name=" + row["name"],
       "-f", "color=" + row["color"],
       "-f", "description=" + row["description"])

after = read_catalog(target)
bad = [
    name for key, row in wanted.items()
    if (item := after.get(key)) is None or
    item.get("color", "").casefold() != row["color"].casefold() or
    item.get("description") != row["description"]
    for name in [row["name"]]
]
print(json.dumps({
    "created": len(missing), "present": len(wanted),
    "mismatchedExistingOrPostwrite": bad
}, ensure_ascii=False))
if bad:
    raise SystemExit("BLOCKED: existing label drift or post-write mismatch; do not overwrite automatically")
PY
~~~

**Acceptance / safety gate:** Confirm the target label list with a fresh API read: all nine donor-canonical names **plus** owner-defined `dev-ops` exist (ten total), colors and descriptions match (with the one documented project-code substitution), and a second execution reports `created=0`. If an existing same-name label has different metadata, report its drift and require a separate decision; **never silently overwrite** it. If donor/target access, permission, pagination, POST or readback fails, record BLOCKED and do not claim migration completion. Do not use a generic `gh issue edit --add-label` action to manufacture a missing repository label, and do not grant a read-only CI workflow label-write privileges.

### If the GitHub connector cannot manage repository labels

**Observed RHC-5 migration follow-up (2026-10-08):** The connected GitHub integration did not expose a repository-label creation/listing action, and its generic read endpoint rejected `GET /repos/{owner}/{repo}/labels` as unsupported. This was an **integration capability limitation**, not a failed label POST or a GitHub repository merge/branch-protection failure. Do not interpret a generic `400` from that connector as proof that the actual GitHub REST endpoint is unavailable.

**Recommended order:** First use the executable `gh api` block above from an explicitly authorized operator environment with target label-management permissions. If the connected environment has no authenticated `gh`/terminal access, a **single-purpose temporary GitHub Actions workflow** is a permissible, separately authorized provisioning transport. Do not grant an existing read-only validation workflow permanent write privileges, and do not use `gh issue edit --add-label` to work around absent repository labels.

For a one-time Actions fallback:

1. Confirm the target repository, current `main` SHA, donor catalog, expected missing-label names, correct `PROJECT_CODE`, and that creating labels is authorized. Do not automatically relabel any existing Issues. Keep the existing source/package/release policy untouched.
2. Add a **temporary** `.github/workflows/<PROJECT_CODE-lowercase>-label-provision-once.yml` to the target with `permissions: contents: read, issues: write`, a specific one-time `workflow_dispatch` confirmation or SHA-scoped push trigger, `GH_TOKEN: ${{ github.token }}`, `TARGET_REPO` and `PROJECT_CODE` set to the intended target, and a short timeout. Execute the **same Python code shown above** in a runner step (copy its Python body into a `python3 - <<'PY'` heredoc); no repository checkout or artifact upload is needed if embedded inline. The `issues: write` scope is necessary for label creation, not for GitHub Releases.
3. Verify the Actions job **completed successfully** and inspect its actual JSON summary: `created`, `present`, `mismatchedExistingOrPostwrite`. A queued/skipped workflow is not PASS. Check the exact labels and adapted descriptions using an independent fresh GitHub API read; if an existing label mismatches, the corrected script now blocks **before any POST**. An interrupted/ambiguous write must be reconciled by reading the catalog before retrying.
4. When successful, **delete the temporary write-enabled workflow in a separate commit**, re-read `main`, and compare the final Git tree with the pre-bootstrap tree. The labels persist as GitHub repository metadata even though the short-lived workflow file is removed. No permanent CI write permission should remain.
5. Re-running the provisioner should produce `created=0` with ten present labels; test this only if the same authorized execution access remains available. If not actually rerun, record idempotence as a **code contract**, not a tested historical fact.

**Actual RHC evidence:** [one-time label workflow run #37757322836](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37757322836) completed successfully: six missing labels created, nine present, zero metadata deviations. The workflow was then removed in [cleanup commit `919592e`](https://github.com/SaschaP1980/RazerHealthCenter/commit/919592eac51b4a3946fa395e30c9dc175c792df6); final Git tree matched the pre-provisioning tree. A second provisioning execution was **not** claimed. This is a successful alternate transport with an observed documentation/safety improvement, not a label provisioning failure.

## Stage 2 — Validate the original product before import

- Extract into a clean directory with ZipSlip/path guard. Check file count and duplicates, encoding, execute bits, BOM and line endings.
- Run the exact existing build/validation entry point on pinned toolchain with no network unless required/approved. Classify cold toolchain setup versus tests. Preserve first-attempt failures and retry evidence.
- Confirm binary SHA match on a clean rebuild; if not byte-identical, isolate deterministic inputs, signing, PE metadata, resource ordering, time, locale and toolchain. Do not silently lower the gate to semantic equivalence.
- When cross-compiled, run separate hosted native OS compatibility tests; never count static source checks as firmware/hardware E2E.

## Stage 3 — Import the complete reviewed source

- Use **a byte-preserving transfer mechanism**. A GitHub connector that only accepts inline text is insufficient for a binary-containing 321-file source archive. Do not claim GitHub is authoritative until every approved file and binary build input can be fetched from GitHub.
- Compare each imported path, size and SHA-256 to the locked extraction manifest, identify intentional exclusions and verify **zero unintended source edits**.
- Confirm `go.mod`/build entry, platform resources, locale and repair scripts exist at canonical relative paths. Keep historical release ZIPs out of source tree unless deliberate and immutable.

## Stage 4 — Hosted intake gates, no release

- Add manual-only `workflow_dispatch` source-intake smoke at first. Use pinned toolchain and least-privilege read-only workflow permissions. Check full existing tests and byte-identical baseline EXE.
- Hosted Linux builds and hosted native Windows/PS5.1 gates are **distinct** evidence. A workflow SKIPPED or a local PASS cannot substitute for a hosted required status.
- Verify job logs, exit status, output hashes and workflow metadata; add failing-test characterization for defects. Once independently GREEN, add protected PR gates intentionally.

## Stage 5 — Adapt, do not clone, the release architecture

- Preserve process *invariants*: one atomic Fast-Path Candidate for small fixes; Work-Branch + cumulative ledger + exact-SHA Development Completion for risky work; mandatory parallel hosted candidate gates; promotion fail-closed; independently reproducible release; single PR/merge activation; postrelease verification, safe cleanup.
- Change only product-specific implementation: version inputs, build/runtime tooling, native OS and architecture, package format, signing, update-pointer policy, anti-tampering validation and safety tests. The donor project's output artifacts are **not** the target product's inputs.
- Formalize failure injection: stale main, mismatched candidate SHA/status, protected-file changes, missing tag or package, signature/hash mismatch, double releases, PR preactivation failure, Work-Branch moving during cleanup.

## Stage 6 — Qualify and activate CI/CD explicitly

- Prove real hosted Linux and Windows gate totals, timings and exact SHA. Measure queue/setup/build/test and orchestration separately. Re-read the ACTIVE main-branch ruleset (matching branch, deletion and non-fast-forward, bypass actors) and the effective `protected` flag; then validate how required PRs/status checks interact with the actual Candidate promotion and Release merge, including bot permissions and fail-closed checks. Only enable mandatory PRs/status rules when their intended workflows and checks have passed on the exact SHA.
- Only after tests and user authorization enable promotion and production publishing. Keep manual review or fail-closed gates for high-risk policies (signing, updater, repair behavior, destructive migration).
- Record first release separately from baseline migration. No fake source-tag or release ZIP just to make dashboards green.

## Stage 7 — Completion and handover

- Confirm GitHub contains full trusted source and build instructions; verify clean checkout can recover any required product state.
- Keep final acceptance table: PASS, BLOCKED, OPEN with exact evidence links and counts; file paths and hashes; actual main SHA, issues, PRs, workflow runs, version and build artifacts.
- Publish unresolved risks and lessons in GitHub, not only a chat. Do not close the migration Issue until all mandatory gates in its scope have passed.

## Lessons / template update rule

After every genuine problem, add **observed symptom → evidence → root cause or uncertainty → smallest correction → preventive rule/test → whether retrospective claims must be corrected**. Update this template with a generalized gate, not an RHC-specific hack. Do not assert a cause solely because a retry succeeded.

### Reusable CI staging and transport guards

- A new PR which does not yet contain the imported product source is **not** a qualified Candidate or migration; hosted smoke gates should fail closed. To avoid wasting Windows runners and red-but-expected checks, first stage complete reviewed bytes, then open the source-import PR when possible.
- For GitHub Actions, check the live hosted runner's Node runtime warnings and the official action metadata. Prefer pinned full commit SHAs of supported versions, and record the versions/rationale; do not blindly retain another project's old action majors.
- A ZIP/file kit under ChatGPT is not a commit, GitHub Action artifact, or GitHub source-of-truth. Require an actual repository head, complete source manifest, exact file-byte comparison, and hosted tests before migrating the authority claim.
- When source is sensitive and the target GitHub repo is public, the authorization to build locally does **not** imply consent to expose historical logs or forensic data publicly.

### Source-byte and reproducible-build controls (new migration lessons)

- A Git blob may exactly match its imported ZIP bytes while a Windows Git checkout rewrites line endings. For byte-frozen imports, choose a committed `.gitattributes` policy **before** cross-OS hash validation, and compare the exact source manifest on all required OSes. In RHC, `* -text` prevents conversions; a normal software development project may need a more selective policy.
- Go builds inside Git worktrees can embed VCS revision/time/dirty metadata by default. An archive-origin golden executable generally has none. Explicitly evaluate `GOFLAGS=-buildvcs=false` or an equivalent `-buildvcs=false` option and confirm the exact binary hash; do not compensate with weaker semantic hash comparisons.
- A temporary automation that pushes back to its own branch must guard against **the trigger's exact SHA**, not a pre-workflow historical head. Respect GitHub's `GITHUB_TOKEN` event recursion rules and dispatch qualification explicitly when needed.
- Remove temporary write-enabled import workflows from the final reviewed tree. Permanent source-intake workflows should remain read-only, and final SHA qualification must occur **after** any such cleanup.

### First-case lessons (RHC, 2026-10-08)

1. **Unborn repository:** `main` can be designated as default while GET branch returns 404 and refs return 409. Bootstrap initial commit before any SHA-lease workflow.
2. **Migration channel mismatch:** a text-only GitHub mutation connector is not proof of ability to import binary assets, source ZIPs or large nested trees. Separate repository bootstrap from verified source transfer; use a manifest-verified importer and a reviewed PR for source intake.
3. **Cold Go toolchain:** first `build.sh` timed out after reaching i18n guard; subsequent guard and full warm rerun passed with exact 3.0.8 reference hash. Budget toolchain setup and log timeout truthfully.
4. **Archive topology matters:** RHC Source ZIP = 321 files; Portable ZIP = 7 files and 12 empty runtime directories; validate both file and directory contracts.
5. **Public repository:** regex secret scan returning no matches is only an initial signal, not legal/privacy clearance for historical logs/forensic data.
6. **Version-authority mismatch:** RHC's `model.go` app/reference version and Go Windows build cannot be replaced by LBS `bin/version.json` or PowerShell release logic.
7. **Unproven deployment:** initial local deterministic build is strong source evidence but still **not** hosted Windows or real hardware verification. Never promote local-only PASS to release-green status.
8. **README conflict:** migration source can include a canonical root README while GitHub bootstrap already has a different README. Require exact collision detection, explicit disposition and original file byte preservation.
9. **GitHub policy visibility:** a repository may expose zero rulesets yet branch-protection reads may return 403 through integration credentials. Mark required branch protection **unverified** until owner-visible review, rather than assuming permissions from successful writes.
10. **Public history is hard to undo:** enforce a real operator review of historical logs/forensics and license/privacy scope before source import; false-positive-free regex scans are not proof of safe publication.

11. **Hosted success is a per-SHA statement:** source verification and platform builds must pass on the exact final PR head before merge; post-merge documentation may record that source success but must not claim a new release.
12. **Temporary elevated workflow lifetime:** remove one-shot write-enabled source staging workflows *before* qualification of the final mergeable PR tree; the remaining permanent intake workflow should be read-only.
13. **Source packaging after archive upload:** a user may upload a canonical Source ZIP at repository root. If source packaging blindly traverses the entire repo, the next Source ZIP may recursively include its own archived source and private provenance files. Establish explicit packaging inclusion/exclusion and deterministic metadata **before** enabling release automation.

14. **Default branch protected flag vs ruleset detail:** a newly created repository can show an unprotected `main` while its build pipeline is already rigorous. The owner-created RHC Stage-1 ruleset was verified via `rulesets/<id>`: `active`, `~DEFAULT_BRANCH`, `deletion`, `non_fast_forward`, empty bypass, and `branches/main.protected=true`. Required PR and status checks remained deliberately open. Record the full effective rules, not just the banner or a successful UI save.

15. **GitHub workflow YAML must be parsed:** a workflow can fail at configuration time and produce *zero* jobs, not a test failure. Never place colon-space inside an unquoted GitHub expression YAML scalar; quote it and perform a preflight parse. Confirm the workflow name/actual jobs appear before measuring queue/setup times.
16. **Exact request marker discipline:** use a literal end-of-commit-message request trailer and a second exact-line Git checkout verification. Substring searches also match explanatory commit messages and can falsely initiate high-cost or privileged workflows.
17. **Reuse completed exact-SHA work gates:** Work-Path Development Completion should verify existing Linux+Windows exact-SHA job results instead of rebuilding blindly, where event/API permissions and source trust are verified. Fail closed on missing/failed results, changed Work head or stale main.
18. **Package allowlist beats blanket recursion:** baseline source/import kits may include archived sources, old logs and forensics. New release packagers must use approved tracked-file scope, fixed archive metadata, negative exclusion tests and separate Portable empty-directory/payload checks.

19. **Unsigned is a separate scope-limited approval, never a default fallback:** lack of a Windows code-signing certificate is not permission to publish. Product-source SHA, version/tag, per-asset hashes, release notes warning, consent and rollback must all be checked for **each** approved unsigned release. SHA-256 and GitHub provenance are not Authenticode or operating-system publisher reputation.
20. **Testmode means zero GitHub release mutations:** a dry-run must simulate Draft creation, tag assignment, merge, publish and postrelease using immutable fixtures/read-only evidence. Creating a real Draft or temporary tag is an integration action needing separate approval; production-disabled policies alone do not make a write-scoped workflow harmless.
21. **Final merge SHA precedes a real GitHub Release tag:** when the public tag is required to identify the final merged source, retain premerge archives as private CI artifacts, merge once after all prerequisites pass, reverify the final SHA and only then construct the Draft and tag. Model postmerge/prepublication gaps as recoverable blocked states; do not silently equate source merge with public binary activation.
22. **Recovery after immutable publication differs from draft cleanup:** never overwrite a published immutable asset to fix an error; preserve previous working versions and use an authorized corrective next version. Confirm actual repository immutability settings and retained artifacts before enabling publishing.

23. **Exact heartbeat timestamps must be captured, not inferred:** a rolling GitHub Issue comment's `Last heartbeat` is an actual, fresh ISO 8601 UTC edit timestamp including seconds and milliseconds. Obtain current time from a checked clock, update the existing comment in place, and verify GitHub's `updated_at` after write. Never substitute a date-only `YYYY-MM-DD`, the Issue's `created_at`, an unrelated workflow event or the statement that 'GitHub timestamps are authoritative' for a real heartbeat. A few seconds of edit/write latency are expected and should not be misrepresented as an exact GitHub event time. If no verified clock is available, record time as unknown and identify the missing evidence.

24. **Static workflow concurrency can silently replace pending Work evidence:** `cancel-in-progress: false` protects an already running job but a later pending event can cancel an earlier pending event sharing a global concurrency group. In RHC-5 several intermediate Infrastructure runs ended `cancelled` with zero jobs during rapid commits; these are neither PASS nor an application-test failure. Key validation concurrency to an exact SHA/event when independent checkpoint evidence matters, freeze the final Work head, and qualify it through actual completed Linux and Windows jobs.

25. **Connector label APIs may be unavailable even when GitHub labels work:** the GitHub connector rejected label-list requests and offered no repository-label-create action, so RHC used a temporary least-privilege Actions job executing the canonical `gh api` provisioning script. It added six missing labels and validated nine, then its write-enabled workflow was removed without changing the final Git tree. Generalize this fallback in the migration guide, and validate **existing-label drift before any POST** (the first template only checked after creation); late checks can leave partial metadata mutations. Do not claim a second idempotence run without evidence. [Successful run #37757322836](https://github.com/SaschaP1980/RazerHealthCenter/actions/runs/37757322836).

**Maintenance rule:** this template is expected to evolve in small reviewable documentation commits after each migration and each confirmed issue.
