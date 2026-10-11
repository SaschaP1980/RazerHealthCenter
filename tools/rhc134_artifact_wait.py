"""RHC-134: bounded read-only SAME-RUN artifact lookup, never a release gate by itself.

The action download must still verify actual artifact transport and Windows must
hash the downloaded ZIP/EXE. This poll ONLY avoids starting artifact download
before the independently running Linux upload has finalized.
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

SHA = re.compile(r"[0-9a-f]{40}\Z")
REPO = re.compile(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+\Z")
PREFIX = re.compile(r"(?:RHC_REUSABLE-INTERNAL-STAGE-|RHC134-SMOKE-)\Z")

def select_artifact(payload, artifact_name):
    """Fail closed on ambiguous, mismatched, expired or untrusted artifact metadata."""
    if not isinstance(payload, dict):
        raise ValueError("invalid GitHub artifact result")
    rows = payload.get("artifacts")
    total = payload.get("total_count")
    if type(total) is not int or total < 0 or total > 100 or not isinstance(rows, list) or len(rows) != total:
        raise ValueError("GitHub artifact listing missing, truncated or ambiguous")
    matches = [r for r in rows if isinstance(r, dict) and r.get("name") == artifact_name]
    if len(matches) > 1:
        raise ValueError("duplicate same-name artifacts in authenticated run")
    if not matches:
        return None
    item = matches[0]
    if type(item.get("id")) is not int or item["id"] <= 0:
        raise ValueError("invalid artifact ID")
    if item.get("expired") is not False:
        raise ValueError("expired/ambiguous artifact")
    if type(item.get("size_in_bytes")) is not int or item["size_in_bytes"] <= 0:
        raise ValueError("incomplete or empty artifact")
    if not isinstance(item.get("archive_download_url"), str) or not item["archive_download_url"].startswith("https://api.github.com/"):
        raise ValueError("untrusted artifact transport URL")
    return item["id"]

def fetch_run_artifacts(repository, run_id):
    proc = subprocess.run(
        ["gh", "api", "repos/%s/actions/runs/%s/artifacts?per_page=100" % (repository, run_id)],
        capture_output=True, text=True, timeout=20, check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError("authenticated same-run GitHub artifact GET failed")
    return json.loads(proc.stdout)

def wait_for_artifact(*, repository, run_id, sha, prefix, max_attempts=90,
                      interval=2.0, fetcher=fetch_run_artifacts, sleeper=time.sleep):
    if not REPO.fullmatch(repository) or not str(run_id).isdigit() or int(run_id) <= 0:
        raise ValueError("repository or exact workflow-run ID invalid")
    if not SHA.fullmatch(sha) or not PREFIX.fullmatch(prefix):
        raise ValueError("expected source SHA or allowlisted artifact prefix invalid")
    if type(max_attempts) is not int or not 1 <= max_attempts <= 120:
        raise ValueError("invalid bounded artifact poll attempts")
    if not isinstance(interval, (int, float)) or not 0.1 <= interval <= 5:
        raise ValueError("invalid bounded artifact poll interval")
    expected = prefix + sha
    for index in range(max_attempts):
        found = select_artifact(fetcher(repository, run_id), expected)
        if found is not None:
            print("RHC134_SAME_RUN_ARTIFACT_READY=PASS run=%s artifact_id=%s sha=%s after_polls=%s" %
                  (run_id, found, sha, index + 1), flush=True)
            return found
        if index + 1 < max_attempts:
            sleeper(interval)
    raise TimeoutError("bounded SAME-RUN Linux artifact wait timed out; not a PASS")

def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--prefix", default="RHC_REUSABLE-INTERNAL-STAGE-")
    p.add_argument("--max-attempts", type=int, default=90)
    p.add_argument("--interval", type=float, default=2.0)
    a = p.parse_args(argv)
    if not os.environ.get("GH_TOKEN"):
        raise ValueError("GH_TOKEN read-only artifact access is missing")
    wait_for_artifact(repository=os.environ.get("GITHUB_REPOSITORY", ""),
                      run_id=os.environ.get("GITHUB_RUN_ID", ""),
                      sha=os.environ.get("GITHUB_SHA", ""),
                      prefix=a.prefix, max_attempts=a.max_attempts,
                      interval=a.interval)

if __name__ == "__main__":
    try:
        main()
    except (ValueError, RuntimeError, TimeoutError, subprocess.TimeoutExpired,
            json.JSONDecodeError) as exc:
        print("RHC134_ARTIFACT_WAIT_BLOCKED=" + str(exc), file=sys.stderr)
        raise SystemExit(2)
