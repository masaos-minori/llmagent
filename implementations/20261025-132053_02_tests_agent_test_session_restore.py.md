# Implementation Procedure — tests/agent/test_session_restore.py

## Goal

Add a real-DB regression test proving that persistence after `restore_session()` is
attributed to the restored `session_id` (REQ-002, post-restore writes land on the
restored session; REQ-004, restore stays non-destructive), which fails before the
getter fix in procedure 01 and passes after it.

## Scope

- Add one new test class with two tests and their fixtures/helpers to
  `tests/agent/test_session_restore.py`.
- Existing mock-based tests in this file stay byte-identical.

## Assumptions

- The in-memory `sqlite3` + fake-helper pattern is the accepted real-DB test idiom
  (verified 2026-10-25: `tests/agent/test_history_compression_consistency.py:88-112`,
  `tests/agent/test_agent_session.py:33`).
- `restore_session()` needs a non-empty target session (raises
  `SessionNoMessagesError` otherwise), so the fixture pre-seeds one message row under
  the restored id.
- `reset_session_stats(ctx)` (`agent/commands/mixin_base.py:19-27`) only touches
  `ctx.stats.*`, satisfied by the existing `MagicMock()` ctx (verified).

## Design decisions

- Drive the real `restore_session()` service end-to-end with a real `AgentSession`
  mounted on a mocked ctx (`ctx.session = <real AgentSession>`,
  `ctx.conv = ConversationState()` — same hybrid as the module's `_make_ctx`), rather
  than manually reassigning `session_id`; the test then encodes REQ-002 literally.
- Patch both import sites `agent.session.SQLiteHelper` and
  `agent.session_message_repo.SQLiteHelper` against one shared in-memory connection so
  `start()` and message writes hit the same DB.

## Alternatives considered

- N/A: pattern mandated by the existing real-DB test idiom; no competing design for a
  test row.

## Implementation
### Target file
`tests/agent/test_session_restore.py`

### Procedure
Append a new test class `TestRestorePersistenceRealDB` (new) with a fixture and two
tests; add the module-level additions required by them.

### Method
Module-level additions:
- `from agent.session import AgentSession` (new) and
  `from agent.context import ConversationState` is already imported at line 12;
  extend it if needed.
- `_SCHEMA_SQL` (new) — a module constant holding the `sessions` + `messages`
  `CREATE TABLE` script, copied from the `test_agent_session.py:33` /
  `test_history_compression_consistency.py:35` idiom (columns: `session_id`,
  `created_at`, `title`, `undo_floor_message_id` for `sessions`; `message_id`,
  `session_id` FK with `ON DELETE CASCADE`, `role`, `content`, `tool_calls`,
  `tool_call_id`, `created_at` for `messages`).
- `_FakeSQLiteHelper` (new) — minimal helper wrapping one `sqlite3.Connection`
  (`open(write_mode=..., row_factory=...)` context manager, `execute`, `executemany`,
  `fetchall`, `commit`), modeled on `test_history_compression_consistency.py`'s
  `_FakeSQLiteHelper` and `/tmp/opencode/test_repo_staleness.py`.

Tests:
1. `test_persist_after_restore_attributes_to_restored_id` (new):
   - open `sqlite3.connect(":memory:")`, `executescript(_SCHEMA_SQL)`; pre-seed
     `sessions(session_id=200)` plus one `messages` row under 200 (restore target);
   - patch `agent.session.SQLiteHelper` and `agent.session_message_repo.SQLiteHelper`
     with the fake helper;
   - `s = AgentSession()`; `s.start()` (creates session row A); `s.save("user",
     "in original session")`;
   - `ctx = MagicMock(); ctx.session = s; ctx.conv = ConversationState();
     ctx.conv.system_prompt_content = ""`;
     `await restore_session(ctx, session_id=200)`; assert `s.session_id == 200`;
   - `s.save("user", "turn in restored session")`;
   - assert the `messages` table: session A holds exactly the original message;
     session 200 holds the seeded message plus the new turn (AC-001);
   - assert `s.skipped_no_session_count == 0`, `s.skipped_invalid_role_count == 0`,
     and (via `caplog`) no `Persistence skipped` / `Invalid role` warnings and no
     `IntegrityError` on the post-restore turn (AC-002).
2. `test_restore_keeps_both_session_rows` (new): after the same sequence, assert both
   `sessions` rows (A and 200) still exist (AC-003, non-destructive).

### Details
- New tests are `async def` like the existing `TestRestoreSession` methods (the file
  already awaits `restore_session`).
- Keep the existing module docstring, `_make_ctx`, and all mock tests untouched
  (REQ-003, existing mock tests unchanged).
- Test the red/green sequence: run before procedure 01 lands to record the failing
  baseline (evidence for the plan's "fails before the fix" criterion), then after.

## Compatibility considerations

N/A: additive test-only change; no existing test is modified or reordered.

## Security considerations

N/A: in-memory DB only; no production DB or network access.

## Rollback considerations

N/A: revert the commit (deletes the added test class and helpers only).

## Validation plan

- Red baseline: run the new tests against unfixed `session.py` — expected failure
  mirroring `/tmp/opencode/test_repo_staleness.py` output `{200: [seed], A: [both new rows]}`.
- Green: after procedure 01, `uv run pytest tests/agent/test_session_restore.py -q`
  fully green, including the pre-existing mock tests (AC-004).
- Determinism: fixed ids (`200`), no time/random dependence.

## Completion criteria

- Both new tests exist, fail before the fix and pass after it (AC-001, AC-003), with
  the red baseline recorded.
- All pre-existing tests in the file pass unmodified.

## Out of Scope

- The `session.py` getter change (procedure 01).
- Any changes to `session_restore.py` or `session_message_repo.py` tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_SCHEMA_SQL` (new), `_FakeSQLiteHelper` (new), and `TestRestorePersistenceRealDB` (new) | Pending | — | — | |
| 2 | Record red baseline against unfixed `session.py` | Pending | — | — | run before procedure 01 lands, or via `git stash`-style check |
| 3 | Run `uv run pytest tests/agent/test_session_restore.py -q` after procedure 01 | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (real-DB regression for restored-id attribution); REQ-004 (restore non-destructive)
- **Source issue**: `issues/done/20261025-115501_sess001_repo-staleness-after-restore.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-121815_sess001_repo-staleness-after-restore.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-132053
- **Related target files**: tests/agent/test_session_restore.py
