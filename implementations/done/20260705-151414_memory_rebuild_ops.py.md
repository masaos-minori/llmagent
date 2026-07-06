# Implementation: agent/commands/memory_rebuild_ops.py — Default dry-run for rebuild, require --confirm

## Goal

Change `/memory rebuild` default behavior to dry-run. Require explicit `--confirm` flag for actual rebuild. Show pre-rebuild summary with JSONL count, current SQLite count, and state-loss warning before proceeding.

## Scope

**In**: Behavior change in `rebuild()` command handler. Add pre-rebuild summary output. Auto-run consistency check after actual rebuild. Return `RebuildResult` for testability.

**Out**: Changes to core `memory/rebuild_ops.py`, schema, other commands.

## Assumptions

1. `memory_rebuild_ops.py` is in `scripts/agent/commands/` (command layer).
2. Current check: `"--dry-run" in args`; default is IMMEDIATE rebuild.
3. New check: `"--confirm" not in args` means dry-run; default is DRY-RUN.
4. `import_from_jsonl()` returns `(jsonl_count, inserted)` — verify before implementing.
5. `mem.store.check_consistency()` returns a `ConsistencyReport` with `.memories` (count) field.
6. `self._out.write()` / `self._out.write_success()` are the output methods.

## Implementation

### Target file
`scripts/agent/commands/memory_rebuild_ops.py`

### Procedure
1. Read `import_ops.py` to confirm `import_from_jsonl()` return signature.
2. Read `memory/store.py` to confirm `check_consistency()` return type.
3. Change `dry_run` logic: `dry_run = "--confirm" not in args`.
4. Add pre-rebuild summary block (always shown, before any changes).
5. Add post-rebuild `check_consistency()` call.
6. Add `RebuildResult` dataclass.

### Method

**New `RebuildResult` dataclass (add near top of file):**
```python
from dataclasses import dataclass

@dataclass
class RebuildResult:
    dry_run: bool
    jsonl_count: int
    sqlite_before: int
    inserted: int | None = None
    sqlite_after: int | None = None
```

**Updated `rebuild()` method:**
```python
def rebuild(self, mem: MemoryServices, args: list[str]) -> RebuildResult:
    dry_run = "--confirm" not in args  # DEFAULT is now dry-run

    # Pre-rebuild summary (always shown, before any mutation)
    jsonl_store = mem.ingestion._jsonl
    jsonl_count = jsonl_store.count_all()
    consistency = mem.store.check_consistency()
    sqlite_before = consistency.memories

    self._out.write(f"  JSONL archive records:   {jsonl_count}")
    self._out.write(f"  Current SQLite memories: {sqlite_before}")
    self._out.write(f"  Expected after rebuild:  {jsonl_count}")
    self._out.write("  WARNING: delete/pin/unpin operations are NOT replayed.")
    self._out.write("           Deleted entries may be re-inserted from JSONL.")

    if dry_run:
        self._out.write("  [dry-run] No changes made. Add --confirm to proceed.")
        return RebuildResult(dry_run=True, jsonl_count=jsonl_count, sqlite_before=sqlite_before)

    # Actual rebuild
    _, inserted = import_from_jsonl(jsonl_store, dry_run=False)
    self._out.write_success(f"Imported {inserted} entries from {jsonl_count} records.")

    # Auto-run consistency check after rebuild
    self.check_consistency(mem)

    after_consistency = mem.store.check_consistency()
    return RebuildResult(
        dry_run=False,
        jsonl_count=jsonl_count,
        sqlite_before=sqlite_before,
        inserted=inserted,
        sqlite_after=after_consistency.memories,
    )
```

### Details

- Existing tests that call `rebuild(mem, [])` expecting actual rebuild must be updated to `rebuild(mem, ["--confirm"])`.
- `rebuild(mem, ["--dry-run"])` still works (new logic: `"--confirm" not in args` — `--dry-run` presence doesn't matter, but it's now the default).
- The `--dry-run` flag can be removed from arg parsing since it's now redundant (default is dry-run). Keep it as a no-op alias if backward compat is needed.

## Validation plan

- `uv run pytest tests/ -v -k "memory_rebuild or rebuild"` — all pass (after updating existing test fixtures to use `["--confirm"]`).
- Verify: `rebuild(mem, [])` → `result.dry_run is True`, no SQLite changes.
- Verify: `rebuild(mem, ["--confirm"])` → `result.dry_run is False`, `result.inserted > 0`.
- Verify: summary output includes JSONL count, SQLite count, warning text.
- `mypy scripts/agent/commands/memory_rebuild_ops.py` — no new errors.
- `ruff check scripts/agent/commands/memory_rebuild_ops.py` — 0 errors.
