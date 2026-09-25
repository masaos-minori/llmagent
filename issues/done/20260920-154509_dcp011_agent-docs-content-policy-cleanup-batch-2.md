# Agent docs content policy cleanup (batch 2)

## Priority
Medium

## Summary
Remove the two mechanically-derivable tables flagged by
`tools/check_docs_content_policy.py` (`GV-021`) in
`docs/agent_05_llm-and-streaming.md` — a partial-completion-persistence table and an
`LLMTransportError` kind-classification table — per `skills/DESIGN.md` Docs content
policy — remove/retain. Three other Agent findings from the same tool run
(`agent_06_02.md:46`/`:117`, `agent_06_03.md:86`, `agent_10_05.md:114`) were
investigated and excluded — see Out of Scope.

## Background
`docscope1`/`docscope2` (see `issues/done/`) established the Docs content policy and the
`check_docs_content_policy.py` detection tool. A prior Agent cleanup batch
(`issues/done/20260805-102307_agent_05_llm-and-streaming_design-intent-cleanup.md` and
sibling `agent_*_design-intent-cleanup` issues) already addressed earlier findings in
this domain, but a fresh tool run today reports new findings in the same file — see
Problem.

## Problem
`uv run python tools/check_docs_content_policy.py` (run 2026-09-20) reports:
- `agent_05_llm-and-streaming.md:52` — error-handling table ("Partial Completion
  Persistence Rules": Case → Action for `partial_text` states and tool-execution failure)
- `agent_05_llm-and-streaming.md:62` — error-handling table ("Error Type Design":
  `LLMTransportError.kind` category → description)

Three further findings from the same tool run were investigated and are **not** in
scope of this issue — they are false positives against `skills/DESIGN.md` Docs content
policy — retain's "security boundary" / fail-safe-default category, not mechanical
restatement:
- `agent_06_02_tool-execution-and-approval-approval.md:46` and `:117`
- `agent_06_03_tool-execution-and-approval-concurrency-safety.md:86`

All three read "Fail-safe: Undefined tools in `tool_safety_tiers` default to
`WRITE_DANGEROUS`" inside a `## Key Constraints` section — this is exactly the
"security boundary / fail-closed-or-fail-open default judgment" content Docs content
policy — retain requires keeping, not a code-derivable value restatement. The tool's
`_DEFAULT_VALUE_RE` pattern (`` `x` defaults to `y` ``) matches the phrasing but its
`_RATIONALE_MARKERS` allowlist does not include "fail-safe"/"fail-closed", producing a
false positive — tracked as a tool-precision gap in a separate issue (see Dependencies).

`agent_10_05_operations-and-observability-monitoring.md:114` ("`workflow_count`,
`task_count`, ... default to 0 or an empty list if querying the workflow DB fails") was
also investigated: this states graceful-degradation behavior on a specific failure mode
(operational note / known limitation), which Docs content policy — retain also protects.
Excluded from this issue for the same reason.

## Reason for Change
Both in-scope tables restate `kind`/action values that are directly readable from the
orchestrator's transport-error-handling code and the `LLMTransportError` enum — per
`docs/00_governance_01_documentation-policy.md` Claim Type Taxonomy, a `runtime-behavior`
claim whose canonical source is the implementation, not the design document. They will
drift the moment a new error kind or persistence rule is added without a corresponding
doc edit.

## Implementation Intent
Apply `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content
policy — remove: replace each table with a pointer to the source (the orchestrator's
transport error handler for the persistence-rules table; the `LLMTransportError` kind
enum/classification function for the error-type table). Retain any surrounding prose
that states *why* a given case is handled a certain way, if present — none was found
directly attached to these two tables during investigation, so both are pure listing
removals.

## Target Files or Areas
- `docs/agent_05_llm-and-streaming.md`

## Required Changes
1. Replace the "Partial Completion Persistence Rules" table (lines ~48-56) with a short
   pointer to the orchestrator's transport error handler as the canonical source for the
   exact case/action mapping.
2. Replace the "Error Type Design" table (lines ~58-69) with a short pointer to the
   `LLMTransportError.kind` enum/classification as the canonical source for the exact
   category list.
3. Re-run `uv run python tools/check_docs_content_policy.py` and confirm zero findings
   for this file.

## Constraints
- Do not alter any other content in this file beyond the two flagged tables and their
  immediately surrounding prose (e.g. the `RobustSSEParser`/`LlmSseHelpers` sentence
  above them stays untouched).
- Do not touch `agent_06_02.md`, `agent_06_03.md`, or `agent_10_05.md` — see Out
  of Scope.

## Acceptance Criteria
- `uv run python tools/check_docs_content_policy.py` reports zero findings for
  `docs/agent_05_llm-and-streaming.md`.
- The section still reads coherently and points to the owning source instead of
  restating the case/category list.
- `uv run python tools/check_docs_structure.py docs/agent_05_llm-and-streaming.md`
  passes.

## Testing Expectations
Documentation-only change. Run `uv run python tools/check_docs_content_policy.py`,
`uv run python tools/check_docs_quality.py`,
`uv run python tools/check_docs_structure.py docs/agent_05_llm-and-streaming.md`, and
`uv run python tools/check_docs_consistency.py --domain agent`. No `pytest`/`mypy`/`ruff`
run required.

## Documentation Impact
Yes — this issue is itself a documentation cleanup, scoped to one file.

## Out of Scope
- `agent_06_02_tool-execution-and-approval-approval.md` (`:46`, `:117`),
  `agent_06_03_tool-execution-and-approval-concurrency-safety.md` (`:86`) — investigated
  and excluded as Docs content policy — retain security-boundary content (see Problem);
  do not remove the "Fail-safe: Undefined tools ... default to `WRITE_DANGEROUS`"
  sentences in this issue or any follow-up to it.
- `agent_10_05_operations-and-observability-monitoring.md:114` — investigated and
  excluded as an operational/known-limitation note (see Problem).
- Fixing `check_docs_content_policy.py`'s `_RATIONALE_MARKERS` false-positive gap itself
  — tracked as a separate tool-precision issue (see Dependencies), not implemented here.

## Dependencies
A follow-up issue should extend `tools/check_docs_content_policy.py`'s
`_RATIONALE_MARKERS` (or an equivalent allowlist) to recognize "fail-safe"/"fail-closed"/
"fail-open" so the three excluded findings above stop appearing as warnings on future
runs. Not filed as part of this issue since it changes `tools/`, not `docs/`, and has a
different acceptance criterion (tool behavior, not doc content).

## Unresolved Questions
N/A: none — both in-scope findings and all three exclusions were confirmed by a direct
tool run and file read on 2026-09-20.

## AI Implementation Instruction
Edit only `docs/agent_05_llm-and-streaming.md`. Replace the two flagged tables with
canonical-source pointers per Required Changes; do not touch any other file, and do not
remove the fail-safe/default-on-failure sentences in the three excluded files listed in
Out of Scope — those are confirmed design-intent content, not findings to fix.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260920-154509
- **Related target files**: see Target Files or Areas above
