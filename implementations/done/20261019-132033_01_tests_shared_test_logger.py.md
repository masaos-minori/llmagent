## Goal
Add tests for the `LLMAGENT_LOG_DIR` (new) override of `Logger` and for the unchanged behavior when it is not set (`REQ-006`).

## Scope
- Three tests appended to the existing module; existing tests stay untouched.

## Assumptions
- The override is implemented by the sibling procedure for `scripts/shared/logger.py` as a function `_apply_log_dir_override` (new) used by `Logger.__init__`.
- `Logger` keeps its handlers per logger name, so each test uses a unique logger name.

## Design decisions
- Request paths under a non-existent `/opt/llm/logs/sub/` directory: without the override the file handler fails to open and nothing is created under `/opt/llm`, so the tests are safe even before the override exists.
- Test the unset case through the function `_apply_log_dir_override` (new) directly, never by constructing a `Logger` on a production path while the variable is unset.

## Alternatives considered
N/A: unit tests of one function and its use in `Logger`.

## Implementation
### Target file
`tests/shared/test_logger.py`

### Procedure
1. Add `test_log_dir_override_redirects_production_path` (new): set `LLMAGENT_LOG_DIR` (new) to `tmp_path / "logs"`, create `Logger(<unique name>, "/opt/llm/logs/sub/x.log")`, find its `logging.FileHandler`, and assert `baseFilename` (new) equals `tmp_path / "logs" / "sub" / "x.log"` and that the parent directory exists.
2. Add `test_log_dir_override_leaves_other_paths_unchanged` (new): with the variable set, a `Logger` on `str(tmp_path / "other.log")` keeps that path.
3. Add `test_apply_log_dir_override_is_inactive_without_variable` (new): with the variable deleted, `_apply_log_dir_override("/opt/llm/logs/x.log")` returns the input unchanged and creates nothing.
4. Run the three tests before the logger change and confirm the override test fails.

### Method
- Use `monkeypatch.setenv` and `monkeypatch.delenv("LLMAGENT_LOG_DIR", raising=False)`; unique logger names via `uuid.uuid4().hex`.
- Import `_apply_log_dir_override` (new) next to the existing `from shared.logger import ...` names.
- Find the handler with `next(h for h in logger._logger.handlers if isinstance(h, logging.FileHandler))`; `logging` and `Path` are already imported in the module.

### Details
- Use only the new, production-safe test files until the conftest isolation exists; do not run the full suite (it writes to `/opt/llm`).
- Expected before the logger change: the override test fails and the other two fail at import of the new function name.

## Compatibility considerations
N/A: tests only.

## Security considerations
N/A: tests only; no path under `/opt/llm` can be created by these tests.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/shared/test_logger.py -q`
- `uv run ruff format tests/shared/test_logger.py && uv run ruff check tests/shared/test_logger.py`

## Completion criteria
- The three tests pass after the logger change and the override test fails before it.

## Out of scope
- Changing the logger (separate procedure)
- Any test that constructs a `Logger` on a production path while the variable is unset

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the three tests and run them against the unchanged logger | Completed | 20261019-140621 | 20261019-140621 | before the logger change: override test and function import failed; after: tests/shared/test_logger.py 31 passed |
| 2 | Confirm they pass after the logger change and run the validation sequence (`rules/toolchain.md`) for the file | Completed | 20261019-140621 | 20261019-140621 |  |

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
- **Requirement ID**: `REQ-006` (logger override tests)
- **Source issue**: issues/20261019-131051_testiso001_tests-write-to-production-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-131444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-132033
- **Related target files**: tests/shared/test_logger.py