# Overview & Architecture

File structure → [`01_overview-files.md`](01_overview-files.md)

## 1. Overview & Purpose

Build a multi-agent orchestration system with agents + MCP servers
- LLM server cluster using llama.cpp
- Single-responsibility tool-execution MCP server cluster
- LLM agent supporting both Japanese and English
- RAG environment with SQLite-based vector DB
- Target OS: Gentoo Linux or Ubuntu Linux
- Use case: program development

## 2. Architecture

### 2.1 Process Configuration

```
User
    │ Interactive input (agent[chat]> / agent[code]> prompt)
    ▼
┌──────────────────────────────────────────────────────┐
│  agent.py (CLI REPL tool)                            │
│  Input → RAG search → LLM call → MCP tool execution → Answer │
└───────┬─────────────┬──────────────────┬─────────────┘
        │             │                  │
        ▼             ▼                  ▼
:8003 embed-LLM  :8001 agent-LLM   MCP server cluster (http)
(RAG search time)                   10 servers (:8004~:8010, :8012~:8014)
```

#### Implementation Notes

- The entry point is `scripts/agent/__main__.py`, started via `python -m agent`. The `agent.py` in the diagram refers to this module entry. (Evidence: docstring of `__main__.py`)
- MCP server transports can be configured as both `http` / `stdio`, but the current implementation uses HTTP POST `/v1/call_tool` by `ToolExecutor`. (Evidence: `HttpTransport` in `shared/tool_executor.py`, stdio transport removed)
- The startup sequence (MCP server startup, health check, security audit, prompt setup) is separated into `StartupOrchestrator` in `agent/startup.py`, delegated from `AgentREPL.run()`. (Evidence: `agent/startup.py`)

#### Configuration File Separation Policy

Each process (agent, each MCP server, crawler, ingester, chunk_splitter) operates independently and **reads only its corresponding configuration file**. It does not read other processes' config files (including `agent.toml`). If DB paths or external service URLs are needed by multiple processes, do not create a common file — write them individually in each process's config file.

| Process | Config file |
|---|---|
| agent | `config/agent.toml` |
| Each MCP server | `config/<key>_mcp_server.toml` |
| crawler | `config/crawler.toml` |
| ingester | `config/ingester.toml` |
| chunk_splitter | `config/chunk_splitter.toml` |

Details → [90_shared_03 §2a](90_shared_03_runtime_and_execution.md#2a-process-separation-policy-config-isolation-policy)

| Service | Port | Model | Role |
|---|---|---|---|
| `agent-llm` | 8001 | Qwen3.6-Instruct-Q4_K_M | LLM (MQE and reranking) |
| `embed-llm` | 8003 | multilingual-E5-small | Text → 384-dim vector conversion |
| `web-search-mcp` | 8004 | — | Web search MCP server (DuckDuckGo) |
| `file-read-mcp` | 8005 | — | File read MCP server |
| `github-mcp` | 8006 | — | GitHub operations MCP server |
| `file-write-mcp` | 8007 | — | File write MCP server |
| `file-delete-mcp` | 8008 | — | File delete MCP server |
| `shell-mcp` | 8009 | — | Shell command execution MCP server |
| `rag-pipeline-mcp` | 8010 | — | RAG pipeline MCP server |
| `cicd-mcp` | 8012 | — | GitHub Actions CI/CD MCP server |
| `mdq-mcp` | 8013 | — | Markdown Context Compression Engine MCP server |
| `git-mcp` | 8014 | — | Local git operations MCP server |

### 2.2 Ingestion Pipeline

Details → [`03_rag_02_ingestion_pipeline.md`](03_rag_02_ingestion_pipeline.md)

```
target_urls → crawler.py (BFS crawl) → rag-src/*.json
            → chunk_splitter.py (JA/EN/code splitting) → rag-src/chunk/*.json
            → ingester.py (embed → SQLite INSERT) → rag-src/registered/
```

### 2.3 Query Pipeline

Details → [`03_rag_03_query_pipeline.md`](03_rag_03_query_pipeline.md)

```
User input
  → MQE + embed → KNN+BM25 → RRF → Rerank → Refiner → Context injection
  → LLM (:8001) → tool_calls → MCP server cluster (:8004~:8010, :8012~:8014)
  → Final answer (SSE streaming)
```

#### Implementation Notes

- Turn processing is separated into 4 layers: `AgentREPL` (REPL loop) → `Orchestrator` (turn control, workflow management) → `LLMTurnRunner` (LLM streaming + internal tool loop) → `agent/tool_runner.py` (tool execution). The responsibilities of each layer are declared in the docstring of `agent/repl.py`.
- MDQ/RAG tool selection: `agent/mdq_rag_classifier.py` parses the query string and injects a hint into history as an ephemeral message for the `system` role, prioritizing MDQ tools when Markdown structural keywords are present, otherwise RAG tools. Can also be fixed via config. (Evidence: `agent/orchestrator.py` `_classify_and_inject_mode`)
- Tool loop guard: Detects 4 types of anomalies within the same turn — duplicate tool calls (`dedup`), retry of failed calls (`retry`), round fingerprint repetition (`cycle`), and consecutive error limit (`consecutive_errors`) — and returns a stop hint to the LLM. (Evidence: `agent/tool_loop_guard.py`)
- Workflow engine: `agent/workflow/workflow_engine.py` manages stage transitions for plan → execute → [approval gate] → verify. Pass human approval gates via `/approve` / `/reject` slash commands. If approval is pending, LLM processing is blocked at turn start. (Evidence: `agent/orchestrator.py` `handle_turn`, `_handle_workflow_engine`)

**Processing Order Within a Turn**

The execution order of `Orchestrator._process_turn()` is fixed in code (`orchestrator.py`):

1. Memory injection (`_handle_memory_injection`) — adds semantic memory as a system message with `_memory_injected` flag
2. MDQ/RAG hint injection (`_classify_and_inject_mode`) — adds as a system message with `_ephemeral` flag
3. User message addition (`_append_user_message`) — adds to `history` after syncing the system prompt, then persists to `session.sqlite`
4. History compression (`_handle_history_compression`) — runs LLM summarization only when character/token limits are exceeded
5. LLM call (`_handle_llm_turn`) — streaming + tool loop via LLMTurnRunner

Messages with `_memory_injected` and `_ephemeral` flags are removed in `_sync_system_prompt()` at the start of each turn. They are not saved to persistent session history.

**Three workflow_mode Types**

| workflow_mode | Behavior | Failure behavior |
|---|---|---|
| `auto` (default) | Activates if a workflow definition exists | Continues with warning log on load failure |
| `required` | Workflow definition is mandatory | Aborts startup with `RuntimeError` on load failure |
| `disabled` | Always direct execution | Completely bypasses workflow |

With `workflow_require_approval=True`, a human approval gate can be inserted between execute → verify. Pending approval state is persisted in `workflow.sqlite` and restored after restart by `StartupOrchestrator._recover_pending_approvals()`. (Evidence: `agent/config_dataclasses.py`, `agent/orchestrator.py`, `agent/startup.py`)

**MCP Server startup_mode**

Two types via `McpServerConfig.startup_mode`:

- `persistent` (default): Connects to servers already running externally
- `subprocess`: `StartupOrchestrator._start_servers()` launches the server as a subprocess at agent startup and confirms readiness via `/health` polling. Startup failure is logged as a warning rather than raising `RuntimeError`, allowing REPL startup to continue (fail-open).

(Evidence: `shared/mcp_config.py` `StartupMode`, `agent/startup.py` `_start_servers`)

### 2.4 Agent Features & Command List

Details → [`05_agent_07_cli-and-commands.md`](05_agent_07_cli-and-commands.md)

### 2.5 Implemented Features Summary

| Feature | Implementation Location |
|---|---|
| RAG search (MQE + KNN + BM25 + RRF + Rerank + Refiner) | `scripts/rag/pipeline.py` |
| MCP tool calling (HTTP, 10 servers) | `agent/tool_runner.py`, `shared/tool_executor.py` |
| Memory layer (semantic/episodic) | `agent/memory/` |
| Session persistence & restore | `agent/session.py`, `db/` |
| Context compression (LLM summarization) | `agent/history.py` |
| Tool result TTL cache | `shared/tool_cache.py`, `shared/tool_executor.py` |
| SSE streaming | `shared/llm_client.py` |
| Slash commands | `agent/commands/` |
| Tool loop guard (dedup/cycle/retry/error limits) | `agent/tool_loop_guard.py` |
| Workflow engine (plan/execute/approval/verify) | `agent/workflow/` |
| MDQ/RAG query routing | `agent/mdq_rag_classifier.py` |
| Dependency injection hub (AgentContext) | `agent/context.py` |
| Diagnostic store (turn/session stats) | `agent/diagnostic_store.py` |

#### Implementation Notes

**Shared State and Dependency Injection**

`AgentContext` (`agent/context.py`) serves as the DI hub for all services. It composes `ConversationState`, `TurnState`, `RuntimeStats`, `WorkflowState`, and `AppServices`, with `AgentREPL`, `Orchestrator`, and each command handler referencing the same instance. (Evidence: `agent/context.py`)

**Memory Layer Activation Modes**

`MemoryServices.get_activation_mode()` returns one of 4 modes depending on startup state: `disabled` (disabled by config), `fts-only` (embed server unavailable), `degraded` (embed circuit breaker open), `hybrid` (normal operation). If semantic search is unavailable, it falls back to FTS only without treating it as an error. (Evidence: `agent/memory/services.py`)

**Tool Routing**

`shared/route_resolver.py` resolves tool names to server keys. Routing priority: (1) `/v1/tools` live discovery map at startup, (2) static registry in `shared/tool_registry.py`. The `tool_names` config is not used for routing — only as metadata for drift validation. (Evidence: `shared/route_resolver.py`)

**Plugin System**

At the end of `factory.build_agent_context()`, `_init_plugin_registry()` is called to dynamically load tools and slash commands from the `plugins/` directory. Config-driven behavior control:

- `plugin_tool_override=False` (default): Plugins conflicting with existing MCP tool names are rejected
- `plugin_strict=False` (default): Load failures are logged as warnings, agent startup continues (fail-open)

(Evidence: `agent/factory.py` `_init_plugin_registry`)

**Scope of sqlite-vec Extension Application**

The `SQLiteHelper` in `db/helper.py` loads the sqlite-vec extension (`vec0.so`) only when `target="rag"`. It is not applied to `session`, `workflow`, or `eventbus` DBs. Intentional separation limiting vector operations to the RAG DB. (Evidence: `db/helper.py` `_default_load_vec = resolved == "rag"`)

**Diagnostic Save on Session End**

In the `finally` block of `AgentREPL._run_repl_loop()`, the following are executed:

1. `_persist_session_diagnostics()` — saves turn count, tool call count, latency, and workflow stats to `DiagnosticStore`
2. `_persist_session_memories()` — extracts and persists memory from session history via rule-based extraction
3. Executes WAL TRUNCATE checkpoint on `session.sqlite` before closing the connection

Diagnostic info can be referenced via the `/db` command or querying the `tool_results` table. (Evidence: `agent/repl.py` `_run_repl_loop`, `_persist_session_diagnostics`, `_close_resources`)

---
