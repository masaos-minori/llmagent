## Goal

Remove the two legacy event-level counter columns (`delivery_failure_count`, `cycle_failure_count`) from the inline fallback schema in `tests/eventbus/test_eventbus_restart_resume.py`, so the test-only schema stub matches the post-removal `schema.sql`, per `REQ-006` (update the tests to the new contract) and `AC-6`.

## Scope

Only `tests/eventbus/test_eventbus_restart_resume.py`. The only legacy-counter references are the two column definitions in the inline fallback DDL inside `TestOutOfOrderAckNoSkipOnReconnect._create_tables`.

## Assumptions

- `schema.sql` (row 6 of this plan) removes the two columns from the real DDL in the same pass.
- The per-consumer `consumer_delivery_failure_count` column and the `consumer_delivery` / `consumer_offsets` tables stay.

## Design decisions

- Edit only the inline fallback `executescript` string. `_create_tables` prefers the real `scripts/eventbus/schema.sql` when present and uses the inline block only as an isolation fallback, so the inline block must not declare columns the real schema no longer emits.

## Alternatives considered

- Leaving the columns in the inline fallback — rejected: the fallback would diverge from the post-removal `schema.sql` and could mask a schema mismatch in the isolated-code path.
- Deleting the inline fallback entirely — rejected: it is the isolation fallback used when `schema.sql` is absent; removing it changes test setup behavior beyond this row's scope.

## Implementation

### Target file

`tests/eventbus/test_eventbus_restart_resume.py`

### Procedure

1. Delete the two legacy column lines from the inline `_create_tables` fallback schema.
2. Run the EventBus test suite.

### Method

- In `TestOutOfOrderAckNoSkipOnReconnect._create_tables`, within the inline `conn.executescript(...)` string, delete:
  - `"delivery_failure_count INTEGER NOT NULL DEFAULT 0, "`
  - `"cycle_failure_count INTEGER NOT NULL DEFAULT 0, "`
  from the `CREATE TABLE IF NOT EXISTS events (...)` definition. Keep `"consumer_delivery_failure_count INTEGER NOT NULL DEFAULT 0"` and the `consumer_delivery` / `consumer_offsets` tables.

### Details

- Evidence in-file: the two columns are the consecutive lines before `"redelivered_from TEXT, "` ... actually they follow `"acked INTEGER NOT NULL DEFAULT 0, "` and precede `"redelivered_from TEXT, "`; the per-consumer line is the last column before the closing `"); "`.
- No assertion in this file reads the removed counters; the offset/resume logic keys on `consumer_delivery` and `consumer_offsets`, which are unchanged.

## Compatibility considerations

N/A: test-only change; no runtime or on-disk contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is touched.

## Rollback considerations

N/A: revert the commit that makes this change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/eventbus/test_eventbus_restart_resume.py` | Integration | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -q` | Pass |
| Whole EventBus suite | Regression | `uv run pytest tests/eventbus -q` | No new failures |

## Completion criteria

The inline `_create_tables` fallback schema lists no `delivery_failure_count` or `cycle_failure_count`, and `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -q` passes.

## Out of Scope

- Any change to the real `scripts/eventbus/schema.sql` (row 6).
- Other test files' inline schemas (each row is handled by its own document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove the legacy counter columns from the inline fallback schema | Completed | 2026-10-22 | 2026-10-22 | |
| 2 | Update tests per Validation plan | Completed | 2026-10-22 | 2026-10-22 | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 2026-10-22 | 2026-10-22 | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A: test-only change | — | — | |

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
- **Requirement ID**: `REQ-006` — update the tests to the new contract after removing the legacy event-level counters
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `tests/eventbus/test_eventbus_restart_resume.py`
