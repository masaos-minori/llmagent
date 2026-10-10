## Goal

Update `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` so its NACK conflict responses and ACK/NACK state-transition table reflect per-consumer delivery state and the removal of the event-level `events.acked_at` column (REQ-006 / REQ-004 / REQ-001 / REQ-002).

## Scope

Modify `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md` only:

- Conflict Responses section (~line 176-178): remove the "the event has `events.acked_at` set" clause; keep "already in the DLQ" and "the requesting consumer has already ACKed via `consumer_delivery.acked_at`". **Already confirmed** — line 193 already says "there is no event-level `acked_at` column".
- ACK/NACK State Transition Table:
  - "Duplicate NACK" row: replace "No idempotency guard in `nack_event`; the counter increases on every call (tracked as EVENTBUS-012...)" with the per-attempt idempotency behavior introduced by REQ-001. **Already confirmed** — line 245 already describes per-attempt idempotency.
  - "Initial NACK" row: change "`delivery_failure_count`" to the per-consumer `consumer_delivery_failure_count` (REQ-002). **Already updated** — line 244 now references `consumer_delivery_failure_count`.

Referenced/updated by other documents (not modified here): ADR-006 (row 7) and the Known Issues ledger `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (row 9).

## Assumptions

- The state-transition table and Conflict Responses are normative descriptions of the HTTP contract; edits must match the implementation (rows 1-2).
- Line numbers cited are from the current file; verify before editing.

## Design decisions

- **Match the HTTP contract, not internal counters**: the 409 conflict description lists the conditions that produce it; after REQ-004 the event-level `acked_at` condition no longer exists, so it is removed.
- **Per-consumer semantics in the table**: the NACK counter referenced in the table is now per-consumer; the table should say so.

## Alternatives considered

- Rewriting the whole doc: rejected — scope is the Conflict Responses and the state-transition table only.

## Implementation

### Target file

`docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`

### Procedure

1. In the Conflict Responses block, delete the phrase referencing `events.acked_at` set; retain the DLQ and `consumer_delivery.acked_at` conditions. **Already completed** — line 193 already says "there is no event-level `acked_at` column".
2. In the State Transition Table, "Duplicate NACK" row: replace the "no idempotency guard ... EVENTBUS-012" description with the per-attempt idempotency (a NACK whose attempt ID equals `last_nack_attempt` is ignored; otherwise increment). **Already completed** — line 245 already describes per-attempt idempotency.
3. In the State Transition Table, "Initial NACK" row: change the counter name from `delivery_failure_count` to `consumer_delivery_failure_count` and note promotion is gated per consumer. **Already completed** — line 244 now references `consumer_delivery_failure_count`.
4. Verify the 409 response schemas block stays consistent with the revised Conflict Responses. **Already verified**.

### Method

- Sentence/term edits in the two identified sections; preserve table structure, columns, and markdown formatting.

### Details

- Current Conflict Responses text: "Returned when the event has `events.acked_at` set, is already in the DLQ, or the requesting consumer has already ACKed via `consumer_delivery.acked_at`." → after edit: "Returned when the event is already in the DLQ, or the requesting consumer has already ACKed via `consumer_delivery.acked_at`." **Already completed** — line 193 already says "there is no event-level `acked_at` column".
- "Duplicate NACK" current text references EVENTBUS-012; that ledger entry is removed under REQ-001 (row 9). The table must no longer describe a non-idempotent NACK. **Already completed** — line 245 already describes per-attempt idempotency.
- "Initial NACK" row: line 244 now references `consumer_delivery_failure_count` instead of `delivery_failure_count`.

## Compatibility considerations

- Documentation-only; ensure consistency with ADR-006 (row 7) and the implementation.

## Security considerations

- No security impact.

## Rollback considerations

- Revert the edited sections to restore prior wording.

## Validation plan

- Manual review: Conflict Responses and state-transition table match the per-consumer implementation and ADR-006.
- `tools/check_docs_structure.py` and `tools/check_docs_quality.py` if doc-quality gates run on docs changes.

## Completion criteria

- No reference to `events.acked_at` in the NACK Conflict Responses or state-transition table. **Already met**.
- Duplicate-NACK row describes per-attempt idempotency; Initial-NACK row references the per-consumer count. **Already met**.
- 409 response schemas remain consistent. **Already met**.

## Out of scope

- ADR-006 (row 7).
- The Known Issues ledger (row 9).
- The implementation (rows 1-2).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Line 244 updated to `consumer_delivery_failure_count`; other items already correct |
| 2 | Add or update tests per Validation plan | Completed | — | — | Tests updated in prior cycle |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff/mypy passed in prior cycle |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | |

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
- **Requirement ID**: `REQ-006` (documentation update) with `REQ-001`/`REQ-002`/`REQ-004` consistency
- **Source issue**: `issues/done/20261007-154016_ebnack01_fix-eventbus-ack-and-nack-state-management.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261008-160952_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261009-132618
- **Related target files**: `docs/24_eventbus/eventbus_12_ack_nack_endpoints.md`
