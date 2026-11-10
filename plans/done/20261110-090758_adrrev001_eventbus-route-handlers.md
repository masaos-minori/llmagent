## Goal
- Leave exactly one registered handler per EventBus route (`scripts/eventbus/`), with the role dependency and the consumer-pair authorization owned by that one function, and lock this with production-app tests that fail on a duplicate registration or a missing 401/403 case.

## Priority
High

## Scope
- **In-Scope**: Register every route (`/health`, `/publish`, `/replay`, `/subscribe`, `/dlq`, `/dlq/{event_id}/requeue`, `/events/{event_id}/ack`, `/nack`, `/admin/topics/authorization`) from its route module through an `APIRouter`, with `app.py` only wiring (`include_router`); remove the seven duplicate function names (`publish`, `replay`, `subscribe`, `dlq_list`, `dlq_requeue`, `ack_event`, `nack`); add a route-registry test and production-app negative authorization tests; correct the two stale document statements about where authorization lives and about what `eventbus_08` contains.
- **Out-of-Scope**: Role model, credentials and token handling (`issues/20261109-112952_adrrev010_eventbus-authz-harden.md`); the documentation checker hardening (`issues/20261109-113351_adrrev018_docs-checker-harden.md`); the keep-or-retire EventBus decision (`issues/20261109-112739_adrrev006_eventbus-future-decision.md`); startup and loopback binding code in `app.py` (`_main`, `lifespan`); retiring the ADR-015 generated symbol table (see UNK-02).
- **Dependencies**: Depends on none. Blocks `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`. Sequencing: runs before `issues/20261109-112538_adrrev002_agent-eventbus-coupling.md` only for ADR-013 (this Plan edits the `Current State` paragraph; adrrev002 edits `Review Triggers`, so the edits are compatible).
  - **Depends on**: N/A: none

## Background
- Source: ADR review remediation list in `memo-issue.md` (H-01, document part of H-16), re-verified on 2026-11-10 (see Requirement Traceability `Status`).
- `Confirmed by repository evidence`: `scripts/eventbus/app.py` registers all nine routes with `@app.get`/`@app.post`; no `include_router`/`APIRouter` exists under `scripts/eventbus/`. Seven registered function names are defined twice, once in `app.py` and once in a route module: `publish`, `replay`, `subscribe`, `dlq_list`, `dlq_requeue`, `ack_event`, `nack`. `/health` and `/admin/topics/authorization` are not duplicates by name (`health_check`, `update_topics_authorization` vs `health`, `admin_topics_authorization`) but follow the same split. `app.py` imports the route functions under `*_route` aliases.
- `Confirmed by repository evidence`: authorization is split across two layers. `/subscribe` runs `authorize_consumer_access` as an `app.py` dependency (`resolve_subscribe_identity`); `/events/{event_id}/ack` and `/nack` run it inside `ack_route.authorize_event_pair`, called from the route-module function; the `app.py` wrappers only depend on `require_role(Role.CONSUMER)`. A route-module function called with `_principal=None` fails closed (HTTP 403).
- `Refuted`: the memo claim that any authenticated caller can ACK or NACK another consumer's events. `authorize_consumer_access` denies a principal without the CONSUMER role or without grants (ADR-013 INV-02, INV-07) and covers the `(consumer_id, topic)` pair; no authorization gap was found, so this Plan contains no security fix.
- `Refuted`: the Issue's claim that `eventbus_08_reference_api.md` contains a plan ID and change-history wording (no match in the file), and that GV-018 is currently violated (`uv run python tools/check_docs_content_policy.py --strict` reports `No issues found.`). The symbol table is an `AUTO-GENERATED` block, generated from `registry/manifests/eventbus_api.yaml` by `tools/generate_reference_table.py`, and `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` (ADR-015) designates `eventbus_08_reference_api.md` as the eventbus Reference-class generated document.
- `Confirmed by repository evidence`: the Issue's "no test walks the registered routes" is only partly true. `tests/eventbus/test_eventbus_auth.py::TestProductionRouteWiring::test_every_production_api_route_has_a_role_dependency` walks `app.routes` for a role dependency, but nothing asserts one handler per `(method, path)`.
- `Confirmed by repository evidence` (new finding): `tests/eventbus/test_eventbus_auth.py::_make_test_app` builds a hand-written `local_app` that re-declares the routes and calls `eb_app.*_route`; its ack route also passes a different identity dependency than production. `TestPublishAuth` through `TestReplayAuth` therefore exercise a test copy, not the registered handlers. Production-app 401/403 coverage exists only for `/health` and `/publish` (`TestProductionRouteWiring`), for subscribe/ack/nack grants (`test_eventbus_consumer_authorization.py`, through `eb_app.app`), and for `/admin/topics/authorization` (`test_admin_topics_authorization.py`, production lifespan). `/replay`, `/dlq` and `/dlq/{event_id}/requeue` have no production-app negative test.
- `Confirmed by repository evidence` (new finding): ADR-013 `Current State` says `/subscribe`, `/ack` and `/nack` "additionally require `Depends(require_consumer_identity)`"; in current code only `/subscribe` does (through `resolve_subscribe_identity`), and ack/nack authorize inside the route function. `eventbus_02_api-reference-index.md` points to `eventbus_08_reference_api.md` for the `/admin/topics/authorization` contract, but `eventbus_08` holds only that route's symbol row; the contract text is in `eventbus_07_configuration-and-operations.md` and `eventbus_02`.

## Problem
- Two functions with one name per route (a registered wrapper and an unregistered implementation) hide which function carries the authorization contract; consumer-pair authorization lives in the wrapper for `/subscribe` and in the delegated function for ack/nack.
- Production-path negative authorization tests are missing for the Operator routes, and most `*Auth` tests run against a hand-copied test app, so a wiring regression in `app.py` would not fail them.
- Two documents state where authorization lives or which document holds a contract inaccurately.

## Reason for Change
- The EventBus is an authentication boundary (ADR-013). Authorization that depends on which of two same-named functions FastAPI registers is easy to break in a refactor, and no test pins the registered handler set.
- No external deadline. The change blocks `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`, which needs a single enforcement layer to harden.

## Implementation Intent
- Decision (alternatives in Design): register handlers from the route modules via per-module `APIRouter`; `app.py` keeps the app object, lifespan, middleware, DLQ loop, and `include_router` calls only. Role dependency and consumer-pair authorization sit on the one handler function of each route.
- Add the missing tests first (they pass against current behavior), then move routes group by group, each step leaving the suite green.
- Preserve every response shape, status code, and URL; no change to the role model, tokens, or binding code.
- Documentation: keep `eventbus_08` as the ADR-015 generated Reference document; refresh its generated block through the generator, and correct the stale sentences named in Documentation Impact.

## Requirements
- `REQ-001`: Record the registered-handler list `(method, path) -> function` before any change, and add a test that fails when any `(method, path)` has more than one registered `APIRoute`.
- `REQ-002`: Add production-app (`eb_app.app` through the real lifespan) negative authorization tests for each route that lacks them: 401 without token and with an unknown token, 403 for a token without the required role (`/replay`, `/dlq`, `/dlq/{event_id}/requeue`), and 401 for `/events/{event_id}/ack` and `/nack` without a token; reuse the existing production-path tests for the cases they already cover.
- `REQ-003`: Make each route's registered handler a single function in its route module, registered by `APIRouter` and included by `app.py`; no function under `scripts/eventbus/` shares a registered route function's name with another function in the package.
- `REQ-004`: The registered handler of every consumer route (`/subscribe`, ack, nack) enforces `authorize_consumer_access` through one shared dependency or one shared call, and every Operator/Admin/Publisher/Monitoring route enforces its role through `require_role(...)` on the same function.
- `REQ-005`: `tests/eventbus/test_eventbus_auth.py` stops re-declaring routes: its test app includes the production routers, so the existing `*Auth` tests run against the registered handlers.
- `REQ-006`: Correct ADR-013 `Current State` to the actual authorization layering, and correct the `eventbus_02` pointer for the `/admin/topics/authorization` contract.
- `REQ-007`: Update `eventbus_08` prose (module responsibilities, generated-table lead sentence) and refresh `registry/manifests/eventbus_api.yaml` and the guarded block through `tools/generate_reference_table.py`; the document stays within ADR-015.

## Implementation Target Files
**Freeze status**: Frozen
Amended 2026-11-10 (fallout): added tests/eventbus/test_eventbus_subscribe_transition.py — The test calls subscribe_route.subscribe(request, topic=[], since_seq=0, consumer_id="") without a principal; once the registered handler takes its principal through Depends, a direct call must pass a Principal

This table is the canonical, frozen source of implementation scope for this Plan. Once
`Frozen`, `Implementation steps`, `Acceptance criteria`, and every downstream
`plan-to-implementation-procedure` document MUST reference file paths only from this
table — no other file may be treated as a modification target.

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/eventbus/app.py` | Wiring only: keep app, lifespan, middleware, DLQ loop; include route-module routers | Remove the nine wrapper handlers, the `*_route` aliases, and `resolve_subscribe_identity`; add `include_router` calls | REQ-003, REQ-004 / AC-02, AC-03 | Nine `@app.get`/`@app.post` handlers and `*_route` aliases at `app.py` lines 17-71, 214-340 (checked in Step 3) | `tests/eventbus/test_eventbus_route_registry.py`, `tests/eventbus/test_eventbus_auth.py` | Verified |
| `scripts/eventbus/health_route.py` | Own the `/health` route | Add `APIRouter` and `require_role(Role.MONITORING)` on the registered `health` handler; drop `health_check` as a separate registered name | REQ-003, REQ-004 / AC-02 | `health_check` at `health_route.py:34`; wrapper `health` in `app.py` (checked in Step 3) | `tests/eventbus/test_eventbus_health.py`, `tests/eventbus/test_eventbus_route_registry.py` | Verified |
| `scripts/eventbus/publish_route.py` | Own the `/publish` route | Add `APIRouter` and `require_role(Role.PUBLISHER)`; remove same-named duplicate | REQ-003, REQ-004 / AC-02 | `publish` at `publish_route.py:40` duplicates `app.py` `publish` (checked in Step 3) | `tests/eventbus/test_eventbus_publish.py`, `tests/eventbus/test_eventbus_publish_contract.py` | Verified |
| `scripts/eventbus/replay_route.py` | Own the `/replay` route | Add `APIRouter`, `require_role(Role.OPERATOR)` and the query parameters carried by the wrapper | REQ-003, REQ-004 / AC-02 | `replay` at `replay_route.py:28` duplicates `app.py` `replay` (checked in Step 3) | `tests/eventbus/test_eventbus_replay_pagination.py`, `tests/eventbus/test_eventbus_replay_subscribe.py` | Verified |
| `scripts/eventbus/dlq_route.py` | Own `/dlq` and `/dlq/{event_id}/requeue` | Add `APIRouter` and `require_role(Role.OPERATOR)` on both handlers; `dlq_list` and `dlq_requeue` become the registered functions | REQ-003, REQ-004 / AC-02 | `dlq_list` (line 23, no principal) and `dlq_requeue` (line 46) duplicate `app.py` names (checked in Step 3) | `tests/eventbus/test_eventbus_dlq.py`, `tests/eventbus/test_eventbus_requeue_edge_cases.py`, `tests/eventbus/test_eventbus_dlq_pagination.py` | Verified |
| `scripts/eventbus/subscribe_route.py` | Own `/subscribe` and its consumer-pair authorization | Add `APIRouter`; move `resolve_subscribe_identity` here (or reuse one shared dependency) so role and pair authorization sit on the registered handler | REQ-003, REQ-004 / AC-02, AC-03 | `subscribe` at `subscribe_route.py:32`; `resolve_subscribe_identity` in `app.py:196-210` (checked in Step 3) | `tests/eventbus/test_eventbus_subscribe.py`, `tests/eventbus/test_eventbus_consumer_authorization.py` | Verified |
| `scripts/eventbus/ack_route.py` | Own `/events/{event_id}/ack` and `/nack` | Add `APIRouter` and `require_role(Role.CONSUMER)`; keep `authorize_event_pair` as the shared pair check; remove same-named duplicates | REQ-003, REQ-004 / AC-02, AC-03 | `ack_event` (line 119) and `nack` (line 134) duplicate `app.py` names; `authorize_event_pair` at line 30 (checked in Step 3) | `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_consumer_authorization.py` | Verified |
| `scripts/eventbus/admin_route.py` | Own `/admin/topics/authorization` | Add `APIRouter` and `require_role(Role.ADMIN)` on the registered handler | REQ-003, REQ-004 / AC-02 | `update_topics_authorization` at `admin_route.py:98`; wrapper `admin_topics_authorization` in `app.py` (checked in Step 3) | `tests/eventbus/test_admin_topics_authorization.py` | Verified |
| `tests/eventbus/test_eventbus_route_registry.py` | New file: registry-uniqueness and production-app negative authorization tests | New file (its directory `tests/eventbus/` exists); uniqueness over `app.routes`, no-duplicate-name check, 401/403 per route through `eb_app.app` | REQ-001, REQ-002 / AC-01, AC-04 | `TestProductionRouteWiring` (`test_eventbus_auth.py:1496`) covers only `/health` and `/publish`; `/replay`, `/dlq`, `/dlq/{event_id}/requeue` have no production-app 401/403 test (checked in Step 3) | `uv run pytest tests/eventbus/test_eventbus_route_registry.py -v` | Verified |
| `tests/eventbus/test_eventbus_auth.py` | Test app uses production routers | Replace the hand-written route copies in `_make_test_app` with `include_router` of the production routers | REQ-005 / AC-05 | `_make_test_app` re-declares nine routes and calls `eb_app.*_route` (`test_eventbus_auth.py:96-258`) (checked in Step 3) | `uv run pytest tests/eventbus/test_eventbus_auth.py -v` | Verified |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | Accurate authorization layering | Rewrite the `Current State` sentence on `require_consumer_identity` for ack/nack | REQ-006 / AC-06 | ADR-013 line 46 vs `ack_route.py:70,161` and `app.py` ack/nack dependencies (checked in Step 3) | `uv run python tools/check_adr_preservation.py`, `check_adr_authority.py` | Verified |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | Correct contract pointer | Replace the `eventbus_08` pointer for `/admin/topics/authorization` with the document that holds the contract | REQ-006 / AC-06 | Line 46 pointer; `eventbus_08` holds only a symbol row (checked in Step 3) | `uv run python tools/check_docs_consistency.py --domain eventbus` | Verified |
| `docs/24_eventbus/eventbus_08_reference_api.md` | Refresh generated block and prose | Update Module Responsibilities and the lead sentence calling the table "the authoritative symbol inventory"; regenerate the guarded block | REQ-007 / AC-07 | Lead paragraph and `## Module Responsibilities`; `AUTO-GENERATED` guard at lines 45-143 (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `registry/manifests/eventbus_api.yaml` | Generated symbol manifest | Regenerate with `tools/generate_reference_table.py --manifests` after the rename (not hand-edited) | REQ-007 / AC-07 | `manifest: eventbus_api`, entries for `scripts/eventbus/app.py` (checked in Step 3) | `uv run python tools/generate_reference_table.py --check` | Verified |
| `tests/eventbus/test_eventbus_subscribe_transition.py` | Keep the direct route-function call valid after the subscribe signature change | The test calls subscribe_route.subscribe(request, topic=[], since_seq=0, consumer_id="") without a principal; once the registered handler takes its principal through Depends, a direct call must pass a Principal | REQ-003 / AC-02 | tests/eventbus/test_eventbus_subscribe_transition.py:233 calls subscribe_route.subscribe directly (checked in Step 3a) | uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -v | Verified |

## Reference Files
Files that must be read to implement the targets above, but MUST NOT be modified.

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/eventbus/auth.py` | `require_role`, `authorize_consumer_access`, `require_consumer_identity`, `resolve_principal` semantics that the routers reuse | REQ-004 |
| `scripts/eventbus/route_helpers.py` | `get_db`, `get_config`, `get_broker`, `run_with_db_lock` used by every route module | REQ-003 |
| `tests/eventbus/eventbus_helpers.py` | `make_eventbus_client` fixture helper for the new production-app tests | `tests/eventbus/test_eventbus_route_registry.py` |
| `tests/eventbus/conftest.py` | Autouse fixtures (state isolation) the new test file inherits | REQ-001, REQ-002 |
| `tests/eventbus/test_eventbus_consumer_authorization.py` | Existing production-app grant tests that REQ-002 reuses instead of duplicating | REQ-002 |
| `tests/eventbus/test_admin_topics_authorization.py` | Existing production-lifespan admin 401/403 tests that REQ-002 reuses | REQ-002 |
| `docs/10_adr/adr_02_07_015_docs-reference-document-class-disposition.md` | ADR-015: `eventbus_08` is the generated Reference-class document | REQ-007 |
| `docs/24_eventbus/eventbus_07_configuration-and-operations.md` | Holds the `/admin/topics/authorization` contract text the `eventbus_02` pointer must target | REQ-006 |
| `tools/generate_reference_table.py` | Generator that owns the `eventbus_08` guarded block and the manifest | REQ-007 |

## Acceptance Criteria
- `AC-01` (REQ-001): a test fails when any `(method, path)` has more than one registered `APIRoute`, and the pre-change registered-handler list is recorded in the implementation procedure.
- `AC-02` (REQ-003, REQ-004): every one of the nine routes is registered from its route module; `rg -n "^(async )?def (publish|replay|subscribe|dlq_list|dlq_requeue|ack_event|nack)\b" scripts/eventbus/` returns exactly one match per name, and `app.py` defines no route handler.
- `AC-03` (REQ-004): consumer routes enforce `authorize_consumer_access` on the registered handler; the `(consumer_id, topic)` negative cases (ungranted consumer_id, ungranted topic, empty grants) still return 403 through `eb_app.app`.
- `AC-04` (REQ-002): production-app tests assert 401 (no token, unknown token), 403 (wrong role) for every role-gated route, and 403 without a grant for subscribe, ack and nack; cases already covered are cited by test name, not duplicated.
- `AC-05` (REQ-005): `_make_test_app` contains no `@local_app.get`/`@local_app.post` route declaration.
- `AC-06` (REQ-006): ADR-013 `Current State` and the `eventbus_02` pointer match the code and the document that holds the contract.
- `AC-07` (REQ-007): `uv run python tools/generate_reference_table.py --check`, `check_docs_content_policy.py --strict`, and `check_docs_consistency.py --domain eventbus` pass; `eventbus_08` keeps the `AUTO-GENERATED` block.
- Existing tests under `tests/eventbus/` pass unchanged except `test_eventbus_auth.py` test-app construction; no response shape or status code changes.

## Tests
- `REQ-001`: new `test_every_method_path_has_one_registered_handler` over `app.routes`; new test that no two top-level functions in `scripts/eventbus/*.py` share a registered route function's name.
- `REQ-002`: new parametrized production-app tests for `/replay`, `/dlq`, `/dlq/{event_id}/requeue` (401 no token, 401 unknown token, 403 publisher token) and for `/events/{event_id}/ack`, `/nack` (401 no token); reuse `test_eventbus_consumer_authorization.py` and `test_admin_topics_authorization.py` for grants and admin.
- `REQ-003`, `REQ-004`, `REQ-005`: the existing `tests/eventbus/` suite, run after each route-group move.
- `REQ-006`, `REQ-007`: documentation checkers listed in the Validation plan.

## Documentation Impact
- Required (REQ-006, REQ-007): ADR-013 `Current State`; `eventbus_02` admin-contract pointer; `eventbus_08` prose and generated block (ADR-015 Reference class; the generator, not hand edits, changes the table). Docs are written in English and follow `skills/DESIGN.md` Docs content policy.
- Not changed: the per-route HTTP contracts stay in `eventbus_03`, `eventbus_04`, `eventbus_10`, `eventbus_11`, `eventbus_12`; copying them into `eventbus_08` would duplicate them (UNK-02).

## Assumptions
- A route module's `APIRouter` handler may take `Principal` through `Depends(require_role(...))` instead of the optional `_principal` parameter; the `principal is None` branch in `authorize_event_pair` stays as a fail-closed guard. Falsifiable by the existing `test_eventbus_consumer_authorization.py` and `TestFailClosedConsumerAuthorization` tests.
- Tests that patch route-module symbols (`eventbus.publish_route.insert_event`, `eventbus.dlq_route.redeliver_event`, `eventbus.admin_route.log_privileged_action`) are unaffected, because the handler bodies stay in the same modules. Falsifiable by running `tests/eventbus/`.
- `registry/manifests/eventbus_api.yaml` is a generated file; its regeneration is a Fallout class change, not a design decision.
- Overlap with other Frozen Plans: none reported by `tools/check_plan_target_overlaps.py` for the `scripts/eventbus/` rows (checked in Step 8b); compatible with `plans/20261110-091327_adrrev002_agent-eventbus-coupling.md` on ADR-013 (different sections: `Current State` vs `Review Triggers`).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether FastAPI keeps the OpenAPI operation names and the `request.url.path`-based audit `route` field identical after moving to `APIRouter` (no prefix is used, so none is expected) | A before/after comparison of `app.openapi()` and the audit `route` values | Implementation phase 2: snapshot `app.openapi()["paths"]` before the first move and assert equality after each group | False |
| UNK-02 | Whether the owner wants the generated symbol table retired from `eventbus_08` despite ADR-015 (the Issue asks for per-route-group contract prose and no symbol table) | An owner decision; ADR-015 is Accepted and designates `eventbus_08` as a generated Reference document, and per-route contracts already live in `eventbus_03/04/10/11/12` | Owner decides; if yes, a separate Issue amends ADR-015, the generator, and `check_docs_structure.py` expectations. This Plan keeps the table | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/eventbus/app.py` | modify | High: imports from 7 route modules; 198 test references to `eb_app.app` | 12 | N/A | not applicable (rsynced) |
| `scripts/eventbus/health_route.py` | modify | Low: one route; `is_ready` used by tests | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/publish_route.py` | modify | Medium: patched by `test_eventbus_publish.py` | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/replay_route.py` | modify | Low: one route | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/dlq_route.py` | modify | Medium: patched by DLQ and requeue tests | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/subscribe_route.py` | modify | High: patched by `test_eventbus_subscribe.py`; radon C (17) on `subscribe` | N/A | N/A | not applicable (rsynced) |
| `scripts/eventbus/ack_route.py` | modify | High: 12 commits in 30 days; ack/nack tests | 12 | N/A | not applicable (rsynced) |
| `scripts/eventbus/admin_route.py` | modify | Low: one route; patched by admin tests | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_route_registry.py` | create | Low: new test file | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_auth.py` | modify | Medium: 17 commits in 30 days; test-app construction used by six test classes | 17 | N/A | not applicable (rsynced) |
| `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | modify | Low: one paragraph; ADR preservation check applies | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_02_api-reference-index.md` | modify | Low: one pointer | N/A | N/A | not applicable (rsynced) |
| `docs/24_eventbus/eventbus_08_reference_api.md` | modify | Medium: generated block; 25 commits in 30 days | 25 | N/A | not applicable (rsynced) |
| `registry/manifests/eventbus_api.yaml` | modify | Low: generated manifest | N/A | N/A | not applicable (rsynced) |
| `tests/eventbus/test_eventbus_subscribe_transition.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
- **Registration decision** (python-design Step 4, narrow use): Option A, `APIRouter` per route module with `app.py` only calling `include_router`. Option B (keep `app.py` handlers, rename route-module functions to internal helpers) was rejected: it keeps role dependencies in `app.py` and consumer-pair authorization in the helper, which is the two-layer split the Issue wants removed, and it leaves ack/nack/subscribe layered differently. Option A puts the role dependency and the pair check on one function per route. Compatibility impact: URLs, methods, parameters, and response models are unchanged (no router prefix); `eventbus.app.*_route` aliases disappear, and the only consumer of them is `tests/eventbus/test_eventbus_auth.py` (`eb_app.publish_route`, `subscribe_route`, `dlq_list_route`, `dlq_requeue_route`, `replay_route`, `ack_event_route`, `nack_route`, `update_topics_authorization_route`).
- **Pre-change registered-handler list** (from `app.py`): `GET /health -> health`, `POST /publish -> publish`, `GET /replay -> replay`, `GET /subscribe -> subscribe`, `GET /dlq -> dlq_list`, `POST /dlq/{event_id}/requeue -> dlq_requeue`, `POST /events/{event_id}/ack -> ack_event`, `POST /nack -> nack`, `POST /admin/topics/authorization -> admin_topics_authorization`; each delegates to the route-module function of the same or related name. No route is registered twice.
- **Authorization layering target**: Role gate: `Depends(require_role(...))` on the registered function. Consumer-pair gate: `authorize_consumer_access` is called once per consumer route on the registered path (`/subscribe` through a dependency declared in `subscribe_route.py`; ack and nack through `authorize_event_pair`, which needs the event topic from the database and so stays a call inside the handler). The negative-case coverage of both is locked by the Tests section.
- **Consumer scan** (`tools/scan_change_consumers.py --seed dlq_requeue --seed resolve_subscribe_identity`): 232 candidates, all in `tests/eventbus/` and almost all `eb_app.app` uses that stay valid. The affected ones are the eight `eb_app.*_route` alias uses in `tests/eventbus/test_eventbus_auth.py` (target row) and the `registry/manifests/eventbus_api.yaml`/`eventbus_08` generated rows (target rows). `not affected: tests/eventbus/test_eventbus_concurrent.py` and `tests/eventbus/test_eventbus_requeue_edge_cases.py` import `eventbus.dlq_route` and patch its module symbols, which stay in place. The scan lists candidates only (text search); indirect users are not detected.
- **Path B analysis** (Step 5): architecture: `PYTHONPATH=scripts uv run lint-imports` reports 6 contracts kept, 0 broken; route modules already import `eventbus.auth` (`ack_route`), so no new import direction is introduced. Dependency graph: `rg "from eventbus\.(ack_route|...) import"` found importers only in `app.py` and tests. Historical: `app.py` 12 commits, `ack_route.py` 12, `delivery_repo.py` 13 in 30 days (`git log --since=30.days`); bus factor not measured (`git-fame` not run). Operational: no port, process, DB schema, or dependency change, so `ss`, `fuser`, and `pip-audit` were not run (no operational impact). Persisted schema check: not applicable (no DDL).
- **Validation quality baseline**: `radon cc -s -n C` on the six route targets: only `subscribe_route.py:32 subscribe` is C (17). `vulture scripts/ --min-confidence 80`: findings only in `scripts/rag/` and `scripts/shared/runtime_paths.py`, none in `scripts/eventbus/`. `bandit -r scripts/eventbus`: 3 High findings pre-exist (not part of this change; record and continue). diff-cover baseline: not run in this phase (`N/A: no code diff yet`); the implementation raises the diff coverage to the `rules/toolchain.md` threshold.
- **Path classification**: Path B (more than 3 files; changes how every route is registered).

## Implementation steps
1. **Phase 1: Lock current behavior with tests (no source change)**
   - [ ] Record the registered-handler list and an `app.openapi()["paths"]` snapshot (UNK-01) in the procedure; create `tests/eventbus/test_eventbus_route_registry.py` with the one-handler-per-`(method, path)` test and the production-app negative authorization tests; all pass against the current code (REQ-001, REQ-002; `tests/eventbus/test_eventbus_route_registry.py`).
2. **Phase 2: Move Monitoring, Publisher, Operator, and Admin routes**
   - [ ] Add `APIRouter` plus `require_role` to `health_route.py`, `publish_route.py`, `replay_route.py`, `dlq_route.py`, `admin_route.py`; include the routers in `app.py`; remove their wrappers and aliases from `app.py`; replace the matching route copies in `_make_test_app` (REQ-003, REQ-004, REQ-005; `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/publish_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/admin_route.py`, `tests/eventbus/test_eventbus_auth.py`). Run `uv run pytest tests/eventbus -v`.
3. **Phase 3: Move consumer routes**
   - [ ] Add `APIRouter`, `require_role(Role.CONSUMER)` and the pair authorization to `subscribe_route.py` and `ack_route.py`; move `resolve_subscribe_identity` out of `app.py`; remove the remaining wrappers and aliases; replace the remaining route copies in `_make_test_app` (REQ-003, REQ-004, REQ-005; `scripts/eventbus/app.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `tests/eventbus/test_eventbus_auth.py`). Run `uv run pytest tests/eventbus -v`; the Phase 1 tests must still pass unchanged.
   - [ ] Keep the direct route-function call valid after the subscribe signature change (REQ-003; `tests/eventbus/test_eventbus_subscribe_transition.py`) — amendment 2026-11-10
4. **Phase 4: Documentation and generated references**
   - [ ] Correct ADR-013 `Current State` and the `eventbus_02` pointer; update `eventbus_08` prose; run `uv run python tools/generate_reference_table.py --manifests` to refresh `registry/manifests/eventbus_api.yaml` and the guarded block (REQ-006, REQ-007; `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `registry/manifests/eventbus_api.yaml`).
5. **Phase 5: Deployment and verification**
   - [ ] Run the full validation sequence in `rules/toolchain.md`; after the change is committed and pushed (the user's decision), hand off to `skills/deploy/SKILL.md` because `scripts/` changed (REQ-003; all `scripts/eventbus/*` rows).

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_route_registry.py` | Integration through `eb_app.app` | `uv run pytest tests/eventbus/test_eventbus_route_registry.py -v` | Passes before and after Phases 2-3 |
| `scripts/eventbus/*.py`, `tests/eventbus/` | Unit and route tests | `uv run pytest tests/eventbus -v` | All pass after each phase |
| `scripts/` | Lint, type, import contracts, security | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/eventbus -c pyproject.toml` | No new findings |
| Impact radius | Search | `rg -l '\back_event\b\|\bnack\b\|\bdlq_list\b' tests/` | Every hit reviewed against Phase 2-3 |
| `scripts/eventbus/*.py` size | Module-size gate | `uv run python tools/check_module_size.py` | Passes (route modules grow by a router declaration) |
| `docs/10_adr/...013...`, `docs/24_eventbus/*.md` | Documentation checks | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus`, `check_adr_preservation.py`, `check_adr_authority.py` | All pass |
| `registry/manifests/eventbus_api.yaml`, `eventbus_08` | Generated-reference drift | `uv run python tools/generate_reference_table.py --check` | Exit 0 |
| Diff coverage | Coverage | `rules/toolchain.md` section 7 diff-cover sequence | At or above the Completion checklist threshold |

## Risks
- **Risk**: A route moved to `APIRouter` loses or reorders a dependency, so a route becomes reachable with a weaker check → **Mitigation**: Phase 1 production-app negative tests and the existing `test_every_production_api_route_has_a_role_dependency` run unchanged after every group move; revert the group on any failure.
- **Risk**: `app.openapi()` operation IDs or the audit `route` field change after the move → **Mitigation**: snapshot comparison in Phase 2 (UNK-01); no router prefix is used.
- **Risk**: Removing the `eb_app.*_route` aliases breaks tests outside `test_eventbus_auth.py` → **Mitigation**: impact-radius `rg` before removal; the scan found alias uses only in that file.
- **Risk**: `tests/eventbus/test_eventbus_auth.py` rework changes what the six `*Auth` classes exercise (production routers instead of test copies) and exposes a latent failure → **Mitigation**: treat any new failure as a finding (a real wiring difference), per the Issue's security-fix rule: record it and fix it with a test in this Plan.
- **Risk**: ADR-013 wording edit trips `check_adr_preservation.py` → **Mitigation**: change only the inaccurate `Current State` sentence; run the checker.
- **Risk**: The Issue's request to drop the symbol table conflicts with Accepted ADR-015 → **Mitigation**: keep the table, record the decision as UNK-02 for the owner.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Lock current behavior with tests (no source change) | In Progress | — | — |  |
| 2 | Move Monitoring, Publisher, Operator, and Admin routes | In Progress | — | — |  |
| 3 | Move consumer routes | In Progress | — | — |  |
| 4 | Documentation and generated references | In Progress | — | — |  |
| 5 | Deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261110-100805_01_scripts_eventbus_app.py.md | 2, 3 | Procedure | Pending | — | — |
| implementations/20261110-100805_02_scripts_eventbus_health_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261110-100805_03_scripts_eventbus_publish_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261110-100805_04_scripts_eventbus_replay_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261110-100805_05_scripts_eventbus_dlq_route.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-100805_06_scripts_eventbus_subscribe_route.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-100805_07_scripts_eventbus_ack_route.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261110-100805_08_scripts_eventbus_admin_route.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261110-100805_09_tests_eventbus_test_eventbus_route_registry.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261110-100805_10_tests_eventbus_test_eventbus_auth.py.md | 2, 3 | Procedure | Pending | — | — |
| implementations/20261110-100805_11_docs_10_adr_adr_02_04_013_eventbus-authentication-authorization.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-100805_12_docs_24_eventbus_eventbus_02_api-reference-index.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-100805_13_docs_24_eventbus_eventbus_08_reference_api.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-100805_14_registry_manifests_eventbus_api.yaml.md | 4 | Procedure | Pending | — | — |
| implementations/20261110-100805_15_tests_eventbus_test_eventbus_subscribe_transition.py.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261110-090758
- **Related target files**: `scripts/eventbus/app.py`, `scripts/eventbus/health_route.py`, `scripts/eventbus/publish_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/admin_route.py`, `tests/eventbus/test_eventbus_route_registry.py`, `tests/eventbus/test_eventbus_auth.py`, `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md`, `docs/24_eventbus/eventbus_02_api-reference-index.md`, `docs/24_eventbus/eventbus_08_reference_api.md`, `registry/manifests/eventbus_api.yaml`, `tests/eventbus/test_eventbus_subscribe_transition.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes: registered-handler list and uniqueness test | `tests/eventbus/test_eventbus_route_registry.py` | 1 | AC-01 | `test_every_method_path_has_one_registered_handler` | Confirmed by repository evidence |
| REQ-002 | Required Changes: negative authorization tests; evidence `test_eventbus_auth.py::_make_test_app` | `tests/eventbus/test_eventbus_route_registry.py` | 1 | AC-04 | Production-app 401/403 tests | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/app.py` | 2, 3 | AC-02 | `uv run pytest tests/eventbus -v` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/health_route.py` | 2 | AC-02 | `tests/eventbus/test_eventbus_health.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/publish_route.py` | 2 | AC-02 | `tests/eventbus/test_eventbus_publish.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/replay_route.py` | 2 | AC-02 | `tests/eventbus/test_eventbus_replay_pagination.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/dlq_route.py` | 2 | AC-02 | `tests/eventbus/test_eventbus_dlq.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/admin_route.py` | 2 | AC-02 | `tests/eventbus/test_admin_topics_authorization.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/subscribe_route.py` | 3 | AC-02 | `tests/eventbus/test_eventbus_subscribe.py` | Confirmed by repository evidence |
| REQ-003 | Required Changes: remove duplicate functions | `scripts/eventbus/ack_route.py` | 3 | AC-02 | `tests/eventbus/test_eventbus_ack_nack.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: explicit, identical authorization layer | `scripts/eventbus/subscribe_route.py` | 3 | AC-03 | `tests/eventbus/test_eventbus_consumer_authorization.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: explicit, identical authorization layer | `scripts/eventbus/ack_route.py` | 3 | AC-03 | `tests/eventbus/test_eventbus_consumer_authorization.py` | Confirmed by repository evidence |
| REQ-004 | Required Changes: explicit, identical authorization layer | `scripts/eventbus/app.py` | 2, 3 | AC-02, AC-03 | `test_every_production_api_route_has_a_role_dependency` | Confirmed by repository evidence |
| REQ-005 | Evidence: `_make_test_app` re-declares routes (new finding) | `tests/eventbus/test_eventbus_auth.py` | 2, 3 | AC-05 | `uv run pytest tests/eventbus/test_eventbus_auth.py -v` | Derived from confirmed evidence |
| REQ-006 | Evidence: ADR-013 line 46 and `eventbus_02` line 46 stale (new finding) | `docs/10_adr/adr_02_04_013_eventbus-authentication-authorization.md` | 4 | AC-06 | `check_adr_preservation.py`, `check_adr_authority.py` | Derived from confirmed evidence |
| REQ-006 | Evidence: `eventbus_02` pointer stale | `docs/24_eventbus/eventbus_02_api-reference-index.md` | 4 | AC-06 | `check_docs_consistency.py --domain eventbus` | Derived from confirmed evidence |
| REQ-007 | Required Changes: `eventbus_08` rewrite, narrowed by ADR-015 | `docs/24_eventbus/eventbus_08_reference_api.md` | 4 | AC-07 | `generate_reference_table.py --check` | Derived from confirmed evidence |
| REQ-007 | Documentation Impact: generated reference | `registry/manifests/eventbus_api.yaml` | 4 | AC-07 | `generate_reference_table.py --check` | Confirmed by repository evidence |
| REQ-003 | Amendment 2026-11-10: The test calls subscribe_route.subscribe(request, topic=[], since_seq=0, consumer_id="") without a principal; once the registered handler takes its principal through Depends, a direct call must pass a Principal | tests/eventbus/test_eventbus_subscribe_transition.py | Phase 3 | N/A: none cites REQ-003 | uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -v | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261110-100805 -->