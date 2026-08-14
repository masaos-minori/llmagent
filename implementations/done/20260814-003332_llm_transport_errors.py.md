# Implementation: Add DeprecationWarning to `LlmTransportErrorHandler.resolve_retryable`

## Goal

Mark the dead `LlmTransportErrorHandler.resolve_retryable` static method
(`scripts/shared/llm_transport_errors.py:60-74`) as deprecated by emitting a `DeprecationWarning`
at call time, pointing callers to the live equivalent `LlmReconnectHandler.resolve_retryable`
(`scripts/shared/llm_reconnect.py`). No behavioral change to the method's return value, signature,
or branch logic.

## Scope

**Target**: `scripts/shared/llm_transport_errors.py`

**In scope**:
- Add `import warnings` to the module's import block.
- Insert one `warnings.warn(...)` call as the first statement inside `resolve_retryable`'s body.

**Out of scope** (per plan `plans/done/20260813-190710_plan.md`):
- Removing the method or its test class (deferred to a future grace-period-gated removal change —
  see plan Unknown UNK-01).
- Any change to `raise_http_status_error` or `translate_stream_error` in this same file.
- Any change to `LlmReconnectHandler.resolve_retryable` / `_evaluate_stream_error`
  (`scripts/shared/llm_reconnect.py`) — the cross-file consolidation sub-task is explicitly gated
  behind sign-off not yet obtained (plan Unknown UNK-02) and is documented, not implemented.
- Any `docs/*.md` edit — the plan's Design section confirms no doc describes
  `resolve_retryable`'s internals.

## Assumptions

- `LlmTransportErrorHandler.resolve_retryable` still has zero production callers at implementation
  time. Re-verify immediately before editing with `rg -n "resolve_retryable" scripts/ tests/` and
  `rg -n "LlmTransportErrorHandler" scripts/` — if a new caller has appeared, stop and re-scope
  rather than proceeding.
- The project's pytest configuration does not turn warnings into errors (no `-W error` /
  `filterwarnings = ["error"]` in `pyproject.toml`), so adding a `DeprecationWarning` will not break
  unrelated tests that call this method incidentally.

## Design decisions

- Warn at the top of the method body (before the existing `if e.kind == "HEARTBEAT_TIMEOUT":`
  branch) so the warning fires on every call regardless of which branch is taken.
- Use `stacklevel=2` so the warning attributes to the caller's line, not to the line inside
  `resolve_retryable` itself — standard practice for library-level deprecation warnings.
- Name the live replacement (`LlmReconnectHandler.resolve_retryable`) explicitly in the warning
  message so a future contributor sees the migration path without needing to consult this doc or
  the plan.

## Alternatives considered

N/A — the plan specifies the exact mechanism (`warnings.warn(..., DeprecationWarning,
stacklevel=2)`) and insertion point; no alternative mechanism (e.g. a decorator, `@deprecated` from
a third-party library) was considered since the requirement calls for a minimal, dependency-free
change.

## Implementation

**Target file**: `scripts/shared/llm_transport_errors.py`

**Procedure**:
1. Add `import warnings` to the top-level import block (after `import httpx`, before the blank
   line preceding `from shared.llm_exceptions import LLMTransportError`, keeping stdlib imports
   ordered before first-party imports per the file's existing style).
2. Insert the `warnings.warn(...)` call as the first line of `resolve_retryable`'s body, before the
   existing docstring's described branch logic executes.

**Method**: `LlmTransportErrorHandler.resolve_retryable` (static method, current signature at
lines 60-65):
```python
@staticmethod
def resolve_retryable(
    e: LLMTransportError,
    heartbeat_timeout_retry: bool,
    malformed_chunk_retry: bool,
    heartbeat_timeout_counter: int,
) -> tuple[bool, int]:
```

**Details grounded in real code** (current body, lines 66-74):
```python
    """Return (effective_retryable, updated_heartbeat_timeout_counter).

    Increments heartbeat timeout counter when e.kind == 'HEARTBEAT_TIMEOUT'.
    """
    if e.kind == "HEARTBEAT_TIMEOUT":
        return heartbeat_timeout_retry, heartbeat_timeout_counter + 1
    if e.kind == "MALFORMED_SSE_FRAME":
        return malformed_chunk_retry, heartbeat_timeout_counter
    return e.retryable, heartbeat_timeout_counter
```

Target body after the change (docstring unchanged; warning inserted immediately after it, before
the first `if`):
```python
    """Return (effective_retryable, updated_heartbeat_timeout_counter).

    Increments heartbeat timeout counter when e.kind == 'HEARTBEAT_TIMEOUT'.
    """
    warnings.warn(
        "LlmTransportErrorHandler.resolve_retryable is deprecated and unused in "
        "production; use LlmReconnectHandler.resolve_retryable instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    if e.kind == "HEARTBEAT_TIMEOUT":
        return heartbeat_timeout_retry, heartbeat_timeout_counter + 1
    if e.kind == "MALFORMED_SSE_FRAME":
        return malformed_chunk_retry, heartbeat_timeout_counter
    return e.retryable, heartbeat_timeout_counter
```

Do not change `raise_http_status_error` (lines 16-27) or `translate_stream_error` (lines 29-57) —
only `resolve_retryable`'s body gains the warning; its three-branch return logic and signature stay
byte-for-byte identical.

## Compatibility considerations

- Return type (`tuple[bool, int]`) and all branch outcomes are unchanged — any caller reading the
  return value observes no behavioral difference.
- `DeprecationWarning` is filtered (ignored) by default in normal Python execution outside of
  `pytest` and `-W` contexts, so production behavior (there are currently zero production callers,
  per the plan's Affected-areas confirmation) is unaffected either way.
- Adding `import warnings` (stdlib) introduces no new dependency and no new import-boundary edge
  for `lint-imports` to flag.

## Security considerations

N/A — this is a diagnostic warning addition with no new external input, no change to
authentication/authorization/data handling, and no new dependency.

## Rollback considerations

Independently revertable: reverting this file's diff (removing the `import warnings` line and the
`warnings.warn(...)` call) restores `resolve_retryable` to its exact current behavior. No other
file needs to change for a clean rollback of this file alone (the paired test-file change in
`tests/shared/test_llm_transport_errors.py` is documented separately and must be reverted together
to keep the test suite green, but this file's revert is self-contained).

## Validation plan

Run, from the repo root:
```
uv run ruff format scripts/shared/llm_transport_errors.py && \
uv run ruff check scripts/shared/llm_transport_errors.py && \
uv run mypy scripts/shared/llm_transport_errors.py && \
uv run bandit scripts/shared/llm_transport_errors.py && \
uv run pytest tests/shared/test_llm_transport_errors.py -v
```
Expected: no new lint/type errors, bandit reports 0 issues, and all `TestResolveRetryable` cases
pass (paired with the corresponding test-file update) including the new warning-fires test.

## Out of scope

- Removing the method or its test class (future grace-period-gated change, blocked on UNK-01).
- The cross-file consolidation of `resolve_retryable`'s three-branch classification logic with
  `LlmReconnectHandler._evaluate_stream_error` (blocked on UNK-02 sign-off; design intent recorded
  in the plan's Design section only).
- Any change to `scripts/shared/llm_reconnect.py` or `scripts/shared/llm_sse_stream.py`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-190710_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-003332
- Related target files: llm_transport_errors.py
