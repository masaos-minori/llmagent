## Goal

Re-render the guarded generated block for the top-level agent modules from the regenerated `agent_api` manifest.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the guarded generated block only; produced by the tool.

## Assumptions

- Verified: the document renders from the `agent_api` manifest, and `--check` fails when the block drifts from it.
- If `--check` is already clean, record `no change needed` in Step 1 Notes.

## Design decisions

- Run after row 41.

## Alternatives considered

N/A: generated artifact; hand edits are rejected by the drift check.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --type agent` (and `--type agent_subpackages` for the subpackage document) and review the diff.

### Method
Use the generator; do not edit between the guard comments.

### Details
- Only entries for the touched modules should change.

## Compatibility considerations

N/A: derived from code.

## Security considerations

N/A: derived metadata only.

## Rollback considerations

N/A: revert the commit or regenerate from the reverted sources.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- `--check` reports no drift for this document.

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
- **Requirement ID**: `REQ-005` (ledger-state to Agent-state mapping and Agent recovery)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
