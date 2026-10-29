## Goal

Pass the wrapper-resolved `Principal` from the admin/DLQ/replay wrappers into their route functions in `scripts/eventbus/app.py` so the audit call sites can derive the acting actor (`REQ-002`; AC-1).

## Scope

Modify `scripts/eventbus/app.py` only: the three wrapper bodies (`replay` `:202-217`, `dlq_requeue` `:253-260`, `admin_topics_authorization` `:301-309`) each gain one extra argument in their route-function call. No new dependency, no route-function body change here (seq 03-05 change the callees).

## Assumptions

- Source claims re-verified this cycle (2026-10-29): the replay wrapper declares `_principal: Principal = Depends(require_role(Role.OPERATOR))` at `app.py:208` and calls `replay_route(request, since_seq=..., fmt=..., limit=..., offset=...)`; the `dlq_requeue` wrapper has `_principal` at `:256` and calls `dlq_requeue_route(request, event_id)`; the `admin_topics_authorization` wrapper has `_principal` at `:304` and calls `update_topics_authorization_route(request)`. In all three the resolved principal is currently discarded.
- The ack/nack wrappers already pass `_principal` (ebauth001 region) and are untouched; the edit regions are disjoint.
- Sequencing: `implementations/20261029-101422_02_scripts_eventbus_admin_route.py.md` (archived plan `plans/done/20261029-091959_eventbus001_admin-authz-publish-order.md`) edits `admin_route.py` lines 125-135 while this plan edits the audit-call region and the wrapper lines; land the seq 03-05 procedure after it or rebase. The `app.py` `subscribe` region (ebresumetest004 doc targets) is disjoint.

## Design decisions

- Pass the principal as a keyword argument (`principal=_principal`) to match the new callee signatures from seq 03-05; keyword passing keeps every existing positional argument order intact.
- Wrapper parameter names stay `_principal` (the underscore prefix matches the existing style of role-guarded wrappers; it is no longer unused).

## Alternatives considered

- Storing the principal on `request.state` in middleware: rejected -- it would add a middleware change the Plan explicitly rules out, and the wrappers already hold the resolved object.

## Implementation
### Target file

`scripts/eventbus/app.py`

### Procedure

1. In the `replay` wrapper, extend the `replay_route(...)` call with `principal=_principal`.
2. In the `dlq_requeue` wrapper, change the call to `dlq_requeue_route(request, event_id, principal=_principal)`.
3. In the `admin_topics_authorization` wrapper, change the call to `update_topics_authorization_route(request, principal=_principal)`.

### Method

Direct edits of three call expressions; import names `replay_route`, `dlq_requeue_route`, `update_topics_authorization_route` already exist at `app.py:57-59`.

### Details

- No signature change on the wrappers themselves; FastAPI dependency wiring (`Depends(require_role(...))`) stays as is.
- mypy: the callees gain the matching `principal: Principal` parameter in seq 03-05; land this row after or together with them in the same implementation pass.

## Compatibility considerations

- Internal call wiring only; HTTP contracts and response bodies are unchanged.

## Security considerations

- The principal object is passed in-process; nothing new is logged. The audit-side exposure is handled in seq 01 (fingerprint only).

## Rollback considerations

- Remove the three added keyword arguments; the callees' `principal` parameter (seq 03-05) then needs its own revert -- roll back in reverse seq order (05, 04, 03, then 02).

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_audit.py tests/eventbus/test_admin_topics_authorization.py tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_replay_pagination.py` (seq 06-09 capture the audit kwargs and assert non-empty actor/request_id).
- `uv run ruff check scripts/eventbus/app.py` and `uv run mypy scripts/eventbus/app.py`.

## Completion criteria

- All three wrappers pass the resolved principal; route audit tests (seq 07-09) show a non-empty `actor` equal to the acting token's fingerprint; static gates clean.

## Out of Scope

- Any change to FastAPI dependencies, middleware, or other wrappers (ack/nack, publish, subscribe).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Passed principal through all three wrappers |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests are seq 07-09 |
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
- **Related target files**: scripts/eventbus/app.py
