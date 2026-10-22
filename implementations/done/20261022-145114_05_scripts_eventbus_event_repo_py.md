## Goal

Remove `delivery_failure_count` from the `fetch_dlq` SELECT list so `GET /dlq` items carry no event-level counter (REQ-004).

## Scope

- Modify `scripts/eventbus/event_repo.py` only.
- The `fetch_dlq()` SELECT column list.

## Assumptions

- `dlq_route.py` serializes the `fetch_dlq` row with `dict(r)`; removing the column from the selection removes it from each item.
- The remaining selected columns (`dlq_requeue_count`, `dlq_at`, plus the identity/topic columns) are sufficient for the listing.

## Design decisions

- Drop `delivery_failure_count` from the SELECT; keep the other columns. The per-consumer count is not part of the event-level DLQ listing.

## Alternatives considered

- Selecting the per-consumer count into the listing: rejected — out of scope; the listing is event-level and the plan removes only the legacy field.

## Implementation

### Target file

`scripts/eventbus/event_repo.py`

### Procedure

1. In `fetch_dlq()` (line 118), remove `delivery_failure_count` from the SELECT column list, leaving `dlq_requeue_count, dlq_at` (and the leading identity columns) intact.

### Method

`fetch_dlq` selects a fixed column set that `dlq_route.py` dumps via `dict(r)`; the event-level counter appears in items only because it was selected. Removing it from the selection removes it from every item.

### Details

- `fetch_dlq()` at lines 110-118; SELECT lists `delivery_failure_count, dlq_requeue_count, dlq_at` at line 118.

## Compatibility considerations

- `GET /dlq` item payloads drop one legacy field; external consumers relying on it see the plan's breaking change.

## Security considerations

- N/A: parameterized query; dropping a selected column.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/eventbus/test_eventbus_dlq.py tests/eventbus/test_eventbus_dlq_pagination.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.

## Completion criteria

- `fetch_dlq()`'s SELECT contains no `delivery_failure_count`; `GET /dlq` items carry no event-level counter.

## Out of Scope

- DLQ record/listing (`dlq.py`), redelivery (`dlq_repo.py`), DDL/constants, tests, documents.

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
- **Related target files**: `scripts/eventbus/event_repo.py`
