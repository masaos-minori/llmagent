---
title: "Agent Configuration - LLMConfig and RAGConfig"
area: agent
tags:
  - agent
  - configuration
related:
  - agent_00_document-guide.md
  - agent_08_01_configuration-loading-agent-config.md
  - agent_08_03_configuration-tools-memory.md
  - agent_08_04_configuration-mcp-approval-obs.md
---

# Agent Configuration

- Operations → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the structure and constraints of LLM and RAG configurations.

## Design Intent

### LLM Configuration

#### Generation Parameters

- `temperature`: Generation temperature (0.0–2.0).
- `max_tokens`: Maximum number of tokens to generate.
- For session titles: `title_llm_temperature`, `title_llm_max_tokens` (values: see `config/agent.toml`).

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

#### Embedding Endpoint

- `embed_url`: Embedding endpoint used by the Agent's memory embedding client and the `embed-llm` health check.

#### Search Parameters

`RAGConfig` has no search-stage parameters (`top_k_search`, `top_k_rerank`, `max_chunks_per_doc`, `rrf_k`, and similar). The RAG pipeline runs inside the rag-pipeline MCP server, and its search parameters are owned by `config/rag_pipeline_mcp_server.toml` (see `rag_05_01-configuration-reference.md`).

#### Refiner

The refiner settings below are parsed and validated by the Agent, but no Agent code path reads them (RAG-006 in `governance_03_issue-and-uncertainty-management.md`).

- `use_refiner`: Compresses chunks with an LLM after reranking.
- `refiner_max_tokens`: Maximum token count for the Refiner LLM.
- `refiner_timeout`: Refiner LLM timeout (seconds).
- `refiner_max_chars_per_chunk`: Maximum characters per chunk passed to the Refiner.

## Responsibility Boundary

- **Canonical Source**: LLM/RAG sections in `config/agent.toml` for Agent-owned settings; `config/rag_pipeline_mcp_server.toml` for RAG pipeline parameters.
- **Validation**: `agent/services/config_validators.py`.
- **Dataclasses**: `LLMConfig` / `RAGConfig` in `agent/config_dataclasses.py`.

## Key Constraints

- `memory.memory_embed_enabled=True` → `rag.embed_url` must not be empty.

## Keywords

- LLMConfig
- RAGConfig
