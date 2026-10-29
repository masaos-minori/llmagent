## Goal

Carry the acting principal's fingerprint into the replay audit record (`REQ-002`; AC-1): the replay handler receives the wrapper-resolved `Principal` and passes its `token_fingerprint` to `log_privileged_action`.

## Scope

Modify `scripts/eventbus/replay_route.py` only: the `replay` signature and its audit call at lines 38-44. Pagination, SSE/JSON rendering and the counts logic are unchanged.

## Assumptions

- Source claims re-verified this cycle (2026-10-29): `async def replay(request: Request, since_seq: int = Query(...), fmt: ..., limit: ..., offset: ...)` is at `replay_route.py:27-33`; the audit call at `:38-44` already passes `request_id=request.state.request_id`, `consumer_id=""`, `target=f"seq:{since_seq}"`, `detail=""`; `log_privileged_action` is imported at `:11`.
- The `app.py` replay wrapper resolves `_principal` (`app.py:208`) and passes it per seq 02.
- Sequencing: seq 01 and seq 02 land before or with this row. The archived `plans/done/20261028-231631_ebpage003_pagination-contract-dlq-index.md` touched this file's pagination contract earlier (procedures under `implementations/20261029-094100_*`); its procedure rows for this file already exist, so re-anchor line numbers at implementation time.

## Design decisions

- `principal: Principal` is added as the second parameter (after `request`); app.py passes it by keyword (seq 02), so the `Query` defaults of the other parameters are untouched.
- `consumer_id=""` stays as is; the identity moves to the `actor` field.

## Alternatives considered

- Deriving the actor inside the route from `request.state`: rejected; the principal is never stored on `request.state` today and adding that would exceed the Plan's wrapper-only plumbing decision.

## Implementation
### Target file

`scripts/eventbus/replay_route.py`

### Procedure

1. Add `principal: Principal` after `request` in the `replay` signature and import `Principal` from `eventbus.auth`.
2. Extend the audit call at `:38-44` with `actor=principal.token_fingerprint`.

### Method

Two-line-scale edits; no logic change.

### Details

- The audit record is emitted once per replay request before the SSE/JSON split; that position stays.

## Compatibility considerations

- Additive call argument and record key only; SSE/JSON response contracts unchanged.

## Security considerations

- Only the non-secret fingerprint is emitted; the raw operator token never appears.

## Rollback considerations

- Remove the parameter and the `actor=` argument; revert together with seq 02's call-site change.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_replay_pagination.py` (seq 09 adds the audit assertion patching `eventbus.replay_route.log_privileged_action`).
- `uv run ruff check scripts/eventbus/replay_route.py` and `uv run mypy scripts/eventbus/replay_route.py`.

## Completion criteria

- A replay request emits a record with non-empty `actor` equal to the operator token fingerprint and the real request id; static gates clean.

## Out of Scope

- Pagination semantics, SSE streaming, `_count_events_since`, the subscribe endpoint.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Land with/after seq 01+02 |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests are seq 09 |
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
- **Related target files**: scripts/eventbus/replay_route.py
