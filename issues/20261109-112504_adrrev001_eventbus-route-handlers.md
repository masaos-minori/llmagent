# Remove duplicate EventBus route handler functions, lock consumer authorization with tests, and rewrite eventbus_08

## Priority
High

## Summary
Leave exactly one handler function per EventBus route, prove with tests that every consumer and Operator route enforces its authorization, and rewrite `docs/24_eventbus/eventbus_08_reference_api.md` as per-route-group contract descriptions instead of a symbol inventory.

## Background
- Source: the ADR review remediation list in `memo-issue.md` (items H-01 and the document part of H-16). The memo's claims were re-checked against current source on 2026-11-09.
- `Explicit in code`: `scripts/eventbus/app.py` registers the routes with `@app.get` / `@app.post` decorators and delegates to same-named functions in the route modules (`ack_route.py`, `dlq_route.py`, and others). The route modules are not mounted with `include_router`, so the `app.py` functions are the only registered handlers.
- `Explicit in code`: the `app.py` wrappers for `ack_event` and `nack` depend only on `require_role(Role.CONSUMER)`, not on `require_consumer_identity`. The route-module functions call `authorize_event_pair`, which authorizes the (consumer_id, event topic) pair before any delivery write. `dlq_list` in `app.py` requires `Role.OPERATOR`; the same-named function in `dlq_route.py` takes no principal.
- `Explicit in documentation`: `eventbus_08_reference_api.md` contains a `Class/Function | Signature | Summary` table that lists both the `app.py` and the route-module functions. `governance_04` lists GV-018 (docs content policy) as Blocking.
- Memo claim refuted by current source: "any authenticated caller can ACK or NACK another consumer's events because the `app.py` handlers have no identity dependency". Authorization of the (consumer_id, topic) pair happens inside the route-module function, which the wrapper calls. `Needs confirmation`: whether this in-function check covers every consumer route and every grant case (no grant for the consumer_id, no grant for the topic).
- Existing authorization tests: `tests/eventbus/test_eventbus_auth.py`, `test_eventbus_consumer_authorization.py`, `test_admin_topics_authorization.py`. `Needs confirmation`: whether they already cover the negative cases listed below.

## Problem
- Two functions with the same name per route (a registered wrapper and an unregistered implementation) make it unclear which one carries the authorization contract. A later refactor could move the authorization check to the wrong layer.
- `eventbus_08_reference_api.md` violates the docs content policy (symbol inventory table, plan ID, change-history wording), and the table is what makes the duplicate names look like duplicate handlers.
- It is `Needs confirmation` whether the negative authorization cases (no token, wrong role, CONSUMER token without a grant) are locked by tests for every route.

## Reason for Change
- The EventBus is an authentication boundary (ADR-013). Authorization that lives only in an implementation detail of a delegated function is easy to lose in a refactor, and no test walks the registered routes.
- A Blocking documentation policy violation (GV-018) is present in a current document. Timing: no external deadline; the document rewrite is a prerequisite for the checker hardening in the later `docs/10_adr` remediation issues.

## Implementation Intent
- Each route has one handler responsibility. Decide, and state in the issue's plan, whether the registered handler lives in the route module (preferred: single place, with `app.py` only wiring) or stays in `app.py` with the route-module function renamed as an internal helper. Either way, no two public functions share a route's name.
- Authorization (consumer identity or Operator role) is enforced at a single, test-locked layer for every route.
- `eventbus_08` describes responsibilities and contracts per route group and points to the source for exhaustive detail, per the docs content policy.
- Preserve current runtime behavior and response contracts; this is a structure and verification change, not a role-model change.

## Target Files or Areas
- `scripts/eventbus/app.py`
- `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/publish_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/health_route.py`
- `tests/eventbus/` (new route-uniqueness and negative authorization tests)
- `docs/24_eventbus/eventbus_08_reference_api.md`

## Required Changes
- Record, for each route, which function FastAPI registers (`/publish`, `/subscribe`, `/events/{event_id}/ack`, `/nack`, `/dlq`, `/dlq/{event_id}/requeue`, `/replay`, `/health`, `/admin/topics/authorization`) before deleting or renaming anything.
- Remove or rename the same-named duplicate functions so that no route name is defined twice in `scripts/eventbus/`.
- Make the layer that enforces consumer identity and the layer that enforces the Operator role explicit and identical for every consumer and Operator route.
- Add a test that walks `app.routes` and asserts exactly one handler per (method, path).
- Add negative authorization tests per route: no token returns 401, a wrong role returns 403, and a CONSUMER token without a grant for the `consumer_id` or topic returns 403. Reuse existing tests where they already cover a case.
- Rewrite `eventbus_08_reference_api.md` as contract descriptions per route group. Remove the symbol table, plan IDs, and change-history wording.

## Constraints
- Do not change response shapes or status codes that current tests assert, except where a test proves an authorization gap.
- If the review finds a real authorization gap (a route reachable without the intended check), treat it as a security fix: record it in `Unresolved Questions` handling and fix it in this issue with a test.
- The documentation must follow `skills/DESIGN.md` "Docs content policy — remove" and "Avoid implementation-reference duplication", and must be written in English.
- The EventBus must keep binding to loopback only; do not touch startup or binding code.

## Acceptance Criteria
- A test fails if any (method, path) has more than one registered handler.
- Negative authorization tests for each route pass (401, 403 wrong role, 403 missing grant), or the issue records which cases were already covered by named existing tests.
- No function under `scripts/eventbus/` duplicates a route handler's name.
- `eventbus_08_reference_api.md` contains no class/function inventory table, no plan ID, and no change-history wording.
- `uv run python tools/check_docs_content_policy.py --strict` and `uv run python tools/check_docs_consistency.py --domain eventbus` pass.

## Testing Expectations
- Unit and route tests under `tests/eventbus/`: `uv run pytest tests/eventbus -v`.
- Impact-radius check per `rules/toolchain.md` before renaming a widely referenced route function: `rg -l '\back_event\b|\bnack\b|\bdlq_list\b' tests/`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`.
- Documentation checks: `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py --strict`, `check_docs_consistency.py --domain eventbus`, and `generate_reference_table.py --check` (eventbus is a generated-reference domain).

## Documentation Impact
- `eventbus_08_reference_api.md` must be rewritten: responsibilities and contracts per route group, who may call each route group, failure behavior. No symbol table, no file-to-behavior mapping.
- Check whether `eventbus_08` is a generated reference (`AUTO-GENERATED` block); if so, change the generator or its guarded block instead of hand-editing generated output.

## Out of Scope
- Changes to the role model, credentials, or token handling (see `issues/20261109-112952_adrrev010_eventbus-authz-harden.md`).
- Fixing the documentation checker that missed the GV-018 violation (see the checker-hardening issue in this batch).
- The decision to keep or retire the EventBus (see the EventBus decision issue in this batch).

## Dependencies
- Depends on: none (do first within the EventBus group).
- Blocks: `issues/20261109-112952_adrrev010_eventbus-authz-harden.md` (EventBus authorization hardening).
- Related, recently archived (re-verify against current source before acting): the `eballow01` and `ebsec001` issues under `issues/done/` (non-empty consumer authorization, auth token startup block). Their fixes may already cover parts of the authorization cases above.

## Unresolved Questions
- `Needs confirmation`: does the in-function `authorize_event_pair` check cover every consumer route (`/subscribe`, ack, nack) for both the consumer_id grant and the topic grant? The answer decides whether this issue contains a security fix or only a structure change.
- `Needs confirmation`: is `eventbus_08` fully generated? This decides whether the rewrite edits a generator or a document.
- Assumption: the preferred structure is "register handlers from route modules"; the choice between that and "keep `app.py` handlers and rename route-module functions" is left to the plan.

## AI Implementation Instruction
- Do not change behavior beyond what a failing authorization test proves is wrong.
- Do not modify unrelated EventBus modules, the role model, or configuration.
- Record the registered-handler list before deleting anything; stop and report if a route is registered twice or an authorization check is missing.
- Write `eventbus_08` content in English and follow the docs content policy; run the listed documentation checkers before finishing.
- Do not commit; do not touch other issues' scope.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261109-112504
- **Related target files**: `scripts/eventbus/app.py`, `scripts/eventbus/ack_route.py`, `scripts/eventbus/dlq_route.py`, `scripts/eventbus/publish_route.py`, `scripts/eventbus/subscribe_route.py`, `scripts/eventbus/replay_route.py`, `scripts/eventbus/admin_route.py`, `scripts/eventbus/health_route.py`, `tests/eventbus/`, `docs/24_eventbus/eventbus_08_reference_api.md`
