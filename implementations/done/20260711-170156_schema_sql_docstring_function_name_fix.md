# Implementation Procedure: scripts/db/schema_sql.py — fix stale docstring function references

Source plan: `plans/20260711-164446_plan.md` — Phase 4 (documentation, checkbox 2)

## Goal

Fix the stale module docstring in `scripts/db/schema_sql.py` that references
`_build_rag_schema_sql`/`_build_session_schema_sql` as functions living in
`create_schema.py`. Neither underscored name exists anywhere in the codebase; the real
functions are `build_rag_schema_sql`/`build_session_schema_sql` (no leading underscore),
defined in `schema_sql.py` itself.

## Scope

**In-Scope:**
- `scripts/db/schema_sql.py`: module-level docstring only (lines 1-15, specifically the
  "Templates use DIMS placeholder..." paragraph referencing `_build_rag_schema_sql` /
  `_build_session_schema_sql` in `create_schema.py`)

**Out-of-Scope:**
- Any function body, DDL template constant, or other docstring in this file
- `create_schema.py` itself — not modified (it does not define these functions; the
  docstring's claim about its location is simply wrong)
- Any other file

## Assumptions

1. The current module docstring (lines 1-15) reads:
   ```
   """db/schema_sql.py
   SQL DDL templates for rag.sqlite, session.sqlite, workflow.sqlite, and eventbus.sqlite schema creation.

   Templates use DIMS placeholder that must be replaced with the actual embedding
   dimension count before execution (done by _build_rag_schema_sql /
   _build_session_schema_sql in create_schema.py).

   Functions:
     build_rag_schema_sql(dims) — return DDL for rag.sqlite with given dimension
     build_session_schema_sql(dims) — return DDL for session.sqlite with given dimension
     build_workflow_schema_sql() — return DDL for workflow.sqlite (metadata DB)
     build_eventbus_schema_sql() — return DDL for eventbus.sqlite (event bus message queue)
     apply_workflow_migrations(conn) — apply incremental schema migrations to an existing workflow DB
   """
   ```
   confirmed by direct read. Note the "Functions:" list below the stale paragraph already
   correctly names `build_rag_schema_sql`/`build_session_schema_sql` (no underscore) — only
   the "Templates use DIMS placeholder..." paragraph above it is wrong.
2. `grep` confirms neither `_build_rag_schema_sql` nor `_build_session_schema_sql` (with
   leading underscore) exists anywhere in the codebase.
3. `build_rag_schema_sql` is defined at line 137 and `build_session_schema_sql` at line 142
   of `schema_sql.py` itself (confirmed by direct read via
   `grep -n "^def build_" scripts/db/schema_sql.py`), not in `create_schema.py`.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. Locate the module docstring's "Templates use DIMS placeholder..." paragraph (lines
   5-7).
2. Replace the parenthetical `(done by _build_rag_schema_sql / _build_session_schema_sql
   in create_schema.py)` with a corrected reference to the real, non-underscored function
   names and their actual location (this module, not `create_schema.py`).
3. Leave the "Functions:" list (lines 9-14) unchanged — it is already correct.

### Method

Direct text replacement within the module docstring only. No code logic changes.

### Details

Corrected docstring paragraph (illustrative wording, adapt exact phrasing as needed):

```python
"""db/schema_sql.py
SQL DDL templates for rag.sqlite, session.sqlite, workflow.sqlite, and eventbus.sqlite schema creation.

Templates use DIMS placeholder that must be replaced with the actual embedding
dimension count before execution (done by build_rag_schema_sql(dims) /
build_session_schema_sql(dims), both defined below in this module).

Functions:
  build_rag_schema_sql(dims) — return DDL for rag.sqlite with given dimension
  build_session_schema_sql(dims) — return DDL for session.sqlite with given dimension
  build_workflow_schema_sql() — return DDL for workflow.sqlite (metadata DB)
  build_eventbus_schema_sql() — return DDL for eventbus.sqlite (event bus message queue)
  apply_workflow_migrations(conn) — apply incremental schema migrations to an existing workflow DB
"""
```

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/db/schema_sql.py` | 0 errors |
| Type check | `uv run mypy scripts/db/schema_sql.py` | No new errors |
| Manual grep | `grep -rn "_build_rag_schema_sql\|_build_session_schema_sql" docs/ scripts/db/schema_sql.py` | No matches remain |
