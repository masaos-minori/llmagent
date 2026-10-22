## Goal

Remove the legacy event-level counter references from the redelivery/requeue description in `docs/24_eventbus/eventbus_07_configuration-and-operations.md`, so the requeue section no longer describes copying `delivery_failure_count` or resetting `cycle_failure_count` (`REQ-004`; `REQ-007`; `AC-4`, `AC-7`).

## Scope

Only `docs/24_eventbus/eventbus_07_configuration-and-operations.md`. The requeue line describes the legacy counters being copied/reset on redelivery; `scripts/eventbus/dlq_repo.py` (row 4) removes those reads from the redelivery INSERT/SELECT, so the doc must stop describing them.

## Assumptions

- `scripts/eventbus/dlq_repo.py` (row 4) drops `_COL_DELIVERY_FAILURE_COUNT` / `_COL_CYCLE_FAILURE_COUNT` from the redelivery INSERT/SELECT, so a redelivered row no longer copies or resets them.
- Redelivery still sets `redelivered_from`, increments `dlq_requeue_count` on the original, and preserves `dlq_at`.

## Design decisions

- Delete only the "`delivery_failure_count` copied, `cycle_failure_count` reset" clause from the requeue parenthetical; keep the rest of the sentence (`redelivered_from`, `dlq_requeue_count`, `dlq_at`) unchanged.
- Keep the rest of the document untouched.

## Alternatives considered

- Rewording the clause to say the counters "used to be copied/reset" — rejected: `REQ-007` asks for the final behavior only, with no history note.

## Implementation

### Target file

`docs/24_eventbus/eventbus_07_configuration-and-operations.md`

### Procedure

1. In the requeue/redelivery description, remove "`delivery_failure_count` copied, `cycle_failure_count` reset" from the parenthetical that lists what the new event row carries.
2. Run the docs checkers.

### Method

- Edit the sentence under the requeue section from:

  > `POST /dlq/{event_id}/requeue` uses the lineage model: it inserts a new event row (`redelivered_from` set to the original, `delivery_failure_count` copied, `cycle_failure_count` reset) and increments `dlq_requeue_count` on the original, whose `dlq_at` is preserved. See `eventbus_05_dlq_offsets_and_delivery_semantics.md` (Requeue (Redelivery)).

  to omit the legacy-counter clause:

  > `POST /dlq/{event_id}/requeue` uses the lineage model: it inserts a new event row (`redelivered_from` set to the original) and increments `dlq_requeue_count` on the original, whose `dlq_at` is preserved. See `eventbus_05_dlq_offsets_and_delivery_semantics.md` (Requeue (Redelivery)).

### Details

- Evidence in-file: line 185 names `delivery_failure_count` and `cycle_failure_count` inside the requeue parenthetical. No other occurrence of either name exists in this document.

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

`docs/24_eventbus/eventbus_07_configuration-and-operations.md` names no `delivery_failure_count` or `cycle_failure_count`, and the docs checkers plus `generate_reference_table.py --check` pass.

## Out of Scope

- Editing any other EventBus document (each is a separate row).
- Changing the redelivery behavior itself (`scripts/eventbus/dlq_repo.py`, row 4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the legacy counter references from the requeue description | Pending | — | — | |
| 3 | Run the documentation checkers | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Related target files**: `docs/24_eventbus/eventbus_07_configuration-and-operations.md`
