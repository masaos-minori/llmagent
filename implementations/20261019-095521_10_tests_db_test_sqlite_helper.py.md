## Goal
Add unit tests that pin the helper's default per target and the explicit override in both directions (`REQ-005`).

## Scope
- One new test class appended to the file; existing tests stay untouched.

## Assumptions
- `SQLiteHelper.__init__` resolves paths through `build_db_config`; the file already patches `db.helper.build_db_config` with a `DbConfig` in `TestSQLiteHelperMissingDbPathMessage`, so the same pattern is used.

## Design decisions
- Parametrize over the four targets so a new target forces a conscious expectation.
- Check the override by patching `SQLiteHelper._load_vec_extension` and asserting whether it is called, so no real extension is needed.

## Alternatives considered
N/A: unit tests of one constructor default.

## Implementation
### Target file
`tests/db/test_sqlite_helper.py`

### Procedure
1. Append `TestSQLiteHelperVecDefault` (new) with two tests.
2. `test_default_load_vec_per_target` (new): for each of `rag`, `session`, `workflow`, `eventbus` build the helper with a patched `build_db_config` and assert `_default_load_vec` is `True` for `rag` and `session`, `False` for `workflow` and `eventbus`.
3. `test_explicit_load_vec_overrides_default` (new): with `_vec_so` set to a dummy path and `_db_path` set to a file under `tmp_path`, assert `open(load_vec=False)` does not call `_load_vec_extension` for `rag`, and `open(load_vec=True)` calls it for `workflow`.

### Method
- Reuse the file's existing imports (`pytest`, `Path`, `SQLiteHelper`); import `DbConfig` inside the test as the neighbor class does.
- Use `unittest.mock.patch.object(SQLiteHelper, "_load_vec_extension")` as `tests/db/test_create_schema.py` does.
- Do not modify `test_dbtarget_enum_member_resolves_to_value` (ADR-008 cites it until the Verification row is replaced).

### Details
- Close connections: use `with helper.open(...)` or call `close()`.

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/db/test_sqlite_helper.py -q`
- `uv run ruff format tests/db/test_sqlite_helper.py && uv run ruff check tests/db/test_sqlite_helper.py`
- `uv run python tools/check_mock_patch_targets.py`

## Completion criteria
- The per-target and override tests pass after the helper change and the per-target test fails against the old `rag`-only default.

## Out of scope
- Real-extension tests (separate procedure)
- Other test classes in the file

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append the new test class | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) for the test file | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (helper default per target)
- **Source issue**: issues/20261019-092704_mem001_session-sqlite-vec-not-loaded-at-runtime.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-094625_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-095521
- **Related target files**: tests/db/test_sqlite_helper.py
