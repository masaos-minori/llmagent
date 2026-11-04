## Goal

Add repository tests to `tests/agent/test_session_message_repo.py` that fail on the pre-change code and pass after it (REQ-004, REQ-005; AC-5): `replace_messages` does not persist messages carrying `_ephemeral` or `_memory_injected`, and the persisted boundary still equals the maximum persisted `message_id`; an all-ephemeral input persists nothing.

## Scope
**Release unit**: N/A: not part of a release unit (Phase 3; the release unit `summary-persist-restore` covers Phases 3–4 only).

## Assumptions

- The file already provides the `repo` fixture, the `TestReplaceMessages` class, `test_replace_messages_with_summary_message` (persists a `"[Conversation summary]"` row), and `test_replace_messages_sets_boundary_to_max_message_id` (pins the boundary = max persisted id).
- `_FakeSQLiteHelper` / `_SCHEMA_SQL` and the `patch("agent.session_message_repo.SQLiteHelper", ...)` pattern are available for the boundary assertions (as in the existing boundary test).
- Ephemeral rows are plain dicts carrying the top-level keys `_memory_injected` / `_ephemeral` (the shape `fetch_messages` would otherwise store).

## Design decisions

- `test_replace_messages_skips_ephemeral_system_rows` (new): build `messages_in` (new) with a valid user row plus a `_memory_injected` system row and an `_ephemeral` system row; call `replace_messages`; fetch and assert only the user row survived.
- `test_replace_messages_all_ephemeral_persists_nothing` (new): use the patched-DB pattern; pass an all-ephemeral list; assert the return is `None` and no messages rows were written for the session.

## Alternatives considered

- Test the boundary alongside the ephemeral filter in one test: rejected; the existing boundary test already pins the max-id rule, and adding the ephemeral assertions there would couple two unrelated behaviors. Keep them separate.

## Implementation
### Target file
`tests/agent/test_session_message_repo.py`

### Procedure
1. Add `test_replace_messages_skips_ephemeral_system_rows` (new) under the `TestReplaceMessages` class: build `messages_in` (new) with a valid user row plus a `_memory_injected` system row and an `_ephemeral` system row; call `replace_messages`; fetch and assert only the user row survived.
2. Add `test_replace_messages_all_ephemeral_persists_nothing` (new) using the patched-DB pattern: pass an all-ephemeral list; assert the return is `None` and no messages rows were written for the session.

### Method
```python
def test_replace_messages_skips_ephemeral_system_rows(
    self, repo: SessionMessageRepository
) -> None:
    messages_in = [
        {"role": "user", "content": "keep me"},
        {"role": "system", "content": "[Conversation summary]\nm", "_memory_injected": True},
        {"role": "system", "content": "hint", "_ephemeral": {"memory": True}},
    ]
    repo.replace_messages(1, messages_in)
    msgs = _msgs(repo.fetch_messages(1))
    assert len(msgs) == 1
    assert msgs[0]["content"] == "keep me"

def test_replace_messages_all_ephemeral_persists_nothing(self) -> None:
    import sqlite3
    from unittest.mock import patch

    conn = sqlite3.connect(":memory:")
    conn.executescript(_SCHEMA_SQL)
    conn.execute("INSERT INTO sessions (session_id) VALUES (1)")
    conn.commit()

    def _make(target: str = "session") -> _FakeSQLiteHelper:
        return _FakeSQLiteHelper(conn)

    with patch("agent.session_message_repo.SQLiteHelper", side_effect=_make):
        r = SessionMessageRepository(session_id=1)
        result = r.replace_messages(
            1,
            [
                {"role": "system", "content": "m", "_memory_injected": True},
                {"role": "system", "content": "h", "_ephemeral": {"memory": True}},
            ],
        )
    assert result is None
    assert conn.execute(
        "SELECT COUNT(*) FROM messages WHERE session_id = 1"
    ).fetchone()[0] == 0
```

### Details
- The boundary test already exists (`test_replace_messages_sets_boundary_to_max_message_id`); the ephemeral tests must not change it, so the boundary still equals the max persisted id when non-ephemeral rows are present.
- Stale-reference marks: none created here; `replace_messages` and the fixtures already exist.

## Compatibility considerations

- Additive tests; the existing `replace_messages` tests (including the summary-row case) keep passing.

## Security considerations

- Confirms the ephemeral memory block is not written to the session DB, closing the "stored indefinitely but never restored" gap.

## Rollback considerations

- Remove the added tests.

## Validation plan

- `uv run pytest tests/agent/test_session_message_repo.py -v` — the two new tests fail on the pre-change code (which stores every role-valid row) and pass after; existing tests pass unchanged.
- Static: `uv run ruff format`, `uv run ruff check`, `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria

- `replace_messages` drops `_ephemeral`/`_memory_injected` rows; the boundary equals the maximum persisted `message_id`; an all-ephemeral input returns `None` and writes nothing; the new tests fail before and pass after the change.

## Out of Scope

- The shared constant/predicate (Row 01), restore (Row 02), the persistence-side code (Row 03), the round-trip test (Row 06), and the docs (Rows 08–10).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | this row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (ephemeral filter), `REQ-005` (persistence tests), `AC-5`
- **Source issue**: issues/done/20261031-180437_restoresummary001_session-load-drops-summary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261104-115505_restoresummary001_session-load-drops-summary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261105-072108
- **Related target files**: tests/agent/test_session_message_repo.py
