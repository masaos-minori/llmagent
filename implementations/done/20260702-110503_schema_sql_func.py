# Implementation: schema_sql.py - Add build_eventbus_schema_sql()

## Goal

Add `build_eventbus_schema_sql() -> str` function to schema_sql.py.

## Scope

- scripts/db/schema_sql.py only: add one function and update module docstring

## Assumptions

1. Module docstring should be updated to list `build_eventbus_schema_sql` alongside existing functions
2. Function follows same pattern as `build_workflow_schema_sql()` (no parameters, returns string)

## Implementation

### Target file

- `scripts/db/schema_sql.py`

### Procedure

1. Add `build_eventbus_schema_sql() -> str` function after `build_workflow_schema_sql()`
2. Update module docstring to include `build_eventbus_schema_sql`

### Method

- Follow existing pattern exactly (same style as build_workflow_schema_sql)

### Details

Update module docstring:
```python
"""db/schema_sql.py
SQL DDL templates for rag.sqlite, session.sqlite, and workflow.sqlite schema creation.

...

Functions:
  build_rag_schema_sql(dims) — return DDL for rag.sqlite with given dimension
  build_session_schema_sql(dims) — return DDL for session.sqlite with given dimension
  build_workflow_schema_sql() — return DDL for workflow.sqlite (metadata DB)
  build_eventbus_schema_sql() — return DDL for eventbus.sqlite (event queue DB)
"""
```

Add function:
```python
def build_eventbus_schema_sql() -> str:
    """Return DDL for eventbus.sqlite (event queue DB)."""
    return _EVENTBUS_SCHEMA
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Type check | `uv run mypy scripts/db/schema_sql.py` | No type errors |
| Lint | `uv run ruff check scripts/db/schema_sql.py` | No lint errors |
