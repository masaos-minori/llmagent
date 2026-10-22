## Goal

Remove the legacy event-level counter `delivery_failure_count` from the `GET /dlq` item description in `docs/24_eventbus/eventbus_04_dlq_endpoint.md`, per `REQ-007` (describe only the per-consumer counter and the final contract) and `AC-7`.

## Scope

Only `docs/24_eventbus/eventbus_04_dlq_endpoint.md`. The `delivery_failure_count` field is removed from `GET /dlq` items by `scripts/eventbus/event_repo.py` (row 5) and `scripts/eventbus/dlq.py` (row 3); this doc must stop describing a field the endpoint no longer returns.

## Assumptions

- `scripts/eventbus/event_repo.py` (row 5) drops `delivery_failure_count` from the `fetch_dlq` SELECT, so `GET /dlq` items no longer carry it.
- Items still carry event identity, `dlq_at`, and `dlq_requeue_count`.

## Design decisions

- Delete the legacy-value bullet entirely rather than rewording it: the field no longer exists, so any description would describe behavior the endpoint does not perform.
- Keep the ordering note (items ordered by `seq` ascending) and the requeue section unchanged.

## Alternatives considered

- Rewording the bullet to say the field "used to be present" — rejected: REQ-007 asks for the final behavior only, with no history note.

## Implementation

### Target file

`docs/24_eventbus/eventbus_04_dlq_endpoint.md`

### Procedure

1. Remove `delivery_failure_count` from the list of fields each `GET /dlq` item carries.
2. Delete the bullet that explains `delivery_failure_count` as a stored events-level legacy value.
3. Run the docs checkers.

### Method

- In the "List DLQ Entries > Behavior" section, edit the second bullet from:

  > The response is a pagination envelope (`total`, `limit`, `offset`) plus an `items` array. Each item carries event identity, `dlq_at` (the time the event was promoted to the DLQ), `dlq_requeue_count` and `delivery_failure_count`.

  to omit the field:

  > The response is a pagination envelope (`total`, `limit`, `offset`) plus an `items` array. Each item carries event identity, `dlq_at` (the time the event was promoted to the DLQ) and `dlq_requeue_count`.

- Delete the third bullet entirely:

  > `delivery_failure_count` is the stored events-level value, a legacy value that NACK does not modify under the per-consumer model; it is not the per-consumer failure count returned by `POST /nack`.

### Details

- Evidence in-file: the field is named in the "Each item carries ..." sentence and in the dedicated legacy-value bullet under "List DLQ Entries > Behavior".

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

`GET /dlq` item descriptions name no `delivery_failure_count`, the legacy-value bullet is deleted, and the docs checkers plus `generate_reference_table.py --check` pass.

## Out of Scope

- Editing the requeue section or any other EventBus document (each is a separate row).
- Changing the `GET /dlq` endpoint behavior itself (`scripts/eventbus/event_repo.py`, row 5).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the legacy counter from the `GET /dlq` item description | Completed | 2026-10-22 | 2026-10-22 | |
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
- **Related target files**: `docs/24_eventbus/eventbus_04_dlq_endpoint.md`
