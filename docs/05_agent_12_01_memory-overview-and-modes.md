---
title: "Memory Layer - Overview and Modes"
category: agent
tags:
  - agent
  - memory
  - overview
  - memory-modes
  - production-checklist
related:
  - 05_agent_00_document-guide.md
  - 05_agent_12_02_memory-gate-data-model-search.md
  - 05_agent_12_03_memory-module-ref-core-and-store.md
  - 05_agent_12_04_memory-module-ref-retrieval-and-injection.md
  - 05_agent_12_05_memory-module-ref-extraction-and-facade.md
  - 05_agent_12_06_memory-module-ref-ops-and-scoring.md
source:
  - 05_agent_12_memory.md
---

# Memory Layer — Module Reference

- Operations and observability → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)
- Configuration → [05_agent_08_03_configuration-tools-memory.md](05_agent_08_03_configuration-tools-memory.md)

## Persistent Semantic Memory — Overview

Persistent Semantic Memory stores abstract rules, design decisions, failure patterns,
and conversational Q&A across agent sessions.

**Memory types**:
- Semantic: long-lived rules and decisions (importance ≥ 0.5 for session startup injection)
- Episodic: session-specific failures and Q&A (injected on first user prompt)

**Source types**: RULE / DECISION / FAILURE / CONVERSATION

**Local-only guarantee**: set `memory_local_only = true` to enforce that the embedding
endpoint is a loopback address. Fails startup if `embed_url` is non-local.

**Automatic context restoration**:
- Session start: pinned + high-importance semantic injected
- First user prompt: task-specific hybrid retrieval (semantic + episodic)

## Production Checklist

- [ ] `memory_local_only = true` if data must not leave the machine
- [ ] `embed_url` points to local embedding service (e.g., `http://localhost:11434`)
- [ ] `/memory status` shows one of: `Hybrid mode`, `FTS-only`, `Degraded mode`, or `disabled`
- [ ] `/memory rebuild` tested after restoring JSONL backup

---

## Purpose

API reference for all modules under `scripts/agent/memory/`. A developer should
understand each module's responsibility, public API surface, and disabled behavior
without reading source code.

---

## Overview

| Module | Responsibility |
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

The memory layer operates in four distinct modes, visible via `/memory status`:

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

## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_12_02_memory-gate-data-model-search.md`
- `05_agent_12_03_memory-module-ref-core-and-store.md`
- `05_agent_12_04_memory-module-ref-retrieval-and-injection.md`
- `05_agent_12_05_memory-module-ref-extraction-and-facade.md`
- `05_agent_12_06_memory-module-ref-ops-and-scoring.md`

## Keywords

persistent semantic memory
production checklist
purpose
memory modes
