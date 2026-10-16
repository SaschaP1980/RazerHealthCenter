"""RHC-214: evidence-bound calibration from a real GitHub Issue create bracket.

No credential access or remote writes. The API reports Issue timestamps
rounded DOWN to whole seconds, so use interval arithmetic, not false precision.
"""
from datetime import datetime, timezone
import json
import re

CLIENT_V2="RHC190_CLIENT_TOOL_OBSERVATION_V2"
CLIENT_V2_CAPTURE="CLIENT_FIRST_ENTRY_ISSUE_CREATE_BRACKET_REF_WRITE_READBACK"
CLIENT_V2_COMMENT="RHC190_CLIENT_OBSERVATION_V2="
CLOCKS={"INJECTED_TIMER_NOT_HOST_ATTESTED",
  "PERFORMANCE_NOW_NOT_HOST_ATTESTED","DATE_NOW_WALL_FALLBACK_NON_MONOTONIC"}
FIELDS={"schema","capture_method","issue","candidate_sha","ref_name",
  "first_tool_utc","issue_create_start_utc","issue_create_ack_utc",
  "issue_server_created_utc","ref_write_start_utc","ref_write_ack_utc",
  "ref_write_duration_ms","server_minus_client_offset_min_ms",
  "server_minus_client_offset_max_ms","first_tool_provenance","ref_provenance"}
def need(ok,msg):
    if not ok:raise ValueError("RHC190_E2E_BLOCKED: "+msg)
def stamp(s):
    need(isinstance(s,str) and bool(re.fullmatch(
        r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d(?:\.\d{1,3})?Z",s)), "invalid UTC")
    v=datetime.fromisoformat(s.replace("Z","+00:00"))
    need(v.utcoffset().total_seconds()==0,"non-UTC")
    return int(round(v.timestamp()*1000))
def issue_observer_from_comments(comments,issue,candidate_sha):
    need(isinstance(comments,list) and len(comments)<100,
         "client observation comments missing or paginated")
    rows=[x for x in comments if isinstance(x,dict) and
          isinstance(x.get("body"),str) and x["body"].startswith(CLIENT_V2_COMMENT)]
    need(len(rows)==1,"expected exactly one persisted observer comment")
    body=rows[0]["body"]
    need(len(body)<8192 and "\n" not in body,"oversized or malformed observer comment")
    try:raw=json.loads(body[len(CLIENT_V2_COMMENT):])
    except (ValueError,TypeError) as e:
        raise ValueError("RHC190_E2E_BLOCKED: malformed client JSON") from e
    need(isinstance(raw,dict) and raw.get("schema")==CLIENT_V2 and
         raw.get("issue")==issue and raw.get("candidate_sha")==candidate_sha,
         "persisted Issue/SHA observer mismatch")
    return raw
def client_v2_values(raw,*,issue,candidate_sha,ci_time,issue_created_at):
    # Older valid RHC-214 V2 observations lacked the optional clock-source
    # field; preserve their compatibility but never invent their clock quality.
    need(isinstance(raw,dict) and set(raw) in (FIELDS,FIELDS|{"client_clock_source"}) and
         ("client_clock_source" not in raw or raw["client_clock_source"] in CLOCKS) and
         raw.get("schema")==CLIENT_V2 and
         raw.get("capture_method")==CLIENT_V2_CAPTURE and
         raw.get("issue")==issue and raw.get("candidate_sha")==candidate_sha and
         raw.get("first_tool_provenance")=="OPERATOR_ENTRY_NOT_HOST_ATTESTED" and
         raw.get("ref_provenance")=="CONNECTOR_WRITE_AND_INDEPENDENT_REF_READBACK" and
         isinstance(raw.get("ref_name"),str) and
         bool(re.fullmatch(r"candidate/v\d+\.\d+\.\d+\.\d+",raw["ref_name"])),
         "V2 observer identity/provenance/secret field inconsistent")
    keys=("first_tool_utc","issue_create_start_utc","issue_create_ack_utc",
          "ref_write_start_utc","ref_write_ack_utc")
    first,begin,ack,refstart,refack=[stamp(raw[k]) for k in keys]
    server=raw.get("issue_server_created_utc")
    need(server==issue_created_at,"client Issue timestamp not authenticated by GitHub")
    anchor=stamp(server)
    need(first<=begin<=ack<=refstart<=refack and refack-first<=86400000,
         "impossible client first-tool/Issue/ref chronology")
    ms=raw.get("ref_write_duration_ms")
    need(type(ms) in (int,float) and 0<=ms<=120000 and
         abs(ms-(refack-refstart))<=2000,
         "monotonic ref duration disagrees with UTC bracket")
    low=anchor-ack
    high=anchor+1000-begin
    need(type(raw.get("server_minus_client_offset_min_ms")) is int and
         type(raw.get("server_minus_client_offset_max_ms")) is int and
         raw["server_minus_client_offset_min_ms"]==low and
         raw["server_minus_client_offset_max_ms"]==high and
         low<=high and high-low<=120000 and
         max(abs(low),abs(high))<=300000,
         "GitHub/client clock offset interval inconsistent")
    ci=stamp(ci_time)
    first_min=round((ci-first-high)/1000,3)
    first_max=round((ci-first-low)/1000,3)
    ref_min=round((ci-refack-high)/1000,3)
    ref_max=round((ci-refstart-low)/1000,3)
    need(first_min<=first_max and ref_min<=ref_max and
         first_max>=0 and ref_max>=0,"candidate CI precedes measured events")
    def state(lo,hi,goal):
        if hi<=goal:return "CONDITIONAL_BOUND_WITHIN_TARGET_NOT_HOST_ATTESTED"
        if lo>goal:return "CONDITIONAL_BOUND_EXCEEDS_TARGET_NOT_HOST_ATTESTED"
        return "INDETERMINATE_INTERVAL_NOT_HOST_ATTESTED"
    return dict(first_tool_utc=raw["first_tool_utc"],
        ref_write_start_utc=raw["ref_write_start_utc"],
        ref_write_ack_utc=raw["ref_write_ack_utc"],
        ref_write_duration_ms=ms,
        first_tool_to_ci_seconds=None,ref_to_ci_lower_seconds=None,
        ref_to_ci_upper_seconds=None,
        first_tool_to_ci_bounds_seconds=[first_min,first_max],
        ref_to_ci_bounds_seconds=[ref_min,ref_max],
        server_minus_client_offset_bounds_ms=[low,high],
        clock_calibration="BOUNDED_ISSUE_CREATION_GITHUB_SERVER_ANCHOR",
        client_clock_source=raw.get("client_clock_source","LEGACY_UNSPECIFIED_TIMER"),
        provenance="CLIENT_OPERATOR_ENTRY_AND_GITHUB_READBACK_NOT_HOST_ATTESTED",
        kpi_first_tool_120s=state(first_min,first_max,120),
        kpi_ref_to_ci_45s=state(ref_min,ref_max,45))
