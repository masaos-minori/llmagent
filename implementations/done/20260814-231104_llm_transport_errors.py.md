## Goal

Remove the deprecated `LlmTransportErrorHandler.resolve_retryable()` method from `scripts/shared/llm_transport_errors.py` after the deprecation grace period has expired.

## Scope

**In-Scope:**
- Remove `resolve_retryable()` method from `LlmTransportErrorHandler` class in `scripts/shared/llm_transport_errors.py`
- Verify zero callers remain across the codebase
- Run targeted tests to confirm no regressions

**Out-of-Scope:**
- Changes to `LlmReconnectHandler.resolve_retryable()` — its equivalent method remains unchanged
- Changes to `tests/shared/test_llm_reconnect.py` — tests for `LlmReconnectHandler.resolve_retryable` remain unchanged
- Any behavioral changes to `LlmReconnectHandler._evaluate_stream_error()`

## Assumptions

- The deprecation warning added in Phase 1 (`plans/20260813-190710_plan.md`) has been in place long enough for consumers to migrate.
- Zero production callers of `LlmTransportErrorHandler.resolve_retryable()` exist (confirmed via grep).
- `LlmReconnectHandler.resolve_retryable()` provides equivalent functionality and is the intended replacement.

## Design decisions

- Direct removal without deprecation — the grace period has expired per the original require.
- No migration path needed since zero callers exist.

## Alternatives considered

- Keep the method but remove the deprecation warning — rejected because the method is dead code with no callers.
- Deprecate again with a longer grace period — rejected because the original Phase 1 deprecation already provided sufficient notice.

## Implementation

### Target file

`scripts/shared/llm_transport_errors.py`

### Procedure

1. Locate `def resolve_retryable(self, ...)` in `LlmTransportErrorHandler` class.
2. Remove the entire method body including docstring, type hints, deprecation warning, and all code.
3. Preserve surrounding class structure and indentation.
4. Verify no blank-line artifacts remain.

### Method

Edit — delete method block.

### Details

- The method signature is: `def resolve_retryable(self, e: LLMTransportError, heartbeat_timeout_retry: bool, malformed_chunk_retry: bool, heartbeat_timeout_counter: int,) -> tuple[bool, int]:`
- The method body contains:
  - A docstring describing the method's purpose
  - A deprecation warning via `warnings.warn(...)`
  - Three conditional branches (`if/elif`) returning `(bool, int)` tuples
- After removal, ensure the next method in the class maintains proper indentation.
- Check for any trailing blank lines between methods — collapse to single blank line.

## Compatibility considerations

- None — zero callers exist in production or test code.
- `LlmReconnectHandler.resolve_retryable()` remains as the replacement for consumers who previously relied on this method.

## Security considerations

N/A — removing dead code does not introduce security risks.

## Rollback considerations

- Simple git revert of the change restores the method.
- No database migrations or config changes involved.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `scripts/shared/llm_transport_errors.py` | Unit — confirm method removed | `rg "def resolve_retryable" scripts/shared/llm_transport_errors.py` | No output (method gone) |
| Project-wide | Integration — no regressions | `uv run pytest` | All tests pass |

## Out of scope

- Removal of `LlmReconnectHandler.resolve_retryable()` — out of scope per plan.
- Removal of `TestResolveRetryable` in `tests/shared/test_llm_transport_errors.py` — handled in separate implementation procedure document.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260814-222355_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-231104
- Related target files: llm_transport_errors.py
