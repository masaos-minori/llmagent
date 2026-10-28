## Goal

Lock both `/session rename` outcomes and the new `set_title` return contract with
regression tests in `tests/agent/commands/test_agent_cmd_session.py`: no-session rename
prints the validation error and no success line; the real-rename success line stays
byte-identical (REQ-3, REQ-4).

## Scope

- `TestCmdSessionRename`: add one failure case (new test
  `test_rename_without_active_session_prints_validation_error` (new)).
- New class `TestSetTitleContract` (new) in the same module: direct `AgentSession.set_title`
  return-value checks for both paths with a patched `SQLiteHelper`.
- Existing `test_rename_updates_title` (L249-253) and the rest of the module stay
  unchanged.

## Assumptions

- The Plan's Tests table allows the unit-level `set_title` check "in the same command
  test module or its existing session-level suite"; the frozen target table only lists
  this module, so the unit tests go here and `tests/agent/test_agent_session.py` is run
  read-only as regression (frozen-table rule: no file outside the table is modified).
- Existing success test stays green untouched: `_make_cmd()` mocks `set_title`, whose
  default `MagicMock` return is truthy, so the branch still prints the success line.
- `AgentSession(*, strict_mode: bool = False) -> None` (verified in source) — construct
  directly with no arguments and set `session_id` as a plain attribute.
- Batch overlap scan (`tools/check_plan_target_overlaps.py`, this pass): no finding
  names this Plan's test-module row.

## Design decisions

- Assert the failure output on the stable markers the output port emits:
  `write_validation_error` prints `  [usage] <text>` (`scripts/agent/commands/output_port.py`
  L133-135), so assertions use `"[usage]"` and the literal usage hint
  `"/session rename <title>"`, plus absence of `"renamed"` (case-insensitive) —
  consistent with the module's existing style (`test_unknown_subcommand_shows_usage`
  asserts on lowercase substrings).
- Unit contract tests patch `agent.session.SQLiteHelper` with a `MagicMock` (no real DB
  file, no sqlite-vec), mirroring the isolation philosophy of the session-level suite's
  in-memory fake helper without importing from it.

## Alternatives considered

- Adding the unit tests to `tests/agent/test_agent_session.py` (the Plan Tests table's
  second option): rejected — that file is not a row in the frozen target table, and the
  frozen table is the canonical scope.
- Marking `test_rename_updates_title` with a stricter `return_value=True` mock:
  unnecessary — MagicMock's truthy default already exercises the success path; the plan
  requires it to stay green unchanged.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_session.py`

### Procedure

Add the failure-case test to `TestCmdSessionRename` and a two-case contract class.

### Method

Append-only test additions; no edits to existing tests or fixtures.

### Details

In `TestCmdSessionRename`:

```python
@pytest.mark.asyncio
async def test_rename_without_active_session_prints_validation_error(
    self, capsys: pytest.CaptureFixture
) -> None:
    cmd = _make_cmd(session_id=None)
    cmd._ctx.session.set_title.return_value = False
    await cmd._cmd_session("rename Should Fail")
    out = capsys.readouterr().out
    cmd._ctx.session.set_title.assert_called_once_with("Should Fail")
    assert "[usage]" in out
    assert "/session rename <title>" in out
    assert "renamed" not in out.lower()
```

New class (module level; add `from agent.session import AgentSession` to the imports):

```python
class TestSetTitleContract:
    def test_set_title_returns_false_without_session_id(self) -> None:
        session = AgentSession()
        session.session_id = None
        with patch("agent.session.SQLiteHelper") as helper:
            assert session.set_title("Title") is False
        helper.assert_not_called()

    def test_set_title_returns_true_after_update(self) -> None:
        session = AgentSession()
        session.session_id = 7
        with patch("agent.session.SQLiteHelper") as helper:
            assert session.set_title("Title") is True
        db = helper.return_value.open.return_value.__enter__.return_value
        db.execute.assert_called_once()
        db.commit.assert_called_once_with()
```

(`patch` is already imported at module top.)

## Compatibility considerations

- Tests depend on the implementation order document _01 → document _02 → this module's
  failure case; the contract class also passes only once document _01 lands (with the
  old `None` return, `is False`/`is True` assertions fail).
- `set_title.return_value = False` on the shared `MagicMock` fixture is per-test
  (`_make_cmd` builds a fresh mock each call) — no cross-test leakage.

## Security considerations

- N/A: test module only; patched helper performs no real DB access.

## Rollback considerations

- Remove the added test/cases; existing module content is untouched, so revert is
  additive-only.

## Validation plan

| Check | Command | Expected |
|-------|---------|----------|
| targeted | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k rename` | all green incl. new failure case |
| contract | `uv run pytest tests/agent/commands/test_agent_cmd_session.py -k TestSetTitleContract` | both contract cases green |
| session regression | `uv run pytest tests/agent/test_agent_session.py` | green unchanged |
| lint/type | `uv run ruff check . && uv run mypy scripts/` | clean |
| full suite | `uv run pytest` | green |

## Completion criteria

- New failure case green: validation error printed, no "renamed" line (Plan AC REQ-2, REQ-3).
- Existing `test_rename_updates_title` green with its exact success assertion (REQ-4).
- `set_title` returns `False`/`True` on the two paths per the contract tests (REQ-1, REQ-3).

## Out of Scope

- Changes to `tests/agent/test_agent_session.py` or any other test module.
- Tests for `sqlite3.Error` propagation (unchanged behavior, already covered by the
  session-level suite's exception cases).
- Title parsing/truncation test changes (Plan OUT-2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261028-075014 | 20261028-080550 | Failure case added to TestCmdSessionRename; TestSetTitleContract appended |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-080550 | This document is the test procedure This document is the test procedure |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-080550 | Shared _02/_03 validation pass: full suite 10255 passed, diff-cover 100%; targeted rename+contract+session-regression green |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-080550 | N/A: Plan has no docs row N/A: Plan has no docs row |

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
- **Requirement ID**: REQ-3, REQ-4
- **Source issue**: `issues/20261026-225105_sess007_validate-session-rename-result.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261027-085735_sess007_validate-session-rename-result.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-001446
- **Related target files**: `tests/agent/commands/test_agent_cmd_session.py`