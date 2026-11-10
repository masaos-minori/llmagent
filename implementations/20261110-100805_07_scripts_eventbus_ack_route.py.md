## Goal
- Make `scripts/eventbus/ack_route.py` own its route(s) `POST /events/{event_id}/ack and POST /nack`: register the handler through an `APIRouter` with the role dependency on the same function (REQ-003 one registered handler per route; REQ-004 role enforced on that function).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, Phase 3 of the Plan.
- Not in scope: `scripts/eventbus/app.py` wiring (separate document), tests, documents.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14).

## Assumptions
- Moving a route to an `APIRouter` keeps URL, method, parameters, and response shape unchanged (no router prefix); `eventbus.app` includes the router. Falsifiable by the Phase 1 registry test and the existing `tests/eventbus/` suite.
- Overlap with plan `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` and plan `plans/20261110-095717_adrrev006_eventbus-future-decision.md`: no shared file in this row (compatible).

## Design decisions
- Keep the existing function name `ack_event` as the registered handler; drop the same-named wrapper in `app.py` (separate document).
- Role dependency: `Depends(require_role(Role.CONSUMER))` declared on the handler's principal parameter; no change to `require_role` or `Principal`.

## Alternatives considered
N/A: the registration decision (APIRouter per module) was made in the Plan's Design section.

## Implementation
### Target file
`scripts/eventbus/ack_route.py`

### Procedure
1. In `scripts/eventbus/ack_route.py`, add `router = APIRouter()` (new) and import `APIRouter`, `Depends` from `fastapi` and `Principal`, `Role`, `require_role` from `eventbus.auth` (existing imports are kept).
2. Decorate `ack_event` with the route decorator(s) listed under Details and give its principal parameter the `Depends(require_role(Role.CONSUMER))` default.
3. Do not change the handler body, logging, audit calls, or responses.
4. Run the module's tests named under Validation plan.

### Method
- Use `@router.get(...)`/`@router.post(...)` with the same path strings `app.py` uses today; keep return annotations as they are in `app.py` today so FastAPI builds the same response handling.

### Details
- Routes: `@router.post("/events/{event_id}/ack")` on `ack_event` and `@router.post("/nack")` on `nack`; both take `_principal: Principal = Depends(require_role(Role.CONSUMER))` and drop the unused `_identity` parameter.
- `authorize_event_pair` stays the single pair check (it needs the event topic from the database, so it remains a call inside the handler); its `principal is None` branch stays as a fail-closed guard for direct callers of `_do_ack`.
- `_do_ack` keeps `_principal: Principal | None` (internal helper); `ack_event` passes `_principal` through as today.
- Keep the `consumer_id: str = Query(...)` and `idempotency_key` query parameters as declared.

## Compatibility considerations
- URL, method, query parameters, status codes, and response bodies are unchanged. The OpenAPI `operationId` of a route follows the function name; it changes only for `/health` (`health` to `health_check`) and `/admin/topics/authorization` (`admin_topics_authorization` to `update_topics_authorization`); no consumer of operationId exists in the repository (checked with `rg operationId`).

## Security considerations
- The role gate moves from the `app.py` wrapper to this function with the same role; the Phase 1 production-app tests (document 09) and `test_every_production_api_route_has_a_role_dependency` must pass unchanged before and after.

## Rollback considerations
- Revert this file's commit; the `app.py` wrapper change is reverted together with it (same phase).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py tests/eventbus/test_eventbus_ack_endpoint.py tests/eventbus/test_eventbus_consumer_authorization.py tests/eventbus/test_eventbus_crash_ack.py -v`
- `uv run pytest tests/eventbus -v`, `uv run ruff check scripts/eventbus/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.

## Completion criteria
- `scripts/eventbus/ack_route.py` defines `router` with the route(s) above; the role dependency sits on the registered function.
- `rg -n "^(async )?def ack_event\b" scripts/eventbus/` returns exactly one match.
- The listed tests and checks pass.

## Out of Scope
- Changing response shapes, the role model, or tokens.
- Editing any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the router, decorators, and the principal dependency in `scripts/eventbus/ack_route.py` | Pending | — | — | |
| 2 | Run the tests named in Validation plan | Pending | — | — | |
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
- **Related target files**: `scripts/eventbus/ack_route.py`
