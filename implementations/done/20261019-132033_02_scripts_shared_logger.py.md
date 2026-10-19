## Goal
Let tests redirect `/opt/llm/logs/` files by setting `LLMAGENT_LOG_DIR` (new), with no behavior change when it is unset (`REQ-002`).

## Scope
- One constant pair, one helper function, two imports, and one call in `Logger.__init__`; no other behavior changes.

## Assumptions
- `LLMAGENT_LOG_DIR` (new) is set only by the test configuration (sibling procedure for `tests/conftest.py`); production processes never set it.

## Design decisions
- Redirect only paths that start with the production prefix `/opt/llm/logs/`, so a caller that already passes another path (such as a test's `tmp_path`) is untouched.
- Create the target's parent directories only in override mode, so production behavior (including the existing `OSError` fallback) is identical when the variable is unset.

## Alternatives considered
Editing the 36 call sites to read a directory from configuration was rejected: it touches many files for one test need. A global `logging.FileHandler` patch in tests was rejected: handlers are created at import during collection, before fixtures run.

## Implementation
### Target file
`scripts/shared/logger.py`

### Procedure
1. Add `import os` and `from pathlib import Path` to the module imports.
2. Define `LOG_DIR_ENV = "LLMAGENT_LOG_DIR"` and `_PRODUCTION_LOG_PREFIX = "/opt/llm/logs/"` at module level.
3. Define `_apply_log_dir_override(log_file: str) -> str`: return `log_file` unchanged when the variable is empty or the path does not start with the prefix; otherwise build `Path(<dir>) / <path after the prefix>`, create its parent directory, and return it as a string.
4. In `Logger.__init__`, after `_require_str(log_file, "log_file")`, set `log_file = _apply_log_dir_override(log_file)` before `_configure_logger`.

### Method
- Keep the existing docstring style; document the variable in the helper's docstring (purpose, only set by the test configuration).
- Do not change `_configure_logger`, formatters, filters, or the stderr handler.

### Details
- Because `Logger` returns early when the named logger already has handlers, the override only matters for the first construction of each name, which is the import-time case that motivates this change.

## Compatibility considerations
No behavior change when `LLMAGENT_LOG_DIR` (new) is unset. Every binary embeds `scripts/shared/`, so `tools/manage_binaries.py check` will report them stale; a rebuild is optional because production behavior is unchanged.

## Security considerations
The variable can only redirect log files into a directory the caller controls; it is not read from configuration and is unset in production.

## Rollback considerations
N/A: revert the commit (additive and inert when unset).

## Validation plan
- `uv run pytest tests/shared/test_logger.py -q`
- `uv run ruff format scripts/shared/logger.py && uv run ruff check scripts/shared/logger.py`
- `uv run mypy --no-namespace-packages scripts/` and `uv run bandit scripts/shared/logger.py`
- `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- With the variable set, a `/opt/llm/logs/` request is written under the given directory; with it unset, the path is unchanged; the sibling tests pass.

## Out of scope
- Changing any call site
- Setting the variable anywhere other than the test configuration
- Rebuilding or redeploying binaries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the imports, constants, helper, and the call in `Logger.__init__` | Completed | 20261019-140621 | 20261019-140621 |  |
| 2 | Confirm the logger tests pass | Completed | 20261019-140621 | 20261019-140621 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the changed module | Completed | 20261019-140621 | 20261019-140621 |  |

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
- **Requirement ID**: `REQ-002` (log-directory override)
- **Source issue**: issues/20261019-131051_testiso001_tests-write-to-production-state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-131444_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-132033
- **Related target files**: scripts/shared/logger.py