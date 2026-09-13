## Goal
Add the missing `Depends(require_role(...))`/`Depends(require_consumer_identity)`
declarations to `_make_test_app()`'s seven local routes (REQ-001, REQ-002), and add
wrong-role-token negative tests (REQ-003), so this file's tests actually exercise
role-based authorization.

## Scope
Only `_make_test_app()`'s seven local route declarations and their delegated-to
call sites in `tests/eventbus/test_eventbus_auth.py`, plus new test methods. No
change to `scripts/eventbus/app.py`, `require_role`, `require_consumer_identity`,
or `_populate_token_maps`.

## Assumptions
- `plans/done/20260913-151824_plan.md` (Issue `eb005`, the `_TOKEN_TOPIC_MAP`
  empty-set contradiction) must be implemented before this document's three
  consumer-identity routes (`/subscribe`, `/events/{event_id}/ack`, `/nack`) are
  exercised end-to-end — per the source Plan's own Assumptions and Risk mitigation.
  **This document's own Step 1 (Precondition check, see Procedure) verifies this
  directly against current source before any other step proceeds** — do not treat
  the source Plan's own dated reference as sufficient evidence on its own.
- `scripts/eventbus/app.py`'s seven route declarations (confirmed by reading the
  file) are: `/publish` → `Depends(require_role(Role.PUBLISHER))`; `/subscribe` →
  `Depends(require_role(Role.CONSUMER))` +
  `Depends(require_consumer_identity)`; `/dlq` and `/dlq/{event_id}/requeue` and
  `/replay` → `Depends(require_role(Role.OPERATOR))`; `/events/{event_id}/ack` and
  `/nack` → `Depends(require_role(Role.CONSUMER))` +
  `Depends(require_consumer_identity)`.

## Design decisions
Mirror `app.py`'s seven route declarations exactly onto `_make_test_app()`'s seven
local routes — same `Depends(require_role(Role.<X>))` per route, plus
`Depends(require_consumer_identity)` on the three that also have it — and thread
`_role`/`_identity` through to each delegated-to route function call the same way
`app.py` does (e.g. `eb_app.publish_route(request, _role=_role)`).

## Alternatives considered
- **Write a shared local dependency-wiring helper instead of repeating the
  `Depends(...)` declarations seven times**: rejected — `app.py` itself declares
  each route's dependencies inline, not via a shared helper; mirroring that same
  style keeps this fixture's structure recognizably parallel to the file it is
  meant to emulate, which is more valuable here than deduplication of seven short
  lines.

## Implementation
### Target file
tests/eventbus/test_eventbus_auth.py

### Procedure
1. **Precondition check**: before making any other change, run `uv run pytest
   tests/eventbus/test_eventbus_subscribe.py::test_subscribe_duplicate_consumer_id_returns_409
   -v` and confirm it passes. If it does not pass, stop this document's cycle and
   report `Blocked: plans/done/20260913-151824_plan.md (eb005) has not landed` —
   do not proceed to Procedure step 2 until it does, per this Plan's own gating
   Assumption.
2. Add `Depends` to the `fastapi` import line and `Role`, `require_role`,
   `require_consumer_identity` to the `eventbus.auth` import block inside
   `_make_test_app()`.
3. Add `_role: Role = Depends(require_role(Role.PUBLISHER))` to `/publish`; thread
   `_role` through to `eb_app.publish_route(request, _role=_role)`.
4. Add `_role: Role = Depends(require_role(Role.CONSUMER))` and `_identity:
   dict[str, Any] = Depends(require_consumer_identity)` to `/subscribe`; thread
   both through to `eb_app.subscribe_route(request, topic=topic,
   since_seq=since_seq, consumer_id=consumer_id, _role=_role,
   _identity=_identity)`.
5. Add `_role: Role = Depends(require_role(Role.OPERATOR))` to `/dlq`; thread
   `_role` through to `eb_app.dlq_list_route(request, limit=limit, offset=offset,
   _role=_role)`.
6. Add `_role: Role = Depends(require_role(Role.OPERATOR))` to
   `/dlq/{event_id}/requeue`; thread `_role` through to
   `eb_app.dlq_requeue_route(request, event_id, _role=_role)`.
7. Add `_role: Role = Depends(require_role(Role.OPERATOR))` to `/replay`; thread
   `_role` through to `eb_app.replay_route(request, since_seq=since_seq, fmt=fmt,
   limit=limit, offset=offset, _role=_role)`.
8. Add `_role: Role = Depends(require_role(Role.CONSUMER))` and `_identity:
   dict[str, Any] = Depends(require_consumer_identity)` to
   `/events/{event_id}/ack`; thread both through to
   `eb_app.ack_event_route(request, event_id=event_id, consumer_id=consumer_id,
   _role=_role, _identity=_identity)`.
9. Add `_role: Role = Depends(require_role(Role.CONSUMER))` and `_identity:
   dict[str, Any] = Depends(require_consumer_identity)` to `/nack`; thread both
   through to `eb_app.nack_route(request, event_id=event_id, _role=_role,
   _identity=_identity)`.
10. After each route's change (steps 3-9), run
    `tests/eventbus/test_eventbus_auth.py` for that route's test class only,
    before moving to the next route — per the source Plan's own Risk mitigation
    (attribute a newly-failing test to the specific route just changed).
11. Add one new wrong-role-token negative test per role-gated route category:
    a `consumer_token` bearer rejected (403) from `/publish` (`TestPublishAuth`); an
    `operator_token`/`publisher_token` bearer rejected (403) from `/subscribe`
    (`TestSubscribeAuth`); a `consumer_token`/`publisher_token` bearer rejected
    (403) from `/dlq`, `/dlq/{event_id}/requeue`, `/replay` (their respective
    classes); a `publisher_token`/`operator_token` bearer rejected (403) from
    `/events/{event_id}/ack` and `/nack` (their respective classes). Each new test
    class's `setup_class` may need an additional per-role token added to its
    `_make_test_app()` call if the class does not already configure one suitable
    for the negative case (e.g. `TestAckAuth` currently only sets `admin_token`,
    which grants every role and cannot demonstrate a *wrong*-role rejection — add
    a genuinely different single-role token, e.g. `operator_token`, for that
    class's new negative test specifically).
12. Remove `TestPublishAuth.test_check_role_rejects_wrong_role_token` (the
    unit-level stopgap added in
    `implementations/done/20260913-122501_02_tests_eventbus_test_eventbus_auth.py.md`)
    once its HTTP-level replacement (step 11's `/publish` case) passes — the
    stopgap's own docstring states it exists only because this fixture's
    `Depends(...)` gap made an HTTP-level test impossible; that gap is now closed.

### Method
Mechanical, per-route `Depends(...)` addition and parameter threading (steps 2-9),
verified incrementally per route (step 10) rather than all at once, then new
negative tests (step 11) and stopgap removal (step 12).

### Details
- Do not change `_init_local_state`, `_do_cleanup_eb`, or any registered route's
  non-dependency parameters (`topic`, `since_seq`, `consumer_id`, `limit`,
  `offset`, `fmt`, `event_id`) — confirmed unchanged between `app.py` and this
  fixture already (source Plan's own Assumptions).
- If the Precondition check (step 1) fails, this document's cycle ends in
  `Blocked` for this file only — per `skills/code-implementation/workflow.md`
  Step 3c's per-file `Blocked` continuation policy — not a reason to skip ahead to
  the four non-consumer-identity routes independently; this document treats all
  seven routes as one Requirement set (source Plan's own Design section).

## Compatibility considerations
Test-only file; no production code or API-contract impact. Every existing test
that authenticates with the *correct* role's token for its route must continue to
pass unchanged (REQ-004) — a test previously passing "by accident" with a
wrong-role token would now correctly fail, which is the fix's intended effect, not
a regression.

## Security considerations
N/A: test-only change; no production authorization logic modified. This document
makes existing production authorization logic (already correct, per eb002's
REQ-005) actually verifiable by this file's own tests.

## Rollback considerations
Single-file, test-only change — revert this file's diff to roll back. No
interaction with the companion `eb005` Plan's own revert: if that Plan's fix is
reverted, this document's three consumer-identity routes would again surface its
bug in previously-passing tests — re-run the Precondition check (step 1) before
re-applying this document if that ever happens.

## Validation plan
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v` after each route's
  change (per Procedure step 10) and once more in full at the end; confirm all 14
  original cases plus the new wrong-role cases pass (AC-1, AC-2, AC-3).
- Run `uv run pytest tests/eventbus/ -q --timeout=30` to confirm no regression.
- Run the standard validation sequence (`rules/toolchain.md`): ruff, mypy,
  lint-imports, bandit, diff-cover.

## Completion criteria
- Every one of `_make_test_app()`'s seven local routes declares the same
  `Depends(...)` as its real `app.py` counterpart (AC-1).
- At least one new test per role-gated route category confirms a wrong-role token
  is rejected (403) through this fixture's own HTTP layer (AC-2).
- All existing tests plus the new wrong-role tests pass (AC-3).
- The unit-level stopgap test is removed once superseded (Procedure step 12).

## Out of scope
- `scripts/eventbus/app.py`'s real routes, `require_role`, `require_consumer_identity`,
  `_populate_token_maps` — no production authorization code is touched.
- The `_TOKEN_TOPIC_MAP` empty-set contradiction itself — covered by
  `plans/done/20260913-151824_plan.md` (Issue `eb005`), gated on by this
  document's Precondition check (Procedure step 1), not fixed here.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260913-164236 | 20260913-164236 | Precondition check passed (eb005 landed); added Depends(require_role(...))/Depends(require_consumer_identity) to all 7 local routes in _make_test_app(), threaded _role/_identity through to each delegated-to call |
| 2 | Add or update tests per Validation plan | Completed | 20260913-164236 | 20260913-164236 | Added 7 wrong-role negative tests (one per role-gated route); replaced the unit-level stopgap with an HTTP-level test for /publish; all 22 tests in this file pass |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260913-164236 | 20260913-164236 | ruff/mypy/bandit/lint-imports/diff-cover(100%, unchanged since this is test-only)/pre-commit all passed; full tests/eventbus/ suite: only pre-existing dlq-requeue/metrics/startup failures remain, 0 new regressions |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260913-164236 | 20260913-164236 | N/A: test-only file, no docs/00_index.md task-scope mapping |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/done/20260913-143134_eb006_make-test-app-missing-authorization-depends.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-152038_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-152902
- **Related target files**: tests/eventbus/test_eventbus_auth.py