---
title: "Process Architecture"
category: overview
tags:
  - process-architecture
  - system-overview
  - architecture
  - process-model
  - agent
  - mcp-server
  - llm-service
related:
  - 01_overview-arch-02-pipelines.md
  - 01_overview-arch-03-features.md
  - 01_overview.md
---

# Overview & Architecture

File Structure → [`01_overview-files-01-build.md`](01_overview-files-01-build.md), [`01_overview-files-02-rag.md`](01_overview-files-02-rag.md), [`01_overview-files-03-scripts.md`](01_overview-files-03-scripts.md), [`01_overview-files-04-shared.md`](01_overview-files-04-shared.md), [`01_overview-files-05-config.md`](01_overview-files-05-config.md), [`01_overview-files-06-misc.md`](01_overview-files-06-misc.md)

## 1. Overview & Purpose

Building a multi-agent orchestration system with Agent + MCP servers
- LLM server group using llama.cpp
- Single-responsibility tool execution MCP server group
- LLM agents supporting both Japanese and English
- RAG environment with SQLite-based vector DB
- Target OS: Gentoo Linux or Ubuntu Linux
- Use case: Program development

## 2. Architecture

### 2.1 Process Configuration

``` text
User
    │ Interaction input (agent[chat]> / agent[code]> Prompt)
    ▼
┌──────────────────────────────────────────────────────┐
│  agent.py (CLI REPL Tool)                           │
│  Input → RAG Search → LLM Call → MCP Tool Exec → Response  │
└───────┬─────────────┬──────────────────┬─────────────┘
        │             │                  │
        ▼             ▼                  ▼
:8081 embed-LLM  :8080 agent-LLM   MCP Server Group (http)
(During RAG search)                 (Count/Ports refer to `[mcp_servers.*]` in `config/agent.toml`)
```

#### Implementation Notes

- The entry point is `scripts/agent/__main__.py`, started with `python -m agent`. The `agent.py` in the diagram refers to this module entry. (Source: `__main__.py` docstring)
- MCP server transport can be configured as both `http` and `stdio`, but currently `ToolExecutor` uses HTTP POST `/v1/call_tool`. (Source: `HttpTransport` in `shared/http_transport.py`; `stdio` transport has been removed)
- The startup sequence (MCP server startup, health checks, security audit, prompt setup) is separated into `StartupOrchestrator` in `agent/startup.py` and delegated from `AgentREPL.run()`. (Source: `agent/startup.py`)

#### Configuration File Isolation Policy

Each process (Agent, each MCP server, crawler, ingester, chunk_splitter) operates independently and **only reads its own corresponding configuration file**. It does not read configuration files of other processes (including `agent.toml`). If multiple processes require common parameters like DB paths or external service URLs, do not create a shared file; instead, describe them individually in each process's configuration file.

| Process | Configuration File |
|---|---|
| agent | `config/agent.toml` |
| Each MCP server | `config/<key>_mcp_server.toml` |
| crawler | `config/crawler.toml` |
| ingester | `config/ingester.toml` |
| chunk_splitter | `config/chunk_splitter.toml` |

Details → [ADR-002](adr/ADR-002-config-isolation.md) / [90_shared_03 §2a](90_shared_03_01_runtime_and_execution-config-and-logging.md#2a-process-separation-policy-config-isolation-policy)

The following table contains representative examples; the exact number and ports of MCP servers are defined in `[mcp_servers.*]` of `config/agent.toml`.

| Service | Port | Model | Role |
|---|---|---|---|
| `agent-llm` | 8080 | Qwen3.6-Instruct-Q4_K_M | Chat/Code Generation LLM (Dual use: MQE & Re-ranking) |
| `embed-llm` | 8081 | multilingual-E5-small | Text → 384D Vector conversion |
| `web-search-mcp` | 8004 | — | Web Search MCP Server (DuckDuckGo) |
| `file-read-mcp` | 8005 | — | File Read MCP Server |
| `github-mcp` | 8006 | — | GitHub Operation MCP Server |
| `file-write-mcp` | 8007 | — | File Write MCP Server |
| `file-delete-mcp` | 8008 | — | File Delete MCP Server |
| `shell-mcp` | 8009 | — | Shell Command Execution MCP Server |
| `rag-pipeline-mcp` | 8010 | — | RAG Pipeline MCP Server |
| `cicd-mcp` | 8012 | — | GitHub Actions CI/CD MCP Server |
| `mdq-mcp` | 8013 | — | Markdown Context Compression Engine MCP Server |
| `git-mcp` | 8014 | — | Local Git Operation MCP Server |
| `eventbus` | 8015 | — | Event Delivery Server (Separate process from MCP servers. Details: `06_eventbus_01_system-overview.md`) |

#### Implementation Notes (LLM Service URL/Port)

The actual connection destinations for `agent-llm`/`embed-llm` are set as individual hosts/ports via `llm.llm_url` / `rag.embed_url` in `config/agent.toml`; the values in this table (e.g., `8080`/`8081`) are representative. Depending on the runtime environment, they may point to different hosts/ports (such as the default `8080` series for llama.cpp). The MCP server group (`8004`–`8015`) matches the `[mcp_servers.*].url` in `agent.toml`. (Explicit in code)

Port `8011` was deprecated (formerly `sqlite-mcp`) and is intentionally absent from the current table and `config/agent.toml`.

## Related Documents

- `01_overview-arch-02-pipelines.md`
- `01_overview-arch-03-features.md`
- [01_overview.md](01_overview.md)

## Keywords

process-architecture
system-overview
agent
mcp-server
llm-service
configuration-isolation
