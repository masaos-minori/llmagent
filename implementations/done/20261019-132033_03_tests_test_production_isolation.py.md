## Goal
Create tests that prove the test run is isolated from `/opt/llm`: redirected configuration, session database path, and log path, the guard, the opt-out marker, and cleanup (`REQ-003`, `REQ-006`).

## Scope
- One new module under `tests/` (the directory exists; `tests/__init__.py` makes `tests.conftest` importable).

## Assumptions
- The conftest procedure defines the fixture `_forbid_production_paths` (new), the marker `production_paths_allowed` (new), and the helpers `_cleanup_isolated_root` (new) and `_production_file_handlers` (new); the module reaches them through `from tests.conftest import ...`.
- The import-time setup in `tests/conftest.py` is idempotent, so importing `tests.conftest` from a test does not create a second root.

## Design decisions
- Every probe that could create a production file uses a non-existent directory under `/opt/llm/` (for example `/opt/llm/__guard_probe__/x`): if the guard were missing, SQLite or the file handler would fail to open instead of creating anything.
- Derive the temporary root from `LLMAGENT_CONFIG_DIR` (its parent) instead of importing a private constant.

## Alternatives considered
Probing with an existing production directory was rejected: a broken guard would create a real file there.

## Implementation
### Target file
`tests/test_production_isolation.py` (new)

### Procedure
1. Add `test_temporary_root_is_outside_production` (new): the parent of `LLMAGENT_CONFIG_DIR` exists, is a directory, and is not under `/opt/llm`.
2. Add `test_config_loader_paths_are_redirected` (new): `ConfigLoader().load("agent.toml")` returns `rag_db_path`, `session_db_path`, `workflow_db_path`, `eventbus_db_path`, `sqlite_archive_dir`, and `memory_jsonl_dir` under the temporary root, and `sqlite_vec_so` is still `/opt/llm/sqlite-vec/vec0.so`.
3. Add `test_session_helper_resolves_under_temporary_root` (new): `SQLiteHelper("session").DB_PATH` is under the temporary root.
4. Add `test_logger_path_is_redirected` (new): a `Logger` with a unique name on `/opt/llm/logs/isolation-probe.log` has its file handler under `LLMAGENT_LOG_DIR` (new).
5. Add `test_guard_rejects_production_sqlite_connect` (new) and `test_guard_rejects_production_file_handler` (new): each expects `AssertionError` for a probe path under the non-existent production directory.
6. Add `test_opt_out_marker_skips_guard` (new), marked `production_paths_allowed` (new): the same `sqlite3.connect` probe raises `sqlite3.OperationalError`, not `AssertionError`.
7. Add `test_cleanup_removes_the_root` (new) using `_cleanup_isolated_root` (new) on a directory under `tmp_path`, and `test_collection_check_flags_production_handler` (new) using `_production_file_handlers` (new) with a handler whose `baseFilename` (new) is set to a production-looking path.

### Method
- Imports: `os`, `sqlite3`, `logging`, `uuid`, `Path`, `pytest`, `ConfigLoader` from `shared.config_loader`, `SQLiteHelper` from `db.helper`, `Logger` from `shared.logger`.
- For `test_collection_check_flags_production_handler` (new), create a `logging.FileHandler` on a `tmp_path` file, assign its `baseFilename` (new) attribute, attach it to a uniquely named logger, assert the helper reports it, and remove the handler afterwards.
- Do not touch `/opt/llm` except through the probes above.

### Details
- Expected before the conftest change: these tests fail (paths are not redirected, no guard); after it they pass.
- Use only the new, production-safe test files until the conftest isolation exists; do not run the full suite (it writes to `/opt/llm`).

## Compatibility considerations
N/A: new test module.

## Security considerations
N/A: tests only; probes cannot create files under `/opt/llm` even when the guard is absent.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/test_production_isolation.py -q`
- `uv run ruff format tests/test_production_isolation.py && uv run ruff check tests/test_production_isolation.py`
- `uv run python tools/check_mock_patch_targets.py` and `uv run python tools/check_suppression_justification.py`

## Completion criteria
- All tests pass after the conftest and logger changes and fail before them; none can create a file under `/opt/llm`.

## Out of scope
- Changing `tests/conftest.py` (separate procedure)
- Running the full suite

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module and run it against the unchanged conftest to see it fail | Completed | 20261019-140621 | 20261019-140621 | before the conftest change: 8 of 9 failed; after: 9 passed. memory_jsonl_dir is a top-level key (corrected during implementation) |
| 2 | Confirm it passes after the logger and conftest changes | Completed | 20261019-140621 | 20261019-140621 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the test file | Completed | 20261019-140621 | 20261019-140621 |  |

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
- **Requirement ID**: `REQ-003`, `REQ-006` (isolation and guard tests)
- **Source issue**: issues/20261019-131051_testiso001_tests-write-to-production-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-131444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-132033
- **Related target files**: tests/test_production_isolation.py