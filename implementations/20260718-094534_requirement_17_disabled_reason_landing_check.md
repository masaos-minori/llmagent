# Implementation procedure: pre-merge dependency check — requirement 15 landing status (requirement 17, plan step 8)

Source plan: `plans/20260717-175327_plan.md` ("RuntimeToolRegistry — represent disabled MCP tools
without exposing them to the LLM", requirement 17), Implementation step 8.

## Goal

Before merging this requirement's work, re-check whether sibling requirement 15
(`plans/20260717-174024_plan.md`, "Add runtime availability metadata" — server-side
`enabled`/`disabled_reason` on `/v1/tools`) has actually landed in real source. If it has, drop
`mcp_tool_discovery.py`'s backward-compat defaulting fallback from being the only tested path and
add an integration-style test against the real server response shape. If it has not landed, keep
the defaulting path as documented behavior and record the dependency in code comments referencing
this plan. This is this plan's own explicit Implementation step 8, not the batch's generic
`full_validation_pass` step — it is a targeted dependency-landing check specific to this
requirement's cross-plan risk (see the source plan's Risks section, "Cross-requirement dependency
risk (primary)").

**Disambiguation note (per this batch's established convention)**: this doc is deliberately named
with the feature/requirement slug (`requirement_17_disabled_reason_landing_check`) rather than the
generic `full_validation_pass`, since that generic slug has already been reused by multiple
unrelated plans in this batch and is not a safe target for a filename-only match. A conceptually
adjacent doc, `implementations/20260718-090830_full_validation_pass_tools_enabled_disabled_reason.md`,
already exists — but its Goal is requirement 15's *own* validation pass (scoped to
`scripts/mcp_servers/file/common.py`, `read_server.py`, `write_server.py`, `delete_server.py`,
`scripts/mcp_servers/git/server.py`, `tests/test_mcp_tools_validation.py`), run from requirement
15's own plan, not this plan's cross-requirement landing check performed from requirement 17's side.
Checked its Goal directly before writing this doc — it does not cover requirement 17's own
implementation steps 1-7 (the actual `RuntimeTool`/`RuntimeToolRegistry`/`mcp_tool_discovery.py`/
`llm_turn_runner.py`/`cmd_mcp.py` changes documented in this batch), so it cannot be treated as
covering this plan's step 8. Not skipped.

**Review note (post-review, 2026-07-18)**: this plan's "own 6 implemented files" (`runtime_tool.py`,
`runtime_tool_registry.py`, listed below in Scope) are not a separate pair of files from requirement
02/03's `runtime_tool.py`/`runtime_tool_registry.py` — per the correction note in
`implementations/20260718-084710_runtime_tool.py.md`, the 13-field/9-method lineage is the adopted
baseline, and requirement 17 extends the *same* `scripts/shared/runtime_tool.py` /
`runtime_tool_registry.py` with disabled-visibility fields/methods rather than owning distinct files.
This does not change this doc's own pre-merge dependency-check procedure (Scope/Procedure below are
unaffected); it only corrects the "own 6 implemented files" framing so a future implementer does not
look for a second, separate pair of source files.

## Scope

**In scope**
- A pre-merge check step (not a source-file change): grep `scripts/mcp_servers/` for
  `disabled_reason` to determine requirement 15's landing status; branch behavior for
  `mcp_tool_discovery.py`'s test suite and code comments accordingly.

**Out of scope**
- Implementing requirement 15 itself (separate plan/lineage, already has its own implementation
  docs as of this writing — see `implementations/20260718-085909_read_tools.py.md` through
  `implementations/20260718-091922_full_validation_pass_call_tool_disabled_gate.md`, an
  already-designed-but-not-yet-real-source lineage for requirement 15 and the related server-side
  `/v1/call_tool` disabled-gate work).
- Re-running the full standard validation sequence for requirement 17's own 6 implemented files
  (`runtime_tool.py`, `runtime_tool_registry.py`, `test_runtime_tool_registry.py`,
  `mcp_tool_discovery.py`, `test_mcp_tool_discovery.py`, `llm_turn_runner.py`, `cmd_mcp.py`,
  `test_cmd_mcp.py`) — each of those 7 paired implementation docs already carries its own
  file-scoped Validation plan table; this step is specifically the cross-requirement dependency
  check, not a duplicate of those.

## Assumptions

- At the time this plan was authored (`plans/20260717-175327_plan.md`'s own Unknowns table),
  `grep -rn "disabled_reason" .` returned zero matches repo-wide — requirement 15 had not landed in
  real source. As of this documents-only workflow pass (today, processing this batch's plans), no
  real source changes have been made by ANY plan in this batch yet — this entire batch produces
  `implementations/*.md` design/procedure docs only, not code. Therefore, re-running
  `grep -rn "disabled_reason" scripts/mcp_servers/` today will still return zero matches in real
  source, regardless of how many implementation *docs* now exist for requirement 15 — a design doc
  existing is not the same as the source landing. This check's real trigger point is downstream, at
  actual code-implementation time (when requirement 17's `mcp_tool_discovery.py` doc above is turned
  into real committed code), not at this documents-only stage.
- This step is therefore recorded here as a **procedure to run at implementation time**, not
  something this documents-only workflow pass can resolve today (there is no real source to check
  against yet in either direction). The procedure itself is fully specified below so the future
  implementer has an unambiguous, mechanical check to run.

## Implementation

### Target file

None (process/checklist step, not a source file) — informs test-suite scope for
`tests/test_mcp_tool_discovery.py` (`implementations/20260718-094245_test_mcp_tool_discovery.py.md`)
and code comments in `scripts/agent/services/mcp_tool_discovery.py`
(`implementations/20260718-094158_mcp_tool_discovery.py.md`).

### Procedure

1. Run `grep -rn "disabled_reason" scripts/mcp_servers/` immediately before opening a merge/PR for
   requirement 17's implementation.
2. **If matches are found** (requirement 15 has landed): confirm the exact field name/shape matches
   what `mcp_tool_discovery.py`'s `_build_runtime_tool()` expects (`tool.get("enabled", True)`,
   `tool.get("disabled_reason", "")` on each `/v1/tools` entry — per this plan's own doc). If the
   shape matches: add one integration-style test to `tests/test_mcp_tool_discovery.py` that
   exercises a real (not mocked) server's FastAPI app + `TOOL_LIST` via `httpx.ASGITransport` (the
   pattern already used by requirement-15's own
   `implementations/20260718-085909_read_tools.py.md`-lineage tests, per
   `tests/test_mcp_tools_validation.py`), asserting a genuinely disabled real tool round-trips
   through discovery with the correct `enabled=False`/`disabled_reason` values. If the shape does
   NOT match (field name drift, e.g. requirement 15 used a different key): update
   `_build_runtime_tool()`'s field-reading logic to match the real shape and file a follow-up note —
   do not silently keep the mismatch.
3. **If no matches are found** (requirement 15 has not landed): keep the defaulting path
   (`enabled=True, disabled_reason=""` for absent fields) as the sole, documented behavior; add/keep
   a code comment in `mcp_tool_discovery.py`'s module docstring stating explicitly: "Backward-compat
   defaulting is the only tested path until `plans/20260717-174024_plan.md` (requirement 15) lands
   server-side `enabled`/`disabled_reason` on `/v1/tools`; see that plan for status." Do not block
   merging requirement 17's own code on requirement 15 landing — per the source plan's own Risk
   mitigation, this plan is "buildable and testable independently today."
4. Record the check's outcome (landed / not landed, date) in the commit message or PR description
   for requiration 17's implementation, so the next person re-running this check has a timestamped
   trail.

### Method

Manual grep + conditional branch, run once at actual implementation/merge time (not automatable as
a CI gate, since "requirement 15 landed" is a cross-plan state this repo has no automated tracking
for beyond grepping for the field name).

### Details

No pseudocode needed — this is a procedural check, not a code change. The two possible outcomes and
their concrete actions are fully enumerated in Procedure steps 2-3 above.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Dependency grep | `grep -rn "disabled_reason" scripts/mcp_servers/` | run at merge time; branch per Procedure steps 2/3 above |
| Shape cross-check (if landed) | Compare real `/v1/tools` response field names against `mcp_tool_discovery.py`'s `_build_runtime_tool()` reads | names match, or code updated to match |
| Regression | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all pass in either branch (defaulting-only or defaulting + new integration test) |
