# RHC-186 — bounded connector Work launch and honest stopwatch

Status: **Nonpublishing infrastructure implementation, not a proven ≤45s/≤120s result**. This code is for an operator **already authenticated with the supported GitHub connector**; it requires no separate GitHub App, private PEM, PAT, GITHUB_TOKEN push, or new repository permissions.

## Executable module

\`tools/rhc186_connector_fastpath.mjs\` is a reusable ES module with a strictly injected connector gateway. Its \`githubConnectorGateway(tools)\` adapter consumes the same \`mcp__GitHub__*\` actions already used for ordinary RHC connector Work commits. It does not make HTTP requests, import tokens, access local credentials, start Actions or publish ZIPs. A ChatGPT tool-script operator can copy/inline the module's exported functions into the existing JavaScript tool-execution environment (which does not support dynamic module imports); the repository file alone does **not** install a permanent server-side executor or cause future conversations to automatically execute it. Do not label operator documentation as enforced runtime.

**Operator execution stages:**

1. \`canonicalIssueInit({gateway,subject,body,labels,nonce,apply:false})\` performs read-only plan checks. The deliberate \`apply:true\` route creates **one provisional Issue**, uniquely reconciles the creation, reads its real number/labels, renames to canonical \`[RHC-N]\` and independently fetches it. Returns \`ISSUE_VERIFIED_AWAIT_VISIBLE_MARKER\`. The chat must visibly announce the real \`RHCNCHAT{12HEX}\` marker **after the number is known**. It cannot be silently synthesized or claimed visible by a background executor.
2. \`bootstrapExisting({gateway,number,baseMain,marker,template,allowWrites:false})\` is read-only by default. With \`allowWrites:true\` it reads Issue/main/no-comments/no-Work concurrently, renders the **entire original 13-heading template** with one real UTC creation instant, creates the one comment, checks actual creation timestamp/content, marks independent readback, creates one Work ref at the pinned main, updates **the same** comment and independently verifies its SHA and clocks. Ambiguous writes are GET-reconciled, never blindly repeated.
3. \`commitVersion({gateway,number,commentId,baseMain,branchCreatedAt,day,allowWrites:false,ownerAuthorizedNewVersion:false})\` is a separate action needing an explicit owner-approved **new version**. When both write flags are true it uses a bounded parallel source/Issue/Comment/Main/Work snapshot, the exact next-four-part version in the saved Issue, a second mutable-authority barrier, and **one two-file Git Object tree+commit**. It separately validates exact commit parent, tree SHA, 1-ahead/0-behind compare, two allowed paths and exact source bytes; then one more authority barrier and a **single expected-SHA ref lease**. Ambiguous ref response is independently reconciled without retry.
4. \`observeWorkCi({gateway,sha,pushObservedUtc})\` reads real exact-SHA \`event=push\` Infrastructure and Development Completion created_at timestamps. It returns \`WORK_CI_CREATED_NOT_GREEN\`, **never completed-success** just from creation. Normal RHC Work gates Linux/native Windows/Node24, Dev Completion, Candidate, unsigned Publisher, staged Download integrity, public HTTPS/native RHC102 and RHC158 remain unchanged.
5. Every observed operation records \`event,group,write,startUtc,endUtc,elapsedMs,outcome,source\`, with bounded \`Promise.all\` read groups (≤8). Times from tool execution are **client observations**; ref creation does not expose GitHub server \`created_at\`. Work CI timestamps must come from GitHub Actions separately. Do not sum overlapping jobs or silently exclude owner/agent wait from first-tool→CI.

**Dependency boundary:** \`Issue init → visible marker → original Rolling saved/read back → Work ref → same Rolling updated/read back → version owner approval → 2-file commit → single lease push → native push CI\`. Only independent reads parallelize. A failed or uncertain control write must preserve fail-closed behavior and stop if exact readback is missing. The module never authorizes a product release by its existence.

## Test coverage and readiness

\`python3 -m unittest tests/test_rhc186_connector_fastpath_contracts.py -v\` launches a **real Node ESM import** with 20 mocked positive/adversarial tests: canonical issue init dry/apply, clean/dry bootstrap, missing marker/template/taxonomy, drift, duplicate or lost comments, exact version-only commit, wrong authorization/Issue drift/extra source path, ambiguous or rejected ref lease and genuinely authenticated CI creation vs false/foreign evidence. The existing GitHub Linux/native Windows Work CI discovers it through \`test_rhc_*_contracts.py\`. These tests are pure mock contracts and must **not** be described as a real authenticated connector performance run.

The separately authorized RHC-186 implementation PR **does not** change \`model.go\`, \`CHANGELOG.md\`, Razer runtime/UAC/repair, Actions workflows or downloads, and does not build or republish v3.0.8.22.

## Measurement acceptance from RHC-157

Latest historical real full-release baseline v3.0.8.22:
- First connector tool observed → first real Work CI: **280.634s**, goal **≤120s**.
- Client-observed Work branch creation → first real Work CI: **122.826s**, goal **≤45s**.
- Prebranch subtotal **157.808s**; postbranch **122.826s**, last observed prepush→CI **8.772s** (not isolated server dispatch).
- Suggested mutually exclusive budget **≤75s prebranch + ≤45s postbranch**.

This module's execution can reduce orchestration overhead when invoked, but performance is **NOT VERIFIED by mocked unit tests or by merely merging it**. The connector-only ChatGPT host cannot import repository modules as scripts, so its operator must run equivalent inline tool logic with the already authorized provider. A future separately owner-authorized ordinary version-only Work hotfix must actually use/measure the complete fastpath, with no missing Issue/clock/readback safeguards, and preserve all existing release gates. Run ≥3 independently comparable live samples (prefer ≥5); report individual timings, apparent variance, no p95 overclaim and any time saved/lost, separately for prebranch, postbranch and complete Issue lifecycle. If original targets cannot be met without gate relaxation, record honest NO-GO and revise the design, not test status.
