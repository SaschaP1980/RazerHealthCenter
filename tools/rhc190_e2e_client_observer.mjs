// RHC-212 nonpublishing client-side observation; explicitly invoke at the
// literal beginning of the FIRST actual ChatGPT connector tool for a flow.
// Merely importing this file after other tools does NOT record first-tool time.
// GitHub REST has no authoritative branch-ref created_at event.
const SCHEMA="RHC190_CLIENT_TOOL_OBSERVATION_V1";
const CAPTURE="CLIENT_INSTRUMENTED_TOOL_ENTRY_AND_REF_WRITE_BRACKET";
const SHA=/^[0-9a-f]{40}$/;
function requireFact(ok,message) {if(!ok) throw Error("RHC190_CLIENT_BLOCKED: "+message);}
function beginFirstTool({issue,utc=()=>new Date().toISOString(),mono=()=>performance.now()}={}) {
  requireFact(Number.isSafeInteger(issue)&&issue>0,"Issue must already be assigned");
  const start=utc(),tick=mono();
  requireFact(Number.isFinite(Date.parse(start))&&Number.isFinite(tick),"no client clock");
  let refStart=null,refEnd=null,refElapsed=null,attempted=false,completed=false;
  return Object.freeze({
    async bracketExactRefWrite(operation) {
      requireFact(!attempted&&typeof operation==="function","one explicit ref write only");
      attempted=true;
      const before=utc(),t0=mono();refStart=before;
      try {
        const answer=await operation();
        const t1=mono(),after=utc();
        requireFact(Number.isFinite(t1)&&t1>=t0&&t1-t0<=120000,
                    "ref write monotonic invalid");
        requireFact(Date.parse(after)>=Date.parse(before),"ref write UTC reversed");
        refEnd=after;refElapsed=Math.round((t1-t0)*1000)/1000;
        completed=true;
        return answer;
      } catch(e) {completed=false;throw e;}
    },
    exportEvidence(candidateSha) {
      requireFact(completed&&SHA.test(candidateSha),"no completed exact mutation");
      requireFact(Date.parse(refStart)>=Date.parse(start),
                  "first-tool and ref-write times out of order");
      requireFact(mono()>=tick,"client monotonic went backwards");
      return Object.freeze({
        schema:SCHEMA,issue,candidate_sha:candidateSha,
        capture_method:CAPTURE,first_tool_utc:start,
        ref_write_start_utc:refStart,ref_write_ack_utc:refEnd,
        ref_write_duration_ms:refElapsed
      });
    }
  });
}
export {beginFirstTool,SCHEMA,CAPTURE};
