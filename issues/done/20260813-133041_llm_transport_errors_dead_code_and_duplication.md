# `LlmTransportErrorHandler.resolve_retryable` appears unused; near-duplicate exists in `LlmReconnectHandler`

## Priority
Medium

## Summary
`LlmTransportErrorHandler.resolve_retryable` in `scripts/shared/llm_transport_errors.py` has
zero callers anywhere in `scripts/`/`tests/` (confirmed via `rg`). A near-duplicate
classification rule (`HEARTBEAT_TIMEOUT` / `MALFORMED_SSE_FRAME` / fallback) already exists and
is actively used as `LlmReconnectHandler._evaluate_stream_error` in
`scripts/shared/llm_reconnect.py` (already refactored in this rollout).

## Reason for Change
Found during a behavior-preserving refactor cycle on `scripts/shared/llm_transport_errors.py`
(2026-08-13). Not acted on there because (a) removing a public method — even apparently dead —
is a behavior/API-relevant change requiring its own deprecation window, and (b) consolidating
the two near-duplicate implementations across files is a genuine (if small) behavior-shape
unification, not a same-file pure extraction (Evidence label: Explicit in code — confirmed via
`rg "resolve_retryable"` showing zero external callers of this specific method).

## Implementation Intent
Two related but separable sub-tasks:
1. Confirm `LlmTransportErrorHandler.resolve_retryable` is genuinely dead code (re-run the
   repo-wide `rg` check), then deprecate it with `warnings.warn(..., DeprecationWarning)` for a
   grace period before removal, per this project's "retain deprecated aliases" convention
   (`skills/python-refactoring/SKILL.md`).
2. Evaluate consolidating this method with `LlmReconnectHandler`'s `_evaluate_stream_error` into
   one shared helper, reconciling the one structural difference: this file's version threads a
   `heartbeat_timeout_counter` through the return tuple, while `llm_reconnect.py`'s version
   returns a bare `bool` and increments the counter separately.

## Target Files or Areas
- `scripts/shared/llm_transport_errors.py` (`LlmTransportErrorHandler.resolve_retryable`)
- `scripts/shared/llm_reconnect.py` (`LlmReconnectHandler._evaluate_stream_error`)
- Their respective test files

## Required Changes
- Re-confirm zero callers of `resolve_retryable` before any change.
- Add a `DeprecationWarning` if keeping it temporarily, or proceed directly to consolidation if
  a maintainer confirms deprecation is unnecessary for genuinely-dead code.
- If consolidating: design one shared signature reconciling the counter-threading difference,
  update both call sites, and ensure full characterization-test parity between them before and
  after the merge.

## Acceptance Criteria
- No behavior change to `LlmReconnectHandler.stream`'s existing retry/heartbeat semantics.
- Either `resolve_retryable` is removed (after a deprecation window) or consolidated into a
  single shared helper used by both files, with identical externally-observable behavior.

## Testing Expectations
Full characterization-test parity between both call sites before/after any merge;
`tests/shared/test_llm_reconnect.py` and any test file covering `llm_transport_errors.py` must
pass unchanged in outcome. `diff-cover` on both files if a merge occurs.

## Documentation Impact
None expected — internal helper consolidation.

## Out of Scope
- Do not change `LlmReconnectHandler.stream`'s reconnect/backoff behavior as part of this
  cleanup.

## AI Implementation Instruction
Re-run `rg "resolve_retryable"` across the whole repo first — do not assume the earlier
finding is still accurate by the time this issue is picked up (code may have moved). Treat
sub-task 1 (deprecate/remove dead code) and sub-task 2 (cross-file consolidation) as
independently schedulable; sub-task 2 carries materially higher risk and should get its own
explicit sign-off before implementation, per the original proposal's classification as a
"genuine behavior-shape unification."
