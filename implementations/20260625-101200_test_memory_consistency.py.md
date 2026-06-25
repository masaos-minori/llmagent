# tests/test_memory_consistency.py — rename rebuild_from_jsonl references

**Plan:** `plans/20260625-093754_plan.md` (req #62)
**Target:** `tests/test_memory_consistency.py`

## What to change

Replace all occurrences of `rebuild_from_jsonl` with `import_from_jsonl`.

Locations (from grep):
- Line 4: module docstring `MemoryStore.rebuild_from_jsonl()` → `MemoryStore.import_from_jsonl()`
- Line 79: section comment `# ── MemoryStore.rebuild_from_jsonl()` → `# ── MemoryStore.import_from_jsonl()`
- Lines 177, 192, 210, 224, 237: call sites `mem_store.rebuild_from_jsonl(...)` → `mem_store.import_from_jsonl(...)`
- Line 332: mock return `mem.store.rebuild_from_jsonl.return_value` → `mem.store.import_from_jsonl.return_value`
- Line 337: mock assert `mem.store.rebuild_from_jsonl.assert_called_once_with` → `mem.store.import_from_jsonl.assert_called_once_with`
- Line 348: mock return `mem.store.rebuild_from_jsonl.return_value` → `mem.store.import_from_jsonl.return_value`

Use `replace_all` edit (or global find-replace) for `rebuild_from_jsonl` → `import_from_jsonl`.

Also update the consistency-check assertions: any tests that assert `jsonl_count == report.memories`
(or equivalent) must be updated to match the new predicate (`memories == fts` only).
Check the test assertions at lines that test `_memory_check_consistency()` behavior.

## Validation

```
uv run pytest tests/test_memory_consistency.py -v
```
