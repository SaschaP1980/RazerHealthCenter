"""RHC-186: execute real Node ESM connector fast-path adversarial contract tests.
Discoverable through the existing Linux/native Windows unittest pattern.
No network, GitHub mutations, new versions or additional credentials.
"""
import pathlib
import shutil
import subprocess
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
NODE_TEST = r'''
import assert from "node:assert/strict";
import fs from "node:fs";
import {
  canonicalIssueInit,bootstrapExisting,commitVersion,composeBootstrap,
  versionTransform,approvedIssue,observeWorkCi
} from "./tools/rhc186_connector_fastpath.mjs";

const S="a".repeat(40), T="b".repeat(40), C="c".repeat(40), D="d".repeat(40);
const marker="RHC900CHAT1234ABCDEF89";
const template=fs.readFileSync("docs/templates/WORK_PATH_ROLLING_COMMENT.md","utf8");
const issueBody="Development path: dev-path: work-branch — qualified GitHub CI version-only hotfix\nOwner-approved version-only target: 3.0.8.23\n";
let tick=Date.parse("2026-10-15T11:00:00.000Z");
const now=()=>tick+=100;
class Fake {
 constructor() {
  this.main=S;this.work=null;this.comment=null;this.issue={
   number:900,title:"[RHC-900] GitHub CI version-only hotfix",
   body:issueBody,state:"open",labels:["enhancement","priority: high",
     "dev-path: work-branch","dev-ops"].map(name=>({name})),
   created_at:"2026-10-15T10:59:00Z"};
  this.comments=[];this.writes=[];this.refMoves=0;
  this.model='const (\n    appVersion = "3.0.8.22"\n    referenceVersion = "3.0.8.22"\n)\n';
  this.log='# Changelog\n\n## 3.0.8.22 — 2026-10-15\n\n- Previous.\n';
  this.newFiles={};this.message=null;this.loseComment=false;this.loseMove=false;
  this.badDiff=false;this.issueMutateOnRead=0;this.issueReads=0;this.rejectMove=false;
  this.runs=[];
 }
 async getIssue(n){this.issueReads++;if(this.issueMutateOnRead&&this.issueReads>=this.issueMutateOnRead)this.issue.body+="foreign\n";return structuredClone(this.issue);}
 async getMain(){return this.main;}
 async getWork(){return this.work;}
 async listComments(){return this.comments.map(x=>structuredClone(x));}
 async getComment(id){return structuredClone(this.comments.find(x=>x.id===id));}
 async createComment(n,body){
  this.writes.push("comment-create");
  const c={id:500,body,created_at:new Date(now()).toISOString(),updated_at:new Date(now()).toISOString()};
  this.comments=[c];this.comment=c;
  if(this.loseComment)throw new Error("ambiguous comment response");
  return c;
 }
 async updateComment(id,body){
  this.writes.push("comment-update");
  this.comment.body=body;this.comment.updated_at=new Date(now()).toISOString();
 }
 async createWork(n,sha){this.writes.push("branch");this.work=sha;return {sha};}
 async getFile(path,ref){if(ref===D)return path==="model.go"?this.newFiles.model:this.newFiles.change;return path==="model.go"?this.model:this.log;}
 async getCommit(sha){return sha===S?{tree:{sha:C}}:{tree:{sha:T},parents:[{sha:S}],message:this.message};}
 async makeTree(tree,elems){this.writes.push("tree");assert.equal(tree,C);this.newFiles.model=elems.find(x=>x.path==="model.go").content;this.newFiles.change=elems.find(x=>x.path==="CHANGELOG.md").content;return {sha:T};}
 async makeCommit(tree,parent,message){this.writes.push("commit");assert.equal(tree,T);assert.equal(parent,S);this.message=message;return {sha:D};}
 async compare(){return {ahead_by:1,behind_by:0,total_commits:1,files:this.badDiff?
   [{filename:"other.go",status:"modified"}]:
   [{filename:"CHANGELOG.md",status:"modified"},{filename:"model.go",status:"modified"}]};}
 async moveWork(n,sha,expected){this.writes.push("ref");this.refMoves++;
  assert.equal(expected,S);if(this.rejectMove)throw Error("lease rejected");
  this.work=sha;if(this.loseMove)throw Error("ambiguous write response");return {success:true};}
 async listRuns(){return this.runs;}
 async createIssue(title,body,labels){this.writes.push("issue-create");this.issue={...this.issue,title,body,labels:labels.map(name=>({name}))};return {number:900};}
 async findIssues(title,body){return this.issue.title===title&&this.issue.body===body?[structuredClone(this.issue)]:[];}
 async renameIssue(n,title){this.writes.push("issue-rename");this.issue.title=title;}
}
const failures=[];
let passed=0;
async function test(name,cb) {try {await cb();passed++;}catch(e){failures.push(name+": "+e.stack);}}
async function blocked(fn){await assert.rejects(fn,/RHC186_BLOCKED/);}
async function initial(){
  const g=new Fake();
  const r=await bootstrapExisting({gateway:g,number:900,baseMain:S,marker,template,allowWrites:true,now});
  assert.equal(r.status,"BOOTSTRAP_VERIFIED");
  assert.equal(g.work,S);assert.equal(g.comments.length,1);
  assert.equal([...g.comment.body.matchAll(/^### /gm)].length,13);
  assert.equal(g.writes.filter(x=>x==="branch").length,1);
  assert.ok(g.writes.indexOf("comment-create")<g.writes.indexOf("branch"));
  return {g,r};
}
await test("canonical Issue init read-only",async()=>{
 const g=new Fake();const r=await canonicalIssueInit({gateway:g,subject:"GitHub CI version-only hotfix",body:issueBody,
  labels:["enhancement","priority: high","dev-path: work-branch","dev-ops"],nonce:"1234567890ab",now});
 assert.equal(r.status,"PLAN_ONLY");assert.deepEqual(g.writes,[]);
});
await test("canonical Issue init one create/rename",async()=>{
 const g=new Fake();const r=await canonicalIssueInit({gateway:g,subject:"GitHub CI version-only hotfix",body:issueBody,
  labels:["enhancement","priority: high","dev-path: work-branch","dev-ops"],nonce:"1234567890ab",apply:true,now});
 assert.equal(r.status,"ISSUE_VERIFIED_AWAIT_VISIBLE_MARKER");assert.equal(r.number,900);
 assert.deepEqual(g.writes,["issue-create","issue-rename"]);
});
await test("bootstrap read-only no writes",async()=>{
 const g=new Fake();const r=await bootstrapExisting({gateway:g,number:900,baseMain:S,marker,template,now});
 assert.equal(r.status,"PLAN_ONLY");assert.deepEqual(g.writes,[]);
});
await test("bootstrap full 13 headings and immutable saved creation",async()=>{
 const {g,r}=await initial();assert.equal(r.commentId,500);
 assert.equal(g.comments[0].body.includes("RHC900CHAT1234ABCDEF89"),true);
 assert.equal(g.writes.filter(x=>x==="comment-update").length,2);
 assert.ok(r.timings.every(x=>x.elapsedMs>=0&&x.source==="CLIENT_OBSERVED_NOT_GITHUB_SERVER"));
});
await test("bootstrap wrong marker fails before writes",async()=>{
 const g=new Fake();await blocked(()=>bootstrapExisting({gateway:g,number:900,baseMain:S,marker:"RHC901CHAT1234ABCDEF89",template,allowWrites:true,now}));
 assert.equal(g.writes.length,0);
});
await test("bootstrap stale main fails closed",async()=>{
 const g=new Fake();g.main="e".repeat(40);await blocked(()=>bootstrapExisting({gateway:g,number:900,baseMain:S,marker,template,allowWrites:true,now}));
 assert.deepEqual(g.writes,[]);
});
await test("bootstrap existing foreign comment refuses duplicate write",async()=>{
 const g=new Fake();g.comments=[{id:999,body:"foreign"}];
 await blocked(()=>bootstrapExisting({gateway:g,number:900,baseMain:S,marker,template,allowWrites:true,now}));
 assert.deepEqual(g.writes,[]);
});
await test("bootstrap lost create reply reconciled without duplicate",async()=>{
 const g=new Fake();g.loseComment=true;
 const r=await bootstrapExisting({gateway:g,number:900,baseMain:S,marker,template,allowWrites:true,now});
 assert.equal(r.status,"BOOTSTRAP_VERIFIED");assert.equal(g.writes.filter(x=>x==="comment-create").length,1);
});
await test("missing 13 heading blocked",async()=>{
 const g=new Fake();await blocked(()=>bootstrapExisting({gateway:g,number:900,baseMain:S,marker,
  template:template.replace("### Evidence audit","### wrong"),allowWrites:true,now}));
 assert.equal(g.writes.length,0);
});
await test("issue label/title mismatch blocked",async()=>{
 const g=new Fake();g.issue.title="[RHC-900] unrelated release";await blocked(()=>bootstrapExisting({
  gateway:g,number:900,baseMain:S,marker,template,allowWrites:true,now}));
 assert.equal(g.writes.length,0);
});
await test("version transform never touches prior changelog tail",async()=>{
 const g=new Fake();const t=versionTransform(g.issue,g.model,g.log,"2026-10-15");
 assert.equal(t.goal,"3.0.8.23");assert.equal(t.model.match(/3\.0\.8\.23/g).length,2);
 assert.equal(t.changelog.split("## 3.0.8.22").length,2);
});
await test("version path plan-only no writes",async()=>{
 const {g,r}=await initial();g.writes=[];
 const v=await commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,day:"2026-10-15",now});
 assert.equal(v.status,"PLAN_ONLY");assert.deepEqual(g.writes,[]);
});
await test("version exact 2 paths one commit/ref",async()=>{
 const {g,r}=await initial();g.writes=[];
 const v=await commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,
  day:"2026-10-15",ownerAuthorizedNewVersion:true,allowWrites:true,now});
 assert.equal(v.status,"WORK_PUSH_VERIFIED");assert.equal(v.workSha,D);assert.equal(g.refMoves,1);
 assert.deepEqual(g.writes,["tree","commit","ref"]);assert.equal(v.actualWorkCiCreatedAt,"NOT_OBSERVED");
});
await test("version no owner authorization no Git-object write",async()=>{
 const {g,r}=await initial();g.writes=[];
 await blocked(()=>commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,
  day:"2026-10-15",allowWrites:true,now}));assert.deepEqual(g.writes,[]);
});
await test("version Issue scope altered before commit stops",async()=>{
 const {g,r}=await initial();g.issueReads=0;g.issueMutateOnRead=2;g.writes=[];
 await blocked(()=>commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,
  day:"2026-10-15",ownerAuthorizedNewVersion:true,allowWrites:true,now}));
 assert.deepEqual(g.writes,[]);
});
await test("version extra source path blocks ref",async()=>{
 const {g,r}=await initial();g.badDiff=true;g.writes=[];
 await blocked(()=>commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,
  day:"2026-10-15",ownerAuthorizedNewVersion:true,allowWrites:true,now}));
 assert.equal(g.refMoves,0);
});
await test("version ambiguous ref reply reconciles only once",async()=>{
 const {g,r}=await initial();g.loseMove=true;g.writes=[];
 const v=await commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,
  day:"2026-10-15",ownerAuthorizedNewVersion:true,allowWrites:true,now});
 assert.equal(v.writeReplyUncertain,true);assert.equal(g.refMoves,1);
});
await test("version declined ref lease blocks no retry",async()=>{
 const {g,r}=await initial();g.rejectMove=true;g.writes=[];
 await blocked(()=>commitVersion({gateway:g,number:900,commentId:500,baseMain:S,branchCreatedAt:r.branchCreatedAt,
  day:"2026-10-15",ownerAuthorizedNewVersion:true,allowWrites:true,now}));
 assert.equal(g.refMoves,1);
});
await test("work CI exact run authenticity and not green on created",async()=>{
 const g=new Fake();g.runs=[
  {id:22,name:"RHC Infrastructure Qualification (nonpublishing)",head_sha:D,event:"push",created_at:"2026-10-15T11:00:03Z",status:"queued",conclusion:null},
  {id:23,name:"RHC Development Completion (exact SHA gate)",head_sha:D,event:"push",created_at:"2026-10-15T11:00:03Z",status:"in_progress",conclusion:null}
 ];
 const v=await observeWorkCi({gateway:g,sha:D,pushObservedUtc:"2026-10-15T11:00:02Z",now});
 assert.equal(v.status,"WORK_CI_CREATED_NOT_GREEN");assert.equal(v.runs.length,2);
});
await test("work CI foreign and duplicates rejected",async()=>{
 const g=new Fake();g.runs=[
  {id:22,name:"RHC Infrastructure Qualification (nonpublishing)",head_sha:D,event:"push",created_at:"2026-10-15T11:00:03Z",status:"queued"},
  {id:23,name:"RHC Development Completion (exact SHA gate)",head_sha:"f".repeat(40),event:"push",created_at:"2026-10-15T11:00:03Z",status:"queued"}
 ];
 await blocked(()=>observeWorkCi({gateway:g,sha:D,pushObservedUtc:"2026-10-15T11:00:02Z",now}));
});
if(failures.length){console.error(failures.join("\n"));process.exit(1);}
console.log("RHC186_CONNECTOR_FASTPATH=PASS tests="+passed);
'''


class RHC186ConnectorFastpathContracts(unittest.TestCase):
    def test_genuine_node_module_guarded_mock_suite(self):
        node = shutil.which("node") or shutil.which("node.exe")
        self.assertIsNotNone(node, "Node required for native connector ESM contract tests")
        run = subprocess.run(
            [node, "--input-type=module", "-e", NODE_TEST],
            cwd=str(ROOT), capture_output=True, text=True, timeout=55,
            check=False,
        )
        self.assertEqual(run.returncode, 0, (run.stdout + "\n" + run.stderr)[-11000:])
        self.assertIn("RHC186_CONNECTOR_FASTPATH=PASS tests=20", run.stdout)


if __name__ == "__main__":
    unittest.main()
