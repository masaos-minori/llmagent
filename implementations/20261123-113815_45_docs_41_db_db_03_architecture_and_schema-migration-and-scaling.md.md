## Goal

Update the mcp_dedup row of the schema table from `PRAGMA user_version = 1` to 2 and name the new result columns.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `mcp_dedup.sqlite` table row (about line 76).

## Assumptions

- Verified: the row says `PRAGMA user_version = 1` and describes the current three-table ledger shape.

## Design decisions

- Keep the recovery column text; only the stamp and shape description change.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`

### Procedure
1. Change the stamp to 2 and mention the nullable result-metadata columns in the shape description.

### Method
One table-row edit.

### Details
- The recovery text (operator archives the refused file, `resolve_store` creates a new generation) stays.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`

## Completion criteria

- The row states version 2 and the new columns; the gates pass.

## Out of Scope

Other rows of the table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (store schema bump and fingerprint refusal), `REQ-007` (documentation of the control contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `docs/41_db/db_03_architecture_and_schema-migration-and-scaling.md`
