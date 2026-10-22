## Goal

Update the EventBus schema assertions in `tests/db/test_create_schema.py` so the fresh-schema stub and its column assertions reflect the `events` table without the two removed event-level counter columns (`delivery_failure_count`, `cycle_failure_count`), per `REQ-006` (drop the legacy event-level counters) and `AC-5` (a database created from `schema.sql` has no event-level counter columns).

## Scope

Only `tests/db/test_create_schema.py`. The inline `_EVENTBUS_SCHEMA_NO_VEC0` stub and the two assertions in `TestEventBusSchemaNewColumns` are the only places in this file that still carry the legacy counters. `tests/db/test_eventbus_schema_equivalence.py` (a reference file) compares two fresh bootstraps, so it stays green once both sides lose the columns; it is not edited here.

## Assumptions

- `schema.sql` (row 6 of this plan) removes `delivery_failure_count` and `cycle_failure_count` from the `events` DDL in the same pass.
- `redelivered_from` is not a counter and is not removed by this plan; its assertion stays.
- The per-consumer `consumer_delivery_failure_count` column stays and must remain in the stub.

## Design decisions

- Edit the in-test DDL stub (`_EVENTBUS_SCHEMA_NO_VEC0`) rather than loading the real `schema.sql`: the tests patch `build_eventbus_schema_sql` with this literal string, so the stub must mirror the post-removal schema for the assertions to be meaningful.
- Delete the `cycle_failure_count` existence assertion and keep the `redelivered_from` one, instead of deleting the whole `TestEventBusSchemaNewColumns` class, to preserve coverage of the retained lineage column.

## Alternatives considered

- Loading the real `schema.sql` via `SQLiteHelper` instead of the patched stub — rejected because the existing tests deliberately skip the `sqlite-vec` extension and drive the DDL through the patched builder.
- Leaving the columns in the stub and only updating the assertions — rejected because a stub that declares columns the real schema no longer emits would drift from `schema.sql` and defeat the equivalence check.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

1. Remove the two legacy column lines from the `events` block of `_EVENTBUS_SCHEMA_NO_VEC0`.
2. Update `TestEventBusSchemaNewColumns` to drop the `cycle_failure_count` assertion and its class docstring mention, keeping the `redelivered_from` assertion.
3. Run the `tests/db` suite and the schema-equivalence check.

### Method

- In `_EVENTBUS_SCHEMA_NO_VEC0`, delete:
  - `    delivery_failure_count INTEGER NOT NULL DEFAULT 0,`
  - `    cycle_failure_count    INTEGER NOT NULL DEFAULT 0,`
  from the `CREATE TABLE IF NOT EXISTS events (...)` block. Leave `consumer_delivery_failure_count` (still required by the per-consumer model) and the `consumer_delivery` table's `consumer_delivery_failure_count` untouched.
- In `TestEventBusSchemaNewColumns`:
  - Delete `test_events_table_has_cycle_failure_count_column` (it asserts a column this plan removes).
  - Keep `test_events_table_has_redelivered_from_column` unchanged.
  - Shorten the class docstring from "includes `cycle_failure_count` and `redelivered_from` columns" to "includes the `redelivered_from` column".

### Details

- Evidence in-file: the legacy columns sit at the `events` block lines `delivery_failure_count` / `cycle_failure_count` (inline stub); the asserting test is `test_events_table_has_cycle_failure_count_column` with its message at the two-line assert; the class docstring reads "includes `cycle_failure_count` and `redelivered_from` columns".
- The `consumer_delivery_failure_count` matches are the per-consumer counter (prefixed `consumer_`) and are NOT removed.
- `test_eventbus_schema_equivalence.py` re-compares fresh bootstraps; after `schema.sql` and this stub both drop the columns, the comparison still holds.

## Compatibility considerations

N/A: this is a test-only change; no runtime or on-disk contract is affected.

## Security considerations

N/A: no auth, authorization, or input-handling path is touched.

## Rollback considerations

N/A: revert the commit that makes this change.

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/db/test_create_schema.py` | Unit | `uv run pytest tests/db -q` | Pass; no assertion references the removed columns |
| Schema equivalence | Regression | `uv run pytest tests/db/test_eventbus_schema_equivalence.py -q` | Pass |

## Completion criteria

The `_EVENTBUS_SCHEMA_NO_VEC0` stub lists no `delivery_failure_count` or `cycle_failure_count`, `TestEventBusSchemaNewColumns` no longer asserts `cycle_failure_count` (it still asserts `redelivered_from`), and `uv run pytest tests/db -q` passes.

## Out of Scope

- Editing `tests/db/test_eventbus_schema_equivalence.py` (reference file; stays green once both bootstraps match).
- Any change to the `events` DDL itself — that is `scripts/eventbus/schema.sql` (row 6).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the EventBus schema stub and assertions to drop the legacy counter columns | Pending | — | — | |
| 2 | Update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
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
- **Related target files**: `tests/db/test_create_schema.py`
