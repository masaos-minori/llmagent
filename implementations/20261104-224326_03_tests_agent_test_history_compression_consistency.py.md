## Goal

Add the real-database compress-then-fail integration test for Row 02's compensation:
a turn that compresses (the boundary rewrite succeeds and captures a pre-image) and then
fails a later boundary write must restore the turn-start rows, `/undo` boundary, and
`conv.history`/`conv.undo_floor` instead of wiping the session. Keep the existing
`test_compression_failure_restores_pre_turn_state` unchanged.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The file's `session_and_conn` fixture (in-memory DB, `_FakeSQLiteHelper` backed by a real
  connection, `AgentSession` + real `SessionMessageRepository`) and the `_make_history`,
  `_TurnBoundaryStub`, `ConversationStateManager` machinery are reused; the boundary here is
  the real `TurnPersistence` bound to the real repository (as the existing failing-compression
  test does).
- Row 01's `capture_session_image` / `restore_session_image` exist on the repository; the
  boundary captures the image inside `replace_messages` (Row 02) after the rewrite succeeds.
- `handle_history_compression` sets `ctx.conv.undo_floor = len(ctx.conv.history)` after a
  successful rewrite (read in `scripts/agent/conversation_state_manager.py`), so a later
  failing write must restore it to its turn-start value (REQ-003).

## Design decisions

- Model the failure exactly as the Issue describes: a *successful* rewrite followed by a
  *failing later write*, rather than a failing rewrite. The failing rewrite is already
  covered by `test_compression_failure_restores_pre_turn_state`; this test targets the
  rewrite-succeeded branch (REQ-001, REQ-005).
- Drive the rewrite through the real `ConversationStateManager.handle_history_compression`
  against the patched DB (like the existing `test_manager_path_sets_undo_floor_to_snapshot_length`),
  so the capture happens on the real code path under test.

## Alternatives considered

- Patching `replace_messages` to fail: rejected; that exercises the failing-rewrite path, not
  the rewrite-succeeded-then-later-fail path this row adds (REQ-005).
- Injecting the later failure at the SQLite level: rejected; the file's `_FakeSQLiteHelper`
  has no injection counter, so patching the repository method is the consistent way to fail a
  single later write (as the existing test patches `replace_messages`).

## Implementation
### Target file
`tests/agent/test_history_compression_consistency.py`

### Procedure
Add one async test after `test_compression_failure_restores_pre_turn_state`:
1. `test_compress_then_later_write_failure_restores_turn_start_rows` (new)

### Method
- Seed six prior rows: `for m in _make_history(3): session.save(...)`, then
  `conn.execute("UPDATE sessions SET undo_floor_message_id = 6 WHERE session_id = 1")`,
  `conn.commit()` (ids 1..6, DB floor at 6).
- Build the real boundary at turn start: `conv = ConversationState()` with
  `conv.history = list(_make_history(3))`, `conv.undo_floor = 3`, `conv.system_prompt_content = ""`;
  `boundary = await session.turn_boundary(conv)` (marker = 6, snapshot = pre-turn).
- Append this turn's user message through the boundary:
  `await boundary.save("user", "this turn's question")` (id 7).
- Run a real compression rewrite via the manager so an image is captured:
  build a `SimpleNamespace` ctx with `hist_mgr.compress` returning
  `(list(conv.history), SimpleNamespace(compressed_count=1, summary_added=True, is_fallback=False))`,
  `mgr = ConversationStateManager(ctx, tasks=set(), on_discard=lambda t: None)`;
  `await mgr.handle_history_compression()` (rewrite clears 1..7, inserts a summary above the marker).
- Simulate the manager's post-rewrite in-memory update, then fail a later write:
  set `conv.undo_floor = len(conv.history)`; with
  `patch.object(SessionMessageRepository, "save_phase_grouped", side_effect=sqlite3.OperationalError("injected later-write failure"))`,
  run `with pytest.raises(ConversationPersistenceError): await boundary.save_phase_grouped([("assistant", "partial", None, None)])`.
- Assert:
  - `SELECT message_id, created_at FROM messages WHERE session_id = 1 ORDER BY message_id` returns ids `1..6`
    with their original `created_at` (turn-start rows restored, not empty);
  - `SELECT undo_floor_message_id FROM sessions` equals `6` (AC-6);
  - `conv.undo_floor == 3` (restored to turn-start, AC-3);
  - `[m["content"] for m in conv.history]` equals the pre-turn snapshot element-wise (AC-3).

### Details
- On pre-change code the rewrite captures no image, so `_compensate` deletes above the marker
  and the session ends with zero rows; the id assertion therefore fails before the change and
  passes after it (AC-5).
- The failing `save_phase_grouped` raises inside the boundary's `to_thread` wrapper, so
  `_fail_from_error` runs the restore; the patched method never touches the DB, so the
  post-rewrite rows remain until the restore rewrites them back (AC-2).
- Stale-reference marks: none created; the test references existing symbols and Row 02's
  `(new)` boundary behaviour (resolved from the sibling).

## Compatibility considerations

- New test lives on the file's patched in-memory database; it never touches the real session
  database. It does not modify any existing test.

## Security considerations

- N/A: test-only additions; no data or policy change.

## Rollback considerations

- Revert the added test.

## Validation plan

- `uv run pytest tests/agent/test_history_compression_consistency.py -v` — the new test passes
  and `test_compression_failure_restores_pre_turn_state` still passes.
- Confirm the new test fails on the pre-change code (AC-5).
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- After a turn that compressed and then failed a later write, the session's rows equal the
  turn-start rows (ids 1..6 with original `created_at`), `conv.undo_floor` equals its turn-start
  value, `conv.history` equals the pre-turn snapshot, and the persisted boundary equals `6`.
- The test fails on the pre-change code and passes after the change.
- No existing test regresses.

## Out of Scope

- The repository capture/restore internals (Row 05).
- The boundary unit tests (Row 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the compress-then-fail integration test per Validation plan | Pending | — | — | depends on Row 02 methods |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no `docs/` |

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
- **Requirement ID**: `REQ-001` (restore rewrite on compensation), `REQ-002` (fail-safe restore),
  `REQ-003` (`conv.undo_floor` restore), `REQ-005` (real-database failing test)
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-224326
- **Related target files**: tests/agent/test_history_compression_consistency.py
