"""RHC-198: fail-closed exact-Candidate hosted PE reuse; no release writes.

The publisher receives GitHub-authenticated run/jobs metadata, and GitHub
Actions artifact bytes, then proves their complete common source identity.
It never accepts the candidate's JSON flags as substitute for real jobs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

COMMIT = re.compile(r"[0-9a-f]{40}\Z")
HASH = re.compile(r"[0-9a-f]{64}\Z")
VERSION = re.compile(r"[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+\Z")
JOB_NAMES = frozenset((
    "Linux Candidate exact-main and deterministic Go artifacts",
    "Windows native PowerShell 5.1 and Go Candidate safety",
    "Exact-SHA Candidate qualification (nonpublishing)",
))
SCHEMA = "RHC190_CANDIDATE_PE_V1"
RUN_NAME = "RHC Candidate Preflight (nonpublishing)"
RUN_PATH = ".github/workflows/rhc-candidate-preflight.yml"


class ArtifactBlocked(ValueError):
    pass


def need(ok, reason):
    if not ok:
        raise ArtifactBlocked("RHC190_CANDIDATE_PE_BLOCKED: " + reason)


def _sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _candidate_exe(path):
    p = Path(path)
    need(p.is_file() and not p.is_symlink() and p.name == "RazerHealthCenter.exe",
         "unsafe/missing executable artifact")
    with p.open("rb") as stream:
        need(stream.read(2) == b"MZ", "invalid executable PE header")
    return p


def _exact_parameters(source_sha, tree_sha, version, repository):
    need(isinstance(source_sha, str) and bool(COMMIT.fullmatch(source_sha)),
         "bad exact source SHA")
    need(isinstance(tree_sha, str) and bool(COMMIT.fullmatch(tree_sha)),
         "bad tree SHA")
    need(isinstance(version, str) and bool(VERSION.fullmatch(version)),
         "bad four-component version")
    need(isinstance(repository, str) and bool(re.fullmatch(
        r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository)),
        "bad canonical repository")


def emit_evidence(exe, output, *, source_sha, tree_sha, version, repository,
                  run_id, run_attempt):
    """Called only after independent PE and package byte-equivalence gates."""
    _exact_parameters(source_sha, tree_sha, version, repository)
    need(isinstance(run_id, int) and run_id > 0 and
         isinstance(run_attempt, int) and run_attempt > 0, "bad run identity")
    src = _candidate_exe(exe)
    out = Path(output)
    out.mkdir(parents=True, exist_ok=True)
    need(not out.is_symlink(), "unsafe evidence directory")
    dest = out / "RazerHealthCenter.exe"
    need(not dest.exists(), "refusing overwrite of candidate PE evidence")
    shutil.copyfile(src, dest)
    need(_sha(src) == _sha(dest), "copied executable hash mismatch")
    record = dict(schema=SCHEMA, sourceSha=source_sha, treeSha=tree_sha,
                  version=version, repository=repository, runId=run_id,
                  runAttempt=run_attempt, exeSha256=_sha(dest),
                  exeSize=dest.stat().st_size, doublePeVerified=True,
                  zipReproducible=True)
    evidence = out / "candidate-evidence.json"
    need(not evidence.exists(), "refusing overwrite of evidence manifest")
    evidence.write_text(json.dumps(record, sort_keys=True, indent=2) + "\n",
                        encoding="utf-8")
    return record


def verify_evidence(meta, run, jobs, exe, *, source_sha, tree_sha,
                    version, repository):
    """Strict metadata + actual hosted 3-job + executable-bytes verification.

    The caller must authenticate both GETs and artifact against same run via
    GitHub Actions. A successful workflow without all three actual jobs fails.
    """
    _exact_parameters(source_sha, tree_sha, version, repository)
    need(all(isinstance(x, dict) for x in (meta, run, jobs)),
         "missing structured independent evidence")
    need(meta.get("schema") == SCHEMA, "wrong attestation schema")
    for field, expected in (("sourceSha", source_sha), ("treeSha", tree_sha),
                            ("version", version), ("repository", repository)):
        need(meta.get(field) == expected, "candidate artifact " + field + " drift")
    need(meta.get("doublePeVerified") is True and
         meta.get("zipReproducible") is True,
         "missing independently reproducible Candidate builds")
    need(isinstance(meta.get("runId"), int) and meta["runId"] > 0 and
         isinstance(meta.get("runAttempt"), int) and meta["runAttempt"] > 0,
         "missing Candidate run identity")
    need(run.get("id") == meta["runId"] and
         run.get("run_attempt") == meta["runAttempt"],
         "Candidate run attempt differs")
    need(run.get("name") == RUN_NAME and run.get("path") == RUN_PATH,
         "different workflow than canonical Candidate")
    need(run.get("event") in ("push", "workflow_dispatch") and
         run.get("status") == "completed" and run.get("conclusion") == "success",
         "Candidate workflow did not complete successfully")
    need(run.get("head_sha") == source_sha and
         run.get("head_branch") == "candidate/v" + version and
         isinstance(run.get("head_repository"), dict) and
         run["head_repository"].get("full_name") == repository,
         "Candidate exact source/branch/origin mismatch")
    rows = jobs.get("jobs")
    need(isinstance(rows, list) and len(rows) == 3 and
         jobs.get("total_count") == 3, "missing, duplicated or paginated hosted jobs")
    need(set(x.get("name") for x in rows if isinstance(x, dict)) == JOB_NAMES,
         "Candidate Linux/Windows/aggregate job set mismatch")
    need(all(isinstance(x, dict) and isinstance(x.get("id"), int) and x["id"] > 0
             and x.get("status") == "completed" and x.get("conclusion") == "success"
             for x in rows), "hosted Candidate jobs not actually GREEN")
    pe = _candidate_exe(exe)
    need(isinstance(meta.get("exeSha256"), str) and
         bool(HASH.fullmatch(meta["exeSha256"])) and
         meta["exeSha256"] == _sha(pe) and
         type(meta.get("exeSize")) is int and
         meta["exeSize"] == pe.stat().st_size,
         "Candidate executable artifact bytes/size differ")
    return dict(result="PASS", sourceSha=source_sha, exeSha256=meta["exeSha256"],
                candidateRunId=meta["runId"], candidateRunAttempt=meta["runAttempt"],
                candidateHostedJobs=len(rows))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    producer = sub.add_parser("emit", help="record verified real Candidate PE")
    consumer = sub.add_parser("verify", help="validate real hosted Candidate and PE")
    for p in (producer, consumer):
        p.add_argument("--source-sha", required=True)
        p.add_argument("--tree-sha", required=True)
        p.add_argument("--version", required=True)
        p.add_argument("--repository", required=True)
    producer.add_argument("--exe", required=True)
    producer.add_argument("--out", required=True)
    producer.add_argument("--run-id", required=True, type=int)
    producer.add_argument("--run-attempt", required=True, type=int)
    consumer.add_argument("--exe", required=True)
    consumer.add_argument("--evidence", required=True)
    consumer.add_argument("--run", required=True)
    consumer.add_argument("--jobs", required=True)
    args = ap.parse_args(argv)
    try:
        common = dict(source_sha=args.source_sha, tree_sha=args.tree_sha,
                      version=args.version, repository=args.repository)
        if args.cmd == "emit":
            result = emit_evidence(args.exe, args.out,
                                   run_id=args.run_id,
                                   run_attempt=args.run_attempt, **common)
            print("RHC190_CANDIDATE_PE_EMIT=" + json.dumps(result,sort_keys=True))
        else:
            meta = json.loads(Path(args.evidence).read_text(encoding="utf-8"))
            run = json.loads(Path(args.run).read_text(encoding="utf-8"))
            jobs = json.loads(Path(args.jobs).read_text(encoding="utf-8"))
            result = verify_evidence(meta,run,jobs,args.exe,**common)
            print("RHC190_CANDIDATE_PE_VERIFY=" + json.dumps(result,sort_keys=True))
        return 0
    except (ArtifactBlocked, ValueError, KeyError, OSError,
            TypeError, json.JSONDecodeError) as error:
        print("RHC190_CANDIDATE_PE_BLOCKED_NOT_VERIFIED: "+str(error),
              file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
