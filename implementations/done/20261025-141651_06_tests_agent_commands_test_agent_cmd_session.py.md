# Implementation Procedure — tests/agent/commands/test_agent_cmd_session.py

## Goal

Add the command-level current-session purge test (plan Test 5) and update the two
service-mock arg assertions that the new keyword breaks (544/558), keeping every
other test in the file byte-identical (AC-003, AC-005).

## Scope

- Modify only `tests/agent/commands/test_agent_cmd_session.py`.
- Two existing assertions change by the kwarg addition (plan re-verification caveat);
  everything else, including the `/session delete` guard test, is untouched
  characterization.

## Assumptions

- `_make_cmd(session_id=...)` builds a real `DbSessionOps` over a `SimpleNamespace`
  ctx (29-60); only `agent.commands.db_session_ops.DbMaintenanceService` is patched in
  existing purge tests (524), so an end-to-end variant can keep the service real and
  patch `SQLiteHelper` inside the service module instead (69).
- Cross-file test import precedent exists (`from tests.eventbus.eventbus_helpers
  import ...` in `tests/eventbus/*`; `tests/__init__.py` present), so
  `from tests.db.test_db_maintenance import _make_session_db` is the fixture source.
- Fallback if that import path proves unimportable under the pytest environment: build
  the in-memory DB inline in the new test with a 4-line `sqlite3.connect(":memory:")`
  + the same two-table schema (recorded as a fallback, not chosen by default).

## Design decisions

- Keep the service real and stub only `SQLiteHelper.open` via `MagicMock`
  (`helper.open.return_value.__enter__.return_value = db`) — MagicMock's native
  context-manager support avoids adding new context helpers.
- The test passes `--max-age-days 1`, so `_build_retention_config` (87-96) returns
  `RetentionConfig(max_age_days=1)` (dataclass default `max_sessions=100`) and
  `RetentionConfig.from_config()` never runs — deterministic in any environment. Rows
  are backdated far-past/far-future, keeping the age rule deterministic and the count
  rule inert (three rows < 100).
- New test class `TestCmdSessionPurgeKeepsActive (new)` rather than editing
  `TestCmdSessionPurge`, so its characterization set stays byte-identical apart from
  the two mandated assertion updates.

## Alternatives considered

- Spy on `purge_old_sessions` only: rejected — AC-005 demands the current row
  actually survives a purge executed through the real service/command chain.
- Patching `agent.commands.db_session_ops.DbMaintenanceService` with a hand-wired
  fake service: rejected — duplicates service logic in the test.

## Implementation
### Target file
`tests/agent/commands/test_agent_cmd_session.py`

### Procedure

1. Update `test_purge_with_max_sessions` line 544 to:

   ```python
   mock_svc.purge.assert_called_once_with(10, None, current_session_id=1)
   ```

   and `test_purge_with_max_age_days` line 558 to:

   ```python
   mock_svc.purge.assert_called_once_with(None, 30, current_session_id=1)
   ```

   (`1` is `_make_cmd`'s default ctx `session_id`, file 31.)

2. Append after `TestCmdSessionPurge`:

   ```python
   class TestCmdSessionPurgeKeepsActive:  # (new)
       @pytest.mark.asyncio
       async def test_purge_keeps_current_session_end_to_end(
           self, capsys: pytest.CaptureFixture
       ) -> None:  # (new)
           from unittest.mock import patch

           from tests.db.test_db_maintenance import _make_session_db

           db = _make_session_db(
               [
                   ("active", "2000-01-01 00:00:00"),  # session_id 1 = ctx session
                   ("old", "2000-01-02 00:00:00"),     # expired decoy
                   ("fresh", "2099-01-01 00:00:00"),
               ]
           )
           cmd = _make_cmd(session_id=1)
           with patch("agent.services.db_maintenance_service.SQLiteHelper") as MockHelper:
               helper = MagicMock()
               helper.open.return_value.__enter__.return_value = db
               MockHelper.return_value = helper
               await cmd._cmd_session("purge --max-age-days 1")  # real service + ops
           out = capsys.readouterr().out
           assert "kept active session 1" in out  # AC-003 wording (procedure 04)
           assert db.conn is not None
           survived = {r[0] for r in db.conn.execute("SELECT session_id FROM sessions")}
           assert survived == {1, 3}  # decoy deleted; guarded row survives
   ```

### Method
New class `TestCmdSessionPurgeKeepsActive (new)` with one test method `(new)`; two
existing assertions edited in place. No changes to `_make_cmd` / `_make_session`.

### Details
- The decoy row makes the age rule actually delete one session, so the success line
  is `Purged: 1 session(s) removed (kept active session 1) [Session]` — the
  substring assert pins AC-003 wording end to end.
- The mock-based `test_purge_success`/`test_purge_error_raises`/validation tests
  remain as-is (`DbPurgeResult(sessions_removed=...)` constructions stay valid via the
  procedure-03 default).

## Compatibility considerations

- 544/558 are the only existing assertions that change, per the plan re-verification
  note; they pin the new kwarg rather than the old two-arg call.
- `/session delete` guard tests and all other purge option-parsing tests are
  byte-identical characterization (AC-005).

## Security considerations

N/A: mocked service + in-memory DB; no production connection opened.

## Rollback considerations

Revert the two assertion edits and delete the appended class.

## Validation plan

- After procedures 02-04 land: `uv run pytest tests/agent/commands/test_agent_cmd_session.py -x -q`
  fully green.
- Characterization: `uv run pytest tests/db/test_db_maintenance.py -x -q` green
  unmodified (procedure 05's additions excepted).
- Full suite: `uv run pytest tests/ -q` (10091 collected at HEAD 529c2fe3e).

## Completion criteria

- AC-003: end-to-end output contains the kept-session note.
- AC-005: current row survives; delete-guard test green unmodified.

## Out of Scope

- The maintenance-layer tests (procedure 05).
- Implementation changes to the command/service layers (procedures 02, 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update assertions 544/558 | Completed | 2026-10-25 | 2026-10-25 | landed with procedure 04 |
| 2 | Append the end-to-end class (red until 02-04 land) | Completed | 2026-10-25 | 2026-10-25 | Deviation: inline DB build with `check_same_thread=False` — `_cmd_session` dispatches purge via `asyncio.to_thread`, so a default in-memory connection raises ProgrammingError in the executor thread; reuses `_SESSION_SCHEMA`/`_FakeDB` from the db test module (procedure fallback path extended for thread safety) |
| 3 | Run targeted + full validation | Completed | 2026-10-25 | 2026-10-25 | targeted 119 passed; full suite deferred to batch-end gate (plan step 5) |

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
- **Requirement ID**: REQ-003, REQ-005 (test 5 encodes AC-003, AC-005)
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: scripts/agent/commands/db_session_ops.py (procedure 04), scripts/agent/services/db_maintenance_service.py (procedure 02)
