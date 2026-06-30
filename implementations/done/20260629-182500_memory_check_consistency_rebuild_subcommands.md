# Implementation: Confirm memory check-consistency repair guidance and rebuild subcommands already implemented

## Goal

Confirm that the memory check-consistency repair guidance and rebuild-fts/rebuild-vec subcommands are already implemented correctly, as noted in the plan's post-implementation note.

## Scope

- **In-Scope**:
  - Verify `_memory_check_consistency` output no longer recommends `/memory rebuild` (JSONL import) for FTS/vec index repair
  - Verify `_memory_rebuild_fts` handler exists and works correctly
  - Verify `_memory_rebuild_vec` handler exists with embedding guard
  - Verify `store.py` has `rebuild_fts()` and `rebuild_vec()` methods
- **Out-of-Scope**:
  - DB schema changes (no new tables)
  - JSONL archive format changes
  - Embedding pipeline changes (vec rebuild reads stored embeddings from `memories` table, not re-embed)
  - Other `/memory` subcommands

## Assumptions

- `MemoryStore.rebuild_fts()` can reconstruct `memories_fts` in full from `memories` table using DELETE + INSERT.
- `MemoryStore.rebuild_vec()` can reconstruct `memories_vec` from `memories.embedding` column (already-stored BLOBs), not by re-calling the embedding API.
- "JSONL archive" is an informational backup; it is not authoritative for SQLite state.
- `memory_embed_enabled` flag controls whether vec consistency is checked and whether `rebuild-vec` is allowed.

## Unknowns & Gaps

| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? |
|---|---|---|---|---|
| UNK-01 | `memories` table stores an `embedding` column that `rebuild_vec` can read directly | Schema not inspected at plan time | Confirmed in store.py L297-298: `SELECT memory_id, embedding FROM memories WHERE embedding IS NOT NULL` | No |
| UNK-02 | Whether `_memory_rebuild_vec` should call embedding API for entries lacking a stored embedding | Requirement says "requires embedding regeneration" but does not specify if it should auto-trigger | Plan treats rebuild-vec as index-only repair; entries without stored embeddings are skipped (per store.py L297) | No |

## Verification Results

### 1. check-consistency output — no longer recommends JSONL import for index repair

**File**: `scripts/agent/commands/cmd_memory.py:374-378`
```python
if fts_gap > 0:
    self._out.write("    Repair: /memory rebuild-fts")
if embed_enabled and vec_gap > 0:
    self._out.write(
        "    Repair: /memory rebuild-vec (requires embedding regeneration)"
    )
```
- No mention of `/memory rebuild` (JSONL import) for FTS/vec repair ✓

### 2. JSONL archive row labeled as info only

**File**: `scripts/agent/commands/cmd_memory.py:350`
```python
["JSONL archive records (info only)", str(jsonl_count)]
```
- JSONL count is labeled as "(info only)" ✓

### 3. `_memory_rebuild_fts` handler exists

**File**: `scripts/agent/commands/cmd_memory.py:415-420`
```python
def _memory_rebuild_fts(self, mem: MemoryServices) -> None:
    count = mem.store.rebuild_fts()
```
- Handler calls `mem.store.rebuild_fts()` ✓

### 4. `_memory_rebuild_vec` handler exists with embedding guard

**File**: `scripts/agent/commands/cmd_memory.py:423-432`
```python
def _memory_rebuild_vec(self, mem: MemoryServices) -> None:
    if not self._ctx.cfg.memory.memory_embed_enabled:
        self._out.write("Embedding is disabled; cannot rebuild vec index")
        return
    count = mem.store.rebuild_vec()
```
- Guard on `memory_embed_enabled` ✓

### 5. `store.py` has `rebuild_fts()` and `rebuild_vec()` methods

**File**: `scripts/agent/memory/store.py:278,293`
```python
def rebuild_fts(self) -> int:
    # DELETE all from memories_fts, INSERT all rows from memories

def rebuild_vec(self) -> int:
    # DELETE all from memories_vec, INSERT rows where embedding IS NOT NULL
```
- Both methods exist ✓

### 6. Dispatch entries registered

**File**: `scripts/agent/commands/cmd_memory.py:99-100`
```python
"rebuild-fts": lambda: self._memory_rebuild_fts(mem),
"rebuild-vec": lambda: self._memory_rebuild_vec(mem),
```
- Both handlers registered in dispatch dict ✓

### 7. `_MEMORY_HELP` updated with new subcommands

**File**: `scripts/agent/commands/cmd_memory.py:57-58`
```
 /memory rebuild-fts                       Rebuild memories_fts index from SQLite
 /memory rebuild-vec                       Rebuild memories_vec index from SQLite
```
- Help text includes both new subcommands ✓

## Summary

All acceptance criteria from the plan are already satisfied by existing code. The plan's post-implementation note is accurate — this requirement was implemented in commit f4103cc2 on 2026-06-28 and all verification points confirm correctness:

| Criterion | Status | Evidence |
|---|---|---|
| check-consistency no longer recommends JSONL import for index repair | Already implemented | `cmd_memory.py:374-378` — only `/memory rebuild-fts` and `/memory rebuild-vec` |
| JSONL archive row labeled as info only | Already implemented | `cmd_memory.py:350` — "JSONL archive records (info only)" |
| `_memory_rebuild_fts` handler exists | Already implemented | `cmd_memory.py:415-420` + `store.py:278` |
| `_memory_rebuild_vec` handler with embedding guard | Already implemented | `cmd_memory.py:423-432` + `store.py:293` |
| Dispatch entries registered | Already implemented | `cmd_memory.py:99-100` |
| `_MEMORY_HELP` updated | Already implemented | `cmd_memory.py:57-58` |

## Risks & Mitigations

- **Risk**: `rebuild_fts()` locks the DB for full table copy, blocking concurrent reads → **Mitigation**: Use `begin_immediate` transaction; FTS rebuild is fast for typical memory counts (<1000 rows)
- **Risk**: `rebuild_vec()` silently skips entries without stored embeddings, leaving vec count < memories count → **Mitigation**: Document in help text that vec rebuild only restores already-embedded entries; re-embedding is a separate operation
- **Risk**: Existing tests for `_memory_check_consistency` may assert on old "rebuild" wording → **Mitigation**: Review `test_memory_consistency.py` before changing output strings; update assertions if needed
