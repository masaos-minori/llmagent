## Goal

Resolve `tests/eventbus/test_eventbus_crash_ack.py::TestCrashBeforeAck`'s 2 failing tests: reconcile `test_crash_ack_event_delivery_verification`'s status-code expectation with confirmed-deliberate current behavior (REQ-002), and root-cause `test_crash_ack_principal_ownership_validation`'s ownership-check non-firing (REQ-003).

## Scope

In scope: these 2 tests only. Out of scope: `scripts/eventbus/ack_route.py`/`scripts/eventbus/auth.py` production code — modify only if REQ-003's investigation confirms a genuine bug, per this Plan's Implementation Target Files amendment requirement.

## Assumptions

- Same as the sibling `test_eventbus_ack_endpoint.py`/`test_eventbus_ack_nack.py` implementation procedure documents (same Plan): absent a discovered Requirement doc contradicting current behavior, `ack_route.py`'s confirmed-deliberate behavior is authoritative.

## Design decisions

- For REQ-002: align the expected status code to confirmed current behavior. For REQ-003: reuse the sibling documents' trace/finding if already resolved (same `require_consumer_identity`/`_do_ack` code paths, exercised via a crash-before-ack scenario rather than ack_endpoint/ack_nack directly); otherwise perform the same tracing procedure independently.

## Alternatives considered

- Same as the sibling documents: rejected changing production behavior without first confirming via Requirement-doc search and live tracing.

## Implementation

### Target file

`tests/eventbus/test_eventbus_crash_ack.py`

### Procedure

1. **REQ-002** (`test_crash_ack_event_delivery_verification`, line ~278): confirm via Read the exact current assertion (`assert resp.status_code == 409`) and align it to the confirmed current-behavior status code (200), following the same Requirement-doc search as the sibling documents' REQ-002 items.
2. **REQ-003** (`test_crash_ack_principal_ownership_validation`, line ~263): reuse the trace/finding from the sibling `test_eventbus_ack_endpoint.py`/`test_eventbus_ack_nack.py` documents if their investigation already resolved the root cause; otherwise perform the same tracing procedure (temporary logging at `require_consumer_identity`'s entry and `_do_ack`'s ownership-check line, reproduce once, determine the correct side to fix) independently for this crash-before-ack scenario specifically, since its exact setup (a crash-recovery flow) may differ enough from the plain ack/nack scenarios to warrant its own confirmation.

### Method

Step 1: direct assertion-value edit following Requirement-doc search. Step 2: reuse or perform investigative tracing, then a conditional fix or stop-and-report.

### Details

- `test_crash_ack_event_delivery_verification`: `assert resp.status_code == 409` → `assert resp.status_code == 200` (pending Requirement-doc search finding no contradiction).
- `test_crash_ack_principal_ownership_validation`: do not edit until the tracing (reused or independent) determines the correct side to fix.

## Compatibility considerations

- REQ-002: no production change. REQ-003: TBD pending investigation (see sibling documents).

## Security considerations

- REQ-003 is security-relevant (same ownership-bypass concern as the sibling documents) — do not relax this test's expectation without completing the investigation.

## Rollback considerations

- REQ-002: `git revert` or manual restoration of the prior assertion value. REQ-003: TBD pending investigation outcome.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/eventbus/test_eventbus_crash_ack.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -q` | All tests pass |

## Completion criteria

- REQ-002: the test passes with the status code matching confirmed current behavior.
- REQ-003: either the test passes with a genuine authorization rejection confirmed, or this row is reported `Blocked: additional target file discovered` pending Plan amendment.

## Out of scope

- `tests/eventbus/test_eventbus_ack_endpoint.py`, `tests/eventbus/test_eventbus_ack_nack.py` (each covered by its own implementation procedure document from this same Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: fixing/tracing the existing 2 tests is itself the work |
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
- **Requirement ID**: REQ-002, REQ-003: resolve `test_eventbus_crash_ack.py`'s 2 failing tests
- **Source issue**: issues/20260927-075241_eb001_eventbus-ack-nack-crash_ack-idempotency-and-ownership-status-codes-regressed.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-082506_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-091732
- **Related target files**: tests/eventbus/test_eventbus_crash_ack.py