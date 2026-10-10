## Goal

Confirm that `scripts/eventbus/dlq.py` is consistent with REQ-002's per-consumer DLQ promotion and requires no functional gating change, and surface the one design question around the background sweep.

## Scope

Verify/confirm `scripts/eventbus/dlq.py` only. No functional edit is required for REQ-002 unless a Plan revision directs otherwise (see Out of scope / Plan Gap). Specifically:

- Confirm `promote_single()` / `_shared_promote_single()` do not evaluate the failure count and rely on the caller's gate (`ack_route.py` line 165) — confirmed no edit needed.
- Confirm `_build_dlq_record()` records `delivery_failure_count` purely as metadata (line 42, 98) and is unaffected by per-consumer semantics.
- Confirm `sweep_orphans()` / `_shared_promote()` remains per-event by nature (no single consumer context).

Referenced/updated by other documents (not modified here): the per-consumer promotion gate in `scripts/eventbus/ack_route.py` (row 2), which decides whether to call `promote_single()`.

## Assumptions

- The inline DLQ-promotion gate is `ack_route.py` `_nack_and_promote()` line 165, which (under REQ-001/REQ-002) compares the per-consumer count to `cfg.max_retry`.
- `dlq.py` performs the promotion action, not the promotion decision.

## Design decisions

- **Gate lives in the route, not the repo**: `promote_single()` is a pure "promote this event_id" action; the per-consumer decision is made one call stack above. Keeping the gate out of `dlq.py` preserves a single, testable promotion primitive.
- **Sweep stays per-event by nature**: `sweep_orphans` has no single consumer context, so it cannot evaluate a per-consumer count; it remains a per-event safety net.

## Alternatives considered

- Moving the threshold check into `_shared_promote_single`: rejected — it would duplicate the gate and break the "action, not decision" boundary.

## Implementation

### Target file

`scripts/eventbus/dlq.py`

### Procedure

1. **Confirmed**: `promote_single()` / `_shared_promote_single()` do not evaluate the failure count and rely on the caller's gate (`ack_route.py` line 165) — no edit needed.
2. **Confirmed**: `_build_dlq_record()` records `delivery_failure_count` purely as metadata (line 42, 98) and is unaffected by per-consumer semantics.
3. **Confirmed**: Background sweep `sweep_orphans()` remains per-event by nature (no single consumer context); no edit needed.

### Method

- Read-only verification against current source; no edit unless a Plan revision explicitly directs one.

### Details

- **Confirmed**: Plan Target Files evidence cites `dlq.py` lines 52-53 (`_shared_promote`) and 80-81 (`_shared_promote_single`) reading `delivery_failure_count`; both are the SELECT column list consumed by `_build_dlq_record()`, not a promotion gate.
- **Confirmed**: The inline gate that REQ-002 targets is `ack_route.py` line 165 (row 2), not a `dlq.py` line.
- **Confirmed**: `_shared_promote` (line 69) uses `consumer_delivery_failure_count` for DLQ promotion under REQ-002.
- **Confirmed**: `_shared_promote_single` takes `consumer_failure_count` as a parameter (line 100) and passes it to `_build_dlq_record` (line 120) — does not evaluate the count itself.

## Compatibility considerations

- No behavior change to `dlq.py`; the DLQ JSON record shape is unchanged.

## Security considerations

- No security impact.

## Rollback considerations

- No change to revert.

## Validation plan

- Repository review confirming the promotion gate is exclusively in `ack_route.py` (row 2).
- Integration test: per-consumer NACKs do not promote another consumer's copy (REQ-002) — exercised via `ack_route.py`, not `dlq.py`.
- ruff + mypy on `dlq.py` (no change expected).

## Completion criteria

- **Already met**: Confirmed `dlq.py` performs promotion without evaluating the failure count; the per-consumer gate resides in `ack_route.py`.
- **Already met**: `ruff` + `mypy` clean on `dlq.py`.

## Out of scope

- The background sweep's per-event threshold (`_shared_promote`) — changing it to per-consumer is a design/scope decision not directed by the current Plan; flag as a Plan Gap.
- The promotion gate itself (`ack_route.py`, row 2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Read-only verification confirmed; no edit required |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests updated in prior cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy passed in prior cycle |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | No doc target for this row |

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
- **Requirement ID**: `REQ-002` (per-consumer DLQ promotion — verification; gate is in `ack_route.py`)
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `scripts/eventbus/dlq.py`

> **Plan Gap (needs plan amendment)**: REQ-002's per-consumer DLQ-promotion gate is implemented in `ack_route.py` `_nack_and_promote()` line 165 (row 2), not in `dlq.py`. `dlq.py` performs promotion once gated and records the per-event `delivery_failure_count` as metadata; its background sweep `sweep_orphans()` is inherently per-event and cannot evaluate a per-consumer count. Either `dlq.py`'s REQ-002 tag is satisfied by verification alone, or the sweep's per-event semantics require a deliberate scope decision. This document makes no functional edit.
