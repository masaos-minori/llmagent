## Goal

Resolve `tests/eventbus/test_eventbus_ack_nack.py`'s 3 `eb001`-tracked failing tests (`test_ack_unknown_event_returns_404`, `test_nack_event_delivery_verification`, `test_nack_event_principal_ownership_validation`): reconcile the first two's status-code expectations with confirmed-deliberate current behavior (REQ-001, REQ-002), and root-cause the third's ownership-check non-firing (REQ-003).

## Scope

In scope: these 3 tests only in this file. Out of scope: this file's 2 other, separately-tracked failures (`test_nack_event_increments_again`, `test_nack_event_increments_failure_count` — `NackResult` tuple-equality issue, tracked under `eb002`, its own Plan). Out of scope: `scripts/eventbus/ack_route.py`/`scripts/eventbus/auth.py` production code — modify only if REQ-003's investigation confirms a genuine bug there, per this Plan's Implementation Target Files amendment requirement.

## Assumptions

- Same as the sibling `test_eventbus_ack_endpoint.py` implementation procedure document (same Plan): absent a discovered Requirement doc contradicting current behavior, `ack_route.py`'s confirmed-deliberate 404-for-nonexistent and no-separate-delivery-gate behavior is authoritative.

## Design decisions

- For REQ-001/REQ-002: align expected status codes to confirmed current behavior. For REQ-003: trace first, following the exact same investigative procedure as the sibling `test_eventbus_ack_endpoint.py` document (this test exercises the same `_do_ack`/`require_consumer_identity` code paths via the `/nack` endpoint's analogous ownership check) — do not duplicate the trace if the sibling document's investigation (processed first or concurrently) already identified the root cause; reuse that finding here if applicable.

## Alternatives considered

- Same as the sibling document: rejected changing production behavior without first confirming via Requirement-doc search and live tracing.

## Implementation

### Target file

`tests/eventbus/test_eventbus_ack_nack.py`

### Procedure

1. **REQ-001** (`test_ack_unknown_event_returns_404`): search for a governing Requirement doc (same search as the sibling document, since this test's name already suggests 404 may be the *intended* label — re-read the test body to confirm its current assertion and docstring exactly before concluding whether this test needs a fix at all, or whether it was miscategorized as failing for a different reason — see Details).
2. **REQ-002** (`test_nack_event_delivery_verification`): same Requirement-doc search and reconciliation as `test_ack_event_delivery_verification` in the sibling document — nack's delivery-verification semantics should mirror ack's, per `_do_ack`'s shared logic path (`ack_route.py`'s `nack` function, confirmed via Read to share `_ack_and_offset`-equivalent logic).
3. **REQ-003** (`test_nack_event_principal_ownership_validation`): reuse the trace/finding from the sibling `test_eventbus_ack_endpoint.py` document if it already resolved the root cause (same `require_consumer_identity`/`_do_ack` code paths); otherwise perform the same tracing procedure independently.

### Method

Steps 1-2: assertion-value reconciliation following a Requirement-doc search. Step 3: reuse or perform investigative tracing, then a conditional fix or stop-and-report, matching the sibling document's approach.

### Details

- Re-confirm via Read that `test_ack_unknown_event_returns_404`'s actual failure is `assert 404 == 409` (test expects 409, gets 404) — i.e. despite its name suggesting 404 is expected, the test body itself currently asserts 409; confirm which value the test *should* assert (align to 404, matching its own name and the confirmed current/deliberate behavior) rather than assuming the docstring name is definitive without checking the assertion body.
- `test_nack_event_delivery_verification`: confirm its exact current assertion and expected value via Read before editing (line numbers not independently re-derived in this Plan's evidence for this specific file — re-verify via `rg`/Read).
- `test_nack_event_principal_ownership_validation`: do not edit until the tracing (reused or independent) determines the correct side to fix.

## Compatibility considerations

- REQ-001/REQ-002: no production change. REQ-003: TBD pending investigation (see sibling document).

## Security considerations

- REQ-003 is security-relevant (same ownership-bypass concern as the sibling document) — do not relax this test's expectation without completing the investigation.

## Rollback considerations

- REQ-001/REQ-002: `git revert` or manual restoration of prior assertion values. REQ-003: TBD pending investigation outcome.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_ack_nack.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -q` | All tests pass except `eb002`'s 2 separately-tracked failures |

## Completion criteria

- REQ-001/REQ-002: the 2 tests pass with status codes matching confirmed current behavior.
- REQ-003: either the test passes with a genuine authorization rejection confirmed, or this row is reported `Blocked: additional target file discovered` pending Plan amendment.

## Out of scope

- `test_nack_event_increments_again`, `test_nack_event_increments_failure_count` (tracked under `eb002`'s own Plan/implementation procedure).
- `test_nack_event_not_found` (`TestNackEvent`): unit test asserting `nack_event(db, "nonexistent-event") == (-1, -1)`; `nack_event` returns a `NackResult` object, not a plain tuple — assertion mismatch. Discovered during this cycle but not tracked under `eb001`/`eb002`; left unfixed. Requires a separate decision (fix the assertion to compare against `NackResult(-1, -1)`, or track as a distinct work item). Not addressed here per this document's scope.
- `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_crash_ack.py` (each covered by its own implementation procedure document from this same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: fixing/tracing the existing 3 tests is itself the work |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A unless REQ-003 resolves to a documented contract change |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003: resolve `test_eventbus_ack_nack.py`'s 3 `eb001`-tracked failing tests
- **Source issue**: issues/20260927-075241_eb001_eventbus-ack-nack-crash_ack-idempotency-and-ownership-status-codes-regressed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082506_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091732
- **Related target files**: tests/eventbus/test_eventbus_ack_nack.py