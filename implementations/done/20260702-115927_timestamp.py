# Implementation: Unify SQLite timestamp defaults to ISO-8601 UTC Z suffix

## Goal

Unify `db/schema_sql.py` internal `datetime('now')` DEFAULT to `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')`, and apply same policy to Event Bus DDL.

## Scope

- scripts/db/schema_sql.py: Fix `_RAG_SCHEMA_TEMPLATE` documents.fetched_at DEFAULT
- scripts/db/schema_sql.py: Fix `_SESSION_SCHEMA_TEMPLATE`:
  - sessions.created_at
  - messages.created_at
  - memories.created_at
  - memories.updated_at
- Verify build_eventbus_schema_sql() published_at DEFAULT uses ISO-8601 UTC Z suffix (confirmed in plan 52)
- docs/90_shared_04_db_architecture_and_schema.md: Remove "keep existing format differences" description
- Add test asserting DEFAULT expression matches expectation

## Assumptions

1. tool_results.created_at and session_diagnostics.created_at already use strftime('%Y-%m-%dT%H:%M:%SZ', 'now') — no change needed
2. DDL DEFAULT change doesn't apply to existing tables (IF NOT EXISTS)
3. Test environment creates new SQLite memory DB to apply schema and verify DEFAULT values

## Implementation

### Target files

- scripts/db/schema_sql.py: Change datetime('now') → strftime('%Y-%m-%dT%H:%M:%SZ', 'now') (5 locations)
- tests/test_create_schema.py: Add DEFAULT expression assertion test
- docs/90_shared_04_db_architecture_and_schema.md: Fix format difference description

### Procedure

#### Phase 1: schema_sql.py fix

- Fix `_RAG_SCHEMA_TEMPLATE` documents.fetched_at DEFAULT
- Fix `_SESSION_SCHEMA_TEMPLATE` sessions.created_at, messages.created_at, memories.created_at, memories.updated_at DEFAULT
- Verify no remaining `datetime('now')` with `rg -n "datetime\('now'\)" scripts/db/schema_sql.py`

#### Phase 2: Add test

- Add `TestTimestampDefaults` class to `tests/test_create_schema.py`
- Verify each table column DEFAULT is `strftime('%Y-%m-%dT%H:%M:%SZ', 'now')` using PRAGMA table_info()

#### Phase 3: Documentation fix

- Fix "keep existing format differences" description in docs/90_shared_04_db_architecture_and_schema.md, specify unified policy

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No remaining datetime('now') | `rg -n "datetime\('now'\)" db docs tests` | 0 matches (active DDL) |
| Format | `ruff format --check scripts/ tests/` | No diff |
| Lint | `ruff check scripts/ tests/` | 0 errors |
| Tests | `uv run pytest tests/test_create_schema.py -v` | all pass |
| docs-consistency | `uv run python -m scripts.checks.check_docs_consistency` | All checks passed |
