## Goal
Replace the swallowed `memories_vec` exception in the corrupt-DB fixture with explicit handling, and expose one shared schema helper for the other integration module (`REQ-007`).

## Scope
- The `corrupt_wal_db` fixture's `try/except` around `build_session_schema_sql`, and one new module-level function in this file.

## Assumptions
- CI has no sqlite-vec extension, so recovery tests must still build a session schema without it; the vec0 statement is the last statement of `build_session_schema_sql`.
- `tests/integration/test_session_recovery.py` already imports `hold_write_lock` from `tests.integration.conftest`, so importing one more helper follows an existing pattern.

## Design decisions
- `apply_session_schema` (new) loads the extension into the raw connection when `/opt/llm/sqlite-vec/vec0.so` exists and runs the full schema; otherwise it runs the schema up to the `memories_vec` statement, explicitly and with a comment saying why.
- No broad `except Exception` and no `# noqa`.

## Alternatives considered
Skipping every recovery test when the extension is missing was rejected: recovery behavior does not depend on vec and would lose CI coverage.

## Implementation
### Target file
`tests/integration/conftest.py`

### Procedure
1. Add `apply_session_schema(conn, schema=None, dims=4)` (new) to this module: default `schema` is `build_session_schema_sql(dims)`.
2. Inside it, when the `.so` exists call `conn.enable_load_extension(True)`, `conn.load_extension(path)`, `conn.enable_load_extension(False)` then `conn.executescript(schema)`; when it does not, `conn.executescript(schema.split("CREATE VIRTUAL TABLE IF NOT EXISTS memories_vec")[0])`.
3. In `corrupt_wal_db`, replace the `try/except` with `apply_session_schema(conn)` (new).

### Method
- Keep the `_has_table` guard that follows.
- Import `build_session_schema_sql` inside the function as the fixture does today.
- A schema string without the `memories_vec` statement (a caller passing a modified schema) is executed whole when the extension is unavailable.

### Details
- `pytest.mark.skip` is not used; the no-extension path is a deliberate schema without the vec table, documented in the docstring.

## Compatibility considerations
Recovery tests keep their current coverage with and without the extension; with the extension present the corrupt DB now also contains `memories_vec`.

## Security considerations
N/A: tests only; the extension path is the fixed local path already used elsewhere in tests.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/integration/test_session_recovery.py -q`
- `uv run ruff format tests/integration/conftest.py && uv run ruff check tests/integration/conftest.py`
- `uv run python tools/check_suppression_justification.py`

## Completion criteria
- No `except Exception` or `# noqa: BLE001` remains for `memories_vec` in this file.
- The recovery tests pass with and without the extension.

## Out of scope
- Changing `hold_write_lock` or other fixtures
- Editing `test_session_recovery.py` (separate procedure)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `apply_session_schema` (new) and use it in `corrupt_wal_db` | Completed | 20261019-101422 | 20261019-101422 |  |
| 2 | Run the recovery tests with the extension present and, by temporarily using a path that does not exist, without it | Completed | 20261019-101422 | 20261019-101422 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the file | Completed | 20261019-101422 | 20261019-101422 |  |

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
- **Related target files**: tests/integration/conftest.py