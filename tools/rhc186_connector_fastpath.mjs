// RHC-186: connector-native bounded Issue -> Work launcher.
// No token acquisition, GitHub Action dispatch, or product publication.
// The caller must supply the existing authenticated provider; do not run on import.
const REPO = "SaschaP1980/RazerHealthCenter";
const SHA = /^[a-f0-9]{40}$/;
const HEADINGS = ["Chat origin","Work-Path authorization and scope","Benchmark configuration","Validation plan and coverage","Measurement ledger","Development Completion attempts","Candidate Entry","Candidate attempts","Release","Final Release Verification","Performance result","Evidence audit","Plan-conformance assessment"];
const VERSION = /^(\s*(appVersion|referenceVersion)\s*=\s*")(\d+(?:\.\d+){3})("[^\n]*)$/gm;
const TARGET = /^Owner-approved version-only target: (\d+\.\d+\.\d+\.\d+)$/gm;
function guard(ok, reason) { if (!ok) throw new Error("RHC186_BLOCKED: " + reason); }
function elapsedStart(now) { return {utc:new Date(now()).toISOString(),mono:now()}; }
function observer(now=()=>Date.now()) {
  const events=[];
  async function step(name,fn,group="serial",write=false) {
    const started=elapsedStart(now);let outcome="PASS";
    try { return await fn(); }
    catch(e) { outcome="BLOCKED"; throw e; }
    finally { const stopped=now();events.push({event:name,group,write,
      startUtc:started.utc,endUtc:new Date(stopped).toISOString(),
      elapsedMs:Math.max(0,stopped-started.mono),outcome,
      source:"CLIENT_OBSERVED_NOT_GITHUB_SERVER"}); }
  }
  async function parallel(group,items) {
    const entries=Object.entries(items);
    guard(entries.length>0 && entries.length<=8,"unbounded parallel read group");
    const pairs=await Promise.all(entries.map(async([key,fn])=>[key,await step(key,fn,group,false)]));
    return Object.fromEntries(pairs);
  }
  return {events,step,parallel};
}
function headings(body) { return [...String(body).matchAll(/^### (.+)$/gm)].map(x=>x[1]); }
function setLine(body,prefix,value) {
  let count=0;const lines=body.split("\n").map(l=>l.startsWith(prefix)?(count++,prefix+" "+value):l);
  guard(count===1,"ambiguous/missing Rolling field: "+prefix);return lines.join("\n");
}
function setRow(body,name,when,evidence) {
  let count=0;const lines=body.split("\n").map(l=>l.startsWith("| "+name+" |")?(count++,"| "+name+" | "+when+" | "+evidence+" |"):l);
  guard(count===1,"ambiguous/missing Rolling ledger: "+name);return lines.join("\n");
}
function utcClock(now) { const instant=new Date(now());guard(Number.isFinite(+instant),"invalid clock");return instant.toISOString(); }
function heartbeat(body,instant) {
  const iso=new Date(instant).toISOString();
  const loc=new Intl.DateTimeFormat("de-DE",{timeZone:"Europe/Berlin",day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",second:"2-digit",hour12:false}).format(new Date(iso));
  const zone=new Intl.DateTimeFormat("en-US",{timeZone:"Europe/Berlin",timeZoneName:"short"}).formatToParts(new Date(iso)).find(x=>x.type==="timeZoneName")?.value;
  body=setLine(body,"**Last heartbeat:**",iso.slice(0,10)+" at "+iso.slice(11,19)+" UTC");
  body=setLine(body,"**Local reference (Europe/Berlin):**",loc+" "+(zone==="GMT+2"||zone==="CEST"?"CEST":"CET"));
  return setLine(body,"**Original ISO timestamp:**",String.fromCharCode(96)+iso+String.fromCharCode(96));
}
function approvedIssue(issue,n,expectedBody) {
  guard(issue && issue.number===n && issue.state==="open" &&
    issue.title?.startsWith("[RHC-"+n+"] ") && typeof issue.body==="string" &&
    !issue.pull_request && (!expectedBody || issue.body===expectedBody),"canonical Issue mismatch");
  const names=issue.labels?.map(x=>typeof x==="string"?x:x.name);
  guard(Array.isArray(names)&&new Set(names).size===names.length&&
    names.filter(x=>x==="bug"||x==="enhancement").length===1&&
    names.filter(x=>/^priority: /.test(x)).length===1&&
    names.filter(x=>/^dev-path: /.test(x)).join("|")==="dev-path: work-branch",
    "RHC115/116 type/priority/development taxonomy");
  const area=/\b(github|ci|infrastructure|issue[- ](?:title|label|initialization)|release automation)\b/i.test(issue.title);
  guard(names.includes("dev-ops")===area,"RHC116 work area title/label mismatch");
  guard(/^Development path: dev-path: work-branch\b/m.test(issue.body),"Issue Work disposition missing");
  return issue;
}
function approvedComment(comment,n,branchAt) {
  guard(comment && Number.isSafeInteger(comment.id) && headings(comment.body).join("|")===HEADINGS.join("|"),
    "Rolling ID/13-section body missing or altered");
  const frozen=comment.body.match(/^\*\*Bootstrap creation ISO timestamp:\*\* .([0-9TZ:.\-]+).$/m)?.[1];
  guard(frozen && Math.abs(Date.parse(comment.created_at)-Date.parse(frozen))<=30000,
    "original BOOTSTRAP creation clock disagrees with GitHub");
  const current=comment.body.match(/^\*\*Original ISO timestamp:\*\* .([0-9TZ:.\-]+).$/m)?.[1];
  guard(current && Math.abs(Date.parse(comment.updated_at)-Date.parse(current))<=30000,
    "current Rolling UTC clock/readback inconsistent");
  guard(comment.body.includes("RHC"+n+"CHAT") &&
    /- Marker posted as a visible message in that chat: yes/.test(comment.body),
    "visible Work chat marker not attested");
  if(branchAt) guard(Date.parse(comment.created_at)<Date.parse(branchAt),
    "BOOTSTRAP not saved before branch");
  return comment;
}
function composeBootstrap(template,n,main,marker,instant) {
  guard(typeof template==="string"&&SHA.test(main)&&
    marker.startsWith("RHC"+n+"CHAT")&&/^RHC[1-9]\d*CHAT[A-F0-9]{12}$/.test(marker),
    "untrusted BOOTSTRAP inputs");
  const match=template.match(/~~~markdown\n([\s\S]+?)\n~~~/);
  guard(match,"missing canonical fenced template");
  let body=match[1].replace("RHC-<GitHub Issue number>","RHC-"+n).replaceAll("<number>",String(n));
  guard(headings(body).join("|")===HEADINGS.join("|"),"full original 13 headings not preserved");
  body=heartbeat(body,instant);
  const fields={
    "**Bootstrap creation ISO timestamp:**":String.fromCharCode(96)+instant+String.fromCharCode(96),
    "**Agent-State:**":"ACTIVE",
    "**Issue:**":"[RHC-"+n+"](https://github.com/"+REPO+"/issues/"+n+")",
    "**Base main:**":String.fromCharCode(96)+main+String.fromCharCode(96),
    "**Work branch / exact head:**":"work/RHC-"+n+" / NOT CREATED",
    "**Last checkpoint:**":main+" main frozen",
    "**Bootstrap readback:**":"NOT VERIFIED — stop before Work branch",
    "**Version:**":"not modified by bootstrap",
    "**Current phase:**":"BOOTSTRAP",
    "**Next action:**":"independently read full saved comment before creating Work",
    "- Originating Work-Chat-ID:":String.fromCharCode(96)+marker+String.fromCharCode(96),
    "- Marker posted as a visible message in that chat:":"yes (owner-visible marker supplied)",
    "- Development-path decision:":"dev-path: work-branch; verify saved Issue taxonomy",
    "- Work-Branch-Reason:":"owner-authorized guarded Work path",
    "- Allowed diff:":"exact scope in saved Issue, no source mutation in bootstrap",
    "- Forbidden changes:":"Razer repair, privilege/UAC, device/state, CI false-green or release bypass",
    "- Protected/deletion intent:":"none",
    "- Issue completion eligibility:":"NO, Work CI and PR unverified",
    "**PASS | PASS WITH CORRECTION | FAIL | NOT READY**":"NOT READY"
  };
  for(const [key,value] of Object.entries(fields))body=setLine(body,key,value);
  body=setRow(body,"Rolling Comment BOOTSTRAP created/read back","NOT VERIFIED","no Work branch before GitHub creation proof");
  return body;
}
function sameAuthority(first,next,main,branch) {
  guard(JSON.stringify(next.issue)===JSON.stringify(first.issue)&&
    JSON.stringify(next.comment)===JSON.stringify(first.comment)&&
    next.main===main&&next.work===branch,"mutable authority changed or pinned ref moved");
}
async function canonicalIssueInit({gateway,subject,body,labels,nonce,apply=false,now=()=>Date.now()}) {
  const m=observer(now);
  guard(typeof subject==="string"&&subject.length>=8&&typeof body==="string"&&
    /^Development path: dev-path: work-branch\b/m.test(body)&&/^[a-f0-9]{10,32}$/.test(nonce||""),
    "Issue init must be explicit, canonical and carry unique nonce");
  const fake={number:1,title:"[RHC-1] "+subject,body,state:"open",labels};
  approvedIssue(fake,1,body);
  const provisional="Initializing RHC Issue: "+subject+" [init-"+nonce+"]";
  if(!apply)return {status:"PLAN_ONLY",writes:0,timings:m.events};
  let result=null,uncertain=false;
  try{result=await m.step("createIssue",()=>gateway.createIssue(provisional,body,labels),"init",true);}
  catch(_){uncertain=true;}
  const matches=await m.step("recoverUniqueProvisional",()=>gateway.findIssues(provisional,body),"init");
  guard(Array.isArray(matches)&&matches.length===1&&Number.isSafeInteger(matches[0].number),
    "uncertain creation: unique Issue not established; never create twice");
  const number=matches[0].number;
  if(result)guard(result.number===number,"created Issue number differs from readback");
  const got=await m.step("getProvisional",()=>gateway.getIssue(number),"init");
  guard(got.title===provisional&&got.body===body&&got.state==="open"&&
    got.labels?.map(l=>typeof l==="string"?l:l.name).sort().join("|")===labels.slice().sort().join("|"),
    "provisional Issue/body/creation-time labels inconsistent");
  const name="[RHC-"+number+"] "+subject;
  try{await m.step("renameIssue",()=>gateway.renameIssue(number,name),"init",true);}
  catch(_){uncertain=true;}
  const final=await m.step("readCanonicalIssue",()=>gateway.getIssue(number),"init");
  approvedIssue(final,number,body);
  guard(final.title===name,"ambiguous Issue rename not reconciled");
  return {status:"ISSUE_VERIFIED_AWAIT_VISIBLE_MARKER",number,createdAt:final.created_at,
    writes:2,writeReplyUncertain:uncertain,timings:m.events};
}
async function bootstrapExisting({gateway,number,baseMain,marker,template,allowWrites=false,now=()=>Date.now()}) {
  const m=observer(now);
  guard(Number.isSafeInteger(number)&&number>0&&SHA.test(baseMain)&&
    /^RHC[1-9]\d*CHAT[A-F0-9]{12}$/.test(marker)&&marker.startsWith("RHC"+number+"CHAT"),
    "bootstrap requires real numbered Issue and visible matching marker");
  const start=await m.parallel("bootstrap-authority",{
    issue:()=>gateway.getIssue(number),main:()=>gateway.getMain(),comments:()=>gateway.listComments(number),
    work:()=>gateway.getWork(number)});
  approvedIssue(start.issue,number);guard(start.main===baseMain&&start.work===null&&
    Array.isArray(start.comments)&&start.comments.length===0,"main drift, existing comment or Work occupied");
  const originalInstant=utcClock(now),original=composeBootstrap(template,number,baseMain,marker,originalInstant);
  if(!allowWrites)return {status:"PLAN_ONLY",writes:0,headings:13,timings:m.events};
  let unknown=false;
  try{await m.step("createFullBootstrap",()=>gateway.createComment(number,original),"bootstrap",true);}catch(_){unknown=true;}
  const rows=await m.step("uniqueCommentReadback",()=>gateway.listComments(number),"bootstrap");
  guard(Array.isArray(rows)&&rows.length===1&&rows[0].body===original&&
    Number.isSafeInteger(rows[0].id),"comment creation uncertain/foreign/duplicate");
  const id=rows[0].id;
  const saved=await m.step("getOriginalComment",()=>gateway.getComment(id),"bootstrap");
  guard(saved.body===original&&Math.abs(Date.parse(saved.created_at)-Date.parse(originalInstant))<=30000,
    "bootstrap first independent timestamp/content readback failed");
  let revised=heartbeat(original,utcClock(now));
  revised=setLine(revised,"**Bootstrap readback:**","original comment #"+id+" independently verified BEFORE Work branch");
  revised=setRow(revised,"Rolling Comment BOOTSTRAP created/read back",saved.created_at,
    "full 13 headings; frozen ISO "+originalInstant+"; comment #"+id);
  try{await m.step("markPrebranchVerified",()=>gateway.updateComment(id,revised),"bootstrap",true);}catch(_){unknown=true;}
  const pre=await m.parallel("prebranch-ref-gate",{
    comment:()=>gateway.getComment(id),issue:()=>gateway.getIssue(number),
    main:()=>gateway.getMain(),work:()=>gateway.getWork(number)});
  guard(pre.comment.body===revised&&pre.main===baseMain&&pre.work===null,"prebranch proof/ref drift");
  approvedIssue(pre.issue,number,start.issue.body);approvedComment(pre.comment,number);
  try{await m.step("createWorkRef",()=>gateway.createWork(number,baseMain),"bootstrap",true);}catch(_){unknown=true;}
  const head=await m.parallel("postbranch-ref-gate",{
    main:()=>gateway.getMain(),work:()=>gateway.getWork(number)});
  guard(head.main===baseMain&&head.work===baseMain,"ambiguous branch creation/changed SHA");
  const branchAt=utcClock(now);
  guard(Date.parse(branchAt)>Date.parse(saved.created_at),"Work not provably after full original comment");
  let after=heartbeat(revised,utcClock(now));
  after=setLine(after,"**Work branch / exact head:**","work/RHC-"+number+" / "+baseMain+" independent remote SHA");
  after=setLine(after,"**Current phase:**","WORK_READY");
  after=setLine(after,"**Last checkpoint:**",baseMain+" Work initial HEAD");
  after=setRow(after,"Work branch created",branchAt,"work/RHC-"+number+" "+baseMain+" client observation");
  try{await m.step("markPostbranch",()=>gateway.updateComment(id,after),"bootstrap",true);}catch(_){unknown=true;}
  const last=await m.parallel("postbranch-comment-gate",{
    comment:()=>gateway.getComment(id),issue:()=>gateway.getIssue(number),
    main:()=>gateway.getMain(),work:()=>gateway.getWork(number)});
  guard(last.comment.body===after&&last.main===baseMain&&last.work===baseMain,"postbranch comment/ref not verified");
  approvedIssue(last.issue,number,start.issue.body);approvedComment(last.comment,number,branchAt);
  return {status:"BOOTSTRAP_VERIFIED",number,commentId:id,branch:"work/RHC-"+number,
    branchCreatedAt:branchAt,baseMain,writeReplyUncertain:unknown,timings:m.events};
}
function versionTransform(issue,model,changelog,day) {
  guard(/^\d{4}-\d{2}-\d{2}$/.test(day),"invalid UTC release day");
  const targets=[...issue.body.matchAll(TARGET)];
  guard(targets.length===1,"exactly one owner-approved version target required");
  const goal=targets[0][1],rows=[...model.matchAll(VERSION)];
  guard(rows.length===2&&rows.map(x=>x[2]).sort().join("|")==="appVersion|referenceVersion"&&
    rows[0][3]===rows[1][3],"both original model constants must match");
  const old=rows[0][3],a=old.split(".").map(Number),b=goal.split(".").map(Number);
  guard(a.length===4&&b.length===4&&b.slice(0,3).join(".")===a.slice(0,3).join(".")&&
    b[3]===a[3]+1,"not exactly next four-part hotfix version");
  guard(changelog.startsWith("# Changelog\n\n## "+old+" — ")&&
    !changelog.includes("\n## "+goal+" — "),"Changelog head missing or target already exists");
  const nextModel=model.replace(VERSION,(_,p,name,v,suffix)=>p+goal+suffix);
  const section="## "+goal+" — "+day+"\n\n- Version-only HOTFIX: appVersion and referenceVersion advanced from "+old+" to "+goal+
    "; Razer runtime, UAC/repair/privilege and release safety gates unchanged.\n\n";
  const nextChangelog="# Changelog\n\n"+section+changelog.slice("# Changelog\n\n".length);
  guard(nextChangelog.endsWith(changelog.slice("# Changelog\n\n".length))&&
    [...nextModel.matchAll(VERSION)].every(x=>x[3]===goal),"version-only pure transform mismatch");
  return {old,goal,model:nextModel,changelog:nextChangelog};
}
async function commitVersion({gateway,number,commentId,baseMain,branchCreatedAt,day,
  ownerAuthorizedNewVersion=false,allowWrites=false,now=()=>Date.now()}) {
  const m=observer(now);
  guard(Number.isSafeInteger(number)&&number>0&&Number.isSafeInteger(commentId)&&commentId>0&&
    SHA.test(baseMain)&&Number.isFinite(Date.parse(branchCreatedAt)),"unsafe Work commit identifiers");
  const input=await m.parallel("initial-version-authority",{
    issue:()=>gateway.getIssue(number),comment:()=>gateway.getComment(commentId),
    main:()=>gateway.getMain(),work:()=>gateway.getWork(number),
    model:()=>gateway.getFile("model.go",baseMain),
    changelog:()=>gateway.getFile("CHANGELOG.md",baseMain),
    parent:()=>gateway.getCommit(baseMain)});
  approvedIssue(input.issue,number);approvedComment(input.comment,number,branchCreatedAt);
  guard(input.main===baseMain&&input.work===baseMain&&SHA.test(input.parent.tree?.sha),
    "source parent/main/ref is not frozen");
  const out=versionTransform(input.issue,input.model,input.changelog,day);
  if(!allowWrites)return {status:"PLAN_ONLY",version:out.goal,writes:0,timings:m.events};
  guard(ownerAuthorizedNewVersion===true,"explicit separate new-version authorization required");
  async function reread(group) {
    const current=await m.parallel(group,{
      issue:()=>gateway.getIssue(number),comment:()=>gateway.getComment(commentId),
      main:()=>gateway.getMain(),work:()=>gateway.getWork(number)});
    sameAuthority(input,current,baseMain,baseMain);return current;
  }
  await reread("precommit-authority");
  const tree=await m.step("createExactTwoPathTree",()=>gateway.makeTree(input.parent.tree.sha,[
    {path:"model.go",mode:"100644",type:"blob",content:out.model},
    {path:"CHANGELOG.md",mode:"100644",type:"blob",content:out.changelog}]),"git-object-write",true);
  guard(SHA.test(tree.sha),"created tree has no verified SHA");
  const message="chore(RHC-"+number+"): advance version-only HOTFIX to v"+out.goal+
    "\n\nRHC-Issue: "+number+"\nRelease-Profile: version-only\nDevelopment-Completion: requested";
  const commit=await m.step("createExactParentCommit",()=>gateway.makeCommit(tree.sha,baseMain,message),"git-object-write",true);
  guard(SHA.test(commit.sha)&&commit.sha!==baseMain,"invalid prepared commit");
  const proof=await m.parallel("independent-prepush-proof",{
    compare:()=>gateway.compare(baseMain,commit.sha),
    commit:()=>gateway.getCommit(commit.sha),
    model:()=>gateway.getFile("model.go",commit.sha),
    changelog:()=>gateway.getFile("CHANGELOG.md",commit.sha)});
  const diff=proof.compare,meta=proof.commit;
  guard(diff.ahead_by===1&&diff.behind_by===0&&diff.total_commits===1&&
    diff.files?.map(x=>x.filename).sort().join("|")==="CHANGELOG.md|model.go"&&
    diff.files.every(x=>x.status==="modified")&&meta.parents?.length===1&&
    meta.parents[0].sha===baseMain&&meta.tree.sha===tree.sha&&meta.message===message&&
    proof.model===out.model&&proof.changelog===out.changelog,
    "Git prepared commit identity/diff/source does not satisfy RHC132");
  await reread("prepush-last-lease");
  let uncertain=false;
  try{await m.step("advanceWorkRefOnce",()=>gateway.moveWork(number,commit.sha,baseMain),"single-ref-write",true);}
  catch(_){uncertain=true;}
  const final=await m.parallel("postpush-remote-readback",{
    issue:()=>gateway.getIssue(number),comment:()=>gateway.getComment(commentId),
    main:()=>gateway.getMain(),work:()=>gateway.getWork(number)});
  sameAuthority(input,{...final,work:baseMain},baseMain,baseMain);
  guard(final.work===commit.sha,"failed/uncertain ref update; never retry");
  return {status:"WORK_PUSH_VERIFIED",number,branch:"work/RHC-"+number,
    mainSha:baseMain,workSha:commit.sha,version:out.goal,allowedPaths:["CHANGELOG.md","model.go"],
    writeReplyUncertain:uncertain,timings:m.events,actualWorkCiCreatedAt:"NOT_OBSERVED"};
}
async function observeWorkCi({gateway,sha,pushObservedUtc,now=()=>Date.now()}) {
  const m=observer(now);guard(SHA.test(sha)&&Number.isFinite(Date.parse(pushObservedUtc)),
    "missing exact Work SHA/observed push time");
  const rows=await m.step("realNativeWorkRuns",()=>gateway.listRuns(sha));
  guard(Array.isArray(rows)&&rows.length<=100,"unbounded or missing native Work-CI runs");
  const expected=["RHC Infrastructure Qualification (nonpublishing)","RHC Development Completion (exact SHA gate)"];
  const chosen=[];
  for(const name of expected) {
    const matches=rows.filter(x=>x.name===name);
    guard(matches.length===1,"missing/duplicated exact Work run: "+name);
    const run=matches[0];guard(run.head_sha===sha&&run.event==="push"&&
      Number.isSafeInteger(run.id)&&Date.parse(run.created_at)>=Date.parse(pushObservedUtc)-5000&&
      ["queued","in_progress","completed"].includes(run.status),
      "stale/wrong SHA/foreign/not-push Work run");
    chosen.push({id:run.id,name,createdAt:run.created_at,status:run.status,conclusion:run.conclusion});
  }
  return {status:"WORK_CI_CREATED_NOT_GREEN",sha,runs:chosen,timings:m.events};
}
function githubConnectorGateway(tools,repo=REPO) {
  guard(repo===REPO&&tools&&typeof tools.mcp__GitHub__fetch==="function",
    "existing authenticated GitHub connector required");
  const api="https://api.github.com/repos/"+repo;
  async function fetch(url) { const x=await tools.mcp__GitHub__fetch({url});return JSON.parse(x.result.content); }
  async function getWork(n) {
    try{return (await fetch(api+"/git/ref/heads/work/RHC-"+n)).object.sha;}
    catch(e){guard(/\b404\b|Not Found/i.test(String(e)),"Work-ref read failed, not a genuine 404");return null;}
  }
  return {
    getMain:async()=>(await fetch(api+"/branches/main")).commit.sha,
    getWork,
    getIssue:n=>fetch(api+"/issues/"+n),
    findIssues:async(title,body)=>{
      const rows=await fetch(api+"/issues?state=open&per_page=100");
      guard(rows.length<100,"Issue search pagination ambiguous; do not create again");
      return rows.filter(x=>!x.pull_request&&x.title===title&&x.body===body);
    },
    createIssue:async(title,body,labels)=>{const x=await tools.mcp__GitHub__create_issue({repository_full_name:repo,title,body,labels});return {number:x.result.issue.number};},
    renameIssue:async(n,title)=>tools.mcp__GitHub__update_issue({repository_full_name:repo,issue_number:n,title}),
    listComments:n=>fetch(api+"/issues/"+n+"/comments?per_page=100"),
    getComment:id=>fetch(api+"/issues/comments/"+id),
    createComment:async(n,body)=>tools.mcp__GitHub__add_comment_to_issue({repo_full_name:repo,pr_number:n,comment:body}),
    updateComment:async(id,body)=>tools.mcp__GitHub__update_issue_comment({repo_full_name:repo,comment_id:id,comment:body}),
    createWork:async(n,sha)=>tools.mcp__GitHub__create_branch({repository_full_name:repo,branch_name:"work/RHC-"+n,sha}),
    getFile:async(path,ref)=>(await tools.mcp__GitHub__fetch_file({repository_full_name:repo,path,ref})).result.content,
    getCommit:sha=>fetch(api+"/git/commits/"+sha),
    makeTree:async(baseTree,elements)=>(await tools.mcp__GitHub__create_tree({repository_full_name:repo,base_tree_sha:baseTree,tree_elements:elements})).result,
    makeCommit:async(tree,parent,message)=>(await tools.mcp__GitHub__create_commit({repository_full_name:repo,tree_sha:tree,parent_sha:parent,message})).result,
    compare:async(base,head)=>(await tools.mcp__GitHub__compare_commits({repo_full_name:repo,base,head})).result,
    moveWork:async(n,sha,expected)=>{const x=await tools.mcp__GitHub__update_ref({repository_full_name:repo,branch_name:"work/RHC-"+n,sha,expected_sha:expected,force:false});guard(x.result.success,"GitHub ref lease rejected");return x.result;},
    listRuns:async(sha)=>(await fetch(api+"/actions/runs?head_sha="+sha+"&per_page=100")).workflow_runs
  };
}
export {REPO,HEADINGS,observer,approvedIssue,approvedComment,composeBootstrap,
 canonicalIssueInit,bootstrapExisting,versionTransform,commitVersion,observeWorkCi,
 githubConnectorGateway};
