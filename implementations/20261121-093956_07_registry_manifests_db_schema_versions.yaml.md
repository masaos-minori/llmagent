## Goal

Regenerate `registry/manifests/db_schema_versions.yaml` so it contains the new `mcp_dedup` entry produced by the updated generator (REQ-009, AC-9).

## Scope
**Release unit**: dedup-lease-identity-rollover

## Assumptions
- Row 06 (generator change) lands before or in the same commit as this regeneration; the manifest is generated output and MUST NOT be hand-edited.

## Design decisions
- Regeneration is run through the repository generator command only; the `generated_by`/`sources` stanzas update themselves.

## Alternatives considered
- N/A: hand-editing a generated manifest is prohibited by the Plan row and the tool's own `--check` gate.

## Implementation
### Target file
`registry/manifests/db_schema_versions.yaml`
### Procedure
Run the generator and commit its output.
### Method
- `uv run python tools/generate_reference_table.py` (manifest regeneration), then verify the new `mcp_dedup` entry shows `kind: schema`, `source: scripts/shared/mcp_dedup.py`, and the stamp recorded by row 01.
### Details
- Current manifest (verified 2026-11-21): three `kind: db_path` entries (rag/session/workflow) plus the `eventbus` `kind: schema` entry; no `mcp_dedup` row.

## Compatibility considerations
- Consumers of the manifest pick up one additional entry; snapshot `schema_versions` composition is validated by the row 03/15 suites.

## Security considerations
- N/A: generated metadata.

## Rollback considerations
- N/A: revert the commit (manifest and generator land in the same commit; regeneration reproduces the pre-change file exactly when the generator is reverted).

## Validation plan
- `uv run python tools/generate_reference_table.py --check` exits 0.

## Completion criteria
- AC-9: manifest carries a `mcp_dedup` entry consistent with the generator output.

## Out of Scope
- Generator implementation (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator and commit the regenerated manifest | Pending | — | — | Never hand-edit |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-009
- **Source issue**: issues/20261120-115841_mcpdl002_store-identity-continuity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261121-083728_mcpdl002_store-identity-continuity.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261121-093956
- **Related target files**: `registry/manifests/db_schema_versions.yaml`
