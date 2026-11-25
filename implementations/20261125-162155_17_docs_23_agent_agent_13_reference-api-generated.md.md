## Goal

Regenerate the agent API reference for the new module and the changed signatures (REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Generated document: regenerate only, never hand-edit; execute after rows 6 and 7 land.
- Overlap with the cliplc006 Plan on this file is compatible: both Plans only regenerate it.

## Design decisions

- N/A: generated output; no content decisions.

## Alternatives considered

N/A: documentation-only change.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`
### Procedure
Run the generator so the new `agent.tool_result_audit` module and the extended `save_transport_failure` signature appear.
### Method
`uv run python tools/generate_reference_table.py`
### Details
N/A.

## Compatibility considerations

N/A: generated document.

## Security considerations

N/A: documentation-only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- The generated reference lists the new module and the changed signatures (AC-4).

## Out of Scope

- The source changes that drive the regeneration (rows 6, 7).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Execute after rows 6 and 7 |
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
- **Requirement ID**: REQ-008 (generated reference regeneration)
- **Source issue**: issues/20261119-140514_mcpai007_dedup-audit-observability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-142023_mcpai007_dedup-audit-observability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-162155
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
