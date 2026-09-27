## Goal

Register a new `POST /admin/topics/authorization` route in `scripts/eventbus/app.py`, wired to the handler in `scripts/eventbus/admin_route.py` (row 2 of this Plan) and gated by the existing `Role.ADMIN` requirement (REQ-001, REQ-002).

## Scope

In scope: one new route registration in `app.py`, following the existing per-route import/registration pattern. Out of scope: the handler's own logic (row 2); the auth-wiring mechanism (row 3, currently Blocked — see that document's Blocker Log).

## Assumptions

- Row 2 (`scripts/eventbus/admin_route.py`) exposes a single async handler function this row imports and registers, following the same shape as `publish_route.py::publish()`/`subscribe_route.py::subscribe()`.

## Design decisions

- Follow the existing registration pattern exactly (`from eventbus.publish_route import publish as publish_route`, then a corresponding `app.add_api_route(...)` or decorator-based registration, whichever `app.py` currently uses for its other routes — confirm the exact mechanism by reading `app.py` in full before editing, since this document's own investigation read only the import list, not the registration calls themselves).

## Alternatives considered

- Registering the route directly in `app.py` without a separate `admin_route.py` module: rejected — breaks the existing one-module-per-route convention this file otherwise follows for every other route.

## Implementation

### Target file

`scripts/eventbus/app.py`

### Procedure

1. Add the import for row 2's handler function: `from eventbus.admin_route import update_topics_authorization as update_topics_authorization_route` (or the actual name row 2 defines), following the exact pattern used for every other route (e.g. `from eventbus.publish_route import publish as publish_route`, confirmed at the top of `app.py`).
2. Register the route with `@app.post("/admin/topics/authorization")` on a thin wrapper `async def` function that delegates to the imported handler, matching the exact shape of `/publish`'s wrapper (lines 154-158).
3. Add `_principal: Principal = Depends(require_role(Role.ADMIN))` as a parameter on the wrapper function — confirmed as the correct, explicit gating mechanism by reading `/replay`, `/dlq`, `/subscribe`, `/events/{event_id}/ack`, and `/nack`'s existing wrappers, every one of which declares its role dependency this way (e.g. `Depends(require_role(Role.OPERATOR))` at line 169); auth is opt-in per route via this explicit parameter, not a global path-prefix middleware.

### Method

Additive route registration, following an established local pattern exactly (confirmed via Read of 5 existing route wrappers) — no new registration mechanism.

### Details

- Confirmed via Read (`app.py` lines 148-247): every role-gated route (`/replay`, `/subscribe`, `/dlq`, `/dlq/{event_id}/requeue`, `/events/{event_id}/ack`, `/nack`) declares `_principal: Principal = Depends(require_role(Role.<X>))` explicitly as a function parameter — this is the confirmed, concrete mechanism for REQ-002's ADMIN gating, not the `_ROUTE_ROLE_MAP` dict alone (that dict's exact runtime role, if any beyond documentation/reference, was not traced further — this row's gating relies on the explicit `Depends()` parameter, which is unambiguous and already proven correct by 5 existing routes).
- `/publish` (lines 154-158) is a rare exception with no visible `Depends(require_role(...))` parameter in the reviewed range — do not use it as the pattern to copy; use one of the 5 role-gated routes instead, as done above.

## Compatibility considerations

Additive change — existing routes are unaffected.

## Security considerations

The `Depends(require_role(Role.ADMIN))` parameter (Procedure step 3) is not optional — omitting it would silently bypass ADMIN gating entirely, since (per Details) gating is opt-in per route, not enforced by a global prefix middleware.

## Rollback considerations

`git revert` the commit, or remove the added import and registration lines.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `scripts/eventbus/app.py` | Integration | `uv run pytest tests/eventbus/test_admin_topics_authorization.py -q` | AC-2 (non-ADMIN rejection) passes, confirming the route is actually gated |
| `scripts/eventbus/app.py` | Static | `uv run ruff check scripts/eventbus/app.py && uv run mypy scripts/eventbus/app.py` | Pass |

## Completion criteria

- The new route is reachable at `POST /admin/topics/authorization` and rejects a non-ADMIN-token request (AC-2).

## Out of scope

- The handler's own request-validation and update logic (row 2).
- The auth-wiring mechanism itself (row 3, Blocked).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260927-144037 | 20260927-144037 | Depends on row 2 (`admin_route.py`) existing to import from |
| 2 | Add or update tests per Validation plan | Completed | 20260927-144037 | 20260927-144037 | Covered by `tests/eventbus/test_admin_topics_authorization.py` (row 5) Covered by tests/eventbus/test_admin_topics_authorization.py (row 5) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260927-144037 | 20260927-144037 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260927-144037 | 20260927-144037 | N/A: no `docs/00_index.md` task-scope row maps this specific route addition |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/done/20260927-115652_eventbus007_implement-agent-eventbus-topic-management-integration.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-121125_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-123813
- **Related target files**: scripts/eventbus/app.py