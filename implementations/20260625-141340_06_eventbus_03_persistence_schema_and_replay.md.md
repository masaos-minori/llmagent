# Implementation: Remove single-thread assumption from persistence doc

Source plan: `plans/20260625-140631_plan.md` (req #21, persistence doc portion)

## Goal

Replace the "FastAPI runs on a single async event loop thread" explanation in `docs/06_eventbus_03_persistence_schema_and_replay.md` with an accurate description of the shared + Lock connection model.

## Scope

- Replace lines 7-8 of the document (the `**Why check_same_thread=False is safe**` block)
- No other changes to schema, field semantics, index, or JSONL archive sections
- Prerequisite: req #16 implemented

## Assumptions

1. The target paragraph starts with `**Why \`check_same_thread=False\` is safe**` on line 7
2. The replacement text references `asyncio.to_thread()` and `threading.Lock`

## Implementation

### Target file

`docs/06_eventbus_03_persistence_schema_and_replay.md`

### Procedure

1. Locate the `**Why \`check_same_thread=False\` is safe**` paragraph (lines 7-8)
2. Replace with new explanation

### Method

Targeted string replacement — only the two-sentence paragraph changes.

### Details

**Remove:**
```markdown
**Why `check_same_thread=False` is safe**: FastAPI runs on a single async event loop thread. All DB operations execute on that thread. WAL mode serializes concurrent writers at the SQLite level.
```

**Replace with:**
```markdown
**Why `check_same_thread=False` is safe**: All DB operations are executed via `asyncio.to_thread()` and protected by a module-level `threading.Lock` (`get_db_lock()` in `db.py`). The lock serializes concurrent DB access across thread-pool workers. WAL mode additionally serializes concurrent writers at the SQLite level.
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Old phrase gone | `grep "single async event loop thread" docs/06_eventbus_03_persistence_schema_and_replay.md` | 0 matches |
| New phrase present | `grep "asyncio.to_thread" docs/06_eventbus_03_persistence_schema_and_replay.md` | 1 match |
| Markdown lint | `markdownlint docs/06_eventbus_03_persistence_schema_and_replay.md` | 0 errors (if installed) |
