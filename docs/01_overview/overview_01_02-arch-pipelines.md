---
title: "Pipeline Architecture"
area: overview
tags:
  - pipeline-architecture
  - ingestion-pipeline
  - query-pipeline
  - rag
  - architecture
  - embedding
  - search
related:
  - overview_01_01-arch-process.md
  - overview_01_03-arch-features.md
  - agent_11_01_memory-overview-and-modes.md
  - overview_02_files.md
  - rag_02_01_ingestion_pipeline-overview.md
  - rag_03_01_query_pipeline-overview.md
  - agent_03_02_turn-processing-flow-llm-tool-loop.md
  - adr_02_001_workflow-engine-mandatory.md
  - agent_03_03_turn-processing-flow-workflow-engine.md
  - adr_02_004_environment-failure-handling-policy.md
---

# Overview & Architecture

File Structure → [`overview_02_files.md`](overview_02_files.md)

## 2. Architecture

### 2.2 Ingestion Pipeline

Details → [`rag_02_01_ingestion_pipeline-overview.md`](../21_rag/rag_02_01_ingestion_pipeline-overview.md)

``` text
target_urls → crawler.py (BFS crawling) → rag-src/*.json
           → chunk_splitter.py (JA/EN/code splitting) → rag-src/chunk/*.json
           → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 Query Pipeline

Details → [`rag_03_01_query_pipeline-overview.md`](../21_rag/rag_03_01_query_pipeline-overview.md)

``` text
User Input
  → Memory / MDQ-RAG hint injection → History compression
  → LLM → tool_calls
      ├─ rag_run_pipeline → rag-pipeline-mcp:
      │    MQE + embed → KNN+BM25 → RRF → Rerank → Context Augmentation → Refiner (optional)
      │    → result returned to the LLM
      └─ other MCP tools
  → Final Answer (SSE streaming)
```

The Agent does not run retrieval before the LLM call. RAG runs only when the LLM calls the `rag_run_pipeline` tool; the MDQ/RAG hint below only steers tool choice.

#### Implementation Notes for Query Pipeline

- **Turn processing is separated into 4 layers**: `AgentREPL` (REPL loop) → `Orchestrator` (Turn control / Workflow management) → `LlmTurnExecutor` (LLM streaming + internal tool loop) → `agent/tool_runner.py` (Tool execution). The responsibilities of each layer are declared in the docstrings of `agent/repl.py`.
- **MDQ/RAG Tool Selection**: `agent/mdq_rag_classifier.py` analyzes the query string; if it contains keywords related to Markdown structure, it injects a hint into the history as an ephemeral message with the `system` role to prioritize MDQ tools, otherwise prioritizing RAG tools. This can also be fixed via configuration. (Explicit in code — `agent/mode_classification.py`)
- **Tool Loop Guard**: Detects abnormal repetitive tool calling patterns within a turn and returns a stop hint to the LLM to force termination. Details → [`agent_03_02_turn-processing-flow-llm-tool-loop.md`](../23_agent/agent_03_02_turn-processing-flow-llm-tool-loop.md) (Explicit in code — `agent/tool_loop_guard.py`)
- **Workflow Engine**: `agent/workflow/workflow_engine.py` manages stage transitions: plan → execute → [Post-execution approval gate] → verify. The post-execution approval gate is passed using `/approve` / `/reject` slash commands. If waiting for approval at the start of a turn, LLM processing is blocked. (Explicit in code — `agent/orchestrator.py`)

**Processing Order within a Turn**

The execution order within a turn is hardcoded (`orchestrator.py`):

1. **Memory Injection** — Adds memory retrieved for the user prompt as a system message with flags; injection timing and scope are defined in [agent_11_01_memory-overview-and-modes.md](../23_agent/agent_11_01_memory-overview-and-modes.md).
2. **MDQ/RAG Hint Injection** — Adds hints as a system message with flags.
3. **User Message Addition** — Added to `history` after synchronizing the system prompt, then saved to `session.sqlite`.
4. **History Compression** — LLM summarization is performed only when character/token limits are exceeded.
5. **LLM Call** — Streaming + tool loop via `LlmTurnExecutor`.

Messages with flags are removed during the system prompt synchronization process at the start of each turn. They are not saved to persistent session history.

**Workflows are Always Required (No Mode Setting)**

See [ADR-001](../10_adr/adr_02_001_workflow-engine-mandatory.md) for rationale and invariants.

**Post-Execution Approval Gates:**
In the workflow definition file (`config/workflows/*.json`), the `require_approval` field enables a post-execution approval gate between the `execute` and `verify` stages. The loader requires it to be `true`: a definition whose `require_approval` is absent or `false` is rejected, and the bundled default definition sets it to `true`. Since the pending approval state is persisted in `workflow.sqlite`, pending approvals are restored even after a restart. (Sources: `agent/workflow/models.py`, `agent/workflow/workflow_loader.py`, `agent/orchestrator.py`, `agent/startup.py`)

For the operations policy that follows from this requirement, see [Approval Gates](../23_agent/agent_03_03_turn-processing-flow-workflow-engine.md#approval-gates).

**MCP Server `startup_mode`**

`McpServerConfig.startup_mode` takes one of the following modes:

- `none` (Default schema value, used when the key is unspecified in TOML): Does not start a subprocess or perform health checks. The server is treated as unavailable.
- `persistent`: Connects to a server that is already running externally.
- `subprocess`: Starts the server as a subprocess upon agent startup and waits for readiness via `/health` polling.

(Explicit in code — `StartupMode` enum in `shared/mcp_config.py`)

The `startup_mode` of each MCP server is set per `[mcp_servers.*]` entry in `config/agent.toml`.

### Implementation Note: Behavior on Server Startup Failure

See [ADR-004](../10_adr/adr_02_004_environment-failure-handling-policy.md) for rationale, tradeoffs, and invariants.

## Keywords

- pipeline-architecture
- ingestion-pipeline
- query-pipeline
- rag
- turn-processing
- workflow-mode
- startup-mode
