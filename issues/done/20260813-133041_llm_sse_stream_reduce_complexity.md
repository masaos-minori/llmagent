# Reduce `LlmSseStreamHandler.stream_once` cyclomatic complexity (radon C→B)

## Priority
Medium

## Summary
`stream_once` in `scripts/shared/llm_sse_stream.py` has radon cyclomatic complexity grade C
(score 12), the highest in this module. Extracting its per-chunk read/parse/finish-reason loop
body into a helper would reduce this, but was not attempted during the file's general
refactor cycle because it touches core SSE read/parse/break control flow.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/llm_sse_stream.py`
(2026-08-13). Deliberately not attempted in that cycle because subtle reordering of the
`is_done`/`finish_reason`/`break` interactions could change premature-EOF or
double-exhaustion semantics — exactly the kind of change the task's "do not change
streaming/timeout/heartbeat behavior even incidentally" constraint forbids doing incidentally.

## Implementation Intent
Extract the per-chunk processing loop body into a well-named private helper, preserving:
- the exact order of `is_done` / `finish_reason` checks
- the exact conditions under which the loop `break`s
- the exact heartbeat-timeout and premature-EOF exception-raising conditions

This requires its own dedicated behavior-lock cycle (new characterization tests specifically
targeting exhaustion/finish_reason edge cases) before any transformation, per
`skills/python-refactoring/workflow.md` Phase 2.

## Target Files or Areas
- `scripts/shared/llm_sse_stream.py` (`LlmSseStreamHandler.stream_once`)
- `tests/shared/test_llm_sse_stream.py`

## Required Changes
- Add characterization tests pinning current exhaustion/finish_reason/premature-EOF behavior
  before any extraction.
- Extract the per-chunk loop body into a private helper with an explicit contract (documented
  inputs/outputs, including what triggers early exit).
- Re-run mutation testing (once `mutmut` is configured for this project) scoped to the extracted
  path, per the original proposal.

## Acceptance Criteria
- `radon cc` grade for `stream_once` improves from C to B or better.
- All existing + new characterization tests pass, with 0 surviving mutants on the extracted
  path once mutation testing tooling is available.
- No change to heartbeat timeout, premature-EOF, or finish_reason handling behavior.

## Testing Expectations
Full existing 24-test `tests/shared/test_llm_sse_stream.py` suite plus new characterization
tests for exhaustion/finish_reason edge cases; diff-cover ≥90% on changed lines.

## Documentation Impact
None expected unless the extracted helper's contract should be documented for future
maintainers (a short docstring is sufficient — no external docs impact).

## Out of Scope
- Do not change heartbeat timeout values, retry classification, or any behavior in
  `llm_reconnect.py`/`llm_retry.py` that consumes this handler's output.

## AI Implementation Instruction
Do not start extraction without first writing characterization tests for every exhaustion/
finish_reason/premature-EOF combination. If `mutmut` is still unconfigured when this issue is
picked up, fall back to manual branch review per `skills/DESIGN.md` §Tool availability guard and
document that fallback explicitly in the resulting report.
