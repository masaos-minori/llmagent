# Implementation: DbTarget enum - Add EVENTBUS member

## Goal

Add `EVENTBUS = "eventbus"` to the DbTarget StrEnum in helper.py.

## Scope

- DbTarget enum class definition only (one line addition)

## Assumptions

1. No other changes to DbTarget needed beyond adding one enum member
2. Existing DbTarget consumers will handle the new member gracefully

## Implementation

### Target file

- `scripts/db/helper.py`

### Procedure

1. Add `EVENTBUS = "eventbus"` after WORKFLOW in DbTarget enum

### Method

- Follow existing enum member pattern exactly

### Details

```python
class DbTarget(StrEnum):
    """SQLite database target type."""

    RAG = "rag"
    SESSION = "session"
    WORKFLOW = "workflow"
    EVENTBUS = "eventbus"  # NEW - one line addition
```

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Type check | `uv run mypy scripts/db/helper.py` | No type errors |
| Lint | `uv run ruff check scripts/db/helper.py` | No lint errors |
| Enum test | `python -c "from db.helper import DbTarget; print(DbTarget.EVENTBUS.value)"` | Output: `eventbus` |
