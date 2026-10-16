// RHC-214 first-tool measured gateway for the genuine branchless Fast Candidate.
// Invoke startInstrumentedFastPath as FIRST statement in FIRST tool call.
// This is an opt-in adapter; it does not authorize/execute a product release.
import {beginFirstTool} from "./rhc190_e2e_client_observer.mjs";
const REPO="SaschaP1980/RazerHealthCenter";
function need(ok,why){if(!ok)throw Error("RHC214_GATE_BLOCKED: "+why);}
function startInstrumentedFastPath(tools,{utc,mono}={}){
 const tracker=beginFirstTool({utc,mono});
 need(tools&&typeof tools.mcp__GitHub__fetch==="function"&&
   typeof tools.mcp__GitHub__create_issue==="function"&&
   typeof tools.mcp__GitHub__create_branch==="function"&&
   typeof tools.mcp__GitHub__add_comment_to_issue==="function","authenticated connector methods unavailable");
 const api="https://api.github.com/repos/"+REPO;
 const fetch=async(path)=>JSON.parse((await tools.mcp__GitHub__fetch({url:api+"/"+path})).result.content);
 let n=null,canonical=false,refDone=false,commentDone=false;
 return Object.freeze({
   async createProvisionalIssue({title,body,labels}){
     need(n===null&&typeof title==="string"&&title.startsWith("Initializing RHC Issue:")&&
       typeof body==="string"&&body.includes("Development path: dev-path: fast")&&
       Array.isArray(labels)&&labels.filter(x=>x==="bug"||x==="enhancement").length===1&&
       labels.filter(x=>/^priority: /.test(x)).length===1&&
       labels.filter(x=>/^dev-path: /.test(x)).length===1&&labels.includes("dev-path: fast")&&
       labels.includes("dev-ops")===/\b(github|ci|infrastructure|issue[- ](?:title|label|initialization)|release automation)\b/i.test(title),
       "provisional Issue must follow existing RHC-115/116 contract");
     const result=await tracker.observeIssueCreate(async()=>{
       const created=await tools.mcp__GitHub__create_issue({repository_full_name:REPO,title,body,labels});
       const url=created.result.url;
       const match=typeof url==="string"&&url.match(/^https:\/\/github\.com\/SaschaP1980\/RazerHealthCenter\/issues\/([1-9]\d*)$/);
       const number=created.result.issue.number??(match?Number(match[1]):null);
       need(Number.isSafeInteger(number),"GitHub created Issue URL lacks exact number");
       const provisional=await fetch("issues/"+number);
       need(provisional.number===number&&provisional.title===title&&provisional.body===body&&
         provisional.created_at===created.result.issue.created_at,"provisional Issue creation readback mismatch");
       return {number,created_at:provisional.created_at};
     });n=result.number;return result;
   },
   async verifyCanonicalIssue(number){
     need(!canonical&&n===number,"expected Issue ID must match create response");
     const read=await fetch("issues/"+number);
     tracker.bindCanonicalIssue(read);canonical=true;
     return read;
   },
   async createVerifiedCandidateRef(refName,candidateSha){
     need(canonical&&!refDone&&/^candidate\/v\d+\.\d+\.\d+\.\d+$/.test(refName)&&
       /^[a-f0-9]{40}$/.test(candidateSha),"Candidate authority not ready");
     refDone=true;
     return tracker.bracketExactRefWrite({refName,candidateSha,operation:async()=>{
       await tools.mcp__GitHub__create_branch({repository_full_name:REPO,branch_name:refName,sha:candidateSha});
       const verified=await fetch("git/ref/heads/"+refName);
       need(verified.object?.sha===candidateSha,"remote ref SHA/readback incorrect");
       return {refName,verifiedSha:verified.object.sha,verified:true};
     }});
   },
   async persistObservation(candidateSha){
     need(canonical&&refDone&&!commentDone,"one finished observation per Issue/ref");
     const evidence=tracker.exportEvidence(candidateSha);
     commentDone=true;
     const body="RHC190_CLIENT_OBSERVATION_V2="+JSON.stringify(evidence);
     try{await tools.mcp__GitHub__add_comment_to_issue({repo_full_name:REPO,pr_number:n,comment:body});}
     catch(_e){/* uncertain reply; reconcile by independently fetching exact body */ }
     const comments=await fetch("issues/"+n+"/comments?per_page=100");
     need(Array.isArray(comments)&&comments.length<100,"comment paging not bounded");
     const matches=comments.filter(c=>c.body===body);
     need(matches.length===1,"one independently persisted exact observation required");
     return {issue:n,commentId:matches[0].id,evidence};
   }
 });
}
export {startInstrumentedFastPath};
