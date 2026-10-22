## Goal

Remove the event-level `delivery_failure_count` from `DlqEventRecord`, the events-level counters from the promotion SELECTs, and log the per-consumer count in the inline promotion message (REQ-004).

## Scope

- Modify `scripts/eventbus/dlq.py` only.
- `DlqEventRecord`, `_build_dlq_record`, the promotion SELECTs, and the inline promotion log line.

## Assumptions

- `consumer_delivery_failure_count` is the surviving per-consumer field; it is already passed through `_build_dlq_record`.
- Redelivery (`dlq_repo.py`) and the `fetch_dlq` listing (`event_repo.py`) are separate documents.

## Design decisions

- Drop `delivery_failure_count: int` from the dataclass; keep `consumer_delivery_failure_count: int | None`.
- Select only `consumer_delivery_failure_count` (and the lineage columns) in the promotion queries; drop `e.delivery_failure_count, e.cycle_failure_count`.

## Alternatives considered

- Keeping the field but always copying `0`: rejected — the plan removes the column class entirely; nothing copies it.

## Implementation

### Target file

`scripts/eventbus/dlq.py`

### Procedure

1. Remove `delivery_failure_count: int` from the `DlqEventRecord` dataclass (line 30); keep `consumer_delivery_failure_count`.
2. In `_build_dlq_record()`, remove the `delivery_failure_count=row["delivery_failure_count"]` argument (line 50) passed to `DlqEventRecord(...)`.
3. In the promotion SELECT (line 92), remove `e.delivery_failure_count, e.cycle_failure_count`; select the remaining columns needed for promotion and the per-consumer count.
4. In the second promotion reference (line 140), remove `delivery_failure_count, cycle_failure_count` from the selected column list.
5. In the inline promotion log (lines 156-158), replace `row["delivery_failure_count"]` with the per-consumer count already logged, and drop the event-level token from the message.

### Method

`DlqEventRecord` is written as JSON by `_atomic_write` and read by no code; removing one field changes only that dead-letter payload's shape (a legacy, unread record, per the plan). The promotion queries only consumed the events-level counters to log them; the per-consumer count is the authoritative value.

### Details

- `DlqEventRecord` fields at lines 21-32; `_build_dlq_record` at lines 37-52; promotion SELECT at line 92; second selection at line 140; inline log at lines 156-158 (`"dlq inline promoted event_id=%s delivery_failure_count=%d"` + `row["delivery_failure_count"]`).

## Compatibility considerations

- The dead-letter JSON format drops one legacy field; no reader exists under `scripts/` (UNK-04) — treat existing files as read-only history.

## Security considerations

- N/A: no authz/SQL-injection surface change beyond dropping a selected column.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_promotion.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.

## Completion criteria

- `DlqEventRecord` has no `delivery_failure_count`; the promotion SELECTs contain no events-level counter; the inline log reports the per-consumer count.

## Out of Scope

- Redelivery (`dlq_repo.py`), the `fetch_dlq` listing (`event_repo.py`), DDL/constants, tests, documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `scripts/eventbus/dlq.py`
