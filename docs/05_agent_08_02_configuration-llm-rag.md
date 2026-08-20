---
title: "Agent Configuration - LLMConfig and RAGConfig"
category: agent
tags:
  - agent
  - configuration
related:
  - 05_agent_00_document-guide.md
source:
  - 05_agent_08_01_configuration-loading-agent-config.md
---

# Agent Configuration

- Operations → [05_agent_10_01_operations-and-observability-startup-and-health.md](05_agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the structure and constraints of LLM and RAG configurations.

## Design Intent

### LLM Configuration

#### Generation Parameters

- `temperature`: Generation temperature (0.0–2.0).
- `max_tokens`: Maximum number of tokens to generate.
- For session titles: `title_llm_temperature` (0.1), `title_llm_max_tokens` (20).

#### HTTP/Connection

- `llm_url`: LLM endpoint URL.
- `http_timeout`: HTTP timeout (seconds).
- `llm_max_retries`: Retry limit for HTTP 429/503/connection errors.
- `llm_retry_base_delay`: Base value for exponential backoff (seconds).

#### SSE Streaming

- `sse_heartbeat_timeout`: SSE idle timeout (0 = disabled).
- `sse_malformed_retry`: Number of malformed SSE frames allowed.
- `sse_reconnect_max`: Maximum SSE reconnection attempts on retryable errors.
- `llm_stream_retry_on_heartbeat_timeout`: Reconnect when `HEARTBEAT_TIMEOUT` occurs.
- `llm_stream_retry_on_malformed_chunk`: Reconnect when `MALFORMED_SSE_FRAME` occurs.

#### Token Counting

- `tokenize_url`: llamacpp `/tokenize` URL; `""` falls back to `chars // 4`.

#### History Compression

- `context_token_limit`: Token-based compression threshold (0 = disabled).
- `context_char_limit`: Character-count-based compression threshold.
- `context_compress_turns`: The oldest N turn pairs to compress in one cycle.
- `history_protect_turns`: The most recent N turn pairs protected from compression.

#### Budget Warning

- `budget_warn_ratio`: Warns when history reaches this ratio of the limit.

### RAG Configuration

#### Search Parameters

- `top_k_search`: Number of vector/FTS search results.
- `top_k_rerank`: Number of candidates for the cross-encoder.
- `max_chunks_per_doc`: Maximum number of chunks per document in results.
- `rrf_k`: Reciprocal Rank Fusion (RRF) constant for the RAG pipeline.

#### Semantic Cache

- `use_semantic_cache`: Enables semantic cache.
- `semantic_cache_threshold`: Cosine similarity threshold for a cache hit.
- `semantic_cache_max_size`: Maximum number of cache entries (FIFO eviction).

#### Refiner

- `use_refiner`: Compresses chunks with an LLM after reranking.
- `refiner_max_tokens`: Maximum token count for the Refiner LLM.
- `refiner_timeout`: Refiner LLM timeout (seconds).
- `refiner_max_chars_per_chunk`: Maximum characters per chunk passed to the Refiner.

## Responsibility Boundary

- **Canonical Source**: LLM/RAG sections in `config/agent.toml`.
- **Validation**: `agent/services/config_validators.py`.
- **Dataclasses**: `LLMConfig` / `RAGConfig` in `agent/config_dataclasses.py`.

## Key Constraints

- `rag.use_semantic_cache=True` → `rag.embed_url` must not be empty (see Part 2).
- `memory.memory_embed_enabled=True` → `rag.embed_url` must not be empty (see Part 2).

## Operational Notes

- Unknown

## Known Limitations

- Unknown

## Related Docs

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config.md`
- `05_agent_08_03_configuration-tools-memory.md`
- `05_agent_08_04_configuration-mcp-approval-obs.md`

## Keywords

LLMConfig
RAGConfig
