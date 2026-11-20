## Goal

- Remove the plan-local identifier from the `validate_diagnostics_retention_days` docstring (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- Plan step 4. A docstring-only change; the docstring feeds the generated agent reference, so the manifest and reference documents are regenerated afterwards (the `registry/manifests/agent_api.yaml` and `agent_14` procedures).

## Assumptions

- The docstring text is rendered into `registry/manifests/agent_api.yaml` and `docs/23_agent/agent_14_reference-api-subpackages-generated.md` (checked in the plan-to-implementation-procedure cycle).

## Design decisions

- Keep the factual part of the docstring (an int; `<= 0` disables purge) and drop only the plan reference.

## Alternatives considered

N/A: a text edit; the Plan fixes the change.

## Implementation
### Target file
`scripts/agent/services/config_validators.py`
### Procedure
1. Change the docstring `Validate retention_days is an int (<= 0 disables purge; preserved per UNK-03).` to `Validate retention_days is an int (<= 0 disables purge).`
### Method
- Direct docstring edit.
### Details
- Run the generator after this edit (see the manifest procedure); never hand-edit the generated files.

## Compatibility considerations

N/A: docstring only.

## Security considerations

N/A: docstring only; no behavior change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run ruff format scripts/agent/services/config_validators.py` and `uv run ruff check scripts/agent/services/config_validators.py`.
- `uv run pytest tests/agent/services/test_typed_validators.py -q`.
- `uv run python tools/check_docstrings.py`.

## Completion criteria

- The docstring contains no `UNK-` token and the typed validator tests pass (AC-2).

## Out of Scope

- Validator logic and the generated files (their own procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the docstring (Plan step 4) | Completed | 20261120-151344 | 20261120-151344 | Run the generator afterwards Docstring replaced; generator re-run in the same change set (see the manifest procedure). |
| 2 | Run the validation sequence for this row (Validation plan) | Completed | 20261120-151344 | 20261120-151344 | All checkers in the Validation plan pass; tests/agent/services/test_typed_validators.py 572 passed with the eventbus run. |

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
- **Requirement ID**: `REQ-004` (script comment)
- **Source issue**: issues/20261117-123012_adrchk012_traceability-id-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261120-124329_adrchk012_traceability-id-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261120-125111
- **Related target files**: `scripts/agent/services/config_validators.py`