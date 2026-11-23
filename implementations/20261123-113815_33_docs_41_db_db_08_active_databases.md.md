## Goal

Update the `mcp_dedup.sqlite` facts for the new columns and version stamp and state that a pre-existing store is refused and re-initialized with the existing runbook.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the `## mcp_dedup.sqlite` bullets and one paragraph in the operator runbook. Other databases are unchanged.

## Assumptions

- Verified: the Schema authority bullet says `PRAGMA user_version = 1`, and the runbook already describes `resolve_store`, which archives a drifted store and creates a new generation, so no new runbook procedure is needed.

## Design decisions

- Reuse the existing runbook for the upgrade path; add one sentence naming the version bump as a `schema_mismatch` cause.

## Alternatives considered

N/A: documentation only.

## Implementation
### Target file
`docs/41_db/db_08_active_databases.md`

### Procedure
1. Change `PRAGMA user_version = 1` to 2 in the Schema authority bullet.
2. In Row semantics, add the five nullable result-metadata columns (`result_sha256`, `result_size_bytes`, `result_class`, `result_code`, `external_ref`) and the four result classes.
3. In the runbook, add that stores created before this change fail the open-time fingerprint gate as `schema_mismatch` and are resolved with `resolve_store`; there is no in-place migration.

### Method
Prose edits only; keep the bullet style.

### Details
- Retention remains `purge_expired`; do not describe new retention behavior.

## Compatibility considerations

N/A: no behavior change in this row.

## Security considerations

N/A: documentation only; no secret value, approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/run_validation_gates.py`
- `uv run pytest tests/tools/test_generate_reference_table.py`

## Completion criteria

- The document states version 2, the new columns, and the re-initialization path; the gates pass.

## Out of Scope

Other db documents (rows 44 and 45).

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
- **Related target files**: `docs/41_db/db_08_active_databases.md`
