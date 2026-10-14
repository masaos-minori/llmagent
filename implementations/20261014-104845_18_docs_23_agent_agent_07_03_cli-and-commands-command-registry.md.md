## Goal

Remove the `/mdq` row from the built-in command index (REQ-004: update documentation).

## Scope

- Delete one table row. The `/mdq` row at line 69 only.

## Assumptions

- Plan `plans/20261014-100930_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- `tests/docs/test_command_docs_sync.py` scans this doc, so the row must go for that test to pass.

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`

### Procedure

Delete the table row `| `/mdq` | Markdown query operations (status, index, search, outline, etc.) |`.

### Method

Edit with the Edit tool.

### Details

No other MDQ text exists in this file.

## Compatibility considerations

N/A: docs-only change

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run pytest tests/docs -q`, `check_docs_quality.py`, `check_docs_structure.py` pass.
- `rg -n -i 'mdq' <this file>` has no match.

## Completion criteria

- The row is gone and the table is still well-formed.

## Out of scope

- Other command rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete the row | Pending | — | — | |
| 2 | Run the documentation checkers named in `routing.md` Tools | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261014-095505_mdq001_remove-the-mdq-slash-command.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-100930_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-104845
- **Related target files**: docs/23_agent/agent_07_03_cli-and-commands-command-registry.md
