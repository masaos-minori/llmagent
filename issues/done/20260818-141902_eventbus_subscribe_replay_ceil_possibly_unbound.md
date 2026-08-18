# pyright reports `replay_ceil` as possibly unbound in `subscribe_route.py`'s cancellation log

## Priority
Medium

## Summary
`uv run pyright scripts/` reports one error in `scripts/eventbus/subscribe_route.py`:
`"replay_ceil" is possibly unbound (reportPossiblyUnboundVariable)` at the log call inside the
`except asyncio.CancelledError` handler. `mypy` and `ruff` do not flag this; only `pyright` does.
Implementation is not attempted here — see AGENTS.md Global Rule 8 (eventbus implementation is
forbidden without explicit sign-off; debug/investigation only).

## Reason for Change
`rules/toolchain.md` lists `pyright` as the cross-validation type checker alongside `mypy`, and
the completion checklist expects a clean run. A non-zero pyright error count on `scripts/`
is a CI-consistency gap even though the underlying runtime behavior is currently safe (see
below), and it should either be fixed or explicitly tracked rather than left as a silent
outstanding error.

## Investigation Findings (Evidence: Explicit in code / Confidence: High)
`scripts/eventbus/subscribe_route.py` (function generating the SSE stream, around lines 61-83):

- `replay_ceil = start_seq` is assigned only after `rows = await run_with_db_lock(_fetch_replay)`
  succeeds (line 61-62).
- If `asyncio.CancelledError` is raised before that assignment executes, `replay_ceil` does not
  exist as a local yet.
- The `except asyncio.CancelledError` handler already guards this at runtime with
  `replay_ceil if locals().get("replay_ceil") is not None else start_seq` (line 82), which is
  correct at runtime — `locals()` is evaluated dynamically and safely detects the unbound case.
- `pyright`'s static analyzer does not understand the `locals().get(...)` guard, so it still
  flags the direct `replay_ceil` reference in the ternary's true-branch as possibly unbound.
- `mypy` does not raise this error (no equivalent unbound-variable flow check for this pattern in
  the current mypy config); `ruff check` is also clean.
- Functional risk is effectively none: the guard produces the correct value (`start_seq`) in the
  edge case where cancellation happens before any replay row is read. This is a static-analysis
  false positive, not a runtime bug.

## Implementation Intent
The likely root-cause fix is to initialize `replay_ceil = start_seq` before the `try`/`await
run_with_db_lock(_fetch_replay)` block (or immediately after `start_seq` is known), so the name
is always bound and the `locals().get(...)` guard in the except handler can be simplified to a
plain `replay_ceil` reference. This is a minimal, behavior-preserving change (the initial value
is already `start_seq` in the unbound case), but it touches `scripts/eventbus/` logic and
therefore requires explicit maintainer sign-off per AGENTS.md Global Rule 8 before any code is
changed.

## Target Files or Areas
- `scripts/eventbus/subscribe_route.py` (the SSE `_sse_gen()` generator, replay/live-delivery
  section)

## Required Changes
- Move/add `replay_ceil = start_seq` initialization before the code path that can raise
  `CancelledError`.
- Simplify the except-handler log call to reference `replay_ceil` directly once it is always
  bound (remove the `locals().get(...)` workaround).
- Re-run `uv run pyright scripts/eventbus/subscribe_route.py` to confirm the error is gone.

## Acceptance Criteria
- `uv run pyright scripts/` reports 0 errors for `scripts/eventbus/subscribe_route.py`.
- `uv run mypy scripts/` and `uv run ruff check scripts/` remain clean (no regressions).
- Existing eventbus/subscribe tests pass unchanged; the logged `seq` value in the
  `CancelledError` branch is unchanged for both the "replay happened" and "cancelled before any
  replay row" cases.

## Testing Expectations
- `uv run pyright scripts/eventbus/subscribe_route.py`
- `uv run mypy scripts/`
- `uv run ruff check scripts/`
- Targeted `pytest` run for the eventbus subscribe/SSE test module (locate via
  `rg -l subscribe_route tests/`) to confirm no behavior change in the cancellation-logging path.

## Documentation Impact
None expected — this is an internal static-analysis/type-safety fix with no observable API or
behavior change.

## Out of Scope
- Do not change replay/live-delivery semantics, SSE payload format, or the broker
  subscribe/unsubscribe lifecycle.
- Do not touch any other eventbus module beyond the minimal initialization/log-call change
  described above.
- Do not implement this issue without the explicit sign-off required by AGENTS.md Global Rule 8
  for eventbus-related implementation work.

## AI Implementation Instruction
This is eventbus-related implementation and is forbidden by AGENTS.md Global Rule 8 without
explicit maintainer sign-off recorded per `rules/coding.md` §Explicit sign-off gates (e.g. a
comment on this issue). Do not implement until that sign-off exists. Once sign-off is granted,
keep the change to the minimal initialization/log-call simplification described above — do not
refactor surrounding replay or live-delivery logic.
