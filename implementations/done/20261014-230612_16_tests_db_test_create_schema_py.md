## Goal

Verify the generated session schema DDL declares `sessions.undo_floor_message_id INTEGER NOT NULL DEFAULT 0`.

## Scope

Only `tests/db/test_create_schema.py`. This document names exactly one target file.

## Assumptions

- The existing `TestCreateSessionSchema` class (lines 271-319) validates a **hardcoded** `_SESSION_SCHEMA_NO_VEC0` string via a fixture that stubs `build_session_schema_sql` (lines 201-217). Those tests do NOT exercise the real builder in `scripts/db/schema_sql.py`.
- Therefore a new assertion must inspect the real generated DDL (the unstubbed builder or the `_SESSION_SCHEMA_TEMPLATE`), not the stubbed fixture.

## Design decisions

- Add a test that reads the real generated session DDL (via `schema_sql.build_session_schema_sql()` or the template) and asserts the new column is present with the exact constraint.
- Keep the existing stubbed-fixture tests unchanged.

## Alternatives considered

- **Assert via the stubbed fixture vs. the real builder** — the existing `TestCreateSessionSchema` validates a hardcoded DDL string through a stubbed builder; a new test must call the real `build_session_schema_sql()` to actually cover the new column.
- **Regex vs. substring match** — a regex asserts the exact `NOT NULL DEFAULT 0` constraint, catching a wrong default or nullability.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

Add a test (in `TestCreateSessionSchema` or a new class) that asserts the real generated session DDL contains `undo_floor_message_id` with `NOT NULL DEFAULT 0`.

### Method

```python
def test_session_schema_has_undo_floor_column(self) -> None:
    import db.schema_sql as schema_sql
    ddl = schema_sql.build_session_schema_sql()   # real builder, not stubbed
    assert "undo_floor_message_id" in ddl
    # assert the NOT NULL DEFAULT 0 constraint is present
    import re
    assert re.search(r"undo_floor_message_id\s+INTEGER\s+NOT NULL\s+DEFAULT\s+0", ddl, re.IGNORECASE)
```

Alternatively assert against `schema_sql._SESSION_SCHEMA_TEMPLATE` directly. Either way, do NOT route through the stubbed `session_tmp_db` fixture (which returns the hardcoded string).

### Details

- If `build_session_schema_sql()` requires arguments (e.g. `dims`), pass them as the real function expects; otherwise call it with no args. Match the real signature.
- The assertion should catch a missing column or a wrong constraint (e.g. nullable / wrong default).

## Compatibility considerations

N/A: purely additive test. Does not touch the stubbed-fixture tests.

## Security considerations

N/A: test-only.

## Rollback considerations

Revert the commit.

## Validation plan

```bash
uv run pytest tests/db/test_create_schema.py -p no.cacheprovider
```

Assert: the new column assertion holds against the real DDL; all existing schema tests still pass.

## Completion criteria

`test_create_schema.py` asserts the real session DDL declares `undo_floor_message_id INTEGER NOT NULL DEFAULT 0`; the test passes.

## Out of scope

The DDL definition itself (row 01) and the migration/recreation strategy.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261015-191020 | 20261015-191020 |  |
| 2 | Add or update tests per Validation plan | Completed | 20261015-191020 | 20261015-191020 | additive; real builder not stubbed |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261015-191020 | 20261015-191020 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | N/A | — | — |  |

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
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261014-214826_plan.md
- **Source implementation procedure**: N/A
- **Generated at**: 20261014-230612
- **Related target files**: tests/db/test_create_schema.py