## Goal

Remove the deprecated `TestResolveRetryable` test class from `tests/shared/test_llm_transport_errors.py` after the deprecation grace period has expired.

## Scope

**In-Scope:**
- Remove `TestResolveRetryable` test class from `tests/shared/test_llm_transport_errors.py`
- Verify no other tests reference `LlmTransportErrorHandler.resolve_retryable()`
- Run targeted tests to confirm no regressions

**Out-of-Scope:**
- Removal of `TestResolveRetryable` in `tests/shared/test_llm_reconnect.py` — handled in separate implementation procedure document.
- Changes to `LlmReconnectHandler.resolve_retryable()` or its tests.

## Assumptions

- The deprecation warning added in Phase 1 (`plans/20260813-190710_plan.md`) has been in place long enough for consumers to migrate.
- Zero production callers of `LlmTransportErrorHandler.resolve_retryable()` exist (confirmed via grep).
- No other tests in this file depend on `LlmTransportErrorHandler.resolve_retryable()`.

## Design decisions

- Direct removal without deprecation — the grace period has expired per the original require.
- No migration path needed since zero callers exist.

## Alternatives considered

- Keep the test class but remove the deprecation warning — rejected because the method being tested is dead code with no callers.
- Deprecate again with a longer grace period — rejected because the original Phase 1 deprecation already provided sufficient notice.

## Implementation

### Target file

`tests/shared/test_llm_transport_errors.py`

### Procedure

1. Locate the section header comment `# ── resolve_retryable ──` (line ~95).
2. Remove the entire section including:
   - Section header comment (line 95)
   - Blank lines between sections (lines 96-97)
   - `class TestResolveRetryable:` definition and all its methods (lines 98-167)
3. Preserve the preceding section's closing structure.
4. Ensure no trailing blank-line artifacts remain.

### Method

Edit — delete section block.

### Details

- Current line range: approximately 95-167 (section header through end of file).
- The section contains 5 test methods:
  - `test_heartbeat_timeout_uses_flag_and_increments_counter`
  - `test_heartbeat_timeout_flag_false_still_increments_counter`
  - `test_malformed_sse_frame_uses_flag_without_touching_counter`
  - `test_other_kind_uses_original_retryable_without_touching_counter`
  - `test_resolve_retryable_emits_deprecation_warning`
- All methods use `pytest.warns(DeprecationWarning)` — these are tests for the deprecated method being removed.
- After removal, ensure the last method of the preceding section maintains proper indentation.
- Check for any trailing blank lines between sections — collapse to single blank line.

## Compatibility considerations

- None — zero callers exist in production or test code.
- Tests for `LlmReconnectHandler.resolve_retryable` remain in `tests/shared/test_llm_reconnect.py`.

## Security considerations

N/A — removing dead test code does not introduce security risks.

## Rollback considerations

- Simple git revert of the change restores the test class.
- No database migrations or config changes involved.

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_llm_transport_errors.py` | Unit — confirm test class removed | `rg "class TestResolveRetryable" tests/shared/test_llm_transport_errors.py` | No output (class gone) |
| Project-wide | Integration — no regressions | `uv run pytest` | All tests pass |

## Out of scope

- Removal of `LlmTransportErrorHandler.resolve_retryable()` method — handled in separate implementation procedure document.
- Removal of `TestResolveRetryable` in `tests/shared/test_llm_reconnect.py` — out of scope per plan.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260814-222355_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-231156
- Related target files: test_llm_transport_errors.py
