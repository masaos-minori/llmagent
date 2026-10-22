## Goal

Remove the event-level counter columns from the redelivery INSERT/SELECT and the `_constants` imports, and update the docstring (REQ-004).

## Scope

- Modify `scripts/eventbus/dlq_repo.py` only.
- The redelivery `INSERT ... SELECT`, the copied/reset columns, and the module/docstring text.

## Assumptions

- Redelivery inserts a fresh event row copying the topic/payload and resetting counters; only the per-consumer model survives.
- `_constants.py` (its own document) removes both constants.

## Design decisions

- The redelivery INSERT copies `_COL_DELIVERY_FAILURE_COUNT` and sets `_COL_CYCLE_FAILURE_COUNT` to `0`; drop both so the new row carries no event-level counter. The per-consumer `consumer_delivery` rows are keyed by `(consumer_id, event_id)` and are not part of this `events`-table redelivery copy.

## Alternatives considered

- Copying `0` for both to preserve the (inert) columns: rejected — the columns are being removed from the schema; copying them keeps dead logic alive.

## Implementation

### Target file

`scripts/eventbus/dlq_repo.py`

### Procedure

1. In the redelivery `INSERT INTO events (...) ... SELECT ...` (lines 58-59), remove `{_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT}` from the insert column list and `{_COL_DELIVERY_FAILURE_COUNT}, 0` from the select list.
2. Remove the `_COL_CYCLE_FAILURE_COUNT` (line 13) and `_COL_DELIVERY_FAILURE_COUNT` (line 14) imports from `_constants`.
3. Update the docstring that describes "copied delivery_failure_count, cycle_failure_count=0" (lines 33-34) to describe the redelivery without the event-level counters.

### Method

`dlq_repo.redeliver` re-inserts an `events` row under the per-consumer model; the two events-level columns are inert leftovers. Removing them here and from the constants makes the redelivery consistent with the new schema.

### Details

- Imports at lines 13-14; INSERT/SELECT at lines 58-59; docstring at lines 33-34.

## Compatibility considerations

- Depends on `schema.sql` (its own document) no longer defining the two columns; edit together. After both, no importer of the constants remains (`_constants.py` removes them).

## Security considerations

- N/A: parameterized SQL unchanged in shape; dropping selected columns.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_requeue_edge_cases.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.

## Completion criteria

- The redelivery INSERT/SELECT contain no event-level counter; `_constants` imports are gone; the docstring no longer mentions them.

## Out of Scope

- DLQ record/listing (`dlq.py`), the `fetch_dlq` listing (`event_repo.py`), DDL/constants removal, tests, documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 2026-10-22 | 2026-10-22 | |
| 2 | Add or update tests per Validation plan | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-22 | 2026-10-22 | |
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
- **Requirement ID**: REQ-004
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `scripts/eventbus/dlq_repo.py`
