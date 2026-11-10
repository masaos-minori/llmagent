## Goal
- Make `scripts/eventbus/subscribe_route.py` own its route(s) `GET /subscribe`: register the handler through an `APIRouter` with the role dependency on the same function (REQ-003 one registered handler per route; REQ-004 role enforced on that function).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 3 of the Plan.
- Not in scope: `scripts/eventbus/app.py` wiring (separate document), tests, documents.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14).

## Assumptions
- Moving a route to an `APIRouter` keeps URL, method, parameters, and response shape unchanged (no router prefix); `eventbus.app` includes the router. Falsifiable by the Phase 1 registry test and the existing `tests/eventbus/` suite.
- Overlap with plan `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` and plan `plans/20261110-095717_adrrev006_eventbus-future-decision.md`: no shared file in this row (compatible).

## Design decisions
- Keep the existing function name `subscribe` as the registered handler; drop the same-named wrapper in `app.py` (separate document).
- Role dependency: `Depends(require_role(Role.CONSUMER))` declared on the handler's principal parameter; no change to `require_role` or `Principal`.

## Alternatives considered
N/A: the registration decision (APIRouter per module) was made in the Plan's Design section.

## Implementation
### Target file
`scripts/eventbus/subscribe_route.py`

### Procedure
0. Confirm no other direct caller exists: `rg -n "subscribe_route\.subscribe|from eventbus.subscribe_route import" scripts tests`.
1. In `scripts/eventbus/subscribe_route.py`, add `router = APIRouter()` (new) and import `APIRouter`, `Depends` from `fastapi` and `Principal`, `Role`, `require_role` from `eventbus.auth` (existing imports are kept).
2. Decorate `subscribe` with the route decorator(s) listed under Details and give its principal parameter the `Depends(require_role(Role.CONSUMER))` default.
3. Do not change the handler body, logging, audit calls, or responses.
4. Run the module's tests named under Validation plan.

### Method
- Use `@router.get(...)`/`@router.post(...)` with the same path strings `app.py` uses today; keep return annotations as they are in `app.py` today so FastAPI builds the same response handling.

### Details
- Move `resolve_subscribe_identity` (new in this module) here from `app.py` with the same body: it calls `require_consumer_identity(request, consumer_id=consumer_id, topics=topic, principal=principal)` with `principal` resolved through `Depends(resolve_principal)`; define it before `subscribe` because the decorator evaluates `Depends(...)` at import.
- Route: `@router.get("/subscribe")`; the signature becomes `request, topic=Query(default=[]), since_seq=Query(default=0, ge=0), consumer_id=Query(default=""), _principal: Principal = Depends(require_role(Role.CONSUMER)), _identity: Principal = Depends(resolve_subscribe_identity)`; dependency evaluation order is unchanged.
- Drop the `None` defaults of `_principal`/`_identity`: the principal is now always injected, and the existing `if _principal is not None` guards in the body may stay (harmless) or be simplified only if tests still pass; do not change the 400/403 outcomes.
- Direct callers: `tests/eventbus/test_eventbus_subscribe_transition.py:233` calls `subscribe_route.subscribe` without a principal; it is a Plan row (document 15) and must be updated in the same phase.
- Tests patch `eventbus.subscribe_route.run_with_db_lock`, `get_broker`, `get_db` through `sr_module`; those names stay.

## Compatibility considerations
- URL, method, query parameters, status codes, and response bodies are unchanged. The OpenAPI `operationId` of a route follows the function name; it changes only for `/health` (`health` to `health_check`) and `/admin/topics/authorization` (`admin_topics_authorization` to `update_topics_authorization`); no consumer of operationId exists in the repository (checked with `rg operationId`).

## Security considerations
- The role gate moves from the `app.py` wrapper to this function with the same role; the Phase 1 production-app tests (document 09) and `test_every_production_api_route_has_a_role_dependency` must pass unchanged before and after.

## Rollback considerations
- Revert this file's commit; the `app.py` wrapper change is reverted together with it (same phase).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_subscribe.py tests/eventbus/test_eventbus_consumer_authorization.py tests/eventbus/test_eventbus_restart_resume.py -v`
- `uv run pytest tests/eventbus -v`, `uv run ruff check scripts/eventbus/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `scripts/eventbus/subscribe_route.py` defines `router` with the route(s) above; the role dependency sits on the registered function.
- `rg -n "^(async )?def subscribe\b" scripts/eventbus/` returns exactly one match.
- The listed tests and checks pass.

## Out of Scope
- Changing response shapes, the role model, or tokens.
- Editing any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move `resolve_subscribe_identity` into `scripts/eventbus/subscribe_route.py` and register `subscribe` on the router | Pending | — | — | |
| 2 | Run the tests named in Validation plan (the direct-call test is updated by document 15 in the same phase) | Pending | — | — | |
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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-090758_adrrev001_eventbus-route-handlers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-100805
- **Related target files**: `scripts/eventbus/subscribe_route.py`
