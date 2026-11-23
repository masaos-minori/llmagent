## Goal

Re-render the generated mandatoriness table in `agent_08_04` from the registry.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `component-mandatoriness-reference` AUTO-GENERATED block only. The hand-written text above it (criteria and the `required` field) is unchanged.

## Assumptions

- Verified: the block lists 10 rows (lines 61-70) with the old rationale; no other part of the document cites it.

## Design decisions

- Run after procedure 01.

## Alternatives considered

Rejected: hand-editing the table (the generator owns it).

## Implementation
### Target file
`docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type mandatoriness` and review the diff: only the rationale column changes.

### Method
Use the generator; do not edit between the guard comments.

### Details
- Run the documentation gates afterwards (Step 6).

## Compatibility considerations

N/A: derived from the registry.

## Security considerations

N/A: derived text only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The table shows the new rationale and `--check` reports no drift.

## Out of Scope

Manual edits and the hand-written criteria text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the artifact with the command in Procedure | Pending | — | — | |
| 2 | Run `uv run python tools/generate_reference_table.py --check` and confirm no drift | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (regenerated mirrors)
- **Source issue**: issues/20261123-104602_gov003_mandatoriness-assessment-registry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111105_gov003_mandatoriness-assessment-registry.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-133747
- **Related target files**: `docs/23_agent/agent_08_04_configuration-mcp-approval-obs.md`
