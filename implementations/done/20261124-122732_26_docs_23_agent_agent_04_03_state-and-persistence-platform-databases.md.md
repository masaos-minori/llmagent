## Goal

Update the maintenance routing table and the RAG vector command name in the platform-databases document so the table maps subcommands to the services as implemented (REQ-007: name matches behavior; REQ-010: documentation reflects the implementation).

## Scope
**Release unit**: R6-rag-vector-contract (Phase 6)

- In scope: the routing lines at `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md:58,64`.

## Assumptions

- The split between `DbMaintenanceService` and `RagMaintenanceService` is unchanged; only the subcommand name in the mapping changes.

## Design decisions

- N/A: the table records existing routing; no new boundary is introduced.

## Alternatives considered

- N/A: a half-applied rename fails `tools/check_docs_quality.py` with the rule in `config/doc_quality_rules.json` (row 35).

## Implementation
### Target file
`docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`

### Procedure
1. Replace the vector subcommand name in the mapping line at `:64` with the renamed form.
2. Keep the service-split description at `:58` as it is.

### Method

- N/A: single-line change.

### Details

- N/A.

## Compatibility considerations

- Part of the same release unit as the code rename and the doc-quality rule.

## Security considerations

- N/A: documentation.

## Rollback considerations

- N/A: revert the Phase 6 commit.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| This document | Checkers | `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md` | No finding |

## Completion criteria

- The routing table names the renamed subcommand and the services that handle it.

## Out of Scope

- The service implementations, the other documents that name the command.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the routing table line | Completed | 20261125-002740 | 20261125-002740 | Phase 6 Phase 6 (R6) done: the routing line names rag-prune-vec; the service split at :58 is unchanged. |
| 2 | Run the documentation checkers (`rules/tool-gates.md`) | Completed | 20261125-002740 | 20261125-002740 | Docs checkers report no finding for this file. |

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
- **Requirement ID**: REQ-007 (name matching behavior), REQ-010 (documentation reflects the implementation)
- **Source issue**: issues/20261119-145301_cliplc003_maintenance-job-framework.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-001800_cliplc003_maintenance-job-framework.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-122732
- **Related target files**: `docs/23_agent/agent_04_03_state-and-persistence-platform-databases.md`