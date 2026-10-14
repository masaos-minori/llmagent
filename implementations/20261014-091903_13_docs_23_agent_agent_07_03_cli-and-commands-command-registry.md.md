## Goal

Remove the `/skill` row from the built-in command index (REQ-004: update documentation).

## Scope

- Delete one table row. The `/skill` row at line 69 only.

## Assumptions

- Plan `plans/20261014-091322_plan.md` is `Frozen`; this file is one of its `Implementation Target Files` rows.
- Source line numbers were verified in this cycle against the current tree and may shift; locate edits by symbol or test name.

## Design decisions

- `tests/docs/test_command_docs_sync.py` does not check `/skill` (its regex covers mcp, db, debug, audit, memory, mdq, rag), so the edit is safe and required for accuracy.

## Alternatives considered

N/A: the docs follow the code removal

## Implementation

### Target file

`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`

### Procedure

Delete the table row `| `/skill` | List skills or load a skill as ephemeral system context |`.

### Method

Edit with the Edit tool.

### Details

Follow `skills/python-documentation` for docs edits; keep English.

## Compatibility considerations

Docs-only change.

## Security considerations

N/A: docs-only change

## Rollback considerations

N/A: revert the commit

## Validation plan

- `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_consistency.py --domain agent`, and `uv run pytest tests/docs -q` pass.

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
- **Source issue**: issues/20261014-090429_skill001_remove-the-skill-slash-command-and-its-ephemeral-plumbing.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-091322_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261014-091903
- **Related target files**: docs/23_agent/agent_07_03_cli-and-commands-command-registry.md
