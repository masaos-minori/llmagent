# Implementation: Update Shared/DB source-of-truth wording after schema integration

## Goal

After schema integration, clearly define "source of truth" in Shared/DB documents for DDL source, initialization entry point, and DB file list, and unify descriptions.

## Scope

- docs/90_shared_01_overview.md: Add source-of-truth model, fix after workflow_schema.py deletion
- docs/90_shared_04_db_architecture_and_schema.md: Add/update source-of-truth table
- docs/90_shared_05_db_api_and_operations.md: Unify initialization entry point description

## Assumptions

1. Assume plan 54 (workflow_schema.py deletion) is complete (or note "valid after completion")
2. Source-of-truth model definition:
   - DDL source: db/schema_sql.py
   - Schema initialization entry point: db/create_schema.py (create_schema())
   - Deploy initialization entry point: deploy/init_db.sh
   - DB connection helper: db/helper.py::SQLiteHelper
   - DB files: rag.sqlite, session.sqlite, workflow.sqlite, eventbus.sqlite
   - Deprecated entry point: db/workflow_schema.py (deleted)

## Implementation

### Target files

- docs/90_shared_01_overview.md: Remove workflow_schema.py rows, add eventbus.sqlite, add source-of-truth section
- docs/90_shared_04_db_architecture_and_schema.md: Add/update source-of-truth table
- docs/90_shared_05_db_api_and_operations.md: Unify initialization entry point to create_schema.py

### Procedure

#### Phase 1: Fix 90_shared_01

- Remove workflow_schema.py from db/ module list (line 22)
- Remove workflow_schema.py row from module function table (line 96)
- Add eventbus.sqlite to DB file description
- Add "DB Schema Source of Truth" note (DDL is schema_sql.py, initialization is create_schema.py)

#### Phase 2: Fix 90_shared_04

- Add source-of-truth table or note block
- Explicitly mark deprecated workflow_schema.py as "deleted"

#### Phase 3: Fix 90_shared_05

- Check initialization entry point description, fix workflow_schema.py reference to create_schema.py if any
- Explicitly document deploy/init_db.sh as deploy initialization entry point

#### Phase 4: Consistency verification

- Run `grep -n "workflow_schema" docs/90_shared_*.md` to confirm no remaining references
- Run `grep -n "eventbus.sqlite\|schema_sql\|create_schema" docs/90_shared_*.md` to verify consistent descriptions

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No workflow_schema.py remaining | `grep -n "workflow_schema" docs/90_shared_*.md` | 0 matches |
| eventbus.sqlite documented | `grep -n "eventbus" docs/90_shared_*.md` | Consistent descriptions in multiple locations |
| docs-consistency | `uv run python -m scripts.checks.check_docs_consistency` | All checks passed |
