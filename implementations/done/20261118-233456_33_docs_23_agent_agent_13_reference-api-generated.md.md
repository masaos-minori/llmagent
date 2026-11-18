## Goal

Refresh the generated API reference so it publishes the post-change docstrings and no longer publishes the
removed orphan approval symbol (REQ-011).

## Scope
**Release unit**: approval-event-cleanup and boundary-and-adr-record (Phase 6 regeneration serves both)

## Assumptions
- `docs/23_agent/agent_13_reference-api-generated.md:143` currently publishes `log_approval_decision`;
  the whole approval-module docstring set is published from the same guarded block.
- The file is generated; the guarded block must never be hand-edited (ADR-015 INV-01).

## Design decisions
N/A: regeneration only.

## Alternatives considered
Hand-editing the removed entry — prohibited by the guarded-block rule and caught by the drift gate.

## Implementation
### Target file
`docs/23_agent/agent_13_reference-api-generated.md`
### Procedure
Run `uv run python tools/generate_reference_table.py --manifests` after Plan rows 01/04/05/06/07/09 land;
commit the regenerated file unchanged.
### Method
Generator invocation only.
### Details
N/A: no hand edits; the generator decides the content.

## Compatibility considerations
Must land in the same commit as the code rows it describes (release-unit rule), otherwise the drift gate
fails on an intermediate commit.

## Security considerations
N/A: generated documentation.

## Rollback considerations
Revert the whole unit commit; re-run the generator after any revert.

## Validation plan
- `uv run python tools/generate_reference_table.py --check`
- `uv run pytest tests/tools/test_generate_reference_table.py -q`

## Completion criteria
The reference contains no `log_approval_decision` entry and matches every current approval-module
docstring with zero drift (AC-011).

## Out of Scope
The source docstrings (rows 01/03/07/09), the manifest (row 34).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the generator and commit the regenerated file | Completed | 20261119-081802 | 20261119-081802 | `generate_reference_table.py --manifests` re-run after rows 01-32; regenerated unchanged from the mid-batch regeneration (final regen is the row 33/34 no-op expected); `log_approval_decision` count in the reference is 0; guarded block not hand-edited |
| 3 | Run the drift gate and the full validation sequence | Completed | 20261119-081802 | 20261119-081802 | `generate_reference_table.py --check`: no drift; 16 test_generate_reference_table tests pass |

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
- **Requirement ID**: `REQ-011` (generated artifacts reflect the change)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/23_agent/agent_13_reference-api-generated.md`
