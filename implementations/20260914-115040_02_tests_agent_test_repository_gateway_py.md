## Goal

Add unit tests for write rejection behavior when `pending_approval_id` is not None,
and regression test for normal execution when it is None. Per REQ-001, REQ-003.

## Scope

- Add two new test methods to `tests/agent/test_repository_gateway.py`:
  - `test_gate_write_rejects_when_approval_pending` — verify write operations are rejected
  - `test_gate_write_allows_when_no_pending_approval` — verify normal execution works
- Use existing `_make_ctx()` fixture as base; override `pending_approval_id` as needed

## Assumptions

- The `_denied_result` helper returns a `ToolCallResult` with `is_error=True` and
  a descriptive `output` string containing the denial reason
- The existing `_make_ctx()` and `_make_gateway()` fixtures in the test file can be used
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Create test subclass or override method to set `pending_approval_id` on the context
- Use `pytest.mark.asyncio` for async test methods
- Assert on both `result.is_error` and `result.output` content for completeness

## Alternatives considered

- Creating a separate test class for pending approval scenarios: rejected — adding
  methods to existing classes keeps related tests together
- Using `patch.object()` to modify `ctx.turn.pending_approval_id`: rejected — creating
  a modified context object is clearer and avoids patching side effects

## Implementation

### Target file

`tests/agent/test_repository_gateway.py`

### Procedure

1. **Add `test_gate_write_rejects_when_approval_pending`** — verify write operations
   are rejected when `pending_approval_id` is not None

2. **Add `test_gate_write_allows_when_no_pending_approval`** — verify normal execution
   works when `pending_approval_id` is None

### Method

1. Read `test_repository_gateway.py` to identify the correct location for new tests
2. Add the first test method under `TestWritePolicy` class
3. Add the second test method under `TestWritePolicy` class
4. Run the tests to verify they pass

### Details

**Step 1 — Add rejection test:**

Location: Add after the existing `test_write_tool_approved_and_executed` method
in the `TestWritePolicy` class (after line 102).

```python
@pytest.mark.asyncio
async def test_gate_write_rejects_when_approval_pending(self) -> None:
    """Write tool rejected when pending_approval_id is not None."""
    executor = AsyncMock(return_value=MagicMock(is_error=False))
    gw = _make_gateway(executor=executor)
    ctx = _make_ctx()
    ctx.turn.pending_approval_id = "approval-123"

    with (
        patch(
            "agent.repository_gateway.classify_operation_type",
            return_value=OperationType.WRITE,
        ),
        patch("agent.repository_gateway.check_preflight"),
    ):
        result = await gw.execute(
            ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"}
        )

    assert result.is_error is True
    assert "Approval pending" in result.output
    assert "/approve" in result.output
    executor.execute.assert_not_awaited()
```

**Step 2 — Add regression test:**

Location: Add after the rejection test (above).

```python
@pytest.mark.asyncio
async def test_gate_write_allows_when_no_pending_approval(self) -> None:
    """Write tool allowed when pending_approval_id is None."""
    expected = MagicMock(is_error=False, output="written")
    executor = AsyncMock(return_value=expected)
    gw = _make_gateway(executor=executor)
    ctx = _make_ctx()
    # pending_approval_id is None by default via _make_ctx()

    with (
        patch(
            "agent.repository_gateway.classify_operation_type",
            return_value=OperationType.WRITE,
        ),
        patch("agent.repository_gateway.check_preflight"),
    ):
        result = await gw.execute(
            ctx, "write_file", {"path": "/tmp/x.txt", "content": "ok"}
        )

    assert result is expected
    executor.execute.assert_awaited_once_with("write_file", {"path": "/tmp/x.txt", "content": "ok"})
```

## Compatibility considerations

- Test-only change: no production code affected
- New tests add coverage for previously untested paths
- Existing tests remain unchanged — no regression expected

## Security considerations

N/A: test code change, no security-sensitive operations.

## Rollback considerations

- Revert the two test method additions to restore original test suite
- No data loss risk — only test code changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/test_repository_gateway.py | Verify new test passes | uv run pytest tests/agent/test_repository_gateway.py::TestWritePolicy::test_gate_write_rejects_when_approval_pending -x -q | Test passes |
| tests/agent/test_repository_gateway.py | Verify regression test passes | uv run pytest tests/agent/test_repository_gateway.py::TestWritePolicy::test_gate_write_allows_when_no_pending_approval -x -q | Test passes |
| tests/agent/test_repository_gateway.py | Regression: all existing tests still pass | uv run pytest tests/agent/test_repository_gateway.py -x -q | All tests pass |

## Completion criteria

- [ ] `test_gate_write_rejects_when_approval_pending` added and passing
- [ ] `test_gate_write_allows_when_no_pending_approval` added and passing
- [ ] Both assertions check `result.is_error` and `result.output` content
- [ ] Existing tests continue to pass without modification
- [ ] Pending approval ID value ("approval-123") visible in test for debugging

## Out of scope

- Integration test covering full approval flow (request → approve → execute)
- Modifying existing tests
- Adding tests for read-only tools (should not be affected)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | This step |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-003
- **Source issue**: issues/20260913-172700_repository_gateway_preflight_skip.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-224241_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-115040
- **Related target files**: tests/agent/test_repository_gateway.py
