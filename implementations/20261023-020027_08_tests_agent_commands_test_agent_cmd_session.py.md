## Goal

Add `/session list` rejection cases and rewrite the two `…_treated_as_none` purge tests as
rejection tests asserting `DbMaintenanceService.purge` is not called, plus bare-flag and
negative-value purge cases, in `tests/agent/commands/test_agent_cmd_session.py` (REQ-004,
REQ-005; AC-3, AC-4, AC-6).

## Scope

In scope: `tests/agent/commands/test_agent_cmd_session.py` — new `/session list` rejection cases
and the rewritten/added purge cases. Out of scope: implementing `_session_list` / `purge`
(`scripts/agent/commands/cmd_session.py`, `db_session_ops.py`) — their own rows.

## Assumptions

- Existing cases to keep passing unchanged: `test_list_default_limit_is_20` (`:88-91`),
  `test_list_custom_limit` (`:94-97`), `test_purge_with_max_sessions` (`:526-537`),
  `test_purge_with_max_age_days` (`:540-551`), and `test_purge_error_raises` (`:554-564`).
- The two rewritten tests are `test_purge_with_non_numeric_max_sessions_treated_as_none` (`:567`)
  and `test_purge_with_non_numeric_max_age_days_treated_as_none` (`:584`); they currently assert
  `purge` is called with `None`, which this Plan removes.
- `test_purge_error_raises` requires `sqlite3.Error` to keep propagating, so only
  `CommandValidationError` may be caught at the call site (AC-6).

## Design decisions

- Add `/session list abc`, `/session list 0`, `/session list -1` rejection cases in the list test
  area, asserting `list_sessions` is not called (mirroring `test_list_custom_limit`'s mock-style
  assertion).
- Rewrite the two `…_treated_as_none` tests as rejection tests: same setup, but assert
  `mock_svc.purge.assert_not_called()` and (optionally) that a usage line is printed, instead of
  `assert_called_once_with(None, None)`.
- Add bare-flag cases (`purge --max-sessions`, `purge --max-age-days`) and a negative-value case
  (`purge --max-sessions -3`), each asserting `purge` is not called.
- Keep `test_purge_with_max_sessions` (`(10, None)`) and `test_purge_with_max_age_days`
  (`(None, 30)`) asserting the still-valid pass-through values.

## Alternatives considered

- Adding separate new test names instead of rewriting: rejected — the Plan explicitly asks to
  rewrite the two `…_treated_as_none` tests, since their names describe the removed behavior.

## Implementation

### Target file

`tests/agent/commands/test_agent_cmd_session.py`

### Procedure

- Add `/session list` rejection cases (in the list test area) asserting `list_sessions` is not
  called:

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("args", ["list abc", "list 0", "list -1"])
async def test_list_rejects_invalid_limit(self, args):
    cmd = _make_cmd(sessions=[])
    await cmd._cmd_session(args)
    cmd._ctx.session.list_sessions.assert_not_called()
```

- Rewrite `test_purge_with_non_numeric_max_sessions_treated_as_none` (`:567`) and
  `test_purge_with_non_numeric_max_age_days_treated_as_none` (`:584`) as rejection tests that assert
  `mock_svc.purge.assert_not_called()` instead of `assert_called_once_with(None, None)`.
- Add bare-flag and negative-value purge cases (`purge --max-sessions`, `purge --max-age-days`,
  `purge --max-sessions -3`), each asserting `purge` is not called.
- Keep `test_purge_with_max_sessions` (`:526`, asserts `(10, None)`), `test_purge_with_max_age_days`
  (`:540`, asserts `(None, 30)`), and `test_purge_error_raises` (`:554`, requires `sqlite3.Error`
  propagation) unchanged.

### Method

Reuse the existing `patch("agent.commands.db_session_ops.DbMaintenanceService")` setup pattern used
by the current purge tests; assert on the mock's `purge` call count.

### Details

The rewritten tests describe the removed "falls back to None" behavior, so their names/body now
assert rejection. `test_purge_error_raises` stays green because only `CommandValidationError` is
caught at the call site.

## Compatibility considerations

- The rewritten tests now assert the NEW behavior (rejection); the old "falls back to None"
  behavior no longer exists, so leaving them unchanged would fail. All other listed cases are
  behavior-preserving and stay green (REQ-009, AC-3, AC-4).

## Security considerations

- Locking the purge rejection cases prevents a regression where an operator misread silently
  changed how much data the destructive command deletes.

## Rollback considerations

- Restoring the two original `…_treated_as_none` tests from `HEAD` reverts the test-side change.

## Validation plan

- `uv run pytest tests/agent/commands/test_agent_cmd_session.py -q` — rejection cases assert
  `list_sessions`/`purge` are not called; `test_list_default_limit_is_20`, `test_list_custom_limit`,
  `test_purge_with_max_sessions`, `test_purge_with_max_age_days`, `test_purge_error_raises` pass
  unchanged (AC-3, AC-4, AC-6).

## Completion criteria

- `/session list` rejection cases assert `list_sessions` is not called; the two `…_treated_as_none`
  tests are rewritten as purge rejection cases asserting `purge` is not called; bare-flag and
  negative-value purge cases are added; the listed behavior-preserving cases stay green
  (AC-3, AC-4, AC-9).

## Out of Scope

Implementing `_session_list` (`cmd_session.py`) and `purge` (`db_session_ops.py`) and the other
test rows — each is its own row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `/session list abc/0/-1` rejection cases; rewrite the two `…_treated_as_none` tests as purge rejection cases; add bare-flag and negative-value purge cases; keep listed cases unchanged | Pending | — | — | REQ-004, REQ-005, REQ-009, AC-3, AC-4, AC-6 |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 3 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |
| 4 | — | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A: no blocking unknown remains (UNK-01..UNK-04 are non-blocking) | N/A: none | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-004`, `REQ-005`, `REQ-009`
- **Source issue**: `issues/20261021-093421_cmd002-invalid-command-args-silently-reinterpreted.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-013404_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261023-020027
- **Related target files**: `tests/agent/commands/test_agent_cmd_session.py`
