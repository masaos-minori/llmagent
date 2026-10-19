## Goal
Cover `tools/manage_binaries.py` with tests that use fake binaries, a temporary git repository, and temporary directories, including drift tests for the source-path table (`REQ-002`).

## Scope
- One new test module under `tests/tools/` (the directory exists); it never reads or writes `/opt/llm` and never runs Nuitka.

## Assumptions
- Tests import the tool as `from tools import manage_binaries as mod`, the way `tests/tools/test_check_db_separation.py` imports its tool.
- `git` is available in the test environment.

## Design decisions
- Fake binaries are small files starting with `\x7fELF` and mode 0755, so the structural check passes without real executables.
- Staleness tests use a real temporary `git init` repository so path-scoped diffs are exercised, not mocked.

## Alternatives considered
Mocking `git` was rejected: path-scoped staleness depends on real diff output.

## Implementation
### Target file
`tests/tools/test_manage_binaries.py` (new)

### Procedure
1. Add helpers `_make_binary` (new) and `_init_repo` (new).
2. Add the tests listed under Details.
3. Add the two drift tests and the two shell-script tests.

### Method
- Parse `ENTRIES` from `deploy/build_binaries.sh` and `BINARY_NAMES` from `deploy/deploy.sh` with a small regex in the test, and compare the output names with the keys of `BINARY_SOURCES` (new).
- For the import-coverage drift test, scan each entry's package under `scripts/` with `ast` for imports of `agent`, `db`, `rag`, `shared`, mcp_servers, and assert the binary's path-table row covers each imported package.
- The rollback script test runs `BIN_DIR=<tmp> bash deploy/build_binaries.sh --rollback` with `subprocess` and a previous set prepared in `<tmp>.prev`; it must not reach Nuitka.

### Details
- `test_write_info_records_checksum_and_commit` (new), `test_check_reports_ok_when_no_relevant_change` (new), `test_check_reports_stale_when_relevant_path_changed` (new), `test_check_ignores_unrelated_commit` (new), `test_check_unknown_without_build_info` (new), `test_check_mismatch_when_checksum_differs` (new), `test_check_invalid_for_non_elf` (new), `test_check_default_warns_only` (new), `test_check_strict_fails_on_stale_and_unknown` (new), `test_list_stale_prints_names` (new).
- `test_swap_success_saves_previous_set` (new), `test_swap_failure_leaves_bin_dir_unchanged` (new) (stage a binary that fails the structural check), `test_rollback_restores_previous_set` (new), `test_record_revision_writes_file` (new).
- `test_binary_sources_cover_entries_and_binary_names` (new), `test_binary_sources_cover_imported_packages` (new), `test_shell_scripts_parse` (new) (`bash -n` on both scripts), `test_build_binaries_rollback_option` (new).
- Each test name above is created by this procedure; mark them (new) when cited elsewhere.

## Compatibility considerations
N/A: new test module.

## Security considerations
N/A: tests only; temporary directories under `tmp_path`.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/tools/test_manage_binaries.py -q`
- `uv run ruff format tests/tools/test_manage_binaries.py && uv run ruff check tests/tools/test_manage_binaries.py`
- `uv run python tools/check_mock_patch_targets.py` and `uv run python tools/check_suppression_justification.py`

## Completion criteria
- Every test passes against the tool and the drift tests fail when a table row or an imported package is removed.

## Out of scope
- Running Nuitka or touching `/opt/llm`
- Tests for the Python entry points of the binaries

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create the module with helpers and the tool tests | Pending | — | — | |
| 2 | Add the drift and shell-script tests | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) for the test file | Pending | — | — | |

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
- **Requirement ID**: `REQ-002` (tool tests and drift tests)
- **Source issue**: issues/20261019-103807_deploybin001_binary-freshness-and-rollback-in-deploy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261019-104249_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261019-105818
- **Related target files**: tests/tools/test_manage_binaries.py
