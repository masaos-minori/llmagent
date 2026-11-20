## Goal

- Regenerate the agent API manifest so it no longer carries the plan-local identifier in the `validate_diagnostics_retention_days` docstring (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 4. A fallout row added to the Frozen Plan in the plan-to-implementation-procedure cycle (`tools/amend_plan.py`, class fallout). This document runs the generator once; the `agent_14` procedure verifies its output.

## Assumptions

- The manifest is generated; it is never hand-edited. Only the `validate_diagnostics_retention_days` entry is expected to change (`generate_reference_table.py --check` reports no drift today).

## Design decisions

- One generator run produces the manifest and the rendered reference documents together.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`registry/manifests/agent_api.yaml`
### Procedure
1. After the `config_validators.py` docstring change, run `uv run python tools/generate_reference_table.py --manifests`.
2. Confirm with `git diff --stat` that only this file and `docs/23_agent/agent_14_reference-api-subpackages-generated.md` changed, each in the docstring row, then run `uv run python tools/generate_reference_table.py --check`.
### Method
- Generated change; no manual edit.
### Details
- If the run changes any other file, stop and report instead of staging it.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit (the reference document reverts with it).

## Validation plan

- `uv run python tools/generate_reference_table.py --check`.
- `uv run pytest tests/tools/test_generate_reference_table.py -q`.

## Completion criteria

- The manifest entry contains no `UNK-` token and `--check` reports no drift (AC-2).

## Out of Scope

- Hand edits of generated content and any other manifest.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Regenerate the manifest (Plan step 4) | Completed | 20261120-151344 | 20261120-151344 | After the config_validators.py procedure Regenerated; single summary line changed in agent_api.yaml; the other manifests were rewritten byte-identical. |
| 2 | Run the validation sequence for this row (Validation plan) | Completed | 20261120-151344 | 20261120-151344 | All checkers in the Validation plan pass. |

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
- **Requirement ID**: `REQ-004` (regenerated manifest)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `registry/manifests/agent_api.yaml`