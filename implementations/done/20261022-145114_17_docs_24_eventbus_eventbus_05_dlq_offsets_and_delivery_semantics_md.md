## Goal

Rewrite `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md` so it describes only the per-consumer counter `consumer_delivery_failure_count` and the redelivery behavior without the removed legacy columns, per `REQ-007` (rewrite the failure-counters section to describe only the per-consumer counter and the redelivery behavior without the legacy columns) and `AC-7`.

## Scope

Only `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`. Every mention of the event-level `delivery_failure_count` and `cycle_failure_count` counters is in scope: the NACK postconditions, the "Failure Count Split" section, the inline/background promotion descriptions, the redelivery (requeue) description, and the state-transition diagram.

## Assumptions

- `schema.sql` (row 6) removes both columns and `scripts/eventbus/dlq_repo.py` (row 4) stops copying/resetting them on redelivery.
- `consumer_delivery_failure_count` remains the sole counter that gates DLQ promotion.

## Design decisions

- Remove the legacy-counter mentions rather than annotating them as deprecated: REQ-007 asks for the final behavior only, with no history note.
- Preserve the per-consumer promotion semantics, offset/resume semantics, and lineage (redelivery inserts a new row) exactly — only the now-absent counters are edited.

## Alternatives considered

- Collapsing the three-counter "Failure Count Split" into one bullet about `consumer_delivery_failure_count` — rejected: the plan keeps a structured description of the single remaining counter, so keep the section but reduce it to that counter.

## Implementation

### Target file

`docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`

### Procedure

1. Clean up the NACK postconditions.
2. Rewrite the "Failure Count Split" section.
3. Clean up the promotion descriptions that name a shared counter.
4. Rewrite the redelivery (requeue) description.
5. Fix the state-transition diagram line that references the removed counters.
6. Run the docs checkers.

### Method

- **NACK Postconditions** ("ACK/NACK Rules > NACK Postconditions"):
  - Delete the clause "The events-level `delivery_failure_count` is a legacy value that NACK does not modify."
  - In the promotion bullet, drop ", not the shared `delivery_failure_count`", leaving "gated on the per-consumer failure count (`consumer_delivery_failure_count`)".
  - Rename the response key: "`{event_id, delivery_failure_count}`, where `delivery_failure_count` is the nacking consumer's per-consumer failure count" → "`{event_id, consumer_delivery_failure_count}`, where `consumer_delivery_failure_count` is the nacking consumer's per-consumer failure count".
- **"Failure Count Split"** (under "Dead Letter Queue (DLQ)"): reduce the three-bullet list to the single remaining counter. Keep a bullet for `consumer_delivery_failure_count` (per-consumer, gates promotion) and delete the `delivery_failure_count` (events-level, legacy) and `cycle_failure_count` (events-level, legacy) bullets. Update the closing sentence that says promotion "is gated on the per-consumer `consumer_delivery_failure_count`, not on `delivery_failure_count` or `cycle_failure_count`" to remove the two named counters.
- **Inline Promotion Path** and **Background Loop Promotion**: drop the clauses "The shared `events.delivery_failure_count` is intentionally ignored for gating" / "The shared `events.delivery_failure_count` is intentionally ignored for gating."
- **Requeue (Redelivery)**: in the numbered steps, delete "`cycle_failure_count = 0` (fresh retry budget)" and "`delivery_failure_count` copied from the original row (stored legacy value carried over)". State that redelivery inserts a fresh row with a new UUID and `redelivered_from` only; it no longer sets or copies either counter.
- **State Transition Table / Prohibited Transitions**: in the `DLQ ──REQUEUE──>` line, drop "(`cycle_failure_count` reset, `delivery_failure_count` preserved)".

### Details

- Evidence in-file: NACK postconditions at the "NACK Postconditions" subsection; the three-counter list under "Failure Count Split"; the "ignored for gating" clauses in the two promotion subsections; the redelivery steps numbering the reset/copy; and the REQUEUE transition line.
- Leave the per-consumer `consumer_delivery_failure_count` references, the offset/resume semantics, and the lineage model untouched.

## Compatibility considerations

N/A: documentation-only change; no runtime contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is described here beyond what already exists.

## Rollback considerations

N/A: revert the commit that makes this change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| Docs | Docs checkers | `check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py` | Pass |
| Reference table sync | Check | `generate_reference_table.py --check` | Pass |

## Completion criteria

No mention of `delivery_failure_count` or `cycle_failure_count` remains in the document except where a per-consumer `consumer_delivery_failure_count` reference legitimately contains the substring, the NACK response key reads `consumer_delivery_failure_count`, and the docs checkers plus `generate_reference_table.py --check` pass.

## Out of Scope

- Editing any other EventBus document (each is a separate row).
- Changing the DLQ promotion rule or redelivery behavior themselves (`scripts/eventbus/dlq.py`, `scripts/eventbus/dlq_repo.py`, rows 3–4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the failure-counters section and redelivery behavior to the per-consumer model | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the documentation checkers | Completed | 2026-10-22 | 2026-10-22 | check_docs_quality/structure/content_policy, generate_reference_table.py --check all pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 2026-10-22 | 2026-10-22 | |

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
- **Requirement ID**: `REQ-007` — update the four EventBus documents to describe only the per-consumer counter and the final contract
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `docs/24_eventbus/eventbus_05_dlq_offsets_and_delivery_semantics.md`
