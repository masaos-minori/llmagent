## Goal

Regenerate the generated API reference after the new and modified reload and validation symbols, so the documented API surface matches the source rather than a hand-edited list (REQ-014).

## Scope
**Release unit**: R7-docs-and-manifests

## Assumptions
- Verified against current source: the file contains an `AUTO-GENERATED` block guarded by `tools/generate_reference_table.py --check` (ADR-015 INV-01), so it is regenerated, never hand-edited.
- The new symbols come from rows 1, 7, 8, 12; the modified symbols from rows 3, 4, 5, 6, 10, 11, 15, 16, 17, 18, 22.

## Design decisions
- Regeneration runs after the last code phase lands, so the reference reflects the final symbol set.

## Alternatives considered
- N/A: the guard fails on any hand edit.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`

### Procedure

### Method
- Run `uv run python tools/generate_reference_table.py --type agent` after Phase 6 lands and commit the result.

### Details
- Only the `AUTO-GENERATED` block changes; the surrounding prose is untouched.

## Compatibility considerations
- N/A: generated artifact.

## Security considerations
- N/A: the reference lists symbols, not values.

## Rollback considerations
- N/A: revert the Phase 7 commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`
- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py`

## Completion criteria
- The generated block lists the new reload, transaction, pending-state, and error symbols, and the check passes against the source.

## Out of Scope
- The symbol definitions (rows 1, 7, 8, 12) and the ownership manifest (row 45).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | runs after Phase 6 |
| 2 | Run the generated-artifact check (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-014
- **Source issue**: issues/20261119-145303_cliplc005_staged-reload-transaction.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-110935_cliplc005_staged-reload-transaction.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-074359
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`
