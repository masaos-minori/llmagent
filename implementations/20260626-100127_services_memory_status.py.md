# Implementation: Add get_stats() to services.py and extend /memory status

Steps covered: Plan 20260626-100127 — Steps 1-3

---

## Goal

Add `get_stats() -> dict` to `MemoryServices` in `scripts/agent/memory/services.py`, collecting entry counts by type/source_type, embed_skip count, and last retrieval mode. Display in `/memory status`.

---

## Scope

- **In scope**:
  - `scripts/agent/memory/services.py`: `get_stats()` method
  - `/memory status` handler: extended quality signals display
  - `docs/05_agent_10_operations-and-observability.md`
- **Out of scope**: metrics platform integration

---

## Assumptions

- `HybridRetriever.last_retrieval_mode` and `fts_fallback_count` exist (retriever.py lines 261-262).
- `MemoryIngestionService.stat_embed_skip` exists (ingestion.py line 56).
- SQLite `memories` table can be queried for counts by `memory_type` and `source_type`.

---

## Implementation

### Target file
`scripts/agent/memory/services.py`

### Procedure
1. Read `scripts/agent/memory/services.py` to find the class and existing methods.
2. Step 1: Add `get_stats()`:
   ```python
   def get_stats(self) -> dict:
       counts = self._store.count_by_type()  # {"semantic": N, "episodic": M, ...}
       source_counts = self._store.count_by_source_type()  # {"RULE": .., "DECISION": .., ...}
       return {
           "total": sum(counts.values()),
           "semantic": counts.get("semantic", 0),
           "episodic": counts.get("episodic", 0),
           "by_source": source_counts,
           "embed_skip": self.ingestion.stat_embed_skip,
           "last_retrieval_mode": self.retriever.last_retrieval_mode,
           "fts_fallback_count": self.retriever.fts_fallback_count,
       }
   ```
3. Step 2: In `/memory status` handler, display:
   ```
   Memory Status:
     mode: hybrid
     entries: 142 (semantic=89, episodic=53)
     source types: RULE=34, DECISION=22, FAILURE=15, CONVERSATION=71
     embed_skip: 8
     last_retrieval: hybrid (fts_fallback=2)
   ```
4. Step 3: Update docs with field descriptions.

### Method
New method addition. Uses existing `stat_*` fields.

---

## Validation plan

- Run: `uv run pytest tests/agent/memory/ -x` — pass.
- Type: `mypy scripts/agent/memory/services.py` — 0 errors.
- Pre-commit: `pre-commit run --all-files` — pass.
