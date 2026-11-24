## Goal

Document the job commands, cancellation behavior, and the renamed RAG vector command in the Session command chapter, and remove the statement that these subcommands are not cancellable (REQ-001: job commands; REQ-002: cancellation; REQ-007: name matches behavior; REQ-010: documentation reflects the registered command set).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6); the behavior text is R7-docs-generated (Phase 7)

- In scope: the command table row at `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md:69` and the offload paragraph at `:73`.

## Assumptions

- The command is registered only under the renamed name; the retired name is not described as an alias.
- A minimal `/jobs` section with the two usage lines was added in Phase 2 (owner decision 2026-11-24) so `check_command_coverage` passes together with the Built-in Command Index row; this row keeps the command row, the cancellation paragraph, and the renamed RAG vector command for Phase 6 and Phase 7.

## Design decisions

- The paragraph keeps the offload description (the subcommands still run off the event loop) and replaces the completion claim with the cooperative-interruption behavior, because the offload mechanism is unchanged.

## Alternatives considered

- N/A: the paragraph states a limitation the plan removes; leaving it would contradict `tests/agent/commands/test_command_blocking_offload.py` (row 47).

## Implementation
### Target file
`docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`

### Procedure
1. Change the table row at `:69` to the renamed command and to what it actually does (removes orphan `chunks_vec` rows).
2. In the paragraph at `:73`, replace "these subcommands are not cancellable at shutdown" with the job-framework behavior: a cooperative job is interrupted at a progress callback, and a `not_cancelable` one is refused with a stated reason.
3. Add the `/jobs` commands to this chapter's command list.

### Method

- Keep the existing cross-reference to `agent_07_03` and the mention of the guard test.

### Details

- N/A: no other section of the file changes.

## Compatibility considerations

- `tools/check_docs_consistency.py` requires each registered command to be described in a chapter; this file is that chapter for `/jobs` subcommand behavior.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md` | No finding |

## Completion criteria

- The chapter describes the job commands and cancellation as implemented, names only registered commands, and contains no "not cancellable" claim.

## Out of Scope

- The Built-in Command Index row (`agent_07_03`, row 24).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the command row and the cancellation paragraph | Pending | — | — | Phase 6, Phase 7 |
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
- **Requirement ID**: REQ-001 (job commands), REQ-002 (cancellation), REQ-007 (name matching behavior), REQ-010 (documentation reflects the registered set)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/23_agent/agent_07_07_cli-and-commands-slash-commands-session-mcp.md`
