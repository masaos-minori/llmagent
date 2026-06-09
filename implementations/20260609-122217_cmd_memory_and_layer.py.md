# Implementation: cmd_memory.py + layer.py — Migrate to MemoryServices, delete layer.py

## Goal

Migrate `cmd_memory.py` from using `MemoryLayer` facade methods to calling
`MemoryServices` sub-services directly, then delete `layer.py`.

## Scope

- `scripts/agent/commands/cmd_memory.py`: replace `MemoryLayer` type annotation and all facade method calls with direct service calls via `MemoryServices`.
- `scripts/agent/memory/layer.py`: delete the file.
- `scripts/agent/memory/retriever.py`: remove the `MemoryRetriever = HybridRetriever` alias.
- `tests/test_memory_layer.py`: rename/restructure to `test_memory_services.py` or update to use `MemoryIngestionService` directly.
- `deploy/deploy.sh`: remove `layer.py` from the copy list.

## Assumptions

1. Steps 1–7 are complete: `InjectionPolicy.dedup_window` removed, `append()` removed, `EmbeddingResult` in use, fallbacks removed, `LINK_ONLY` removed, `retriever.py` split, `MemoryServices` wired in `factory.py` and `context.py`.
2. `MemoryLayer`'s facade methods map to service methods as follows:
   - `list_entries(mem_type, limit)` → `mem.store.search_by_type(memory_type, limit)` (combined for both types)
   - `get_entry(id)` → `mem.store.get_by_id(id)`
   - `pin_entry(id)` → `mem.store.pin(id)`
   - `unpin_entry(id)` → `mem.store.unpin(id)`
   - `delete_entry(id)` → `mem.store.delete(id)`
   - `prune(days)` → `db.maintenance.prune_old_memories()` directly via `SQLiteHelper`
   - `count_prunable(days)` → `mem.store.count_prunable(days)` (new method on `MemoryStore`)
   - `search(query, limit)` → `mem.retriever.search(MemoryQuery(query, limit=limit))`
3. `MemoryStore` needs a `count_prunable(days: int) -> int` method (currently in `layer.py`).
4. The `prune()` logic (via `db.maintenance.prune_old_memories`) can be called directly from `cmd_memory.py` using `SQLiteHelper`.

## Implementation

### Target files

- `scripts/agent/commands/cmd_memory.py`
- `scripts/agent/memory/layer.py` (delete)
- `scripts/agent/memory/retriever.py` (remove alias)
- `scripts/agent/memory/store.py` (add `count_prunable`)
- `tests/test_memory_layer.py` (update imports and class references)
- `deploy/deploy.sh` (remove layer.py)

### Procedure

**store.py — add count_prunable:**
```python
def count_prunable(self, days: int) -> int:
    """Return count of entries older than `days` days."""
    try:
        with SQLiteHelper("session").open() as db:
            row = db.fetchall(
                "SELECT COUNT(*) FROM memories WHERE created_at < datetime('now', ?)",
                (f"-{days} days",),
            )
            return int(row[0][0]) if row else 0
    except Exception as e:
        logger.warning("MemoryStore.count_prunable failed: %s", e)
        return 0
```

**cmd_memory.py — update type annotation:**

Change:
```python
from agent.memory.layer import MemoryLayer
...
def _memory_list(self, mem: MemoryLayer, ...) -> None:
```

To:
```python
from agent.memory.services import MemoryServices
...
def _memory_list(self, mem: MemoryServices, ...) -> None:
```

**cmd_memory.py — _memory_list:**
```python
def _memory_list(self, mem: MemoryServices, args: list[str]) -> None:
    mem_type = next((a for a in args if a in ("semantic", "episodic")), "")
    limit_args = [a for a in args if a.isdigit()]
    limit = int(limit_args[0]) if limit_args else 10
    if mem_type:
        entries = mem.store.search_by_type(memory_type=mem_type, limit=limit)
    else:
        sem = mem.store.search_by_type("semantic", limit=limit)
        epi = mem.store.search_by_type("episodic", limit=limit)
        entries = sorted(sem + epi, key=lambda e: (not e.pinned, -e.importance))[:limit]
    ...
```

**cmd_memory.py — _memory_search:**
```python
from agent.memory.types import MemoryQuery
...
def _memory_search(self, mem: MemoryServices, args: list[str]) -> None:
    query = " ".join(args)
    hits = mem.retriever.search(MemoryQuery(query=query, limit=10))
    ...
```

**cmd_memory.py — _memory_show, _memory_pin, _memory_delete:**
```python
entry = mem.store.get_by_id(mid)
ok = mem.store.pin(mid)
ok = mem.store.unpin(mid)
ok = mem.store.delete(mid)
```

**cmd_memory.py — _memory_prune:**
```python
from db.helper import SQLiteHelper
from db.maintenance import prune_old_memories

def _memory_prune(self, mem: MemoryServices, ctx: AgentContext, args: list[str]) -> None:
    ...
    if dry_run:
        count = mem.store.count_prunable(days)
        ...
        return
    try:
        with SQLiteHelper("session").open(write_mode=True) as db:
            deleted = prune_old_memories(db, days)
        ...
    except Exception as e:
        logger.warning("prune failed: %s", e)
        deleted = 0
    ...
```

**layer.py — delete the file:**
```bash
git rm scripts/agent/memory/layer.py
```

**retriever.py — remove MemoryRetriever alias:**
Remove the line:
```python
MemoryRetriever = HybridRetriever
```

**deploy/deploy.sh — remove layer.py:**
Remove the line copying `layer.py`.

**tests/test_memory_layer.py:**
Update imports: replace `MemoryLayer` references with `MemoryIngestionService` and
`MemoryInjectionService` direct instantiation. The file can be renamed to
`test_memory_ingestion.py` and `test_memory_injection.py` or kept as one file
focusing on the service-level behavior.

### Method

Sequential edits. Start with `store.py` (add `count_prunable`), then `cmd_memory.py`,
then delete `layer.py` and remove alias.

### Details

`ctx.services.memory` in `cmd_memory.py` is now typed as `MemoryServices | None`.
The existing `if mem is None:` guard at the start of `_cmd_memory()` continues to work unchanged.

After deletion, run `grep -r "layer.py\|from agent.memory.layer\|MemoryLayer" scripts/` to
confirm no remaining references.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| layer.py deleted | `ls scripts/agent/memory/layer.py` | file not found |
| No MemoryLayer references | `grep -r "MemoryLayer\|from agent.memory.layer" scripts/` | 0 matches |
| No MemoryRetriever alias | `grep "MemoryRetriever = HybridRetriever" scripts/agent/memory/retriever.py` | 0 matches |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | 0 new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest -v` | all pass |
| deploy.sh updated | `grep "layer.py" deploy/deploy.sh` | 0 matches |
