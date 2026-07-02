# Implementation: Clarify migration helper responsibilities in create_schema.py

## Goal

Fix `db/create_schema.py` module docstring to match actual behavior, and clarify `_migrate_*` helper responsibilities with comments.

## Scope

- scripts/db/create_schema.py: Fix module docstring
  - Remove "Creates the latest schema only. No migration logic."
  - Clarify it handles both schema creation and compatibility fixes
- Add documentation to each `_migrate_*` function
  - `_migrate_rag_schema()`
  - `_migrate_session_schema()`
  - `_migrate_add_undone_column()`
  - `_migrate_workflow_schema()`
- Fix "DDL-only" misdescription in Shared/DB documents if any

## Assumptions

1. create_schema.py implementation changes are minimal (docstring/comments only). Minor refactoring (comment additions) is acceptable.
2. If "DDL-only" description exists in docs/90_shared_04_db_architecture_and_schema.md, fix it.

## Implementation

### Target files

- scripts/db/create_schema.py: Fix module docstring, add comments to _migrate_* functions
- docs/90_shared_04_db_architecture_and_schema.md: Fix if "DDL-only" misdescription exists

### Procedure

#### Phase 1: Check for misdescriptions in documents

Run `rg -n "DDL.only\|No migration\|DDL only" docs/` to identify locations.

#### Phase 2: Fix module docstring

Replace "Creates the latest schema only. No migration logic." with:
"現行スキーマを作成し、限定的な互換性修復（_migrate_*）を適用する。破壊的マイグレーションは行わない。"

#### Phase 3: Add _migrate_* function comments

- `_migrate_rag_schema()`: Confirm/strengthen comment about idempotent addition of chunk_type/source_file columns
- `_migrate_session_schema()`: Confirm/strengthen comment about FK constraint addition to tool_results.session_id
- `_migrate_add_undone_column()`: Confirm/strengthen comment about idempotent addition of tool_results.undone column
- `_migrate_workflow_schema()`: Confirm/strengthen comment about idempotent addition of tasks.workflow_id column

#### Phase 4: Document fix

- Fix misdescription in docs/90_shared_04_db_architecture_and_schema.md if any

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Format | `ruff format --check scripts/` | No diff |
| Lint | `ruff check scripts/` | 0 errors |
| Type check | `mypy scripts/` | No new type errors |
| Tests | `uv run pytest tests/test_create_schema.py -v` | all pass |
| docs-consistency | `uv run python -m scripts.checks.check_docs_consistency` | All checks passed |
