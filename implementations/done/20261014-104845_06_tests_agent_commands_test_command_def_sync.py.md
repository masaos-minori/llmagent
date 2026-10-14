## Goal

Remove the `_cmd_mdq_*` entries from the handler exclusion set (REQ-002: update tests).

## Scope

- Delete seven set entries. Lines 22-28 of `INTENTIONAL_HANDLER_EXCLUSIONS` only.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- After removal the frozenset keeps `_cmd_mcp_status` and `_cmd_mcp_tools`; the rest of the file never mentions mdq.

## Alternatives considered

N/A: deletion is the decided direction (Plan Design)

## Implementation

### Target file

`tests/agent/commands/test_command_def_sync.py`

### Procedure

Delete the seven `"_cmd_mdq_*"` strings (get, grep, index, outline, refresh, search, status).

### Method

Edit by value; run `uv run ruff format` on the file.

### Details

`test_every_handler_has_commanddef` would not fail if the entries stayed, but they would be stale.

## Compatibility considerations

N/A: test-only change

## Security considerations

N/A: test-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/agent/commands/test_command_def_sync.py -q` passes.
- `rg -n 'mdq' tests/agent/commands/test_command_def_sync.py` has no match.

## Completion criteria

- The set contains only the two `_cmd_mcp_*` entries.

## Out of scope

- Other sync tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the entries | Completed | 20261014-110318 | 20261014-110318 |  |
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
- **Requirement ID**: REQ-002
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: tests/agent/commands/test_command_def_sync.py