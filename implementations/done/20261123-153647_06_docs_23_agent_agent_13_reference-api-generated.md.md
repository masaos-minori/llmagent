## Goal

Re-render the generated Agent API reference after the manifest is regenerated.

## Scope
**Release unit**: eventbus-client-retirement

In scope: the guarded generated block only (lines for the two retired modules, about 69-76).

## Assumptions

- Verified: the block lists the retired modules' classes and is generated from `agent_api.yaml`.

## Design decisions

- Run after procedure 05.

## Alternatives considered

N/A: generated artifact; hand edits are rejected by the drift check.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type agent` and review the diff.

### Method
Use the generator; do not edit between the guard comments.

### Details
- Run the documentation gates afterwards.

## Compatibility considerations

N/A: derived from code.

## Security considerations

N/A: derived metadata only.

## Rollback considerations

N/A: revert the commit or regenerate from the reverted sources.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The block no longer lists the retired modules and `--check` reports no drift.

## Out of Scope

Manual edits.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the artifact with the command in Procedure | Completed | 20261123-153846 | 20261123-154223 | Regenerated with generate_reference_table.py; only the retired entries removed |
| 2 | Run `uv run python tools/generate_reference_table.py --check` and confirm no drift | Completed | 20261123-154223 | 20261123-154223 | --check No drift; gates pass |

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
- **Requirement ID**: `REQ-002` (remove modules, tests, and generated entries)
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111218_gov004_eventbus-client-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-153647
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
