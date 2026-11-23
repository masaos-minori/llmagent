## Goal

Regenerate the subpackage generated API table so the new transition service and changed service symbols appear (REQ-010 generated-reference freshness; AC-6).

## Scope
**Release unit**: N/A: not part of a release unit

Generated-block row: content is produced by the generator, never hand-edited.

## Assumptions
- The guarded AUTO-GENERATED block currently lists `session_restore` and `conversation_service` entries and will drift once seq 02-07 land (plan evidence, checked in Step 3).

## Design decisions
- Run the generator with --type agent_subpackages after all code rows are merged; commit the regenerated block verbatim.

## Alternatives considered
N/A: hand-editing guarded blocks is prohibited by ADR-015.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`
### Procedure
1. Run uv run python tools/generate_reference_table.py --type agent_subpackages (with --dry-run first).
2. Commit the regenerated guarded block.
### Method
Generator invocation only.
### Details
N/A: the generator owns all table content.

## Compatibility considerations
- Must be regenerated after seq 01-14 land, in the same plan step, so --check passes at plan close.

## Security considerations
N/A: generated documentation.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` (exits 1 on drift).

## Completion criteria
The guarded block matches the live sources and --check passes (AC-6).

## Out of Scope
The package-level table (seq 19) and the manifests (seq 20).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the guarded block with the generator | Pending | — | — | Docs-only row: no test step |
| 2 | Run generate_reference_table.py --check and the doc checkers from `rules/tool-gates.md` | Pending | — | — | |

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
- **Requirement ID**: `REQ-010` (generated API table freshness)
- **Source issue**: `issues/20261119-145300_cliplc002_session-transition-generation.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261122-232757_cliplc002_session-transition-generation.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-094714
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`
