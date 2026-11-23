## Goal

Regenerate the agent public-API manifest so it lists the new recovery module and the changed public signatures.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the generated manifest only.

## Assumptions

- Verified: the manifest lists per-symbol `file`, `kind`, `name`, and `signature` entries for `scripts/agent`; adding `scripts/agent/mcp_call_recovery.py` and changing `classify_stale_pending` and `WorkflowEngine` signatures changes it.
- If `--check` is already clean after rows 11-13, 37, and 46, record `no change needed` in Step 1 Notes.

## Design decisions

- Regenerate after the agent rows are implemented.

## Alternatives considered

N/A: generated artifact; hand edits are rejected by the drift check.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests --type agent` and review that only entries for the touched modules changed.

### Method
Use the generator.

### Details
- Rows 42 and 43 re-render the documents from this manifest.

## Compatibility considerations

N/A: derived from code.

## Security considerations

N/A: derived metadata only.

## Rollback considerations

N/A: revert the commit or regenerate from the reverted sources.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`

## Completion criteria

- `--check` reports no drift for the `agent` domain.

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
- **Related target files**: `registry/manifests/agent_api.yaml`
