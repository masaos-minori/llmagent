# Implementation Procedure: Add Integration Test for Empty Result Repeat Guard

## Goal

Add an integration test for the new empty result repeat guard to verify its behavior at the integration boundary.

## Scope

- Modify `tests/integration/test_rag_llm_integration.py`: add new test function for empty result repeat detection.
- No other files modified in this document.

## Assumptions

- The test follows the same pattern as existing guard tests (`test_c07`, `test_c08`).
- The test uses mocked dependencies similar to `_make_guard_ctx()`.
- The test verifies both the trigger condition and the non-trigger condition.

## Design decisions

- Add a new test function `test_c11_tool_loop_guard_fires_on_empty_result_repeat()`.
- Use the same helper functions (`_make_guard_ctx`, `_tool_call`, `_message_with_calls`) as existing tests.
- Verify both the trigger condition (empty results repeated) and the non-trigger condition (non-empty results).

## Alternatives considered

1. **Use a separate test file**: Would isolate the new test but would fragment the guard tests across multiple files.
2. **Use a parameterized test**: Would allow testing multiple scenarios in one test but would reduce readability.
3. **Add to existing test_c07**: Would combine the tests but would make the test less focused.

## Implementation

### Target file
`tests/integration/test_rag_llm_integration.py`

### Procedure

1. Add `tool_empty_result_max_repeats` field to `_make_guard_ctx()`.
2. Add new test function `test_c11_tool_loop_guard_fires_on_empty_result_repeat()`.
3. Verify both the trigger condition and the non-trigger condition.

### Method

#### Update _make_guard_ctx()

```python
def _make_guard_ctx(
    *,
    dedup_max: int = 2,
    cycle_window: int = 0,
    retry_max: int = 0,
    empty_result_max: int = 0,
) -> MagicMock:
    """Return a minimal AgentContext mock for ToolLoopGuard tests."""
    ctx = MagicMock()
    ctx.cfg.tool.tool_dedup_max_repeats = dedup_max
    ctx.cfg.tool.tool_cycle_detect_window = cycle_window
    ctx.cfg.tool.tool_error_retry_max = retry_max
    ctx.cfg.tool.tool_empty_result_max_repeats = empty_result_max
    ctx.diagnostics = None
    return ctx
```

#### Add new test function

```python
# ── TC-C11: ToolLoopGuard fires on repeated empty tool result ─────────────────

def test_c11_tool_loop_guard_fires_on_empty_result_repeat():
    from agent.tool_loop_guard import ToolLoopGuard

    ctx = _make_guard_ctx(empty_result_max=2)
    guard = ToolLoopGuard(ctx)

    call = _tool_call("read_text_file", '{"path": "/etc/hosts"}')
    msg = _message_with_calls(call)

    seen_calls: dict[str, int] = {}
    round_fp: list[str] = []
    failed: set[str] = set()

    # First call — no guard (record_tool_result called after execution)
    # Simulate empty result by calling record_tool_result directly
    guard.record_tool_result("read_text_file", "")
    result1 = guard.check_empty_result_repeat(msg)
    assert result1 is None

    # Second call with same tool returning empty — empty result repeat fires
    guard.record_tool_result("read_text_file", "")
    result2 = guard.check_empty_result_repeat(msg)
    assert result2 is not None
    assert "empty" in result2.lower() or "Empty" in result2

    # Third call with non-empty result — counter resets
    guard.record_tool_result("read_text_file", "some content")
    result3 = guard.check_empty_result_repeat(msg)
    assert result3 is None
```

### Details

- Added `tool_empty_result_max_repeats` field to `_make_guard_ctx()`.
- Added new test function `test_c11_tool_loop_guard_fires_on_empty_result_repeat()`.
- Verified both the trigger condition (empty results repeated) and the non-trigger condition (non-empty results).
- Used the same helper functions as existing tests for consistency.

## Compatibility considerations

- Adding a new test does not change the codebase behavior.
- The new test should follow the same pattern as existing tests for consistency.
- The test should be deterministic and reproducible.

## Security considerations

- No security impact. This change only affects testing.

## Rollback considerations

- Revert: remove the new test function and the updated `_make_guard_ctx()` function.
- No migration needed since the default `None` value ensures backward compatibility.

## Validation plan

1. Run the new test to verify it passes.
2. Run all existing tests to ensure no regressions.
3. Verify the test covers both the trigger condition and the non-trigger condition.

## Completion criteria

- [ ] New test function is added to the test file.
- [ ] Test verifies both the trigger condition and the non-trigger condition.
- [ ] Test follows the same pattern as existing tests.
- [ ] All tests pass when run.

## Out of scope

- Implementing the guard logic itself (covered in `scripts/agent/tool_loop_guard.py`).
- Adding the config field (covered in `scripts/agent/config_dataclasses.py`).
- Wiring tool results into guard state (covered in `scripts/agent/tool_runner.py`).
- Updating documentation (covered in respective documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 (Detect repeated empty tool results within a single turn)
- **Source issue**: issues/done/20260908-194034_toolloop002_detect-empty-tool-result-repetition.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-221112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-181137
- **Related target files**: tests/integration/test_rag_llm_integration.py
