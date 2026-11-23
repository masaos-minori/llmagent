## Goal

Regenerate the schema-version manifest so the `mcp_dedup` entry records version 2 and the new content hash of the schema module.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the generated manifest only; produced by the tool, not edited by hand.

## Assumptions

- Verified: the entry has `version: 1` and a `content_hash` of `scripts/shared/mcp_dedup_schema.py`, and the drift check fails once that file changes.

## Design decisions

- Regenerate after row 02 is implemented, not before.

## Alternatives considered

N/A: generated artifact; hand edits are rejected by the drift check.

## Implementation
### Target file
`registry/manifests/db_schema_versions.yaml`

### Procedure
1. Run `uv run python tools/generate_reference_table.py --manifests --type deployment` and review the diff: only the `mcp_dedup` `version` and `content_hash` change.

### Method
Use the repository generator; never edit YAML by hand.

### Details
- The guarded block in the deployment document does not render this entry, so no doc change follows.

## Compatibility considerations

N/A: derived from code.

## Security considerations

N/A: derived metadata only.

## Rollback considerations

N/A: revert the commit or regenerate from the reverted sources.

## Validation plan

- `uv run python tools/generate_reference_table.py --check`
- `uv run pytest tests/tools/test_generate_reference_table.py`

## Completion criteria

- The manifest shows version 2 and the current hash; `--check` reports no drift.

## Out of Scope

Any manual edit.

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
- **Requirement ID**: `REQ-006` (store schema bump and fingerprint refusal)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `registry/manifests/db_schema_versions.yaml`
