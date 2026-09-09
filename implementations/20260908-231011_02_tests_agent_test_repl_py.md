## Goal

Add a verification test asserting that `KeyboardInterrupt` routes through `_abort_input()` in the `shutdown_event is not None` branch, confirming REQ-REPL001B-1 acceptance criterion.

## Scope

Modify only `tests/agent/test_repl.py` to add a test that verifies `KeyboardInterrupt` is properly handled in the `shutdown_event is not None` branch.

## Assumptions

- The existing `test_keyboard_interrupt_breaks_loop` test at line 162 exercises the `shutdown_event is not None` path (via `_make_bare_repl()`, which always sets `repl._shutdown_event = asyncio.Event()`).
- The test currently fails because `KeyboardInterrupt` propagates past the `except KeyboardInterrupt:` clause at line 154 of `scripts/agent/repl_input_loop.py`.
- After fixing the bug in Row 1, this test should pass.

## Design decisions

- Add assertions to `test_keyboard_interrupt_breaks_loop` to verify that `_abort_input()` was called (i.e., `_view.write_turn_end()` was called and `_input_coro` was cleared).
- This provides explicit verification of the fix rather than relying on the test passing silently.

## Alternatives considered

1. **Create a new test** — Would duplicate logic; better to enhance the existing test.
2. **Use monkeypatch to verify `_abort_input` calls** — More complex; simpler to check observable side effects.
3. **Add assertions to the existing test** — Best approach; minimal change, clear intent.

## Implementation

### Target file

`tests/agent/test_repl.py`

### Procedure

1. Enhance `test_keyboard_interrupt_breaks_loop` (line 162-167) to add assertions verifying `_abort_input()` behavior.
2. Verify that `_view.write_turn_end()` was called after `KeyboardInterrupt`.
3. Verify that `_input_coro` was cleared after `KeyboardInterrupt`.

### Method

Enhance the existing test:

```python
    @pytest.mark.asyncio
    async def test_keyboard_interrupt_breaks_loop(self) -> None:
        repl = _make_bare_repl()
        mock_banner = MagicMock()
        mock_persister = AsyncMock()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            await repl._input_loop.run(mock_banner, mock_persister)
```

Change to:

```python
    @pytest.mark.asyncio
    async def test_keyboard_interrupt_breaks_loop(self) -> None:
        repl = _make_bare_repl()
        mock_banner = MagicMock()
        mock_persister = AsyncMock()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            await repl._input_loop.run(mock_banner, mock_persister)
        # Verify KeyboardInterrupt routed through _abort_input
        repl._view.write_turn_end.assert_called_once()
        assert repl._input_loop._input_coro is None
```

### Details

The assertion `repl._view.write_turn_end.assert_called_once()` verifies that `_abort_input()` was called (since `_abort_input()` calls `self._view.write_turn_end()`).

The assertion `assert repl._input_loop._input_coro is None` verifies that `_abort_input()` also cleared the tracked input task (since `_abort_input()` sets `self._input_coro = None`).

These assertions provide explicit verification of the fix rather than relying on the test passing silently.

## Compatibility considerations

- The test enhancement does not change the test's behavior; it adds assertions to verify the fix.
- No compatibility issues with existing tests.

## Security considerations

- No security implications.

## Rollback considerations

- Simple revert: remove the two assertions added to `test_keyboard_interrupt_breaks_loop`.
- No data loss risk.

## Validation plan

1. Run the enhanced test: `uv run pytest tests/agent/test_repl.py::TestReplLoop::test_keyboard_interrupt_breaks_loop -v`
2. Verify the test passes after Row 1's fix.
3. Run the full test suite: `uv run pytest tests/agent/test_repl.py -q -p no:randomly`

## Completion criteria

- `test_keyboard_interrupt_breaks_loop` passes with the new assertions.
- All existing tests in `tests/agent/test_repl.py` continue to pass.

## Out of scope

- Modifying any source files (only adding test assertions).
- Adding new test methods beyond enhancing the existing one.
- Modifying any other files.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add verification test asserting KeyboardInterrupt routes through _abort_input | Completed | 20260909-105920 | 20260909-122726 | Applied exactly as designed (no correction needed) — `_abort_input()`'s call shape (`write_turn_end()` + clearing `_input_coro`) is unchanged by Row 1's `_InputAborted` correction. |
| 2 | Run validation sequence (`rules/toolchain.md`) | Completed | 20260909-105920 | 20260909-122726 | ruff format/check, mypy: clean. `test_keyboard_interrupt_breaks_loop` passes with the new assertions; full `tests/agent/test_repl.py` run: 47 passed, 8 failed (all pre-existing/unrelated — see sibling procedure's Step 3 Notes). |

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
- **Requirement ID**: REQ-REPL001B-3
- **Source issue**: issues/20260907-140047_repl001_keyboard_interrupt_not_caught_with_shutdown_event.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-071725_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260908-231011
- **Related target files**: tests/agent/test_repl.py
