## Goal

Add a command-drift test for the log-path false positive (REQ-005: keep docs checks warning-free).

## Scope

- Add one test method. One method in `TestCheckCommandDrift` (lines 140-186).

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- Build the same temp repo as `test_unregistered_command_is_warning` with `/help` registered, a doc line `Logs: <log_dir>/mdq-mcp.log`, and assert `check_command_drift(...) == []`.
- Name it `test_log_path_with_command_like_name_is_not_a_reference` (new); keep the existing `/db rag stats` warning test as the positive case.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/tools/test_check_agent_docs_consistency.py`

### Procedure

Add the method after `test_unregistered_command_is_warning`.

### Method

Reuse `_mk_file` and the temp-repo setup; run `ruff format` and `ruff check` on the file.

### Details

Tests do not depend on the real `_COMMANDS`; they write a temporary `command_defs_list.py`.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/tools/test_check_agent_docs_consistency.py -q` passes and the new test fails without procedure 14.

## Completion criteria

- The new test exists and passes.

## Out of scope

- Other drift tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the test | Completed | 20261014-110318 | 20261014-110318 |  |
| 2 | Run the tests that cover this file | Completed | 20261014-110318 | 20261014-110318 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261014-110318 | 20261014-110318 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/tools/test_check_agent_docs_consistency.py