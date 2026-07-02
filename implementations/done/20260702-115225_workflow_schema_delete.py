# Implementation: Delete db/workflow_schema.py and use create_schema.py as workflow schema entrypoint

## Goal

Delete `db/workflow_schema.py` and make `db/create_schema.py` the sole initialization entrypoint for workflow schema.

## Scope

- scripts/db/workflow_schema.py: DELETE
- tests/test_workflow_schema.py: DELETE
- tests/test_cmd_workflow.py: import change
- tests/test_workflow_state_store.py: import change
- tests/test_workflow_engine.py: import change
- tests/test_create_schema.py: remove workflow_schema equivalence test (lines 357-416)
- docs/90_shared_01_overview.md: remove workflow_schema.py line
- docs/90_shared_04_db_architecture_and_schema.md: update workflow_schema.py → create_schema.py references

## Assumptions

1. test_workflow_schema.py is mostly duplicate of test_create_schema.py — safe to delete
2. _migrate_workflow_schema is already exposed via create_schema.py
3. create_workflow_schema() has no arguments (unlike init_schema(path))

## Implementation

### Target files

- scripts/db/workflow_schema.py → DELETE
- tests/test_workflow_schema.py → DELETE
- tests/test_cmd_workflow.py → import change
- tests/test_workflow_state_store.py → import change
- tests/test_workflow_engine.py → import change
- tests/test_create_schema.py → remove equivalence test
- docs/90_shared_01_overview.md → remove reference
- docs/90_shared_04_db_architecture_and_schema.md → update references

### Procedure

#### Phase 1: Test import changes

Change in all 3 test files:
```python
# Before:
from db.workflow_schema import init_schema

# After:
from db.create_schema import create_workflow_schema
```

And change `init_schema()` calls to `create_workflow_schema()`.

#### Phase 2: Remove workflow_schema references in test_create_schema.py

Delete lines 357-416 (workflow_schema.init_schema() equivalence tests).

#### Phase 3: Delete workflow_schema.py

```bash
rm scripts/db/workflow_schema.py
```

#### Phase 4: Delete test_workflow_schema.py

```bash
rm tests/test_workflow_schema.py
```

#### Phase 5: Documentation updates

In docs/90_shared_01_overview.md: Remove the workflow_schema.py line.

In docs/90_shared_04_db_architecture_and_schema.md: Change `workflow_schema.py` references to `create_schema.py`. Update code samples from `init_schema("/opt/llm/db/workflow.sqlite")` to `python -m db.create_schema`.

### Method

- Follow existing pattern exactly (same style as other schema functions)
- Use git rm for file deletion to track removals

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Lint | `uv run ruff check scripts/ tests/` | 0 errors |
| Type check | `uv run mypy scripts/` | No new type errors |
| Architecture | `lint-imports` | 0 violations |
| Tests | `uv run pytest tests/ -v -k "workflow"` | all pass |
| Verify no remaining references | `rg -n "workflow_schema\|db\.workflow_schema" . --include="*.py" --include="*.sh" --include="*.md"` | No matches (except in this plan file) |
