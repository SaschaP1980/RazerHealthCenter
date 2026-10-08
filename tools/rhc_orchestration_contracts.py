#!/usr/bin/env python3
"""Pure fail-closed RHC CI/CD state gates; cannot publish or mutate GitHub."""
import json
import re
from pathlib import PurePosixPath

from rhc_release_contracts import SEMVER, assert_future_version, require

REQUIRED_CANDIDATE_CONTEXTS = ('rhc/preflight/linux', 'rhc/preflight/windows', 'rhc/preflight/candidate')
REQUIRED_RELEASE_CONTEXTS = ('rhc/release/source', 'rhc/release/portable', 'rhc/release/verification')


def safe_ref(ref, prefix):
    require(isinstance(ref, str) and re.fullmatch(prefix + r'/v(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)\.(?:0|[1-9][0-9]*)', ref),
            'invalid branch name or version')
    return ref.split('/v', 1)[1]


def validate_candidate(*, previous, version, changed_paths, release_profile, current_main_parent):
    assert_future_version(version, previous)
    require(release_profile in ('version-only', 'patch'), 'unknown release profile')
    require(current_main_parent, 'candidate must be based on exact current main')
    changed = set(changed_paths)
    require(changed and len(changed)==len(changed_paths), 'empty/duplicate candidate diff')
    require({'model.go', 'CHANGELOG.md'}.issubset(changed), 'model.go and CHANGELOG.md are required')
    require(not any('..' in PurePosixPath(x).parts or x.startswith('/') or '\\' in x for x in changed),
            'unsafe candidate paths')
    require(not any(x.lower().endswith(('.exe','.zip','.key','.pem','.pfx')) for x in changed),
            'binary/secret artifact changes prohibited')
    require(not any(x in ('docs/migration/RHC-v3.0.8-source-file-manifest.json',
                          '.github/workflows/rhc-source-intake.yml') for x in changed),
            'frozen migration source identity cannot be modified in Candidate')
    if release_profile == 'version-only':
        require(changed == {'model.go','CHANGELOG.md'},
                'version-only must change model.go and CHANGELOG.md exclusively')
    else:
        require(len(changed) < 300, 'candidate diff abnormally large')
    return {'result':'PASS','version':version,'profile':release_profile,'paths':sorted(changed)}


def exact_statuses(payload, required):
    require(isinstance(payload, dict) and isinstance(payload.get('statuses'), list),
            'status endpoint payload missing')
    latest = {}
    for row in payload['statuses']:
        if not isinstance(row, dict):
            continue
        name, state = row.get('context'), row.get('state')
        if name in required and name not in latest:
            latest[name] = state  # GitHub combined-status endpoint is latest first
    require(set(latest)==set(required), 'missing required exact-SHA statuses')
    require(all(x == 'success' for x in latest.values()), 'status failure/pending/unknown')
    return latest


def validate_work_completion(evidence, *, work_sha, base_main_sha):
    require(evidence.get('result')=='PASS', 'work completion did not pass')
    require(evidence.get('workSha')==work_sha, 'stale work completion SHA')
    require(evidence.get('baseMainSha')==base_main_sha, 'stale main/ancestry evidence')
    require(evidence.get('linux')=='success' and evidence.get('windows')=='success',
            'both hosted OS gates required')
    return True


def publication_policy(policy):
    require(isinstance(policy, dict), 'missing release policy')
    require(policy.get('productionEnabled') is True, 'production releases disabled by policy')
    require(policy.get('distribution') in ('github-release','repository-pointer'),
            'distribution/update-pointer contract not selected')
    require(policy.get('signingDecision') in ('unsigned-approved', 'signed-verified'),
            'signed/unsigned Windows trust decision missing')
    require(policy.get('rollbackVerified') is True, 'rollback contract not verified')
    return True


def validate_preactivation(*, public_version, staged_version, expected_previous,
                           candidate_sha, release_sha, candidate_statuses, release_statuses,
                           policy):
    publication_policy(policy)
    require(public_version == expected_previous, 'public version changed before activation')
    assert_future_version(staged_version, expected_previous)
    require(isinstance(candidate_sha, str) and len(candidate_sha)==40 and
            isinstance(release_sha, str) and len(release_sha)==40,
            'exact commit SHA missing')
    exact_statuses(candidate_statuses, REQUIRED_CANDIDATE_CONTEXTS)
    exact_statuses(release_statuses, REQUIRED_RELEASE_CONTEXTS)
    return {'result':'PASS','previous':expected_previous,'version':staged_version,
            'candidateSha':candidate_sha,'releaseSha':release_sha}
