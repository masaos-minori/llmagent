---
title: "Process Architecture"
area: overview
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

The system consists of three categories of processes: the Agent CLI REPL, LLM services, and MCP servers. Each category runs as an independent process with its own lifecycle and configuration.

**Component responsibilities:**

- **Agent CLI REPL** (`scripts/agent/__main__.py`): Orchestrates the user interaction loop — receives prompts, performs RAG search, invokes the LLM, executes MCP tools, and returns responses. This is the single entry point for all agent operations.
- **LLM services**: Provide chat/completion and embedding capabilities. The Agent CLI connects to these via HTTP; they operate independently of the agent lifecycle.
- **MCP server group**: Each server implements a single-responsibility tool domain (file read/write/delete, shell execution, GitHub operations, RAG pipeline, CI/CD, MDQ compression, local git, web search). Servers communicate with the Agent CLI exclusively over HTTP POST `/v1/call_tool`.

**Owned state:**

- The Agent CLI owns the conversation context (turn history, prompt construction, response assembly).
- Each LLM service owns its model weights and inference state.
- Each MCP server owns its tool-specific runtime state (e.g., file handles, connection pools).
- Shared data (vector stores, SQLite databases) is accessed by multiple components but owned by the infrastructure layer, not any single process.

**Allowed dependency direction:**

- The Agent CLI depends on LLM services and MCP servers (it initiates calls to them).
- LLM services depend on neither the Agent CLI nor MCP servers.
- MCP servers depend on neither the Agent CLI nor LLM services.
- No MCP server depends on another MCP server.
- Infrastructure (SQLite, vector DB) is depended upon by both the Agent CLI and MCP servers but does not depend on either.

**Reason for process separation:**

Each MCP server runs as a separate process because:
- Failure isolation: a crash in one tool domain does not affect others.
- Security boundary: each server can enforce its own access controls and permissions.
- Independent scaling: write-heavy domains (file-write-mcp) may require different resource allocation than read-only domains (web-search-mcp).
- Deployment independence: individual servers can be updated or restarted without affecting the entire system.

**Reason for per-process configuration separation:**

Each process reads only its own configuration file. Common parameters (DB paths, external service URLs) are described individually in each process's configuration rather than shared across files. This ensures that changing one process's configuration never inadvertently affects another, and each process can be configured independently for different environments (development, staging, production).

#### Implementation Notes

- The entry point is `scripts/agent/__main__.py`, started with `python -m agent`. The `agent.py` in the diagram refers to this module entry. (Source: `__main__.py` docstring)
- MCP communication uses HTTP exclusively; `stdio` transport is not supported (ADR-007). `ToolExecutor` calls MCP servers via HTTP POST `/v1/call_tool`. (Source: `HttpTransport` in `shared/http_transport.py`)
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

| Service | Role |
|---|---|
| `agent-llm` | Chat/Code Generation LLM (Dual use: MQE & Re-ranking) |
| `embed-llm` | Text → Vector conversion (dimension: `scripts/db/store_protocols.py::get_embedding_dims()`) |
| `web-search-mcp` | Web Search MCP Server (DuckDuckGo) |
| `file-read-mcp` | File Read MCP Server |
| `github-mcp` | GitHub Operation MCP Server |
| `file-write-mcp` | File Write MCP Server |
| `file-delete-mcp` | File Delete MCP Server |
| `shell-mcp` | Shell Command Execution MCP Server |
| `rag-pipeline-mcp` | RAG Pipeline MCP Server |
| `cicd-mcp` | GitHub Actions CI/CD MCP Server |
| `mdq-mcp` | Markdown Context Compression Engine MCP Server |
| `git-mcp` | Local Git Operation MCP Server |
| `eventbus` | Event Delivery Server (Separate process from MCP servers. Details: `06_eventbus_01_system-overview.md`) |

#### Implementation Notes (LLM Service URL/Port)

The actual connection destinations for `agent-llm`/`embed-llm` are set as individual hosts/ports via `llm.llm_url` / `rag.embed_url` in `config/agent.toml`; the values shown above are representative. Depending on the runtime environment, they may point to different hosts/ports (such as the default `8080` series for llama.cpp). The MCP server group matches the `[mcp_servers.*].url` in `agent.toml`. (Explicit in code)

Port `8011` was deprecated (formerly `sqlite-mcp`) and is intentionally absent from the current table and `config/agent.toml`.

### 2.2 Design Boundaries Requiring Joint Review

- Architecture decisions that affect multiple subsystems require joint review by all affected teams.
- Process documentation that impacts operational procedures requires review by operations stakeholders.
- Changes to ADRs that alter architectural rationale require review by the architecture committee.
- Configuration changes to one process's config file must be reviewed against its dependency boundaries (e.g., changing `agent.toml`'s `mcp_servers` section affects which MCP servers the Agent CLI can reach).
- Cross-component state transitions (Agent CLI ↔ LLM service ↔ MCP server) require coordinated testing when any component's contract changes.

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
