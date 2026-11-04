## Goal

Add boundary unit tests for the compression-rewrite compensation added in Row 02:
restore-after-rewrite, the first-image-only rule, the fail-safe path (a failing restore
deletes nothing and still raises), the unchanged append-only path, and `conv.undo_floor`
restoration.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The `wired` fixture (in-memory DB, `_FakeSQLiteHelper` backed by a real connection,
  `state["fail_next"]` injection) and the `_boundary` / `_message_rows` helpers are reused;
  the boundary here is the real `TurnPersistence` bound to a real `SessionMessageRepository`
  (as the existing `TestCompensation` / `TestSnapshotRestore` tests do).
- Row 01's `capture_session_image` / `restore_session_image` exist on the repository; the
  boundary captures the image inside `replace_messages`.
- A failing `restore_session_image` is simulated by patching that method to raise, because a
  single `fail_next` tick cannot fail the later write and then the restore separately.

## Design decisions

- Group the new tests in a `TestRewriteCompensation` class so they read as one concern and
  reuse the `wired` fixture like the neighbouring classes.

## Alternatives considered

- Driving the rewrite through `ConversationStateManager`: rejected; these are focused
  boundary tests, so the rewrite is produced directly by `boundary.replace_messages`, which
  is the code under test.

## Implementation
### Target file
`tests/agent/test_turn_persistence.py`

### Procedure
Add a `TestRewriteCompensation` class after `TestSnapshotRestore`:
1. `test_restore_after_rewrite_returns_turn_start_rows`
2. `test_second_rewrite_does_not_move_the_captured_image` (first-image-only)
3. `test_failing_restore_leaves_rows_and_raises` (fail-safe)
4. `test_append_only_turn_captures_no_image` (append-only unchanged)
5. `test_conv_undo_floor_restored_after_rewrite_compensation`

### Method
- **restore-after-rewrite**: seed prior rows `INSERT ... (1,"prior-a"),(2,"prior-b")`,
  `marker=2`, `boundary = await _boundary(...)`. Run a real rewrite
  `await boundary.replace_messages([{"role":"assistant","content":"summary"}])` (succeeds,
  clears 1-2 and inserts a compressed row above the marker). Set `state["fail_next"] = 1`
  and `with pytest.raises(ConversationPersistenceError): await boundary.save_phase_grouped([...])`.
  Assert `_message_rows(conn)` equals the two prior rows `(1,"prior-a"),(2,"prior-b")` with
  their original `message_id` and `created_at` restored.
- **first-image-only**: seed rows 1-2, `marker=2`; rewrite A to `["summaryA"]`, then rewrite B
  to `["summaryB"]` (both succeed). Fail a later write. Assert the restored rows are the
  pre-rewrite-A rows (1-2), i.e. the second rewrite did not replace the captured image.
- **fail-safe**: seed rows 1-2, `marker=2`; run one real rewrite so an image is captured.
  `patch.object(SessionMessageRepository, "restore_session_image",
  side_effect=sqlite3.OperationalError("restore failed"))`. Fail a later write. Assert the
  raised object is `ConversationPersistenceError` and the rows are still the post-rewrite set
  (the boundary did NOT fall back to delete-above-marker, which would leave zero rows).
- **append-only unchanged**: no `replace_messages` call; `state["fail_next"] = 1` on a write.
  Assert `boundary._pre_rewrite_image is None` and compensation deleted only rows above the
  marker (existing prior-turn rows survive, this turn's rows gone).
- **conv.undo_floor restoration**: set `conv.undo_floor = 0` at turn start; after a successful
  rewrite assign `conv.undo_floor = 3` to simulate the manager's post-rewrite update; fail a
  later write; assert `conv.undo_floor == 0` after the raised error.

### Details
- The failing write consumes the single `fail_next` tick in `save_phase_grouped`'s
  `begin_immediate`; the subsequent `restore_session_image` then runs with `fail_next == 0`
  and succeeds, so the restore-after-rewrite assertions observe a real restore.
- For the fail-safe test the patched `restore_session_image` raises before any delete commits,
  so the transaction rolls back and the post-rewrite rows remain — that is exactly the
  delete-above-marker fallback the boundary must avoid (AC-2).
- Stale-reference marks: none created; the tests reference existing symbols and Row 01's
  `(new)` repository methods (resolved from the sibling).

## Compatibility considerations

- New tests live on the file's patched in-memory database; they never touch the real session
  database.

## Security considerations

- N/A: test-only additions; no data or policy change.

## Rollback considerations

- Revert the added tests.

## Validation plan

- `uv run pytest tests/agent/test_turn_persistence.py -v` — the five new tests pass; the
  existing `TestCompensation` / `TestSnapshotRestore` tests still pass.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages
  scripts/`.

## Completion criteria

- All five new tests pass on the changed code; the restore-after-rewrite and fail-safe tests
  fail on the pre-change code (AC-5 style: they exercise the new compensation branch).
- No existing test regresses.

## Out of Scope

- The repository capture/restore internals (Row 05).
- The real-database compress-then-fail integration test (Row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the five boundary unit tests per Validation plan | Pending | — | — | depends on Row 01/02 methods |
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
- **Requirement ID**: `REQ-002` (fail-safe restore), `REQ-003` (`conv.undo_floor` restore),
  `REQ-004` (append-only path unchanged)
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-224326
- **Related target files**: tests/agent/test_turn_persistence.py
