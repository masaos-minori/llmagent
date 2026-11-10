## Goal
- Reduce `scripts/eventbus/app.py` to wiring: keep the app object, lifespan, middleware, and DLQ loop, and include the route modules' routers; remove all nine wrapper handlers (REQ-003) so the role and pair authorization live only on the route-module functions (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, in two steps: Phase 2 removes the wrappers for `/health`, `/publish`, `/replay`, `/dlq`, `/dlq/{event_id}/requeue`, `/admin/topics/authorization`; Phase 3 removes the `/subscribe`, `/events/{event_id}/ack`, `/nack` wrappers and `resolve_subscribe_identity`.
- Not in scope: `lifespan`, `_shutdown_lifespan`, `_dlq_loop`, `_main`, host binding (loopback verification stays untouched).
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14).

## Assumptions
- Moving a route to an `APIRouter` keeps URL, method, parameters, and response shape unchanged (no router prefix); `eventbus.app` includes the router. Falsifiable by the Phase 1 registry test and the existing `tests/eventbus/` suite.
- Tests depend on these `eventbus.app` attributes and they stay: `app`, `lifespan`, `_shutdown_lifespan`, `open_db`, `EventBroker`, `orjson`, `load_config`, `get_schema_path`, `_ENVELOPE_SCHEMA_PATH`, `reconcile_missing_dlq_files`, `log_privileged_action`. The `*_route` aliases are removed; their only users are the hand-copied routes of `tests/eventbus/test_eventbus_auth.py` (document 10).
- Overlap with plans 002 and 006: none on this file (compatible).

## Design decisions
- Register routers in the original route order (health, publish, replay, subscribe, dlq, ack/nack, admin) so `app.routes` order and the OpenAPI path order stay as before.
- `attach_auth_middleware(app)` stays before the `include_router` calls.

## Alternatives considered
N/A: decided in the Plan's Design section (Option A, APIRouter per module).

## Implementation
### Target file
`scripts/eventbus/app.py`

### Procedure
1. Phase 2: import `router as health_router` from `eventbus.health_route`, and the routers of `publish_route`, `replay_route`, `dlq_route`, `admin_route` (name each alias `<module>_router` (new)); call `app.include_router(...)` for each after `attach_auth_middleware(app)`; delete the wrappers `health`, `publish`, `replay`, `dlq_list`, `dlq_requeue`, `admin_topics_authorization` and their `*_route`/`health_check` imports.
2. Phase 3: import and include the `subscribe_route` and `ack_route` routers; delete the wrappers `subscribe`, `ack_event`, `nack` and `resolve_subscribe_identity`.
3. Remove imports left unused (`Depends`, `Query`, `Request`, `JSONResponse`, `Literal`, `Principal`, `Role`, `require_consumer_identity`, `require_role`, `resolve_principal`, any unused `typing.Any` use) as `ruff` reports them; keep `get_config`, `get_db`, `run_with_db_lock`, `current_generation`, `build_and_publish_generation`, `log_privileged_action`.
4. Before the first removal, snapshot `app.openapi()["paths"]` (UNK-01) and compare after each phase ignoring `operationId`.

### Method
- `app.include_router(<router>)` with no prefix and no extra dependencies, so each route keeps exactly the dependencies declared on its function.

### Details
- Import cycle check: route modules import `eventbus.auth`, `eventbus.route_helpers`, repositories; none imports `eventbus.app`, so `app.py` importing them is acyclic (`PYTHONPATH=scripts uv run lint-imports` also confirms).
- Do not touch `_LoopbackVerifyingServer` or `_main`.

## Compatibility considerations
- Registered paths, methods, and parameters are unchanged; `operationId` changes for two routes (see the route documents). `eventbus.app.<name>_route` aliases disappear (only test code used them).

## Security considerations
- Authentication and authorization behavior must not change: run the Phase 1 production-app tests before and after each phase; the loopback-only bind code is untouched.

## Rollback considerations
- Revert the phase's commit (the route-module documents of the same phase revert with it).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_route_registry.py -v` (uniqueness and negative authorization), then `uv run pytest tests/eventbus -v`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`.

## Completion criteria
- `app.py` defines no route handler and no `resolve_subscribe_identity`; `rg -n "@app\.(get|post)" scripts/eventbus/app.py` returns nothing.
- `app.routes` contains the same nine `(method, path)` pairs as before (registry test).
- Listed checks pass.

## Out of Scope
- Lifespan, DLQ loop, startup, and binding code.
- Any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 2: include the five routers and remove their wrappers from `scripts/eventbus/app.py` | Pending | — | — | |
| 2 | Phase 3: include the two consumer routers, remove the remaining wrappers and `resolve_subscribe_identity`, and clean unused imports | Pending | — | — | |
| 3 | Run the tests named in Validation plan after each phase | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Related target files**: `scripts/eventbus/app.py`
