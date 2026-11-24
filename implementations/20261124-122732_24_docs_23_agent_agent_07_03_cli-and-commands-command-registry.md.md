## Goal

Add the `/jobs` row to the Built-in Command Index so the coverage checker does not report a registered command missing from the index (REQ-001: job commands are registered; REQ-010: documentation reflects the registered command set).

## Scope
**Release unit**: R2-job-commands (Phase 2)

- In scope: the index table at `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md:46-59`.

## Assumptions

- The chapter description of the job behavior lives in `agent_07_07` (row 23); this file only carries the index row, as `check_command_coverage` requires both (`tools/check_docs_consistency.py:220-232,275-296`).

## Design decisions

- N/A: the index row follows the existing table format; one line, one description.

## Alternatives considered

- N/A: the checker cannot be satisfied without the index row.

## Implementation
### Target file
`docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`

### Procedure
1. Add a `| /jobs | ... |` row to the Built-in Command Index table.
2. Keep the wording consistent with the other rows: name, one-line purpose.

### Method

- N/A: no other section changes.

### Details

- N/A.

## Compatibility considerations

- The row must match the registered name exactly; the same phase registers it in `command_defs_list.py` (row 9).

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the Phase 2 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checker | `uv run python tools/check_docs_consistency.py` | Command coverage passes with the new command |
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_07_03_cli-and-commands-command-registry.md` | No finding |

## Completion criteria

- Every registered command, including `/jobs`, appears in the index and is described in a chapter.

## Out of Scope

- The behavior chapter, the registration code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the `/jobs` index row | Pending | — | — | Phase 2 |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (job commands), REQ-010 (documentation reflects the registered set)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/23_agent/agent_07_03_cli-and-commands-command-registry.md`
