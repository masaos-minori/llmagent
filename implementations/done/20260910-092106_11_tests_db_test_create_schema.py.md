## Goal
Add an assertion that `create_eventbus_schema()` produces the new
`consumer_delivery`/`consumer_offsets` tables in addition to `events` (REQ-001,
REQ-002; AC-7).

## Scope
In scope: one new assertion (or a new small test) using the existing `_table_names()`
helper against a database created via `create_eventbus_schema()`. Out of scope: any
change to `_EVENTBUS_SCHEMA_NO_VEC0`, `TestCreateRagSchema`, `TestCreateSessionSchema`,
`TestCreateWorkflowSchema`, or any other unrelated test class in this file.

## Assumptions
- `_table_names(conn)` (existing helper) works unchanged against an
  eventbus-schema database — it already returns the full set of table names for any
  connection, no eventbus-specific special-casing needed.
- `test_eventbus_schema_timestamps` (existing test, line-anchored near
  `_EVENTBUS_SCHEMA_NO_VEC0` usage) already constructs an eventbus test database via
  `create_eventbus_schema()` — reuse the same construction pattern rather than
  inventing a new one.

## Design decisions
Add a test (e.g. `test_create_eventbus_schema_produces_new_tables`) that builds an
eventbus test database the same way `test_eventbus_schema_timestamps` does, then
asserts `{"events", "consumer_delivery", "consumer_offsets"} <= _table_names(conn)` —
using a subset check (not exact-set equality) so the assertion does not need updating
again if an unrelated future table is added.

## Alternatives considered
Extending `test_eventbus_schema_timestamps` itself with the new assertion (rather than
adding a separate test) was considered; adding a separate, narrowly-named test is
preferred so a future failure's test name immediately identifies which concern broke
(timestamp defaults vs. table presence).

## Implementation
### Target file
`tests/db/test_create_schema.py`

### Procedure
1. Add a new test function near `test_eventbus_schema_timestamps`, reusing its
   database-construction setup (mocking `db.create_schema.build_eventbus_schema_sql`
   if that test's pattern does so, or calling `create_eventbus_schema()` directly
   against a `tmp_path` database if that is simpler and equally valid).
2. Assert the new table names are present via `_table_names()`.

### Method
`pytest` test function, following this file's existing style for eventbus-schema
tests.

### Details
```python
def test_create_eventbus_schema_produces_new_tables(self, tmp_path: Path) -> None:
    db_file = tmp_path / "eventbus_tables.sqlite"
    cs.create_eventbus_schema(eventbus_db_path=str(db_file))
    with sqlite3.connect(db_file) as conn:
        tables = _table_names(conn)
    assert {"events", "consumer_delivery", "consumer_offsets"} <= tables
```
Adapt the exact call signature of `create_eventbus_schema()` to what this file's
existing eventbus tests already use (confirm parameter name, e.g.
`eventbus_db_path`, from `test_eventbus_schema_timestamps` or the `target ==
"eventbus"` branch near line 152).

## Compatibility considerations
Additive test only; no existing test in this file is modified.

## Security considerations
Test-only file; no production security surface.

## Rollback considerations
Revert this file's diff; no production behavior depends on this file.

## Validation plan
`uv run pytest tests/db/test_create_schema.py -v` — new test passes alongside all
existing tests in this file.

## Completion criteria
The new test passes, confirming `create_eventbus_schema()`'s bootstrap path produces
`consumer_delivery` and `consumer_offsets` alongside `events` (AC-7).

## Out of scope
Any change to the rag/session/workflow schema test classes in this same file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `test_create_eventbus_schema_produces_new_tables` | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: tests/db/test_create_schema.py
