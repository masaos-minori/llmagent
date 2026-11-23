## Goal

Persist the result metadata at finalization, expose a read-only `call_state_view` (new), and add the history append used to record a reconcile decision.

## Scope
**Release unit**: N/A: not part of a release unit

In scope: `_fetch_locked`, `record_completed`, `record_failed`, and two new methods. Behavior of lease, acquisition, and `reconcile_execution` is unchanged. Size gate: file is about 19.2 KB of 24.6 KB.

## Assumptions

- Verified: `record_completed` binds `_cap_result(result)` in its UPDATE and `_fetch_locked` selects an explicit column list, so both must be widened together.
- Verified: `reconcile_execution` already refuses a live lease and exhausted attempts with `DedupLeaseConflict` and appends a `reconciled` history row.
- If the added code pushes the file past the size gate, move `call_state_view` (new) into a new `shared/mcp_dedup_view.py` (Plan risk fallback); that would be an additional target file and stops this procedure as Blocked.

## Design decisions

- `record_completed(..., external_ref=None)`: classify with `classify_result`; write `result_json`, `result_sha256` (new), `result_size_bytes` (new), and `result_class` (`secure_reference` when `external_ref` is given, otherwise the classified class), plus `external_ref`.
- `record_failed` writes `result_class='replay_unavailable'` and `result_code=error_class` in the same UPDATE.
- `call_state_view(key, now_epoch=None)` returns `CallStateView | None` from one `_fetch_locked` read: `lease_live` (new) is `pending` with an unexpired lease; `attempts_exhausted` (new) is `attempt_number >= max_attempts`; `agent_state` (new) from `agent_state_for`; `error_code` is `handler_failed` (new) for failed rows else `none`.
- `append_reconcile_evidence(key, outcome, digest, now_epoch=None)` inserts one `call_attempt_history` row (outcome `reconcile_decision` (new), detail `<outcome>:<digest>`) in a write transaction; it never touches `dedup_call_state`.

## Alternatives considered

Rejected: computing the view in the control API from `get_execution` (the ledger owns lease and attempt semantics; duplicating them risks drift).

## Implementation
### Target file
`scripts/shared/mcp_dedup_ledger.py`

### Procedure
1. Widen the `_fetch_locked` SELECT with the five columns.
2. Update `record_completed` and `record_failed` UPDATE statements and bindings.
3. Add `call_state_view` (new) and `append_reconcile_evidence` (new).

### Method
Reuse `_write_txn` and `_append_history`; reads stay under `self._lock`. No new SQL outside these statements.

### Details
- Keep terminal rows immutable: the metadata is written only by the owner-conditional finalization UPDATE.
- Do not log result bodies or digests above debug level.

## Compatibility considerations

Callers of `record_completed` and `record_failed` are unchanged (new keyword is optional). The widened SELECT needs the version-2 schema, which row 02 guarantees.

## Security considerations

The view contains only structured fields; `result_code` (new) is the error class name, never an exception message or path.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/shared/test_mcp_dedup.py tests/shared/test_mcp_dedup_identity.py tests/shared/test_mcp_dedup_concurrency.py tests/mcp_servers/test_mcp_dispatch.py`

## Completion criteria

- Completed and failed rows carry the metadata; `call_state_view` (new) returns the projection for known keys and `None` otherwise; `append_reconcile_evidence` (new) records one history row; the file is under the size gate.

## Out of Scope

The control endpoints (row 09) and reconcile decision logic (row 09).

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
- **Requirement ID**: `REQ-001` (control endpoints and response shape), `REQ-003` (result metadata and result classes at finalization), `REQ-004` (reconciler contract)
- **Source issue**: issues/20261120-115843_mcpdl004_call-state-control-api.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-090353_mcpdl004_call-state-control-api.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-113815
- **Related target files**: `scripts/shared/mcp_dedup_ledger.py`
