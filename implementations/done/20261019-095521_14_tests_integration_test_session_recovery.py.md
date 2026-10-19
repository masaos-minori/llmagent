## Goal
Remove the four swallowed `memories_vec` exceptions in the session recovery tests by using the shared schema helper (`REQ-007`).

## Scope
- The four sites that run `conn.executescript(build_session_schema_sql(4))` inside `try/except Exception`: the lock-test setup, `_make_partial_session_db`, `_make_orphaned_message_db`, and `_make_orphaned_memory_link_db`.

## Assumptions
- `apply_session_schema` (new) exists in `tests/integration/conftest.py` (previous procedure for that file) and accepts an optional `schema` string.

## Design decisions
- Import the helper next to the existing `hold_write_lock` import; keep each function's other behavior unchanged.
- `_make_partial_session_db` passes its modified schema string through the helper.

## Alternatives considered
N/A: mechanical replacement.

## Implementation
### Target file
`tests/integration/test_session_recovery.py`

### Procedure
1. Add `apply_session_schema` (new) to the existing `from tests.integration.conftest import hold_write_lock` import.
2. At each of the four sites replace the `try/conn.executescript(...)/except Exception` block with `apply_session_schema(conn)` (new) (or `apply_session_schema(conn, schema)` (new) in `_make_partial_session_db`).
3. Remove the `build_session_schema_sql` import from a function when it becomes unused.

### Method
- Leave the surrounding `PRAGMA journal_mode=WAL`, inserts, `commit`, and `close` as they are.
- No `# noqa` is left behind; run the suppression checker to confirm.

### Details
- Do not change assertions or test names.

## Compatibility considerations
Recovery tests behave as before without the extension; with it the schema includes `memories_vec`.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/integration/test_session_recovery.py -q`
- `uv run ruff format tests/integration/test_session_recovery.py && uv run ruff check tests/integration/test_session_recovery.py`
- `uv run python tools/check_suppression_justification.py`

## Completion criteria
- No `except Exception` or `# noqa: BLE001 — memories_vec` remains in this file.
- All recovery tests pass.

## Out of scope
- Changing test logic, names, or assertions
- Editing `conftest.py` (separate procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace the four swallowed-exception blocks with the shared helper | Completed | 20261019-101422 | 20261019-101422 |  |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the file | Completed | 20261019-101422 | 20261019-101422 |  |

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
- **Requirement ID**: `REQ-007` (stop swallowing the schema exception)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: tests/integration/test_session_recovery.py