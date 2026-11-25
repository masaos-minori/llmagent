## Goal

Regenerate the API manifest that is the source of both reference blocks (REQ-012).

## Scope
**Release unit**: N/A: not part of a release unit (Phase 6 is outside R3-ownership)

## Assumptions
- Never hand-edit the manifest (Plan row: Regenerate); the generator owns it.

## Design decisions
- N/A: regeneration only.

## Alternatives considered
- N/A: hand-editing is prohibited for generated artifacts.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`

### Procedure
Run `uv run python tools/generate_reference_table.py` after rows 01-10 land; the manifest gains the new lifecycle symbols (`ManagedProcessRecord` (new), the error family (new), the new `LifecycleState` members).

### Method
Generator run, not an edit.

### Details
- The manifest already lists `scripts/agent/http_lifecycle*.py` symbols; the new record module must be picked up by the generator's domain scan.

## Compatibility considerations
- N/A: generated artifact; consumers are the two regenerate rows (21, 22).

## Security considerations
- N/A.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run python tools/generate_reference_table.py --check` — no drift after regeneration (AC-6).

## Completion criteria
- The manifest lists the new symbols and the check gate passes.

## Out of Scope
- The source changes that create the symbols (rows 01-10).

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
- **Related target files**: `registry/manifests/agent_api.yaml`
