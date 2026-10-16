// RHC-214. Instantiate at the FIRST connector tool entry, before any awaited
// GitHub action. Importing alone does NOT hook ChatGPT or certify tool entry.
const SCHEMA="RHC190_CLIENT_TOOL_OBSERVATION_V2";
const CAPTURE="CLIENT_FIRST_ENTRY_ISSUE_CREATE_BRACKET_REF_WRITE_READBACK";
const SHA=/^[0-9a-f]{40}$/;
const ISO=/^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z$/;
const REF=/^candidate\/v\d+\.\d+\.\d+\.\d+$/;
function need(ok,why){if(!ok)throw Error("RHC190_CLIENT_BLOCKED: "+why);}
function millis(s){need(typeof s==="string"&&ISO.test(s)&&Number.isFinite(Date.parse(s)),"invalid UTC");return Date.parse(s);}
function beginFirstTool({utc=()=>new Date().toISOString(),mono=()=>performance.now()}={}){
 const first=utc(),firstTick=mono();millis(first);need(Number.isFinite(firstTick),"no monotonic clock");
 let creation=null,bound=null,ref=null,usedCreate=false,usedRef=false;
 function snap(){const u=utc(),m=mono();millis(u);need(Number.isFinite(m)&&m>=firstTick,"monotonic invalid");return {utc:u,tick:m};}
 function duration(a,b){const elapsed=b.tick-a.tick,wall=millis(b.utc)-millis(a.utc);
   need(elapsed>=0&&elapsed<=120000&&Math.abs(wall-elapsed)<=2000,"UTC/monotonic drift or oversized tool call");
   return Math.round(elapsed*1000)/1000;
 }
 return Object.freeze({
   async observeIssueCreate(operation){
     need(!usedCreate&&typeof operation==="function","Issue creation must occur once");usedCreate=true;
     const a=snap();const result=await operation();const b=snap();duration(a,b);
     need(result&&Number.isSafeInteger(result.number)&&result.number>0&&
          typeof result.created_at==="string","GitHub create response needs number and server created_at");
     const server=millis(result.created_at);
     need(result.created_at.endsWith("Z")&&server%1000===0,"GitHub Issue time must be second precision");
     creation={number:result.number,created_at:result.created_at,start:a,end:b};
     return result;
   },
   bindCanonicalIssue(issue){
     need(creation!==null&&!bound&&issue&&issue.number===creation.number&&
       issue.created_at===creation.created_at&&issue.state==="open"&&
       issue.title?.startsWith("[RHC-"+creation.number+"] ")&&
       !issue.pull_request,"canonical independently fetched Issue mismatch");
     bound={number:issue.number};return issue.number;
   },
   async bracketExactRefWrite({refName,candidateSha,operation}){
     need(bound&&!usedRef&&REF.test(refName)&&SHA.test(candidateSha)&&typeof operation==="function",
       "single canonical Candidate ref write and exact SHA required");
     usedRef=true;const a=snap();const result=await operation();const b=snap();const ms=duration(a,b);
     need(result&&result.refName===refName&&result.verifiedSha===candidateSha&&
       result.verified===true,"exact post-write independent remote SHA readback absent");
     ref={a,b,ms,refName,candidateSha};return result;
   },
   exportEvidence(candidateSha){
     need(bound&&creation&&ref&&ref.candidateSha===candidateSha,
       "no bound Issue or verified exact candidate write");
     // Issue creation occurs during [client send, client reply]. GitHub's
     // seconds-precision created_at is conservatively an interval of 1 second.
     const lower=millis(creation.created_at)-millis(creation.end.utc);
     const upper=millis(creation.created_at)+1000-millis(creation.start.utc);
     need(lower<=upper&&upper-lower<=120000&&
       Math.max(Math.abs(lower),Math.abs(upper))<=300000,"unbounded cross-host clock offset");
     const last=ref.b;const delta=millis(last.utc)-millis(first),monoDelta=last.tick-firstTick;
     need(Math.abs(delta-monoDelta)<=2000,"cross-event UTC step detected");
     need(millis(creation.start.utc)>=millis(first)&&
          millis(ref.a.utc)>=millis(creation.end.utc),"not first-tool→Issue→ref order");
     return Object.freeze({schema:SCHEMA,capture_method:CAPTURE,
       issue:bound.number,candidate_sha:candidateSha,ref_name:ref.refName,
       first_tool_utc:first,issue_create_start_utc:creation.start.utc,
       issue_create_ack_utc:creation.end.utc,issue_server_created_utc:creation.created_at,
       ref_write_start_utc:ref.a.utc,ref_write_ack_utc:ref.b.utc,
       ref_write_duration_ms:ref.ms,server_minus_client_offset_min_ms:lower,
       server_minus_client_offset_max_ms:upper,
       first_tool_provenance:"OPERATOR_ENTRY_NOT_HOST_ATTESTED",
       ref_provenance:"CONNECTOR_WRITE_AND_INDEPENDENT_REF_READBACK"});
   }
 });
}
export {beginFirstTool,SCHEMA,CAPTURE};
