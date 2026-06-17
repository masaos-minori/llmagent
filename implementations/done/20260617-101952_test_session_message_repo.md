# Implementation: test_session_message_repo.py — counter and strict mode tests

## Goal

Add test coverage for the new skip counters and strict mode behavior in
`SessionMessageRepository`.

## Scope

`tests/test_session_message_repo.py` — add a new `TestCountersAndStrictMode` class.

## Assumptions

1. Existing fixture `repo` uses `session_id=1` and non-strict mode. Continue using it for counter tests.
2. Strict mode tests need their own repos (constructed inline with `strict_mode=True`).
3. The `_FakeSQLiteHelper` and `patch` pattern already established in the file should be reused.

## Implementation

### Target file

`tests/test_session_message_repo.py`

### Procedure

Append a new test class `TestCountersAndStrictMode` after `TestFetchMessages`.

### Method

Follow existing test style: patch `agent.session_message_repo.SQLiteHelper`, use the
`_FakeSQLiteHelper` in-memory backend, assert counter values directly on the repo instance.

### Details

Tests to add:

1. `test_save_increments_no_session_counter` — `SessionMessageRepository(session_id=None)`, call `save()`, assert `stat_skipped_no_session == 1`.
2. `test_save_increments_invalid_role_counter` — `repo` fixture, call `save("bad_role", "x")`, assert `stat_skipped_invalid_role == 1`.
3. `test_save_many_increments_no_session_counter` — `SessionMessageRepository(session_id=None)`, call `save_many([...])`, assert `stat_skipped_no_session == 1`.
4. `test_save_many_increments_invalid_role_counter` — `repo` fixture, call `save_many([("bad", "x", None, None)])`, assert `stat_skipped_invalid_role == 1`.
5. `test_strict_mode_save_raises_on_no_session` — `SessionMessageRepository(session_id=None, strict_mode=True)`, call `save()`, expect `RuntimeError`.
6. `test_strict_mode_save_raises_on_invalid_role` — strict repo with `session_id=1`, call `save("bad_role", "x")`, expect `RuntimeError`.
7. `test_strict_mode_save_many_raises_on_no_session` — `SessionMessageRepository(session_id=None, strict_mode=True)`, call `save_many([...])`, expect `RuntimeError`.
8. `test_non_strict_mode_does_not_raise` — ensure default (non-strict) `save()` with invalid role returns silently.

For strict mode tests with `session_id=1`, the repo still needs the DB patch since it won't early-return on missing session_id.

## Validation plan

```bash
uv run pytest tests/test_session_message_repo.py -v
```
