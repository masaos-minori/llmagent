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
