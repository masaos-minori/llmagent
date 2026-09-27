## Goal

Resolve `tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint`'s 3 failing tests: reconcile `test_ack_event_not_found`'s and `test_ack_event_delivery_verification`'s status-code expectations with `ack_route.py`'s confirmed-deliberate behavior (REQ-001, REQ-002), and root-cause why `test_ack_event_principal_ownership_validation`'s expected 403/409 rejection does not fire (REQ-003).

## Scope

In scope: this file's 3 failing tests only. Out of scope: `scripts/eventbus/ack_route.py`'s `_do_ack` 404-via-`found`-check design and `scripts/eventbus/auth.py`'s `require_consumer_identity`/`resolve_principal` — modify only if REQ-003's investigation confirms a genuine production bug there, per the Plan's own Implementation Target Files amendment requirement (not yet confirmed as of this document).

## Assumptions

- No Requirement/design document was found (at Plan-creation time) governing the not-found/delivery-verification status-code contract; absent one, `ack_route.py`'s current, well-commented behavior (404 for nonexistent event; no separate pre-ack delivery gate) is treated as authoritative per the Plan's Implementation intent.

## Design decisions

- For REQ-001/REQ-002: align the 2 tests' expected status codes to the confirmed current behavior (404, and 200-without-a-separate-delivery-gate respectively) rather than modifying `ack_route.py`, since its behavior is explicitly documented in-code and no contradicting spec was found.
- For REQ-003: do not guess a fix — add temporary tracing first to observe the actual resolved `principal`/`consumer_id` values, per the Plan's Implementation intent, before deciding whether to fix the test or `scripts/eventbus/auth.py`/`ack_route.py`.

## Alternatives considered

- Changing `ack_route.py` to add a pre-ack delivery gate and to return 409 for nonexistent events (matching the tests' original expectations) instead of updating the tests: rejected absent a discovered Requirement contradicting the current, deliberately-commented design (`_do_ack`'s "found is the authoritative existence check" comment).

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_endpoint.py`

### Procedure

1. **REQ-001** (`test_ack_event_not_found`): search `plans/done/*.md`/`issues/done/*.md` for a Requirement governing this test's "REQ-003: no delivery record" docstring reference (a different REQ numbering scheme than this cycle's own REQ-001/002/003 — confirm it does not contradict the current 404 behavior). If none found or none contradicts, change the test's assertion from `assert resp.status_code == 409` to `assert resp.status_code == 404`.
2. **REQ-002** (`test_ack_event_delivery_verification`): same Requirement-doc search for the "verifies event was delivered before accepting ACK" docstring claim. If none found or none contradicts, change the test's assertion from `assert resp.status_code == 409` to the actual current-behavior status code (confirmed 200 in this cycle's investigation) — and update the test's docstring/name if it becomes misleading (e.g. rename to reflect "ack creates delivery record atomically" rather than "verifies prior delivery").
3. **REQ-003** (`test_ack_event_principal_ownership_validation`): add temporary logging (e.g. `logger.warning`/`print`) at `require_consumer_identity`'s entry (`scripts/eventbus/auth.py`) and `_do_ack`'s ownership-check line (`scripts/eventbus/ack_route.py`) to record the actual resolved `principal.allowed_consumer_ids` and `consumer_id` at request time. Reproduce this specific test once with the tracing active. Based on the trace: if the values are correct but the check still doesn't fire, this points to a FastAPI dependency-injection/parameter-sharing issue (a production bug — stop, do not proceed further in this document, and report `Blocked: additional target file discovered` per the Plan's own note, since fixing it would require modifying `scripts/eventbus/auth.py`/`ack_route.py`, files not yet in this Plan's frozen `Implementation Target Files`). If the trace instead reveals a test/fixture gap (e.g. the `principal_client` fixture not actually taking effect for this specific request), fix the test accordingly and remove the temporary tracing.

### Method

Steps 1-2: direct assertion-value edits, following a Requirement-doc search per the Plan's Implementation intent. Step 3: investigative tracing first, then a conditional fix (test-side) or a stop-and-report (production-side, pending Plan amendment) — not a blind edit.

### Details

- `test_ack_event_not_found` (line ~167): `assert resp.status_code == 409` → `assert resp.status_code == 404` (pending Requirement-doc search finding no contradiction).
- `test_ack_event_delivery_verification` (line ~232): `assert resp.status_code == 409` → `assert resp.status_code == 200` (pending Requirement-doc search finding no contradiction); consider whether the test's docstring/name still accurately describes the verified behavior after this change.
- `test_ack_event_principal_ownership_validation` (line ~218): do not edit until the tracing in Procedure step 3 determines the correct side to fix.

## Compatibility considerations

- REQ-001/REQ-002: no production change; test-only fix. REQ-003: if it resolves to a production fix, `scripts/eventbus/ack_route.py`/`scripts/eventbus/auth.py`'s ownership-enforcement behavior for `/events/{event_id}/ack` would change — compatibility impact TBD pending that investigation.

## Security considerations

- REQ-003 is security-relevant: an unauthorized `consumer_id` currently is not rejected by this endpoint in the tested scenario. Do not relax this test's expectation to match the current (potentially insecure) behavior without first completing the tracing investigation and confirming which side is correct.

## Rollback considerations

- REQ-001/REQ-002: `git revert` the commit, or manually restore the prior assertion values. REQ-003: if a production fix is applied (pending Plan amendment), its rollback path depends on that future change's own nature — not yet determined.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_ack_endpoint.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -q` | All tests pass |

## Completion criteria

- REQ-001/REQ-002: `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_not_found tests/eventbus/test_eventbus_ack_endpoint.py::TestAckEndpoint::test_ack_event_delivery_verification -q` passes.
- REQ-003: either the test passes with a genuine authorization rejection confirmed via the trace, or this document's cycle is reported `Blocked: additional target file discovered` pending Plan amendment — not silently left unresolved.

## Out of scope

- `tests/eventbus/test_eventbus_ack_nack.py`, `tests/eventbus/test_eventbus_crash_ack.py` (each covered by its own implementation procedure document from this same Plan).
- `eb002`'s `NackResult` tuple-equality failures (distinct root cause, tracked separately).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing/tracing the existing 3 tests is itself the work |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A unless REQ-003 resolves to a documented contract change |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003: resolve `test_eventbus_ack_endpoint.py`'s 3 failing tests
- **Source issue**: issues/20260927-075241_eb001_eventbus-ack-nack-crash_ack-idempotency-and-ownership-status-codes-regressed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082506_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091732
- **Related target files**: tests/eventbus/test_eventbus_ack_endpoint.py
