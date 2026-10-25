# Implementation Procedure — tests/db/test_db_maintenance.py

## Goal

Write the four retention-guard regression tests first (red), covering the age rule,
the count rule, the absent guard, and a no-op guard against a real in-memory SQLite
via the existing `_make_session_db` fixture (Phase 1; AC-001, AC-002, AC-004).

## Scope

- Modify only `tests/db/test_db_maintenance.py`: append four methods to
  `TestPurgeOldSessions` (127).
- Existing tests, fixtures (`_FakeDB` 76-106, `_SESSION_SCHEMA` 37-50), and helpers
  stay byte-identical.

## Assumptions

- `_make_session_db` inserts rows in list order into the `sessions` table (37-50), so
  ids are 1..N in the order given — tests reference rows by those ids.
- The fixture's `_FakeDB.conn` is a real `sqlite3.Connection` with
  `PRAGMA foreign_keys=ON`, so `messages` rows cascade on session delete
  (schema mirrors `scripts/db/schema_sql.py:102`).
- Before procedures 01-03 land, the `keep_session_id (new)` keyword does not exist
  and the tests fail red (TypeError / missing key) — intended Phase 1 state.

## Design decisions

- Reuse `_make_session_db` (in-memory real SQLite) rather than temp-file DBs — this
  is the file's established purge pattern; `_make_real_sqlite` (128) exists only for
  file-integrity tests and is not needed here.
- Messages are inserted directly through `db.conn.execute` to pin the cascade
  behavior AC-001 names explicitly.
- Backdating uses fixed far-past/far-future literals (established file convention,
  e.g. 148-156), not `datetime('now')` arithmetic — deterministic.

## Alternatives considered

- A new tmp_path file-based fixture: rejected — duplicates `_make_session_db` with
  no additional guarantee (FK/cascade are identical in-memory).

## Implementation
### Target file
`tests/db/test_db_maintenance.py`

### Procedure

Append to `TestPurgeOldSessions`:

```python
def test_age_rule_keeps_active_session(self) -> None:  # (new)
    db = _make_session_db(
        [
            ("active", "2000-01-01 00:00:00"),  # session_id 1
            ("old", "2000-01-02 00:00:00"),     # session_id 2
            ("new", "2099-01-01 00:00:00"),     # session_id 3
        ]
    )
    assert db.conn is not None
    db.conn.execute("INSERT INTO messages (session_id, role, content) VALUES (1, 'u', 'live')")
    db.conn.execute("INSERT INTO messages (session_id, role, content) VALUES (2, 'u', 'gone')")
    db.conn.commit()
    cfg = RetentionConfig(max_sessions=100, max_age_days=1)
    result = purge_old_sessions(db, cfg, keep_session_id=1)  # red until procedure 01
    assert result.success is True
    assert result.data is not None
    assert result.data["age_deleted"] == 1
    assert result.data["kept_active_session"] == 1
    survived = {r[0] for r in db.conn.execute("SELECT session_id FROM sessions")}
    assert survived == {1, 3}
    msgs = {r[0] for r in db.conn.execute("SELECT session_id FROM messages")}
    assert msgs == {1}  # session 2's messages cascade-deleted

def test_count_rule_keeps_active_session(self) -> None:  # (new)
    db = _make_session_db(
        [
            ("s1", "2099-01-01 00:00:00"),  # oldest
            ("s2", "2099-01-02 00:00:00"),  # active: 3rd by created_at
            ("s3", "2099-01-03 00:00:00"),
            ("s4", "2099-01-04 00:00:00"),
        ]
    )
    assert db.conn is not None
    cfg = RetentionConfig(max_sessions=2, max_age_days=0)
    result = purge_old_sessions(db, cfg, keep_session_id=2)  # red until procedure 01
    assert result.success is True
    assert result.data is not None
    assert result.data["count_deleted"] == 1  # only s1 removed
    assert result.data["kept_active_session"] == 2
    survived = {r[0] for r in db.conn.execute("SELECT session_id FROM sessions")}
    assert survived == {2, 3, 4}  # kept count exceeds max_sessions by one (plan Assumption 2)

def test_absent_guard_deletes_expired_active_equivalent(self) -> None:  # (new)
    db = _make_session_db(
        [
            ("active", "2000-01-01 00:00:00"),
            ("old", "2000-01-02 00:00:00"),
            ("new", "2099-01-01 00:00:00"),
        ]
    )
    cfg = RetentionConfig(max_sessions=100, max_age_days=1)
    result = purge_old_sessions(db, cfg)  # no guard: today's behavior (AC-004)
    assert result.success is True
    assert result.data is not None
    assert result.data["age_deleted"] == 2
    assert result.data["kept_active_session"] is None

def test_guard_not_present_in_sessions_is_noop(self) -> None:  # (new)
    db = _make_session_db(
        [
            ("active", "2000-01-01 00:00:00"),
            ("old", "2000-01-02 00:00:00"),
            ("new", "2099-01-01 00:00:00"),
        ]
    )
    cfg = RetentionConfig(max_sessions=100, max_age_days=1)
    result = purge_old_sessions(db, cfg, keep_session_id=999)  # red until procedure 01
    assert result.success is True
    assert result.data is not None
    assert result.data["age_deleted"] == 2  # identical counts to the unguarded run
    assert result.data["kept_active_session"] is None
```

### Method
Four new test methods `(new)` appended inside the existing `TestPurgeOldSessions`;
no new fixtures, imports, or helper functions. New keywords/keys referenced
(`keep_session_id (new)`, `kept_active_session (new)`) are created by procedures
01-03.

### Details
- The `kept_active_session (new)` assertions in tests 3-4 pin the key's presence
  (`is None`), matching procedure 01's "always present, None when not exempted" shape.
- Session/message id assumptions follow insertion order; if AUTOINCREMENT behavior
  ever diverges, re-derive ids via a SELECT on title before asserting.

## Compatibility considerations

- All existing tests in the file run unmodified in the same class (characterization
  guarantee for the keep=None path).
- `# type: ignore[arg-type]` style used by existing purge tests for the `_FakeDB`
  parameter is inherited by the new calls.

## Security considerations

N/A: in-memory test DBs only; no production purge executed (plan Validation plan).

## Rollback considerations

Delete the four appended methods; the file is otherwise untouched.

## Validation plan

- Red phase: `uv run pytest tests/db/test_db_maintenance.py -x -q` fails only on the
  four new tests before procedures 01-03.
- Green phase after procedure 01: same command fully green.
- Full: `uv run pytest tests/ -q` (10091 collected at HEAD 529c2fe3e).

## Completion criteria

- AC-001: tests 1 green (age guard + cascade).
- AC-002: test 2 green (count guard + surfaced key).
- AC-004: tests 3-4 and all pre-existing tests green unmodified.

## Out of Scope

- The command-level test (procedure 06).
- Implementation changes to `scripts/db/maintenance.py` (procedure 01).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the four tests (red run recorded) | Completed | 2026-10-25 | 2026-10-25 | red confirmed: exactly 4 new failed (TypeError `keep_session_id` x3, KeyError `kept_active_session` x1), 51 pre-existing passed; `# type: ignore[arg-type]` added on new purge calls per file convention |
| 2 | Re-run after procedure 01 lands (green) | Completed | 2026-10-25 | 2026-10-25 | 55 passed (4 new green, 51 pre-existing) |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-006 (tests 1-4 encode AC-001, AC-002, AC-004)
- **Source issue**: `issues/20261025-115826_sess005_purge-deletes-current-session.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261025-124106_sess005_purge-deletes-current-session.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261025-141651
- **Related target files**: scripts/db/maintenance.py (procedure 01)
