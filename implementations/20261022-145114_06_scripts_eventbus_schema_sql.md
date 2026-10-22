## Goal

Remove the two `events` columns `delivery_failure_count` and `cycle_failure_count` from `schema.sql` so new databases do not carry the legacy counters (REQ-005).

## Scope

- Modify `scripts/eventbus/schema.sql` only.

## Assumptions

- The schema-migration removal is already in place (commit `31f8c3be9`); this is the single DDL source for fresh databases.
- The deployed database keeps the two inert columns (UNK-02); inserts that omit them keep working.

## Design decisions

- Delete the two column definitions from the `events` table only; keep `consumer_delivery_failure_count` on `consumer_delivery`.

## Alternatives considered

- Keeping the columns as `NOT NULL DEFAULT 0`: rejected — the plan removes the class; keeping them re-introduces the inert counters.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

1. Delete the `delivery_failure_count INTEGER NOT NULL DEFAULT 0,` line (line 10) and the `cycle_failure_count    INTEGER NOT NULL DEFAULT 0,` line (line 11) from the `events` table definition.

### Method

`schema.sql` is the single source for fresh-database schema; removing the columns here makes new databases match the per-consumer model. The equivalence tests compare fresh bootstraps only.

### Details

- Column definitions at lines 10-11 within the `events` table.

## Compatibility considerations

- Only affects newly created databases; the deployed database is untouched (UNK-02). `tests/db/test_eventbus_schema_equivalence.py` compares fresh bootstraps and must stay green.

## Security considerations

- N/A: DDL only.

## Rollback considerations

- revert the commit.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py tests/db/test_eventbus_schema_equivalence.py -q`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_db_separation.py`.

## Completion criteria

- `schema.sql` defines no `delivery_failure_count` / `cycle_failure_count` columns on `events`; the fresh-schema and equivalence tests pass.

## Out of Scope

- The deployed database, redelivery/DLQ code, constants, tests (beyond schema), documents.

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
- **Requirement ID**: REQ-005
- **Source issue**: `issues/20261022-124142_evcounter_decide-event-level-failure-counters.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261022-130338_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261022-145114
- **Related target files**: `scripts/eventbus/schema.sql`
