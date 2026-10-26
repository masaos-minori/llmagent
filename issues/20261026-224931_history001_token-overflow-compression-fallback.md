# Apply fallback truncation on token-only compression overflow failure

## Priority
Medium

## Summary
History compression falls back to truncation only when the character limit is
exceeded. When only the token limit is exceeded and the summarizer LLM fails, the
oversized history is returned unchanged and sent to the backend. Extend the
fallback to the token-only overflow case.

## Background
From a python-code-review pass over the REPL turn path (finding F-006). Evidence
(Explicit in code) in `scripts/agent/history.py`:
- `compress()` triggers on either char or token overflow.
- When summarization returns `None`, `_fallback_truncate` is applied only if
  `_is_over_char_limit` is true; a token-only overflow returns the unchanged
  history with `error="compression returned None"`.
- `scripts/agent/orchestrator.py` then proceeds to the backend call with the
  still-oversized history.

## Problem
With the summarizer failing (backend down for summary, timeout) and the token limit
exceeded, every subsequent turn fails with a backend context-length error, and the
history never gets smaller — a repeating failure state with no recovery path short
of `/clear`.

## Reason for Change
The char-limit path already has a truncation fallback; the token path's gap turns a
one-off summarizer failure into a persistent session-level failure.

## Implementation Intent
Make the fallback decision depend on "history is over a hard limit", not on which
limit was exceeded: when summarization is unavailable and any hard limit is
exceeded, apply the existing unit-drop fallback (`_fallback_truncate`) so token
overflow also converges. Keep the existing protected-turns/never-orphan-a-tool-row
guarantees of the fallback.

## Target Files or Areas
- `scripts/agent/history.py` (`compress`, `_fallback_truncate` gating)
- `scripts/agent/orchestrator.py` (post-compression turn path)

## Required Changes
- Apply `_fallback_truncate` (or a token-aware equivalent) when token-only overflow
  coincides with summarizer failure.
- Report the fallback in the `CompressResult` as it is today for char overflow.
- Add a regression test for the token-only + summarizer-failure state.

## Constraints
- The fallback must keep dropping whole turn units and must never orphan a tool row
  (existing invariant).
- Token estimation is approximate; the fallback does not need to guarantee
  sub-limit size, only progress toward it (same tolerance as the char path).

## Acceptance Criteria
- Test: token-only overflow + summarizer returns None → history is shortened via
  fallback and `CompressResult.is_fallback` is set.
- Repeated turns in that state keep the history bounded (no permanent failure).
- Existing compression/fallback tests pass unchanged.

## Testing Expectations
- Unit test for the token-only failure branch (mock summarizer returning None).
- Unit test asserting tool-row integrity after token-path fallback.
- `mypy`/`ruff` pass.

## Documentation Impact
Update the history-compression docs to describe both overflow triggers (char, token)
and the fallback behavior when summarization is unavailable (failure behavior).

## Out of Scope
- Improving token estimation accuracy.
- Changing summarizer retry/timeout policy.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether token overflow should reuse the char-limit unit-drop fallback directly or
  a token-budgeted variant — a design choice for the plan stage.

## AI Implementation Instruction
Change only the fallback gating in `history.py` and its reporting; do not alter
selection policy, protected-turn handling, or the summarizer call. Preserve the
no-orphan-tool-row invariant of `_fallback_truncate`.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-224931
- **Related target files**: `scripts/agent/history.py`, `scripts/agent/orchestrator.py`
