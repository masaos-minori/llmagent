## Goal

Regenerate the agent API manifest after the two modules are removed.

## Scope
**Release unit**: eventbus-client-retirement

In scope: the generated manifest only (entries for the two retired modules disappear).

## Assumptions

- Verified: `agent_api.yaml` lists the two modules' public classes; no other entry changes.

## Design decisions

- Run after procedures 03 and 04.

## Alternatives considered

N/A: generated artifact; hand edits are rejected by the drift check.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests --type agent` and review the diff: only the retired modules' entries are removed.

### Method
Use the repository generator.

### Details
- Procedure 06 re-renders the generated reference from this manifest.

## Compatibility considerations

N/A: derived from code.

## Security considerations

N/A: derived metadata only.

## Rollback considerations

N/A: revert the commit or regenerate from the reverted sources.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- No entry names either module and `--check` reports no drift.

## Out of Scope

Manual edits.

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
- **Requirement ID**: `REQ-002` (remove modules, tests, and generated entries)
- **Source issue**: issues/20261123-104603_gov004_eventbus-client-decision.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111218_gov004_eventbus-client-decision.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-153647
- **Related target files**: `registry/manifests/agent_api.yaml`
