---
title: "Memory Layer - Activation Gate, Data Model, and Search"
category: agent
tags:
  - agent
  - memory
  - activation-gate
  - data-model
  - search-strategies
  - disabled-behavior
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_memory-overview-and-modes.md
  - 05_agent_12_memory-module-ref-core-and-store.md
  - 05_agent_12_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_operations-and-observability-startup-and-health.md](05_agent_10_operations-and-observability-startup-and-health.md)
- Configuration → [05_agent_08_configuration-tools-memory.md](05_agent_08_configuration-tools-memory.md)

## Activation Gate

The memory layer has a 3-layer activation gate that controls when memory operations execute.

**Layer 1: Config bypass**
- `use_memory_layer` config flag (default: `False`)
- When `False`, memory services are not built; `ctx.services.memory` is `None`
- All callers guard with `if ctx.services.memory is None: return`
- Bypasses injection, ingestion, and retrieval entirely

**Layer 2: Embedding client enabled**
- Embedding client enabled flag gates HTTP and embedding calls
- When `False`: `fetch()` returns `EmbeddingResult(success=False, error_kind=DISABLED)` immediately
- `HybridRetriever.search()` falls back to FTS5-only when embedding is unavailable

**Layer 3: Service facade invocation**
- `MemoryServices` is the single entry point (`on_session_start`, `on_user_prompt`, `on_session_stop`)
- All memory operations route through this facade; direct sub-service access is for testing only

### Disabled Behavior by Module

| Module | Disabled condition | Behavior |
|---|---|---|
| `services.py` | `use_memory_layer=False` (Layer 1) | `ctx.services.memory` is `None`; callers skip |
| `injection.py` | Layer 1 bypassed | `MemoryInjectionService` never constructed; no snippets injected |
| `ingestion.py` | Layer 1 bypassed | `MemoryIngestionService` never constructed; no entries written |
| `embedding_client.py` | `enabled=False` (Layer 2) | `fetch()` returns `EmbeddingResult(error_kind=DISABLED)` without HTTP call |
| `retriever.py` | Layer 2 disabled | `HybridRetriever.search()` uses FTS5-only; `knn_search()` returns `[]` |
| `jsonl_store.py` | Layer 1 bypassed | `write()` never called; file unchanged |
| `store.py` | Layer 1 bypassed | `upsert()` never called; SQLite index unchanged |
| `extract.py` | Layer 1 bypassed | `extract_memories()` never called |
| `mapper.py` | N/A (pure utility) | Always available |
| `models.py` | N/A (pure data) | Always available |
| `types.py` | N/A (pure data) | Always available |
| `enums.py` | N/A (pure data) | Always available |
| `exceptions.py` | N/A (pure data) | Always available |

---

## Data Model

### MemoryEntry (stored in JSONL + SQLite)

| Field | Type | Description |
|---|---|---|
| `memory_id` | `str` | UUID v4, primary key |
| `memory_type` | `MemoryType` | `"semantic"` \| `"episodic"` |
| `source_type` | `SourceType` | `"RULE"` \| `"CONVERSATION"` \| `"DECISION"` \| `"FAILURE"` |
| `session_id` | `int \| None` | Parent session ID |
| `turn_id` | `str \| None` | UUID linking to the originating conversation turn |
| `project` | `str` | Project name for context filtering |
| `repo` | `str` | Repository name for context filtering |
| `branch` | `str` | Git branch for context filtering |

> **Current behavior:** When a non-empty branch is provided, retrieval applies a hard SQL
> filter that includes only:
> - memories with `branch = ''` (global memories — always included)
> - memories with `branch = <current branch>`
>
> Memories from other branches are excluded entirely (not merely ranked lower).
| `content` | `str` | Full message content |
| `summary` | `str` | Short summary of the content |
| `tags` | `list[str]` | Keyword tags for classification |
| `importance` | `float` | 0.0–1.0; higher = higher retrieval priority (default: 0.5) |
| `pinned` | `bool` | When `True`, injected at every session start |
| `created_at` | `str` | ISO 8601 UTC timestamp; filled by `write_ops.add()` |
| `updated_at` | `str` | ISO 8601 UTC timestamp |

**DB mapping:** Stored in `memories` table (SQLite) and one line per entry in the JSONL file. FTS5 index in `memories_fts`. Vector index in `memories_vec` (when embedding enabled).

### MemorySnippet (injected into LLM context)

| Field | Type | Description |
|---|---|---|
| `text` | `str` | Formatted string with memory type prefix (e.g. `"[Semantic memory] ..."`) |
| `source` | `str` | `"semantic"` \| `"episodic"` |
| `score` | `float` | Relevance score from search (RRF merge rank or FTS5 rank) |

---

## JSONL Format

Each line in the JSONL store is a single JSON object serializing all `MemoryEntry` fields:

```json
{"memory_id": "uuid-here", "memory_type": "semantic", "source_type": "RULE", "session_id": 1, "turn_id": null, "project": "myproj", "repo": "myrepo", "branch": "main", "content": "Use orjson for JSON.", "summary": "orjson preference", "tags": [], "importance": 0.7, "pinned": false, "created_at": "2026-06-19T23:00:00Z", "updated_at": "2026-06-19T23:00:00Z"}
```

**Properties:**
- Append-only: entries are never modified or deleted in the file
- One entry per line; UTF-8 encoded; valid JSON per line
- File path controlled by `memory_jsonl_dir` config (filename: `memories.jsonl`)
- Source of truth: SQLite index is rebuilt from JSONL if needed

---

## Search Strategies

### FTS5 (Full-Text Search)

- **Engine:** SQLite FTS5 with BM25 ranking
- **Index:** Tokenized `content` column in `memories_fts`
- **Fallback:** Used when `EmbeddingClient.enabled=False` or no embedding returned
- **Strengths:** Exact keyword matching, no API dependency, fast on small datasets
- **Weaknesses:** No semantic understanding

### KNN (Vector Search)

- **Engine:** sqlite-vec extension with cosine similarity
- **Index:** Dense embedding vectors in `memories_vec`
- **Requirement:** `EmbeddingClient.enabled=True` with a valid embedding API endpoint
- **Strengths:** Semantic similarity matching, language-agnostic
- **Weaknesses:** Requires embedding API call, sqlite-vec extension must be loaded

### Hybrid (RRF Merge)

- **Engine:** Combines FTS5 + KNN results using Reciprocal Rank Fusion (RRF)
- **Formula:** `rrf_score = 1.0 / (k + rank + 1)` where `k=60`, `rank` is 0-based
- **Result:** Deduplicated, sorted by descending RRF score
- **Strengths:** Best-of-both-worlds across query types
- **Weaknesses:** Higher latency (two searches + merge); requires embedding API

---

## Disabled Behavior

See the [Activation Gate](#activation-gate) section and [Disabled Behavior by Module](#disabled-behavior-by-module) table above for the full per-module breakdown.

Summary:
- `use_memory_layer=False` → `ctx.services.memory` is `None`; all memory operations are skipped
- `EmbeddingClient.enabled=False` → `fetch()` returns `DISABLED` error; retrieval falls back to FTS5-only
- `cli_view.py` reflects memory layer status at startup banner

---

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_memory-overview-and-modes.md`
- `05_agent_12_memory-module-ref-core-and-store.md`
- `05_agent_12_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_memory-module-ref-ops-and-scoring.md`

## Keywords

activation gate
disabled behavior by module
MemoryEntry
MemorySnippet
JSONL format
FTS5
KNN
hybrid RRF
disabled behavior
