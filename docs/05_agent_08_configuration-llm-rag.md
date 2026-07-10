---
title: "Agent Configuration"
category: agent
tags:
  - agent
  - agent
  - configuration
  - config
  - settings
related:
  - 05_agent_00_document-guide.md
---

# Agent Configuration

.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `llm_url` | `""` | LLM endpoint URL |
| `http_timeout` | `30.0` | HTTP timeout (seconds) |
| `llm_max_retries` | `3` | Retry limit for HTTP 429/503/connection errors |
| `llm_retry_base_delay` | `1.0` | Exponential backoff base (seconds) |
| `llm_temperature` | `0.2` | Generation temperature (0.0–2.0) |
| `llm_max_tokens` | `1024` | Max generation tokens |
| `title_llm_temperature` | `0.1` | Session title generation temperature |
| `title_llm_max_tokens` | `20` | Session title max tokens |
| `sse_heartbeat_timeout` | `30.0` | SSE idle timeout (0 = disabled) |
| `sse_malformed_retry` | `2` | Malformed SSE frame tolerance |
| `sse_reconnect_max` | `1` | Max SSE reconnects on retryable error |
| `llm_stream_retry_on_heartbeat_timeout` | `True` | Reconnect on HEARTBEAT_TIMEOUT |
| `llm_stream_retry_on_malformed_chunk` | `False` | Reconnect on MALFORMED_SSE_FRAME |
| `tokenize_url` | `""` | llamacpp `/tokenize` URL; `""` = chars//4 fallback |
| `context_token_limit` | `0` | Token-based compression threshold (0 = disabled) |
| `context_char_limit` | `8000` | Char-based compression threshold |
| `context_compress_turns` | `4` | Oldest N turn pairs to compress per cycle |
| `history_protect_turns` | `2` | Most recent N turn pairs protected from compression |
| `budget_warn_ratio` | `0.8` | Warn when history reaches this fraction of limit |

---

## RAGConfig (`cfg.rag

.*`)

Source: `config/agent.toml`

| Field | Default | Description |
|---|---|---|
| `top_k_search` | `10` | Vector/FTS search result count |
| `top_k_rerank` | `15` | Cross-encoder candidate count |
| `max_chunks_per_doc` | `2` | Max chunks per document in results |
| `embed_url` | `http://127.0.0.1:8003/embedding` | Embedding API endpoint |
| `use_semantic_cache` | `False` | Enable semantic cache for RAG results |
| `semantic_cache_threshold` | `0.92` | Cosine similarity threshold for cache hit |
| `semantic_cache_max_size` | `100` | Max cache entries (FIFO eviction; oldest removed first) |
| `use_refiner` | `False` | Compress chunks via LLM after reranking |
| `refiner_max_tokens` | `512` | Refiner LLM max tokens |
| `refiner_timeout` | `30.0` | Refiner LLM timeout (seconds) |
| `refiner_max_chars_per_chunk` | `300` | Max chars per chunk passed to refiner |

---

## ToolConfig (`cfg.to

## Related Documents

- `agent`
- `configuration`
- `config`

## Keywords

agent
configuration
config
settings
