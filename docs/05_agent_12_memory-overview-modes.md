---
title: "Memory Layer — Module Reference"
category: agent
tags:
  - agent
  - agent
  - memory
  - semantic
  - episodic
  - embedding
related:
  - 05_agent_00_document-guide.md
---

# Memory Layer — Module Reference

mory_local_only = true` if data must not leave the machine
- [ ] `embed_url` points to local embedding service (e.g., `http://localhost:11434`)
- [ ] `/memory status` shows one of: `Hybrid mode`, `FTS-only`, `Degraded mode`, or `disabled`
- [ ] `/memory rebuild` tested after restoring JSONL backup

---

## Purpose

API reference for all 

modules under `scripts/agent/memory/`. A developer should
understand each module's responsibility, public API surface, and disabled behavior
without reading source code.

---

## Overview

| Module | Responsibi

lity |
|---|---|
| `__init__.py` | Public API barrel — re-exports all public symbols |
| `types.py` | Core runtime types (MemoryEntry, MemoryQuery, MemoryHit, EmbeddingResult) |
| `enums.py` | Domain enums (MemoryType, DedupAction, RetrievalMode, ExtractionDecision) |
| `exceptions.py` | Exception hierarchy |
| `models.py` | Frozen DTOs (HistoryMessage, JsonlRecord, MemorySnippet, ConsistencyReport) |
| `store.py` | CRUD for memories / memories_fts / memories_vec tables |
| `retriever.py` | FTS5 / KNN / Hybrid search (FtsRetriever, VectorRetriever, HybridRetriever) |
| `injection.py` | MemoryInjectionService — lifecycle hooks for snippet injection |
| `ingestion.py` | MemoryIngestionService — extract, dedup, persist |
| `extract.py` | Rule-based extraction from conversation history |
| `jsonl_store.py` | Append-only JSONL archive |
| `embedding_client.py` | HTTP embedding client with retry and circuit breaker |
| `services.py` | MemoryServices facade over injection, ingestion, store, retriever |
| `mapper.py` | SQLite row conversion, embedding blob serialisation |

---

## Memory Modes

The memory layer 

operates in four distinct modes, visible via `/memory status`:

| Mode | Description | Retrieval Behavior |
|---|---|---|
| `Hybrid mode (semantic + FTS)` | Full operation — embedding endpoint available and healthy | Hybrid search using RRF merge of vector similarity and FTS results |
| `Memory enabled, embedding disabled (FTS-only)` | Embedding endpoint unavailable but circuit closed | FTS-only search; no vector similarity component |
| `Degraded mode (circuit open, FTS fallback)` | Embedding circuit breaker triggered by repeated failures | FTS-only search; same as above but indicates active health issues with the embedding service |
| `Memory layer disabled` | Memory subsystem disabled entirely (`use_memory_layer = false`) | No memory retrieval at all |

**When each mode applies:**

- **Hybrid mode**: Default when memory is enabled and the embedding endpoint is reachable and returning valid embeddings.
- **FTS-only**: When the embedding endpoint fails (network error, timeout, invalid response), the system falls back to FTS-only. This happens automatically without manual intervention.
- **Degraded mode**: When the embedding circuit breaker opens due to persistent failures. The circuit breaker threshold is configurable in `embedding_client.py`. Degraded mode uses the same FTS fallback but signals that the embedding service has ongoing issues.
- **Disabled**: When `use_memory_layer = false` in `config/agent.toml`. No memory retrieval occurs regardless of embedding availability.

**Transition between modes:**

- Hybrid → FTS-only: Automatic on embedding failure
- FTS-only → Hybrid: Automatic when embedding recovers
- Degraded → Hybrid: Automatic when circuit breaker closes after recovery period
- Any → Disabled: Requires config change and agent restart

```
session_start
    |
    v
+-----------------+
| services.py     |  MemoryServices.on_session_start()
|                 |---> injection.on_session_start()
+--------+--------+
         |
         v
+-----------------+     +------------------+
| injection.py    |---->| retriever.py     |
| MemoryInject    |     | HybridRetriever  |
| Service         |     | top_semantic()   |
+--------+--------+     +------------------+
         |
         v
+-----------------+
| models.py       |  MemorySnippet[] -> injected into LLM context
| MemorySnippet   |
+-----------------+

user_prompt (during session)
    |
    v
+-----------------+     +-----------------+     +---------------------+
| services.py     |---->| injection.py    |---->| embedding_client.py |
| on_user_prompt  |     | on_user_prompt  |     | EmbeddingClient     |
+-----------------+     +--------+--------+     +---------------------+
                                 |
                                 v
                         +------------------+
                         | retriever.py     |
                         | HybridRetriever  |
                         | search() (RRF)   |
                         +--------+---------+
                                  |
                                  v
                         +-----------------+
                         | models.py       |
                         | MemorySnippet[] |
                         +-----------------+

session_stop
    |
    v
+-----------------+
| services.py     |  MemoryServices.on_session_stop()
|                 |---> ingestion.on_session_stop()
+--------+--------+
         |
         v
+-----------------+     +------------------+     +-----------------------------+
| ingestion.py    |---->| extract.py       |---->| For each MemoryEntry:       |
| MemoryIngestion |     | extract_memories |     | 1. EmbeddingClient.fetch()  |
| Service         |     +------------------+     | 2. Dedup check (KNN)        |
+--------+--------+                              | 3. JsonlMemoryStore.write() |
         |                                       | 4. write_ops.upsert()       |
         v                                       +-----------------------------+
+-----------------+
| jsonl_store.py  |  Append-only archive
| JsonlMemoryStore|
+--------+--------+
         |
         v
+-----------------+     +------------------+
| store.py        |---->| retriever.py     |
| MemoryStore     |     | .fts_search()    |
| (SQLite index)  |     | .knn_search()    |
+-----------------+     +------------------+
```

---

## Activation Gate

The memory lay

er has a 3-layer activation gate that controls when memory operations execute.

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

### MemoryEntry (st

## Related Documents

- `agent`
- `memory`
- `semantic`

## Keywords

agent
memory
semantic
episodic
embedding
