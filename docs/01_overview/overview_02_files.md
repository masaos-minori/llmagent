---
title: "File Structure"
area: overview
tags:
  - file-structure
  - build
  - llama-cpp
  - models
  - gguf
  - deployment
  - rag
  - rag-src
  - crawler
  - chunk-splitter
  - ingester
  - embedding
  - scripts
  - agent
  - mcp-server
  - shared
  - db
  - sqlite
  - configuration
  - toml
  - agent-toml
  - mcp-server-config
  - rag-config
  - eventbus
  - logs
  - system-configuration
related:
  - overview_00_document-guide.md
  - overview_01_01-arch-process.md
  - overview_01_02-arch-pipelines.md
  - overview_01_03-arch-features.md
---

# File Structure

Architecture Overview → [`overview_01_01-arch-process.md`](overview_01_01-arch-process.md), [`overview_01_02-arch-pipelines.md`](overview_01_02-arch-pipelines.md), [`overview_01_03-arch-features.md`](overview_01_03-arch-features.md)

## 3. File Structure

This document covers the file structure by logical directory boundaries: build and models, RAG, scripts, shared infrastructure, configuration, and miscellaneous.

## 3.1 Build and Models

See `deploy/` for the current file layout.

### Build Component Responsibilities

**Build artifacts** — Compiles and maintains the inference runtime. Owns the compiled shared libraries and headers produced by the build process. Consumed by the deployment layer.

**Model assets** — Chat and embedding model weights acquired independently. Consumed by their respective LLM processes. Dependency direction flows from model acquisition into these components.

### Deployment Artifacts

**Build scripts** — One-time setup operations: sqlite-vec extension compilation, Python script and configuration deployment, and SQLite schema initialization. Each runs sequentially; later steps depend on earlier ones completing successfully.

**Service orchestration** — Runs the workflow pre-flight checks and starts the Event Bus; requires workflow definitions validated and database tables present before starting. MCP servers are started by the agent as subprocesses on agent startup. LLM services (`embed-llm`, `agent-llm`) are not started by any script in the repository and must already be running (see [deployment_01_deployment.md](../90_deployment/deployment_01_deployment.md)).

**Agent launcher** — Starts the AgentREPL process. Prefers the production pyproject.toml over development alternatives. Dependent on service orchestration completing first.

### Startup Sequence Dependencies

Workflow validation is a hard prerequisite for both deployment and service orchestration. Database existence check is a precondition for service orchestration.

Startup order: build scripts → deployment → schema initialization → service orchestration → agent launcher

### Reason for Process Separation

Deployment is split into separate scripts under `deploy/` (`build_sqlite_vec.sh`, `deploy.sh`, `init_db.sh`, `setup_services.sh`, `start_agent.sh`), each an independent bash script using `set -euo pipefail`. (Explicit in code — `deploy/*.sh`)
- One-time steps (such as building the sqlite-vec extension) are not repeated on every deployment.
- Each step can be re-run on its own, for example `start_agent.sh` can be run again without re-running the deployment steps.

## 3.2 RAG Files

See `rag-src/` for the current file layout.

### RAG Component Responsibilities

**Crawled content** — Raw crawled data collected by the crawler process. Owned by the crawler; feeds into the chunking stage. Dependency direction flows from crawler into this component.

**Chunked content** — Produced by the chunk_splitter process from crawled content. Feeds into the ingester stage. Dependency direction flows from chunk_splitter into this staging area.

**Post-ingestion staging** — Files moved here by the ingester after successful database insertion. No automated retention or cleanup applies to this staging area; files accumulate until removed manually.

**Vector search extension** — SQLite extension module providing vector search capability. Runtime dependency of the RAG pipeline's vector store layer.

### Data Flow Dependencies

Crawler produces crawled content consumed by chunk_splitter; chunk_splitter produces chunks consumed by ingester for database insertion; ingester moves processed files to post-ingestion staging; vector search extension supports embedding similarity queries across all stages.

## 3.3 Scripts: Agent Core and Memory

### Key Directories and Responsibilities

- `scripts/agent/` — Agent REPL package: entry point, startup sequence, turn control, tool execution and policy, session management, lifecycle of MCP server processes, and diagnostics.
- `scripts/agent/memory/` — Memory subpackage: data model, storage, search, ingestion, injection, and scoring.

For the per-file layout, refer to the repository tree under these directories.

### Notes on Changes

- When changing tool approval flow, check both `tool_approval.py` and `repository_gateway.py` together.
- When changing memory search algorithms, check both `retriever.py` and `scoring.py` together.

## 3.4 Shared Infrastructure: venv/db/ and scripts/db/

See `venv/` for the virtual environment contents. See `db/` for the DB layer package. See `shared/` for the current file layout.

### Virtual Environment (venv/)

Python virtual environment managed by uv; `uv.lock` tracks the dependency list. Owned by the build/deployment process; consumed by all Python processes.

### Database Domains (db/)

Isolated SQLite databases: `rag.sqlite`, `session.sqlite`, `workflow.sqlite`, `eventbus.sqlite`. Each operates in WAL mode; persistence separated by domain to isolate different write patterns, limit failure impact, and clarify ownership. See ADR-008 for the rationale behind the per-domain separation. Shared DB path builder via `DbConfig` dataclass in `config.py`.

### DB Layer Package (scripts/db/)

Schema initialization, connection management (WAL mode, busy_timeout), and maintenance operations. Protocol abstraction layer defining VectorStore, DocumentStore, and SessionStore interfaces with SQLite implementations. Data models for checkpoint counts, purge counts, health metrics, document rows, session rows, and message rows. Consistency checking, rotation, and recovery utilities.

### Shared Infrastructure Components (scripts/shared/)

**LLM Client/Transport** — SSE streaming, exponential backoff retry, transport error handling, payload handling.

**Tool Routing/Execution** — MCP server routing, tool registry, runtime tool metadata, route resolution.

**Configuration** — TOML/JSON loader, typed value accessors, validators, MCP server configuration dataclasses, health tracking.

**Other Utilities** — Type definitions, action results, events, formatters, git helper, HTTP transport, JSON utilities, logging, OpenTelemetry, token counting.

**protocols/** — ShellPolicy protocol definition.

### Design Intent and Operational Specifications

#### Caching Strategy

`ToolResultCache` is a standalone LRU+TTL cache utility, currently unused in the codebase.

#### Health Check-Based Dispatch Control

Health checks using `mcp_health.py` enable dispatch control based on server status (HEALTHY/DEGRADED/UNAVAILABLE/HALF_OPEN/UNKNOWN).

#### Drift Validation Behavior

Config Drift defaults to warnings, raises RuntimeError if `routing_drift_strict` enabled. Live Drift defaults to warnings, becomes FATAL if `tool_definitions_strict` enabled. Ownership Duplication always results in FATAL regardless of mode.

## 3.5 Configuration

See `config/` for the current file layout.

### Configuration Directory Structure

**`config/workflows/default.json`** — Default workflow definition file; required by deploy.sh and setup_services.sh for startup validation. Owned by the deployment process; consumed by all services requiring workflow definitions.

**`config/agent.toml`** — Global agent settings including DB paths, embedding URLs, and MCP server configurations. Owned by the agent process; provides shared configuration for the AgentREPL runtime.

**`config/<key>_mcp_server.toml`** — Per-MCP-server configuration files (one per server, for example `shell_mcp_server.toml`); each contains the server's service-specific settings such as allowlists and the auth token reference.

### Per-Process Config Isolation Policy

Each process reads only its own config file — no cross-process config sharing. This prevents configuration drift between processes and ensures that changes to one process's config do not affect others. The MCP servers read their respective `<key>_mcp_server.toml` files; the agent reads `agent.toml`.

### MCP Server Configuration Responsibilities

MCP server configs define service-specific settings (allowlists, limits, auth token reference). Transport, URL, and startup settings for each server are defined in `config/agent.toml` (`McpServerConfig`). Each MCP server has its own config file because each server operates independently and may have different requirements.

## 3.6 Miscellaneous

See `scripts/eventbus/` for the current file layout. See `conf.d/` for MCP server configuration files.

### Event Bus Architecture

The event bus provides event-driven communication between system components. It uses SQLite-backed persistence for durability and implements publish-subscribe semantics for decoupled messaging. The event bus enables loose coupling between producers and consumers while maintaining delivery guarantees.

### Delivery Mechanisms

At-least-once delivery via SQLite transactional writes ensures no event loss during normal operation. A retry mechanism handles transient failures, with a dead letter queue (DLQ) capturing messages that exceed the maximum retry threshold. DLQ inspection and recovery are performed through dedicated endpoints; requeuing restores events to the active queue. Replay functionality (independent of DLQ recovery) allows consumers to reload from past offsets.

### Persistence Layer

SQLite-based event store with WAL mode for concurrent access. Events are indexed by topic and sequence number.

### Configuration Files (conf.d/)

Per-MCP-server configuration files under `conf.d/`: operational credentials for CI/CD, git, GitHub, and web search providers. These files contain sensitive settings and are managed separately from code.

## Keywords

file-structure
build
llama-cpp
models
gguf
deployment
rag
rag-src
crawler
chunk-splitter
ingester
embedding
scripts
agent
mcp-server
shared
db
sqlite
configuration
toml
agent-toml
mcp-server-config
rag-config
eventbus
logs
system-configuration
