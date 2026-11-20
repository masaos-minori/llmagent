## Goal

- Regenerate the agent subpackage reference from the manifests so it no longer renders the plan-local identifier (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 4. Produced by the same generator run as the `registry/manifests/agent_api.yaml` procedure; execute after the `config_validators.py` docstring change.

## Assumptions

- The file is generated; it is never hand-edited. Only line 118 (the `validate_diagnostics_retention_days` row) is expected to change.

## Design decisions

- Use the generator; verify the diff instead of editing.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`docs/23_agent/agent_14_reference-api-subpackages-generated.md`
### Procedure
1. Run the generator once, as described in the manifest procedure, and confirm that this file changes only in the `validate_diagnostics_retention_days` row.
2. Run `uv run python tools/generate_reference_table.py --check` and confirm `No drift found`.
### Method
- Generated change; no manual edit.
### Details
- `git diff -- docs/23_agent/agent_14_reference-api-subpackages-generated.md` shows a single-row change.

## Compatibility considerations

N/A: documentation row; no decision text changes.

## Security considerations

N/A: documentation row.

## Rollback considerations

N/A: revert the commit (the manifest and this document revert together).

## Validation plan

- `uv run python tools/generate_reference_table.py --check`.
- `uv run pytest tests/tools/test_generate_reference_table.py -q`.
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`.

## Completion criteria

- The reference row contains no `UNK-` token and `--check` reports no drift (AC-2).

## Out of Scope

- Any hand edit of generated content.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify the regenerated reference (Plan step 4) | Pending | — | — | Same generator run as the manifest procedure |
| 2 | Run the validation sequence for this row (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (regenerated reference)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `docs/23_agent/agent_14_reference-api-subpackages-generated.md`
