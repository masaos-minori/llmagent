## Goal

Regenerate the subpackages reference block for the `ProcessInfoSnapshot` and `services` symbol changes (REQ-012).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 6 is outside R3-ownership)

## Assumptions
- Guarded block generated from `registry/manifests/agent_api.yaml` (row 23); never hand-edit (ADR-015 INV-01).

## Design decisions
- N/A: regeneration only.

## Alternatives considered
- N/A: hand-editing is prohibited for generated blocks.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`

### Procedure
Run `uv run python tools/generate_reference_table.py` after row 09 lands; the `termination_outcome` (new, row 09) field appears on `ProcessInfoSnapshot` (already listed at `:196`).

### Method
Generator run, not an edit.

### Details
- The `--check` gate must pass afterward (AC-6).

## Compatibility considerations
- N/A: generated artifact.

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` — no drift (AC-6).

## Completion criteria
- The regenerated block shows the new field and the check gate passes.

## Out of Scope
- The field addition (row 09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Generator run, not a hand edit |
| 3 | Run the validation sequence (`rules/tool-gates.md` generated-block check) | Pending | — | — | `generate_reference_table.py --check` |

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
- **Requirement ID**: REQ-012 (generated reference artifacts)
- **Source issue**: issues/20261119-145305_cliplc007_mcp-process-ownership.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261125-232847_cliplc007_mcp-process-ownership.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261125-235436
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`
