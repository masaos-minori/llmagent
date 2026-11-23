## Goal

Add five nullable result-metadata columns to `dedup_call_state` and raise `_USER_VERSION` from 1 to 2, so every existing store fails the open-time fingerprint gate as `schema_mismatch`.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the DDL string and the version constant. No new table, no NOT NULL column, no migration code.

## Assumptions

- Verified: `_SCHEMA` defines `dedup_call_state` with `result_json TEXT` as its last column; the fingerprint is computed from the canonical DDL, so editing the DDL moves it without further code.
- Verified: `tools/check_db_separation.py` registers tables, not columns, so it needs no change.
- Persisted-schema checklist outcomes are recorded in the Plan Design section; this row applies them.

## Design decisions

- Append `result_sha256 TEXT`, `result_size_bytes INTEGER`, `result_class TEXT`, `result_code TEXT`, `external_ref TEXT` after `result_json`; all nullable.
- Do not add a CHECK on `result_class` (new): the closed vocabulary is enforced in code (`RESULT_CLASSES`), and a CHECK would change nothing the fingerprint gate does not already guard.

## Alternatives considered

Rejected: a separate call_result_meta table (would change the three-table set that three tests and `check_db_separation.py` pin).

## Implementation
### Target file
`scripts/shared/mcp_dedup_schema.py`

### Procedure
1. Edit the `_SCHEMA` DDL to add the five columns in the order above.
2. Set `_USER_VERSION = 2`.
3. Update the comment above `RESULT_MAX_CHARS` only if it implies the preview is the only stored fact.

### Method
Single-file edit of the constants in `scripts/shared/mcp_dedup_schema.py`; `CREATE TABLE IF NOT EXISTS` stays, because an existing store is refused before DDL runs.

### Details
- Do not touch `store_meta` or `call_attempt_history`.
- Rows 26, 27, 38, 39 and 40 carry the fallout of the version bump (pinned `== 1` checks, the deploy gate, the generated manifest).

## Compatibility considerations

Breaking for existing stores by design: they are refused as `schema_mismatch` and the operator re-initializes them (disposable-store policy, `docs/41_db/db_08_active_databases.md` runbook).

## Security considerations

N/A: no new data class; columns hold hashes, sizes, class labels, and an opaque external reference.

## Rollback considerations

Revert the commit; a store initialized at version 2 is then refused by the old code and re-initialized (disposable store).

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_identity.py tests/shared/test_mcp_dedup_concurrency.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- The DDL carries the five nullable columns, `_USER_VERSION` is 2, and a fresh store initializes at version 2 while an old-shape store is refused as `schema_mismatch`.

## Out of Scope

Ledger writes (row 04), row classification (row 03), and operator runbook text (docs rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (result metadata and result classes at finalization), `REQ-006` (store schema bump and fingerprint refusal)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/shared/mcp_dedup_schema.py`
