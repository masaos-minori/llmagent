# Implementation Procedure: ack_route.py DB-only inline promotion

## Goal

Adjust `_nack_and_promote` in `scripts/eventbus/ack_route.py` so inline promotion is a
DB-only commit with no OSError deferral, keeping NACK independence and ADR-006 INV-13 gating
unchanged (REQ-003, REQ-009; plan AC-2).

## Scope

**In scope:**
- `ack_route.py:201-218`: drop the `try/except OSError` deferral around the promote call.

**Out of scope:**
- `_nack_event`, invalid-state handling (177-195), authorization, response shape, the
  `run_with_db_lock` call at `:221`, INV-13 gating condition (201-204).

## Assumptions
- Verified at HEAD `124e340b4`: `_nack_and_promote` at `ack_route.py:166`; gating at 201-204
  (`consumer_failure_count >= cfg.max_retry` + `is_promotable`); promote call at 208-212;
  `except OSError` deferral at 213-218 (`promoted = False`, "deferred to sweep" log);
  `run_with_db_lock(_nack_and_promote)` at 221.
- Row 03 has already removed file I/O from `promote_single`; it can no longer raise
  `OSError`, so the deferral branch is dead code under the new contract.

## Design decisions
- Remove the `try/except OSError` block (207-218) and call `is_promotable(...) and
  promote_single(...)` directly. NACK independence (REQ-009) now rests on the transaction:
  the NACK commit is already durable before promotion is attempted, and a promotion-side DB
  failure that aborts the closure is the same failure class today's code has for DB errors.
- The sweep remains the self-healing repair path for a promotion interrupted by a crash
  between commit boundaries (unchanged semantics, `dlq.py:181-188` docstring).

## Alternatives considered
- Keeping `except OSError` as defensive dead code: rejected — REQ-003's whole point is that
  file-system failure cannot enter this path; dead handlers invite future re-introduction of
  file I/O here.

## Implementation
### Target file
`scripts/eventbus/ack_route.py`

### Procedure
1. Replace lines 207-218 (try/except OSError block) with the direct gated call.

### Method
Deletion of one handler; gating expression and log semantics around it unchanged.

### Details
- The `"nack: inline DLQ promotion failed, deferred to sweep"` log disappears with the
  handler; there is no test asserting that exact log (row 09/`test_eventbus_ack_nack.py`
  assert response bodies, not this log line).
- `promoted` semantics unchanged: True only when this call newly promoted (`rowcount > 0`).

## Compatibility considerations
- Endpoint response JSON (status + `promoted` flag) is byte-identical for every non-crash
  case (REQ-009, plan out-of-scope: DLQ endpoint contracts).
- Behavior change is limited to the previously-OSError path: the DLQ transition now commits
  and the outbox row guarantees later file generation instead of deferring the whole
  promotion to the sweep.

## Security considerations
- None beyond existing authz flow (untouched).

## Rollback considerations
- Revert together with row 03 (the OSError it guards against is only gone because of row 03).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_ack_nack.py`
  — NACK success independent of any file state (row 09 asserts no file exists right after
  NACK+promote, yet `promoted: true` and the outbox row exists); INV-13 multi-consumer
  regression tests stay byte-identical.

## Completion criteria
- Inline promotion never touches the filesystem; NACK independence holds under injected
  filesystem failure elsewhere (worker path).

## Out of Scope
- Promotion transaction internals (row 03), loop wiring (row 06).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the OSError deferral handler | Pending | — | — | After row 03 |
| 2 | Run DLQ + ack/nack tests | Pending | — | — | |

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
- **Requirement ID**: `REQ-003`, `REQ-009`
- **Source issue**: `issues/20261029-104501_dlqbox001_dlq-sqlite-outbox.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/done/20261029-221254_dlqbox001_dlq-sqlite-outbox.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-103000
- **Related target files**: `scripts/eventbus/ack_route.py`
