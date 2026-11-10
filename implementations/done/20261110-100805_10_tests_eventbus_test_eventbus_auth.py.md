## Goal
- Make `_make_test_app` in `tests/eventbus/test_eventbus_auth.py` use the production routers instead of hand-copied routes, so the `*Auth` test classes exercise the registered handlers (REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this one file, in two steps (Phase 2 for the routes whose routers exist then, Phase 3 for the rest).
- Not in scope: the test classes' assertions (unchanged unless a real wiring difference surfaces, see Assumptions), `TestProductionRouteWiring`, other test files.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14).

## Assumptions
- The hand-copied ack route passes an extra `Depends(require_consumer_identity)`, which production does not; the production router removes that difference. A test that only passed because of the copy is a real finding: record it, fix the production behavior or the test expectation with a note, per the Plan's Risks (security-fix rule).
- `_make_test_app` mutates `eb_app.load_config` and `eb_app.get_schema_path`; those attributes remain on `eventbus.app` (document 01).

## Design decisions
- Replace each `@local_app.get/post(...)` block with `local_app.include_router(<module>.router)` for the production routers, imported in `_make_test_app` from `eventbus.<module>_route`.
- Keep `_init_local_state`, the token configuration, the `Principal` override, and the middleware attach.

## Alternatives considered
N/A: decided in the Plan (REQ-005).

## Implementation
### Target file
`tests/eventbus/test_eventbus_auth.py`

### Procedure
1. Phase 2: replace the local `/health`, `/publish`, `/replay`, `/dlq`, `/dlq/{event_id}/requeue`, `/admin/topics/authorization` routes (`test_eventbus_auth.py:145-258`) with `include_router` of `health_route`, `publish_route`, `replay_route`, `dlq_route`, `admin_route` routers.
2. Phase 3: replace the local `/subscribe`, `/events/{event_id}/ack`, `/nack` routes and the local `resolve_subscribe_identity` with `include_router` of the `subscribe_route` and `ack_route` routers; remove imports that become unused (`require_consumer_identity`, `resolve_principal`, `Depends`, `Query`, `JSONResponse` as ruff reports).
3. After each phase run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`; investigate any new failure as a possible wiring difference before changing an assertion.
4. Assert at the end that `_make_test_app` declares no `@local_app.get`/`@local_app.post` (`rg -n "@local_app\.(get|post)" tests/eventbus/test_eventbus_auth.py` returns nothing).

### Method
- `local_app.include_router(router)` for each production router; the local app keeps its own state and token configuration.

### Details
- `TestPublishAuth` through `TestReplayAuth` and the audit classes use `cls.app` from `_make_test_app`; their requests then reach production handlers.
- The `/health` route in the local app now returns the production body; no test in this file calls `/health` through the local app (only `TestProductionRouteWiring` does, on the production app).

## Compatibility considerations
N/A: test code only.

## Security considerations
- Strengthens coverage: authorization tests now run against the registered handlers; no weakening of any assertion.

## Rollback considerations
- Revert the phase's commit (the matching route-module changes revert together).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_auth.py -v` after each phase, then `uv run pytest tests/eventbus -v`.
- `uv run ruff check tests/eventbus/test_eventbus_auth.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`.

## Completion criteria
- `_make_test_app` contains no route declaration and no `eb_app.*_route` reference.
- All tests in the file pass (or each changed expectation is justified in the commit message as a wiring finding).

## Out of Scope
- Reorganizing the test classes or the fixtures beyond the route wiring.
- Any other file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 2: switch the Phase 2 routes of `_make_test_app` to production routers | Completed | 20261110-113335 | 20261110-113335 | No wiring finding: every existing *Auth test passed unchanged against the production routers; Literal/JSONResponse imports removed by ruff. |
| 2 | Phase 3: switch the consumer routes and remove the local `resolve_subscribe_identity` | Completed | 20261110-113335 | 20261110-113335 |  |
| 3 | Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v` after each phase | Completed | 20261110-113335 | 20261110-113335 |  |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261110-113335 | 20261110-113335 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-090758_adrrev001_eventbus-route-handlers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-100805
- **Related target files**: `tests/eventbus/test_eventbus_auth.py`