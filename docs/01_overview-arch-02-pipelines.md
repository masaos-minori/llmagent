---
title: "Pipeline Architecture"
category: overview
tags:
  - pipeline-architecture
  - ingestion-pipeline
  - query-pipeline
  - rag
  - architecture
  - embedding
  - search
related:
  - 01_overview-arch-01-process.md
  - 01_overview-arch-03-features.md
---

# Overview & Architecture

File Structure → [`01_overview-files-01-build.md`](01_overview-files-01-build.md), [`01_overview-files-02-rag.md`](01_overview-files-02-rag.md), [`01_overview-files-03-scripts.md`](01_overview-files-03-scripts.md), [`01_overview-files-04-shared.md`](01_overview-files-04-shared.md), [`01_overview-files-05-config.md`](01_overview-files-05-config.md), [`01_overview-files-06-misc.md`](01_overview-files-06-misc.md)

## 2. Architecture

### 2.2 Ingestion Pipeline

Details → [`03_rag_02_01_ingestion_pipeline-overview.md`](03_rag_02_01_ingestion_pipeline-overview.md)

``` text
target_urls → crawler.py (BFS crawling) → rag-src/*.json
           → chunk_splitter.py (JA/EN/code splitting) → rag-src/chunk/*.json
           → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 Query Pipeline

Details → [`03_rag_03_01_query_pipeline-overview.md`](03_rag_03_01_query_pipeline-overview.md)

``` text
User Input
  → MQE + embed → KNN+BM25 → RRF → Rerank → Refiner → Context Augmentation
  → LLM (:8080) → tool_calls → MCP Servers (:8004〜:8014)
  → Final Answer (SSE streaming)
```

#### Implementation Notes for Query Pipeline

- **Turn processing is separated into 4 layers**: `AgentREPL` (REPL loop) → `Orchestrator` (Turn control / Workflow management) → `LLMTurnRunner` (LLM streaming + internal tool loop) → `agent/tool_runner.py` (Tool execution). The responsibilities of each layer are declared in the docstrings of `agent/repl.py`.
- **MDQ/RAG Tool Selection**: `agent/mdq_rag_classifier.py` analyzes the query string; if it contains keywords related to Markdown structure, it injects a hint into the history as an ephemeral message with the `system` role to prioritize MDQ tools, otherwise prioritizing RAG tools. This can also be fixed via configuration. (Source: `agent/orchestrator.py`)
- **Tool Loop Guard**: Detects abnormal repetitive tool calling patterns within a turn and returns a stop hint to the LLM to force termination. Details → [`05_agent_03_02_turn-processing-flow-llm-tool-loop.md`](05_agent_03_02_turn-processing-flow-llm-tool-loop.md) (Source: `agent/tool_loop_guard.py`)
- **Workflow Engine**: `agent/workflow/workflow_engine.py` manages stage transitions: plan → execute → [Post-execution approval gate] → verify. The post-execution approval gate is passed using `/approve` / `/reject` slash commands. If waiting for approval at the start of a turn, LLM processing is blocked. (Source: `agent/orchestrator.py`)

**Processing Order within a Turn**

The execution order within a turn is hardcoded (`orchestrator.py`):

1. **Memory Injection** — Adds semantic memory as a system message with flags.
2. **MDQ/RAG Hint Injection** — Adds hints as a system message with flags.
3. **User Message Addition** — Added to `history` after synchronizing the system prompt, then saved to `session.sqlite`.
4. **History Compression** — LLM summarization is performed only when character/token limits are exceeded.
5. **LLM Call** — Streaming + tool loop via `LLMTurnRunner`.

Messages with flags are removed during the system prompt synchronization process at the start of each turn. They are not saved to persistent session history.

**Workflows are Always Required (No Mode Setting)**

`workflow_mode` is not a valid configuration key. `build_agent_config()` does not consume this key, so even if it exists in the configuration file, it is ignored without error or warning. Workflow definitions (deployed as `config/workflows/default.json`, which is a **required workflow deployment artifact**) are always mandatory; if they are missing or invalid, startup is interrupted with a `RuntimeError` before proceeding. There is no fallback to direct execution or any way to disable workflows.

**Enabling Post-Execution Approval Gates:**
In the workflow definition file (`config/workflows/*.json`), the `require_approval` field (defaults to `false`) can enable a post-execution approval gate between the `execute` and `verify` stages. Since the pending approval state is persisted in `workflow.sqlite`, pending approvals are restored even after a restart. (Sources: `agent/workflow/models.py`, `agent/workflow/workflow_loader.py`, `agent/orchestrator.py`, `agent/startup.py`)

**MCP Server `startup_mode`**

There are two types in `McpServerConfig.startup_mode`:

- `none` (Default schema value, used when the key is unspecified in TOML): Does not start a subprocess or perform health checks. The server is treated as unavailable.
- `persistent`: Connects to a server that is already running externally.
- `subprocess`: Starts the server as a subprocess upon agent startup and waits for readiness via `/health` polling.

(Source: `StartupMode` enum in `shared/mcp_config.py`)

Currently, `config/agent.toml` explicitly specifies `startup_mode = "subprocess"` for all MCP servers. (Note: While `persistent` exists in the schema, it is unused. Source: Explicit in code, `config/agent.toml`)

### Implementation Note: Behavior on Server Startup Failure

The behavior when an MCP server fails to start with `startup_mode="subprocess"` depends on the `security_profile` (Source: `_start_servers()` in `agent/startup.py`):

- `security_profile = "production"`: Raises a `RuntimeError` and aborts startup (fail-fast).
- `security_profile = "local"` (Current setting in `config/agent.toml`): Only logs a warning and displays it on screen, continuing REPL startup (fail-open).

Note that this is not a uniform fail-open policy. (Source: Explicit in code)

## Related Documents

- `01_overview-arch-01-process.md`
- `01_overview-arch-03-features.md`
- [01_overview.md](01_overview.md)

## Keywords

pipeline-architecture
ingestion-pipeline
query-pipeline
rag
turn-processing
workflow-mode
startup-mode
