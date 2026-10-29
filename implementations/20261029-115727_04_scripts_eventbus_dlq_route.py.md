## Goal

Carry the acting principal's fingerprint into the DLQ requeue audit record (`REQ-002`; AC-1): `dlq_requeue` receives the wrapper-resolved `Principal` and passes its `token_fingerprint` to `log_privileged_action`.

## Scope

Modify `scripts/eventbus/dlq_route.py` only: the `dlq_requeue` signature and its audit call at lines 70-76. The requeue logic, status mapping and response shape are unchanged.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): `dlq_requeue(request: Request, event_id: str)` is at `dlq_route.py:45`; the audit call at `:70-76` already passes `request_id=request.state.request_id`, `consumer_id=""` (rendered `-` by `_build_audit_record`), `target=event_id`, `detail=""`; `log_privileged_action` is imported directly at `:9`.
- The `app.py` wrapper already resolves `_principal` (`app.py:256`) and passes it per seq 02.
- Sequencing: seq 01 (audit signature with `actor`) and seq 02 (wrapper pass-through) land before or with this row. `plans/done/20261028-231610_ebdlqrecon002_rebuild-missing-dlq-files.md` targets `scripts/eventbus/dlq.py`, not this route file; no conflict.

## Design decisions

- `principal: Principal` is added as the third parameter (after `event_id`); app.py passes it by keyword (seq 02).
- `consumer_id=""` stays as is: the actor identity moves to the dedicated `actor` field instead of overloading `consumer_id`.

## Alternatives considered

- Putting the fingerprint into `consumer_id`: rejected; REQ-002 names a new `actor` field and REQ-007 freezes existing field semantics.

## Implementation
### Target file

`scripts/eventbus/dlq_route.py`

### Procedure

1. Add `principal: Principal` to `dlq_requeue`'s signature and import `Principal` alongside the existing `from eventbus.audit import log_privileged_action` block (`from eventbus.auth import Principal`).
2. Extend the audit call at `:70-76` with `actor=principal.token_fingerprint`.

### Method

Two-line-scale edits; no logic change.

### Details

- Only the successful-requeue branch emits the audit record today; that guard stays.

## Compatibility considerations

- Additive call argument; the record gains only the `actor` key (seq 01 typing). No HTTP contract change.

## Security considerations

- Only the non-secret fingerprint is emitted; the raw operator token never appears.

## Rollback considerations

- Remove the parameter and the `actor=` argument; revert together with seq 02's call-site change.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py` (seq 08 adds the audit assertion patching `eventbus.dlq_route.log_privileged_action`).
- `uv run ruff check scripts/eventbus/dlq_route.py` and `uv run mypy scripts/eventbus/dlq_route.py`.

## Completion criteria

- A successful requeue emits a record with non-empty `actor` equal to the operator token fingerprint and the real request id; static gates clean.

## Out of Scope

- DLQ requeue/promotion logic, `dlq_list`, DLQ file operations.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land with/after seq 01+02 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests are seq 08 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | Doc rows are seq 10 |

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
- **Requirement ID**: REQ-002 (AC-1)
- **Source issue**: `issues/20261028-122415_ebaudit005_privileged-audit-actor-context.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261028-234417_ebaudit005_privileged-audit-actor-context.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261029-115727
- **Related target files**: scripts/eventbus/dlq_route.py
