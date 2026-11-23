## Goal

Regenerate the component-mandatoriness manifest so its `rationale` values mirror the registry.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the generated manifest only.

## Assumptions

- Verified: the manifest has 10 `rationale:` lines that copy the registry text; the drift check fails when they differ.

## Design decisions

- Regenerate after procedure 01, not before.

## Alternatives considered

N/A: generated artifact; hand edits are rejected by the drift check.

## Implementation
### Target file
`registry/manifests/component_mandatoriness.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests --type mandatoriness` and review the diff: only the 10 `rationale` values change.

### Method
Use the repository generator.

### Details
- Procedure 03 re-renders the table in `agent_08_04` from the same registry.

## Compatibility considerations

N/A: derived from the registry.

## Security considerations

N/A: derived metadata only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- The manifest shows the new rationale and `--check` reports no drift.

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
- **Requirement ID**: `REQ-004` (regenerated mirrors)
- **Source issue**: issues/20261123-104602_gov003_mandatoriness-assessment-registry.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-111105_gov003_mandatoriness-assessment-registry.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-133747
- **Related target files**: `registry/manifests/component_mandatoriness.yaml`
