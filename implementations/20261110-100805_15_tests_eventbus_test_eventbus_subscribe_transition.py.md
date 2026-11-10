## Goal
- Keep the direct call `subscribe_route.subscribe(...)` in `tests/eventbus/test_eventbus_subscribe_transition.py` valid after the registered `subscribe` handler takes its principal through `Depends` (REQ-003 fallout of the one-handler change).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the one test (around line 233) that calls `subscribe_route.subscribe(request, topic=[], since_seq=0, consumer_id="")` after monkeypatching `run_with_db_lock` to raise `CancelledError`.
- Not in scope: other tests in the file; they go through the HTTP client.
- Execution order follows the Plan's phases, not the `seq` order: Phase 1 (document 09) first, then Phase 2 (documents 02, 03, 04, 05, 08, then 01 and 10 for the Phase 2 share), then Phase 3 (documents 06, 07, then 01, 10, 15 for the Phase 3 share), then Phase 4 (documents 11-14). This document belongs to Phase 3, together with document 06.

## Assumptions
- After document 06, `subscribe` always receives `_principal` and `_identity`; with a non-`None` principal the body runs `effective_topics(_principal, consumer_id, topic)` and raises 403 `no topics granted` for an empty result (`scripts/eventbus/subscribe_route.py`, checked in Step 3a). The direct call must therefore pass a principal with a grant and a non-empty topic list to reach the cancelled replay path. Falsifiable by running the test.
- This file is a fallout row added to the Plan by amendment on 2026-11-10 (class fallout, found in Step 3a).

## Design decisions
- Use a `Principal` with the CONSUMER role and one grant `("c1", "t")`; call with `consumer_id="c1"`, `topic=["t"]`; pass the same object as `_principal` and `_identity`.
- Keep the monkeypatch of `run_with_db_lock` and the `seq=0` log assertion unchanged.

## Alternatives considered
- Keep `_principal`/`_identity` defaulting to `None` in `subscribe` (rejected in document 06: the production handler must never run without an injected principal).

## Implementation
### Target file
`tests/eventbus/test_eventbus_subscribe_transition.py`

### Procedure
1. In the test, import `Principal` and `Role` from `eventbus.auth` and build `principal = Principal(roles=frozenset({Role.CONSUMER}), consumer_grants=frozenset({("c1", "t")}), token_fingerprint="test")` (field names: `scripts/eventbus/auth.py` `Principal`).
2. Change the call to `await subscribe_route.subscribe(request, topic=["t"], since_seq=0, consumer_id="c1", _principal=principal, _identity=principal)`.
3. Re-run the test and confirm the cancelled-replay path is still reached and the `seq=0` log line is asserted.

### Method
- Minimal edit of one call plus the principal construction.

### Details
- The original call relied on `_principal=None`, which skipped the grant logic; the new call reproduces the same cancelled-replay scenario under a granted principal.

## Compatibility considerations
N/A: test code only.

## Security considerations
N/A: test code only; no credentials involved.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -v`
- `uv run ruff check tests/eventbus/test_eventbus_subscribe_transition.py`

## Completion criteria
- The test passes with the new `subscribe` signature and still asserts the seq-0 log line.

## Out of Scope
- Changing other tests or production code.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the direct `subscribe_route.subscribe` call to pass a granted principal | Pending | — | — | |
| 2 | Run `uv run pytest tests/eventbus/test_eventbus_subscribe_transition.py -v` and the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261109-112504_adrrev001_eventbus-route-handlers.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261110-090758_adrrev001_eventbus-route-handlers.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261110-100805
- **Related target files**: `tests/eventbus/test_eventbus_subscribe_transition.py`
