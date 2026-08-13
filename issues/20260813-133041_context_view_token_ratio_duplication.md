# Consolidate duplicated ratio-based token-estimation logic in `context_view.py` with `shared/token_estimation.py`

## Priority
Medium

## Summary
`scripts/agent/services/context_view.py` defines its own private `_RATIO_TEXT`/
`_RATIO_TOOL_CALL`/`_RATIO_SYSTEM` constants and inline arithmetic that duplicate
`scripts/shared/token_estimation.py`'s `RATIO_TEXT`/`RATIO_TOOL_CALL`/`RATIO_SYSTEM` constants
and its `estimate_tokens_for_text`/`estimate_tokens_for_assistant_with_tool_calls` functions.

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/token_estimation.py`
(2026-08-13). Not touched there because `context_view.py` is outside `scripts/shared/` and the
cycle's scope was limited to one file at a time (Evidence label: Explicit in code — both
modules' ratio constants and arithmetic were compared directly). Two independently-maintained
copies of the same token-estimation formula risk silently diverging (e.g. a future ratio tuning
applied to one but not the other).

## Implementation Intent
Export the shared ratio constants and/or helper functions from `scripts/shared/token_estimation.py`
for reuse by `context_view.py`, removing the duplicate private constants and inline arithmetic
there. This should be a pure consolidation — the two implementations must currently produce
identical results for identical inputs; confirm this before merging (if they've already
diverged, that divergence itself may be a separate correctness bug worth flagging).

## Target Files or Areas
- `scripts/agent/services/context_view.py`
- `scripts/shared/token_estimation.py`

## Required Changes
- Compare both implementations' current output for representative inputs to confirm they are
  equivalent before merging (if not equivalent, stop and report the discrepancy instead of
  silently picking one).
- Have `context_view.py` import and use `scripts/shared/token_estimation.py`'s constants/
  functions instead of its own private copies.
- Remove the now-redundant private constants/arithmetic from `context_view.py`.

## Acceptance Criteria
- `context_view.py` no longer defines its own ratio constants; it imports from
  `shared.token_estimation`.
- Token-estimation output for `context_view.py`'s existing test cases is unchanged (or, if a
  pre-existing divergence is found, it is documented and resolved with explicit approval before
  merging).

## Testing Expectations
Full test suite for `context_view.py` and `token_estimation.py`'s consumers before/after;
`diff-cover` on both changed files.

## Documentation Impact
None expected unless the consolidation changes a documented public contract of either module.

## Out of Scope
- Do not change the ratio values themselves as part of this consolidation — that would be a
  behavior change requiring separate justification.
- Do not touch `context_view.py`'s other responsibilities beyond the token-ratio duplication.

## AI Implementation Instruction
Before merging, write a small comparison script or test computing both implementations' output
for the same set of representative messages/tool-calls; if outputs differ for any input, stop
and report the discrepancy rather than assuming one is authoritative. This file was not part of
the `scripts/shared/` refactor rollout that discovered this issue, so re-verify current state
before implementing (it may have changed since 2026-08-13).
