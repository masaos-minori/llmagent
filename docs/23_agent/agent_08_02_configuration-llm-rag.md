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
  - agent_10_01_operations-and-observability-startup-and-health.md
  - rag_05_01-configuration-reference.md
  - governance_03_issue-and-uncertainty-management.md
---

# Agent Configuration

- Operations → [agent_10_01_operations-and-observability-startup-and-health.md](agent_10_01_operations-and-observability-startup-and-health.md)

## Purpose

Documents the structure and constraints of LLM and RAG configurations.

## Design Intent

### LLM Configuration

The Agent-owned LLM settings cover generation parameters, HTTP/connection, SSE streaming, token counting, history compression, and the budget warning (schema: `LLMConfig`; values: `config/agent.toml`). The settings below carry semantics that the schema alone does not show:

- `tokenize_url = ""` falls back to the category-aware estimate in `shared/token_estimation.py`.
- `context_token_limit = 0` disables token-based compression; `context_char_limit` is the character-count threshold that remains the fallback-truncation trigger.
- `sse_heartbeat_timeout = 0` disables the SSE idle timeout.
- `llm_stream_retry_on_heartbeat_timeout` / `llm_stream_retry_on_malformed_chunk` select whether the corresponding stream error classes reconnect, bounded by `sse_reconnect_max`.
- `history_protect_turns` protects the most recent turn pairs from compression; `context_compress_turns` is the number of oldest pairs compressed per cycle.

### RAG Configuration

#### Embedding Endpoint

- `embed_url`: Embedding endpoint used by the Agent's memory embedding client and the `embed-llm` health check.

#### Search Parameters

`RAGConfig` has no search-stage parameters (`top_k_search`, `top_k_rerank`, `max_chunks_per_doc`, `rrf_k`, and similar). The RAG pipeline runs inside the rag-pipeline MCP server, and its search parameters are owned by `config/rag_pipeline_mcp_server.toml` (see `rag_05_01-configuration-reference.md`).

#### Refiner

The refiner is configured in `config/rag_pipeline_mcp_server.toml`; refiner keys (`use_refiner`, `refiner_max_tokens`, `refiner_timeout`, `refiner_max_chars_per_chunk`) in `config/agent.toml` are rejected at startup.

## Responsibility Boundary

- **Canonical Source**: LLM/RAG sections in `config/agent.toml` for Agent-owned settings; `config/rag_pipeline_mcp_server.toml` for RAG pipeline parameters.
- **Validation**: `agent/services/config_validators.py`.
- **Schema**: `LLMConfig` / `RAGConfig` in `agent/config_dataclasses.py`.

## Key Constraints

- `memory.memory_embed_enabled=True` → `rag.embed_url` must not be empty.

## Keywords

- LLMConfig
- RAGConfig
