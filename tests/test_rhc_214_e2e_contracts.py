"""RHC-214: real Node ESM gateway tests and Python evidence bounds contracts."""
import json
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"tools"))
import rhc190_e2e_timeline as t
from test_rhc_212_e2e_timeline_contracts import fixture,SHA

NODE=r'''
import assert from "node:assert/strict";
import {beginFirstTool} from "./tools/rhc190_e2e_client_observer.mjs";
import {startInstrumentedFastPath} from "./tools/rhc214_instrumented_fastpath.mjs";
const SHA="a".repeat(40),BAD="b".repeat(40);
let passed=0;async function check(name,fn){try{await fn();passed++}catch(e){console.error("FAIL "+name,e);process.exitCode=1}}
async function blocked(p,fragment){await assert.rejects(p,new RegExp(fragment))}
function mock({wrongRef=false,badCanonical=false,lostComment=false,missingComment=false,clockGap=false}={}){
 let ms=Date.parse("2026-10-16T05:10:00Z"),issue,ref,comments=[],created=0,refs=0;
 const c={utc:()=>new Date(ms+=100).toISOString(),mono:()=>ms};
 const tools={
  mcp__GitHub__create_issue:async({title,body,labels})=>{
   created++;ms+=220;issue={number:901,title,body,state:"open",
    created_at:clockGap?"2026-10-16T06:10:00Z":new Date(Math.floor(ms/1000)*1000).toISOString()};
   return {result:{url:"https://github.com/SaschaP1980/RazerHealthCenter/issues/901",
     issue:{title,created_at:issue.created_at}}};
  },
  mcp__GitHub__create_branch:async({branch_name,sha})=>{
   refs++;ms+=110;ref={name:branch_name,sha:wrongRef?BAD:sha};return {result:{branch:branch_name}};
  },
  mcp__GitHub__add_comment_to_issue:async({comment})=>{
   ms+=80;if(!missingComment)comments.push({id:73,body:comment});
   if(lostComment)throw Error("lost response");
   return {result:{id:73}};
  },
  mcp__GitHub__fetch:async({url})=>{
   ms+=45;
   let d=url.includes("/git/ref/")?{object:{sha:ref?.sha}}:
    url.includes("/comments?")?comments:url.includes("/issues/901")?
      {...issue,...(badCanonical?{created_at:"2000-01-01T00:00:00Z"}:{})}:null;
   if(d===null)throw Error("unknown mock read path");
   return {result:{content:JSON.stringify(d)}};
  }
 };
 const args={title:"Initializing RHC Issue: GitHub CI test [init-abcd1234]",
   body:"Development path: dev-path: fast — owner approved",labels:["enhancement","priority: high","dev-path: fast","dev-ops"]};
 return {c,tools,args,comments,counts:()=>[created,refs],
   canonical:()=>{issue.title="[RHC-901] GitHub CI test"}};
}
async function prepared(opts={}){
 const g=mock(opts),p=startInstrumentedFastPath(g.tools,g.c);
 const i=await p.createProvisionalIssue(g.args);assert.equal(i.number,901);
 g.canonical();await p.verifyCanonicalIssue(901);
 return {g,p};
}
await check("first tool can precede Issue identity",async()=>{
 const tracker=beginFirstTool({utc:()=>new Date().toISOString(),mono:()=>performance.now()});
 assert.equal(typeof tracker.observeIssueCreate,"function");
});
await check("exact connector Issue, canonical, ref, comment and calibrated evidence",async()=>{
 const {g,p}=await prepared();
 await p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA);
 const out=await p.persistObservation(SHA);
 assert.equal(out.commentId,73);assert.equal(out.evidence.issue,901);
 assert.equal(out.evidence.schema,"RHC190_CLIENT_TOOL_OBSERVATION_V2");
 assert.ok(out.evidence.server_minus_client_offset_min_ms<=out.evidence.server_minus_client_offset_max_ms);
 assert.equal(out.evidence.first_tool_provenance,"OPERATOR_ENTRY_NOT_HOST_ATTESTED");
 assert.deepEqual(g.counts(),[1,1]);assert.equal(g.comments.length,1);
});
await check("real version-only Fast-Path Issue without dev-ops label accepted",async()=>{
 const g=mock(),p=startInstrumentedFastPath(g.tools,g.c);
 const input={title:"Initializing RHC Issue: Version-only Hotfix 3.0.8.28 [init-xyz]",
   body:"Development path: dev-path: fast — owner authorized version-only",
   labels:["enhancement","priority: high","dev-path: fast"]};
 const result=await p.createProvisionalIssue(input);
 assert.equal(result.number,901);assert.deepEqual(g.counts(),[1,0]);
});
await check("no Candidate ref before canonical",async()=>{
 const g=mock(),p=startInstrumentedFastPath(g.tools,g.c);await p.createProvisionalIssue(g.args);
 await blocked(p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA),"Candidate authority");
 assert.deepEqual(g.counts(),[1,0]);
});
await check("real readback mismatch cannot bind Issue",async()=>{
 const g=mock({badCanonical:true}),p=startInstrumentedFastPath(g.tools,g.c);
 await blocked(p.createProvisionalIssue(g.args),"readback mismatch");assert.deepEqual(g.counts(),[1,0]);
});
await check("foreign Candidate SHA blocks observation",async()=>{
 const {g,p}=await prepared({wrongRef:true});
 await blocked(p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA),"SHA/readback");
 await blocked(p.persistObservation(SHA),"verified exact candidate");assert.deepEqual(g.counts(),[1,1]);
});
await check("main or Work branch name forbidden",async()=>{
 const {g,p}=await prepared();
 await blocked(p.createVerifiedCandidateRef("main",SHA),"Candidate authority");
 await blocked(p.createVerifiedCandidateRef("work/RHC-901",SHA),"Candidate authority");
 assert.deepEqual(g.counts(),[1,0]);
});
await check("uncertain comment reply independently reconciled",async()=>{
 const {g,p}=await prepared({lostComment:true});
 await p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA);
 const c=await p.persistObservation(SHA);assert.equal(c.commentId,73);assert.equal(g.comments.length,1);
});
await check("failed comment readback does not retry",async()=>{
 const {g,p}=await prepared({lostComment:true,missingComment:true});
 await p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA);
 await blocked(p.persistObservation(SHA),"observation required");assert.equal(g.comments.length,0);
});
await check("Issue create clock absurdly out of sync rejected",async()=>{
 const {p}=await prepared({clockGap:true});
 await p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA);
 await blocked(p.persistObservation(SHA),"clock offset");
});
await check("one Issue, one ref, one persisted comment",async()=>{
 const {g,p}=await prepared();await blocked(p.createProvisionalIssue(g.args),"provisional Issue");
 await p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA);
 await blocked(p.createVerifiedCandidateRef("candidate/v3.0.8.28",SHA),"Candidate authority");
 await p.persistObservation(SHA);
 await blocked(p.persistObservation(SHA),"finished observation");
 assert.deepEqual(g.counts(),[1,1]);assert.equal(g.comments.length,1);
});
console.log("RHC214_NODE_CONTRACT_TESTS="+passed);
'''
def client():
    return dict(schema=t.CLIENT_V2,
        capture_method="CLIENT_FIRST_ENTRY_ISSUE_CREATE_BRACKET_REF_WRITE_READBACK",
        issue=212,candidate_sha=SHA,ref_name="candidate/v3.0.8.28",
        first_tool_utc="2026-10-16T03:59:58.000Z",
        issue_create_start_utc="2026-10-16T03:59:59.200Z",
        issue_create_ack_utc="2026-10-16T04:00:00.800Z",
        issue_server_created_utc="2026-10-16T04:00:00Z",
        ref_write_start_utc="2026-10-16T04:00:05.000Z",
        ref_write_ack_utc="2026-10-16T04:00:07.000Z",
        ref_write_duration_ms=2000,server_minus_client_offset_min_ms=-800,
        server_minus_client_offset_max_ms=1800,
        first_tool_provenance="OPERATOR_ENTRY_NOT_HOST_ATTESTED",
        ref_provenance="CONNECTOR_WRITE_AND_INDEPENDENT_REF_READBACK")
class Contracts(unittest.TestCase):
    def test_real_node_esm_connector_mock_suite(self):
        node=shutil.which("node")
        if not node:self.skipTest("Node unavailable; must pass on hosted Node24")
        out=subprocess.run([node,"--input-type=module","-e",NODE],cwd=ROOT,
                           capture_output=True,text=True,timeout=45)
        self.assertEqual(out.returncode,0,out.stdout+"\n"+out.stderr)
        self.assertIn("RHC214_NODE_CONTRACT_TESTS=11",out.stdout)
    def test_exact_interval_bounds_conditional_not_host_attested(self):
        d=fixture();d["client_observation"]=client();res=t.build_report(d)
        c=res["client_observation"]
        self.assertEqual(c["server_minus_client_offset_bounds_ms"],[-800,1800])
        self.assertEqual(c["first_tool_to_ci_bounds_seconds"],[15.2,17.8])
        self.assertEqual(c["ref_to_ci_bounds_seconds"],[6.2,10.8])
        self.assertEqual(c["kpi_ref_to_ci_45s"],"CONDITIONAL_BOUND_WITHIN_TARGET_NOT_HOST_ATTESTED")
        self.assertEqual(res["original_first_tool_to_ci_kpi"],"CONDITIONAL_BOUNDS_NOT_HOST_ATTESTED")
        self.assertIsNone(res["actual_ref_created_utc"])
    def test_wrong_offset_sha_issue_server_timestamp_and_secret_blocked(self):
        for patch in ({"server_minus_client_offset_min_ms":-799},
                      {"candidate_sha":"b"*40},{"issue":999},
                      {"issue_server_created_utc":"2026-10-16T04:00:01Z"},
                      {"GH_TOKEN":"secret"},
                      {"first_tool_provenance":"GITHUB_HOST_ATTESTED"},
                      {"ref_write_duration_ms":8000},
                      {"ref_name":"work/RHC-212"}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                d=fixture();d["client_observation"]={**client(),**patch};t.build_report(d)
    def test_wrong_event_order_and_future_ref_do_not_claim_speed(self):
        for patch in ({"issue_create_start_utc":"2026-10-16T03:59:57Z"},
                      {"ref_write_start_utc":"2026-10-16T03:59:58Z"},
                      {"ref_write_ack_utc":"2026-10-16T04:01:00Z"}):
            with self.subTest(patch=patch),self.assertRaises(ValueError):
                d=fixture();d["client_observation"]={**client(),**patch};t.build_report(d)
    def test_read_only_issue_comment_discovery_is_unique_and_exact(self):
        body=t.CLIENT_V2_COMMENT+json.dumps(client(),separators=(",",":"))
        self.assertEqual(t.issue_observer_from_comments([{"body":"other"},{"body":body}],212,SHA),client())
        for rows in ([],[{"body":body},{"body":body}],
                     [{"body":body+"\nextra"}],
                     [{"body":t.CLIENT_V2_COMMENT+"{}"}]):
            with self.subTest(rows=rows),self.assertRaises(ValueError):
                t.issue_observer_from_comments(rows,212,SHA)
    def test_old_historical_v1_absent_evidence_remains_unchanged(self):
        d=fixture();r=t.build_report(d)
        self.assertIsNone(r["client_observation"]["first_tool_utc"])
        self.assertEqual(r["original_first_tool_to_ci_kpi"],"NOT_VERIFIED")
        self.assertIsNone(r["p95_seconds"])
    def test_adapter_is_not_a_product_publisher(self):
        gateway=(ROOT/"tools/rhc214_instrumented_fastpath.mjs").read_text()
        self.assertNotIn("publishRelease",gateway)
        self.assertNotIn("gh workflow run",gateway)
        self.assertIn("mcp__GitHub__fetch",gateway)
if __name__=="__main__":unittest.main()
