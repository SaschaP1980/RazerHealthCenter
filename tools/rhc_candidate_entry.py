#!/usr/bin/env python3
"""Read-only atomic Candidate Entry; no publish/repair/remote mutation."""
import argparse,json,re,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from rhc_release_contracts import SEMVER,require,version_from_model
from rhc_orchestration_contracts import safe_ref,validate_candidate

def git(root,*args):
    r=subprocess.run(['git','-C',str(root),*args],capture_output=True,text=True)
    require(r.returncode==0,'git command failed: '+' '.join(args)+' '+r.stderr[:200])
    return r.stdout.strip()

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--candidate-ref',required=True)
    args=p.parse_args()
    root=args.root.resolve()
    version=version_from_model(root)
    require(safe_ref(args.candidate_ref,'candidate')==version,'branch/version mismatch')
    require(not git(root,'status','--porcelain'),'dirty checkout')
    main_sha=git(root,'rev-parse','refs/remotes/origin/main')
    head=git(root,'rev-parse','HEAD')
    require(git(root,'rev-list','--parents','-n1','HEAD').split()==[head,main_sha],
            'candidate is not one atomic commit based on current main')
    prior=git(root,'show','origin/main:model.go')
    versions=re.findall(r'^\s*appVersion\s*=\s*"([^"]+)"\s*$',prior,re.M)
    require(len(versions)==1 and SEMVER.fullmatch(versions[0]),'invalid main version')
    message=git(root,'log','-1','--pretty=%B')
    profiles=re.findall(r'^Release-Profile: (version-only|patch|hotfix)
    issues=re.findall(r'^RHC-Issue: ([1-9][0-9]*)$',message,re.M)
    require(len(profiles)==1 and len(issues)==1,'missing unique RHC Issue/profile trailer')
    result=validate_candidate(previous=versions[0],version=version,
        changed_paths=git(root,'diff','--name-only','origin/main','HEAD').splitlines(),
        release_profile=profiles[0],current_main_parent=True)
    result.update(candidateSha=head,baseMainSha=main_sha,issue='RHC-'+issues[0])
    print('RHC_CANDIDATE_ENTRY_SUMMARY='+json.dumps(result,sort_keys=True))

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('RHC_CANDIDATE_ENTRY=BLOCKED: '+str(e),file=sys.stderr)
        sys.exit(1)
,message,re.M)
    issues=re.findall(r'^RHC-Issue: ([1-9][0-9]*)$',message,re.M)
    require(len(profiles)==1 and len(issues)==1,'missing unique RHC Issue/profile trailer')
    result=validate_candidate(previous=versions[0],version=version,
        changed_paths=git(root,'diff','--name-only','origin/main','HEAD').splitlines(),
        release_profile=profiles[0],current_main_parent=True)
    result.update(candidateSha=head,baseMainSha=main_sha,issue='RHC-'+issues[0])
    print('RHC_CANDIDATE_ENTRY_SUMMARY='+json.dumps(result,sort_keys=True))

if __name__=='__main__':
    try:main()
    except Exception as e:
        print('RHC_CANDIDATE_ENTRY=BLOCKED: '+str(e),file=sys.stderr)
        sys.exit(1)
