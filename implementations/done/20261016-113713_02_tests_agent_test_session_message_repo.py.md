## Goal
- `REQ-003`: add a regression test with a helper that really closes its connection on exit, so a messages query issued after the `with` block is caught.

## Scope
- Additions to `tests/agent/test_session_message_repo.py` only. The code change is the other row's document (`scripts/agent/session_message_repo.py`).

## Assumptions
- The real `SQLiteHelper` closes the connection in `__exit__` and its `fetchall()` raises `RuntimeError("DB not open — call open() first")` when closed (`scripts/db/helper.py`); the test double mirrors that.
- The existing `_FakeSQLiteHelper` and the `_SCHEMA_SQL` constant are reusable as they are.

## Design decisions
- Subclass the existing fake so only the close behaviour differs; leave every existing test on the unchanged fake.
- Put the test in its own class so it is clear it guards the connection lifecycle, not the message content.

## Alternatives considered
N/A: switching all tests to a closing fake was rejected as a wider change than the Plan allows.

## Implementation
### Target file
`tests/agent/test_session_message_repo.py`

### Procedure
- Add `_ClosingFakeSQLiteHelper` (new) after `_FakeSQLiteHelper`: its `__init__` calls the parent and sets a closed flag; `__exit__` sets the flag; `fetchall` raises `RuntimeError("DB not open — call open() first")` when the flag is set, otherwise delegates to the parent.
- Add class `TestFetchMessagesConnectionLifecycle` (new) with `test_existing_session_messages_read_before_close` (new): build an in-memory DB from `_SCHEMA_SQL`, insert session 1 and one user message, patch `agent.session_message_repo.SQLiteHelper` with a factory returning the closing fake, call `SessionMessageRepository(session_id=1).fetch_messages(1)`, and assert it returns one message, `found is True`, and floor 0.
- In the same class add `test_missing_session_returns_not_found_with_closing_helper` (new): same setup without session 1's messages, call `fetch_messages(999)`, and assert `([], False, 0)`.

### Method
- Follow the patching pattern of the neighbouring tests: a local `_make(target: str = "session")` factory and `patch("agent.session_message_repo.SQLiteHelper", side_effect=_make)`.
- Build the DB rows with plain `conn.execute(...)` as `TestFetchMessages` does.
- Add a short comment naming `scripts/db/helper.py` as the behaviour being mirrored.

### Details
- Red check (done in this document's cycle): copy `scripts/agent/session_message_repo.py` aside, remove only the unused out-of-range read from the working file, run the new tests and confirm the existing-session test fails with `RuntimeError`, then restore the file. Record the observed result in the Notes of the Execution Status row.
- Tests use in-memory SQLite only and never open a production DB.

## Compatibility considerations
N/A: additive tests; no existing test or helper is edited.

## Security considerations
N/A: test-only change with no secrets or external access.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_session_message_repo.py -v` (new existing-session test fails with only the unused read removed, passes with both fixes)
- `uv run ruff format tests/agent/test_session_message_repo.py`, `uv run ruff check tests/agent/test_session_message_repo.py`, `uv run mypy --no-namespace-packages tests/agent/test_session_message_repo.py` (compare against the baseline error count)
- `uv run python tools/check_mock_patch_targets.py`
- `uv run coverage run -m pytest tests/agent`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` (confirm the report actually lists the changed lines)

## Completion criteria
- The closing helper and the two tests exist and pass after both code fixes; the existing-session test fails with only the unused read removed.
- All existing tests in the file still pass and no new mypy error appears in it.
- The diff-cover report covers the changed lines, or its gap is recorded in Notes.

## Out of scope
- Editing other test modules, changing `_FakeSQLiteHelper`, other repository methods (UNK-02), and any `docs/*.md` edit.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the closing helper and the lifecycle test class | Completed | 20261016-114515 | 20261016-114707 | changed: tests/agent/test_session_message_repo.py |
| 2 | Run the red check with only the unused read removed | Completed | 20261016-114707 | 20261016-114707 | red check (HEAD with only the unused read removed): existing-session test failed with RuntimeError, missing-session test passed |
| 3 | Run the validation sequence (`rules/toolchain.md`) after the code fix | Completed | 20261016-114707 | 20261016-114707 | ruff clean; mypy 9 errors identical to baseline; 115 tests in 4 modules passed; check_mock_patch_targets clean; diff-cover 100% on session_message_repo.py (1 changed line); full suite 8422 passed |

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
- **Requirement ID**: REQ-003 (regression test with a closing helper)
- **Source issue**: issues/20261016-110710_sess001_fix-fetch_messages-indexerror-on-undo-floor-column.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261016-113359_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261016-113713
- **Related target files**: tests/agent/test_session_message_repo.py