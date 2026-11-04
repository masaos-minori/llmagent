## Goal

Add repository unit tests for Row 01's two new methods: the captured image round-trips
`message_id` and `created_at` and returns the persisted `undo_floor_message_id`;
`restore_session_image` resets the `/undo` boundary and re-inserts only rows at or below the
marker with their original ids and `created_at`; and a failing restore leaves the existing
rows untouched and re-raises.

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- The `repo` fixture (in-memory DB, `_FakeSQLiteHelper`, real `SessionMessageRepository`) and
  the `grouped_repo` fixture (adds a single `fail_next` injection point) are reused; the new
  methods live on the same repository under test.
  Corrected during adversarial verification (2026-11-05): the `repo` fixture yields only the
  repository, while four of the five new tests need raw-connection access (created_at
  comparison, `UPDATE sessions`, explicit-id summary insert). All five tests therefore use
  `grouped_repo`, which yields `(repo, conn, state)` and behaves like `repo` while
  `fail_next` stays 0; `grouped_repo` is used for the failing-restore test as planned.
- The image is a `(rows, undo_floor)` tuple where `rows` is a list of
  `(message_id, role, content, tool_calls, tool_call_id, created_at)` ordered by `message_id`,
  and `restore_session_image(session_id, image, undo_floor, marker)` deletes all rows,
  re-inserts the image rows with `message_id <= marker` preserving id and `created_at`, and
  resets `undo_floor_message_id` in one transaction (Row 01).

## Design decisions

- Group the new tests in a `TestCaptureAndRestoreImage` (new) class so they read as one concern and
  reuse the existing fixtures like the neighbouring `TestReplaceMessages` / `TestDeleteMessagesFrom`.

## Alternatives considered

- Driving the restore through the turn boundary: rejected; these are focused repository unit
  tests, so the image and restore are exercised directly on the repository (the code under
  test), matching how `TestReplaceMessages` calls `replace_messages` directly.

## Implementation
### Target file
`tests/agent/test_session_message_repo.py`

### Procedure
Add a `TestCaptureAndRestoreImage` (new) class after `TestDeleteMessagesFrom`:
1. `test_capture_returns_rows_with_message_id_and_created_at` (new)
2. `test_capture_returns_persisted_undo_floor` (new)
3. `test_restore_resets_boundary_and_keeps_only_rows_at_or_below_marker` (new)
4. `test_restore_preserves_original_created_at` (new)
5. `test_failing_restore_leaves_rows_untouched_and_raises` (new)

### Method
- **round-trip ids and created_at**: `repo.save_many([...])` three rows (ids 1..3);
  `image = repo.capture_session_image(1)`; `rows, undo_floor = image`; query the raw connection
  `SELECT message_id, created_at FROM messages ORDER BY message_id` and assert each captured
  row's `message_id` and `created_at` equal the stored values (the capture must include both,
  not only role/content/tool fields).
- **returns persisted undo_floor**: seed rows, `conn.execute("UPDATE sessions SET undo_floor_message_id = 3 WHERE session_id = 1")`;
  assert `image[1] == 3` (the captured value equals the persisted boundary).
- **resets boundary, keeps rows at/below marker**: seed rows 1..6 with distinct contents,
  `image = repo.capture_session_image(1)`; simulate a rewrite by deleting all rows and inserting
  a summary at id 7 (`conn.execute` + `commit()`); call `repo.restore_session_image(1, image, 6, 6)`;
  assert exactly six rows remain with ids `1..6` (id 7 gone), and
  `conn.execute("SELECT undo_floor_message_id FROM sessions")` equals `6`.
- **preserves original created_at**: capture the image, change a row's `created_at` via
  `UPDATE messages SET created_at = '2000-01-01T00:00:00Z' WHERE message_id = 1`, call the
  restore, and assert the restored row 1's `created_at` equals the *original* value (not the
  mutated one), proving the explicit-id re-insert preserves timestamps (AC-1).
- **failing restore leaves rows untouched and raises**: use `grouped_repo`; seed rows 1..3,
  `image = repo.capture_session_image(1)`; set `state["fail_next"] = 1`;
  `with pytest.raises(sqlite3.Error): repo.restore_session_image(1, image, 3, 3)`; assert the
  rows are still ids 1..3 unchanged (the failed transaction rolled back; the boundary did not
  delete above the marker, which would leave zero rows).

### Details
- The "simulate a rewrite" step inserts the summary at id 7 explicitly (AUTOINCREMENT advances),
  so the pre-rewrite image holds ids 1..6 and the restore correctly discards id 7 (it is not in
  the image and is above the marker).
- The failing-restore test relies on `begin_immediate`'s guard firing on `BEGIN IMMEDIATE`, so
  no delete commits; this is exactly the delete-above-marker fallback the boundary must avoid
  (AC-2).
- Stale-reference marks: none created; the tests reference Row 01's `(new)` methods (resolved
  from the sibling).

## Compatibility considerations

- New tests run on the file's patched in-memory database; they never touch the real session
  database. They do not modify any existing test.

## Security considerations

- N/A: test-only additions; no data or policy change.

## Rollback considerations

- Revert the added tests.

## Validation plan

- `uv run pytest tests/agent/test_session_message_repo.py -v` — the five new tests pass; the
  existing `TestReplaceMessages` / `TestDeleteMessagesFrom` tests still pass.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- `capture_session_image` returns rows with original `message_id` and `created_at` and the
  persisted `undo_floor_message_id`.
- `restore_session_image` resets the boundary and re-inserts only rows at or below the marker
  with preserved ids and `created_at`; a failing restore leaves the rows untouched and raises.
- No existing test regresses.

## Out of Scope

- The boundary compensation wiring (Row 02 / Row 04).
- The real-database compress-then-fail integration test (Row 03).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the repository capture/restore tests per Validation plan | Completed | 20261105-084000 | 20261105-085000 | depends on Row 01 methods TestCaptureAndRestoreImage added after TestDeleteMessagesFrom; all five tests use grouped_repo (repo fixture lacks raw conn access - verification finding) |
| 2 | Add or update tests per Validation plan | Completed | — | 20261105-085000 | no separate test step: this procedure's row IS the test-file row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261105-085000 | ruff pass; file suite 67 passed (62 existing unchanged + 5 new); Row 01 completion criteria now test-covered |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261105-085000 | N/A: no `docs/` |

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
- **Requirement ID**: `REQ-001` (faithful restore with id and `created_at`), `REQ-002` (fail-safe restore)
- **Source issue**: issues/20261031-180341_compresscomp001_compression-compensation-wipes-session.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-114113_compresscomp001_compression-compensation-wipes-session.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261104-224326
- **Related target files**: tests/agent/test_session_message_repo.py