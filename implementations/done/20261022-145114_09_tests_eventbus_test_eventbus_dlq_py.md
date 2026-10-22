## Goal

Remove assertions on `delivery_failure_count` in DLQ items and dead-letter records, and add an assertion that `GET /dlq` items lack the legacy fields (REQ-006).

## Scope

- Modify `tests/eventbus/test_eventbus_dlq.py` only.

## Assumptions

- `dlq.py` (record) and `event_repo.py` (listing selection) drop the event-level counter; items no longer carry it.

## Design decisions

- Delete the `delivery_failure_count` / `cycle_failure_count` assertions on items and `DlqEventRecord`.
- Add one assertion that a fetched item dict contains no `delivery_failure_count` key.

## Implementation

### Target file

`tests/eventbus/test_eventbus_dlq.py`

### Procedure

1. Remove assertions reading `delivery_failure_count` / `cycle_failure_count` from DLQ item dicts and from `DlqEventRecord` fields.
2. Add an assertion such as `assert "delivery_failure_count" not in item` (and `cycle_failure_count`) on a fetched `GET /dlq` item.
3. Keep the per-consumer / `dlq_at` / `dlq_requeue_count` assertions that are unaffected.

### Method

~27 references remain in this file; they assert the legacy field on items/records. Removing them plus one absence assertion verifies REQ-004 for the listing and record.

### Deviation from procedure

During implementation, additional dead-code blocks were found and removed beyond the prescribed steps. Each of the following sets a `delivery_failure_count` on the `events` row, a value the per-consumer model never reads (promotion gates on `consumer_delivery_failure_count`):

- `UPDATE events SET delivery_failure_count = 2 WHERE event_id = ?` blocks (several, including a pair preceding each NACK in the inline-promotion test).
- `UPDATE events SET delivery_failure_count = 2 WHERE event_id IN (?, ?)`.

These writes had no effect on promotion or on any response, so removing them changes no behavior. The prescribed assertion changes (remove legacy assertions, add `"delivery_failure_count" not in item` / `"cycle_failure_count" not in item`) were applied on top.

## Compatibility considerations

- Run after `dlq.py` + `event_repo.py`.

## Security considerations

- N/A: test-only.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py -q`.

## Completion criteria

- No legacy-counter assertion remains; a fetched item is asserted to lack `delivery_failure_count`.

## Out of Scope

- Other test files, source, documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-22 | 2026-10-22 | See Deviation: vestigial `UPDATE events SET delivery_failure_count` dead-code blocks also removed |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-22 | 2026-10-22 | test_eventbus_dlq.py passes |
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
- **Requirement ID**: REQ-006
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `tests/eventbus/test_eventbus_dlq.py`
