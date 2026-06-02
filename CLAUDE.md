# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Role

- You are a senior engineer. Always respond in Japanese.

# Assistant: Style

- Use concise and simple sentences that are easy for AI to understand.
- Use half-width alphanumeric characters and symbols. Do not use emojis.
- Keep responses brief. Use bullet points when appropriate.

# Assistant: Policy

- Separate facts and assumptions clearly. Base answers only on information available in the given context.
- If any point is ambiguous or unknown, explicitly state "Unknown" and request additional information.

# Global Rules

- Read only necessary skills and docs (minimal context)
- **Always read `routing.md` immediately after this file** — it maps task type → skills to load AND docs to load
- Do NOT load all `docs/*.md`; load only what `routing.md`'s "Docs → task mapping" specifies
- **Do not proceed speculatively on code generation, documentation, or any other task — stop and ask when anything is unclear.**
- **Do not commit changes without a clear commit message that explains the "why" of the changes.**

## Context Loader Pattern

```
Task → routing.md → Minimal Skills + Shared Rules → Relevant docs → Execution
```

Always-load rules are in `routing.md` (`## Always load alongside the skill`).

## File Split Rule

When a document or skill file grows too large, split it according to these rules.

**Trigger:** a single file exceeds 400 lines AND contains multiple independent responsibilities.

**Four principles:**

| Principle | Rule |
|---|---|
| **routing** | After splitting, add task-type → file entries to the "Docs → task mapping" table in `routing.md` |
| **dependency direction** | Keep dependencies between new files strictly one-directional; no circular imports or references |
| **minimal loading** | Draw responsibility boundaries so that any single task requires reading as few files as possible |
| **shared normalization** | Consolidate shared specs or protocol definitions into one file; all others reference it, never duplicate |

**Procedure:**

1. Group sections/functions by responsibility and write the split proposal in a temporary plan file (e.g. `04_split_plan.md`); review the plan before touching any file
2. After splitting, convert the original file to an index (link list) or remove its content
3. Apply ripple-effect changes in the same pass: `routing.md`, `rules/env.md`, skill references, `docs/00_llm-implementation-guide.md`, `docs/06_common.md`
4. For code files, confirm `ruff` / `mypy` / `pytest` pass before closing the task

## Target environment

- **OS:** Gentoo Linux + OpenRC
- **Python:** 3.13 (production venv: `/opt/llm/venv/`; dev venv: `.venv/` managed by uv)
- **DB:** SQLite + `sqlite-vec` extension at `/opt/llm/sqlite-vec/vec0.so`

Full environment details, schema, config reference, and service ports: `rules/env.md`

## Development

```bash
uv sync --dev --system-certs    # create .venv/ and install all deps
source .venv/bin/activate       # activate dev venv

ruff format scripts/                                 # format first
ruff check scripts/ tests/ --fix && ruff check scripts/ tests/   # lint + auto-fix
mypy scripts/ tests/                                 # type check
PYTHONPATH=scripts lint-imports                      # enforce import layer contracts (see below)
pytest tests/test_<module>.py -v                     # single module
pytest -v                                            # full suite

# coverage gate — new/changed lines must hit 90%
coverage run -m pytest tests/ && coverage xml
diff-cover coverage.xml --compare-branch=master --fail-under=90

pre-commit run --all-files             # full gate (run before commit)

# CST-based bulk refactoring (bowler v0.9.0 confirmed installed)
bowler rename_func old_name new_name --write --dry-run   # always dry-run first
```

Full validation sequence: `rules/toolchain.md`

**Import layer contracts (enforced by `.importlinter`):** `shared` → external only · `db` → shared · `rag` → db, shared · `mcp` → db, shared · `agent` → all. Violations fail `lint-imports`. Never import from a higher layer into a lower one (e.g. `shared` must not import from `agent`, `rag`, `db`, or `mcp`).

**Execution policy:** Run **all local commands** directly without asking the user for confirmation first. This includes destructive local operations such as file deletion, `git reset`, and `git checkout`. The only exceptions that still require confirmation are actions that affect systems outside the local machine: pushing to remote repositories, modifying shared infrastructure, or sending messages to external services.

**mypy note:** `warn_unused_ignores = true` is set in `pyproject.toml`, so any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run, so the same rule applies there.

**Key library choices:** Use `orjson` (not stdlib `json`) for all JSON serialization — `orjson.dumps()` returns `bytes`; call `.decode()` when a `str` is required; use `option=orjson.OPT_SORT_KEYS` / `OPT_INDENT_2` instead of `sort_keys=True` / `indent=2`. Use `httpx` (not `requests`) for HTTP — `httpx.Client` for sync, `httpx.AsyncClient` for async.

**Test coverage:** Unit tests exist for `agent/commands/cmd_config.py`, `agent/commands/cmd_mcp.py`, `agent/commands/cmd_rag.py`, `agent/session.py`, `agent/repl_tool_exec.py` (approval logic also in `test_tool_approval.py`), `agent/factory.py`, `agent/cli_view.py`, `mcp/file/delete_service.py`, `mcp/file/write_service.py`, `mcp/file/read_server.py` (models), `mcp/github/service.py`, `mcp/git/service.py`, `agent/history.py`, `shared/llm_client.py`, `shared/token_counter.py`, `shared/mcp_config.py`, `shared/config_loader.py`, `agent/memory/layer.py`, `agent/memory/store.py`, `agent/memory/extract.py`, `agent/memory/retriever.py`, `agent/memory/jsonl_store.py`, `agent/orchestrator.py`, `shared/otel_tracer.py`, `shared/plugin_registry.py`, `rag/utils.py`, `rag/pipeline.py`, `mcp/shell/service.py`, `mcp/rag_pipeline/service.py`, `mcp/sqlite/service.py`, `mcp/cicd/service.py`, `shared/route_resolver.py`, `agent/lifecycle.py`, `mcp/server.py` (base class), `shared/tool_executor.py` (routing paths), `db/helper.py`, `db/maintenance.py`, `db/tool_results.py`. Core module `agent/repl.py` has no tests. Any refactoring task that touches this module must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting work.

## Architecture

→ For details, find the relevant `docs/` file via the "Docs → task mapping" table in `routing.md`.

### Agent REPL

`agent/repl.py` (`AgentREPL`) drives the REPL loop and manages component lifecycle. DI wiring (service injection into `AgentContext`) is delegated to `agent/factory.py` (`build_agent_context(ctx, view)`). Turn-level logic (compression → LLM loop → tool dispatch) is delegated to `Orchestrator` (`agent/orchestrator.py`). Satellite modules: `agent/repl_health.py` / `agent/repl_tool_exec.py` / `agent/repl_debug.py`. UI output goes through `CLIView` callbacks — no library module calls `print()` directly.

`agent/factory.py` exports `build_agent_context(ctx, view)` — injects `audit_logger / http / llm / tools / lifecycle / hist_mgr / memory` into `ctx.services.*`; also exports `init_tracer(ctx)`. `CommandRegistry` and `Orchestrator` are wired by `AgentREPL._init_components()` after `build_agent_context()` returns.

`agent/repl_tool_exec.py` implements risk-based tool approval: `AgentConfig.approval_risk_rules` maps tool names to risk tiers (`READ_ONLY` / `LOW` / `MEDIUM` / `HIGH` / `CRITICAL`); tools absent from the map fall back to tier defaults. Tools listed in `approval_dry_run_tools` automatically receive `dry_run=True` before the user sees the approval prompt. When `AgentConfig.use_tool_dag=True`, `execute_all_tool_calls()` runs `WRITE_TOOLS` as a first gather group before remaining tools, ensuring write-before-read ordering within a turn. Ignored when `serial_tool_calls=True`.

Details: `docs/05_agent-impl-class.md` (class API) / `docs/05_agent-impl-flow.md` (pipeline flow) / `docs/06_ref-agent-repl.md`

### Shared State

`AgentContext` (`agent/context.py`) owns per-session mutable state and acts as the DI hub. All services via `ctx.services.<key>` (no property shims); `ServiceContainer.audit_logger: Logger | None` provides structured audit logging; `ServiceContainer.memory: MemoryLayer | None` is the 4-tier memory facade (enabled by `use_memory_layer=True`). Per-turn trace IDs and token stats managed by `Orchestrator`. Memory implementation: `agent/memory/types.py` (MemoryEntry / MemoryQuery / MemoryHit dataclasses) / `agent/memory/store.py` (SQLite CRUD, `memories` + `memories_fts` tables) / `agent/memory/retriever.py` (FTS5 search + BM25/importance/recency scoring) / `agent/memory/extract.py` (rule-based extraction from history) / `agent/memory/jsonl_store.py` (append-only JSONL source of truth) / `agent/memory/layer.py` (SessionStart / UserPrompt / Stop lifecycle facade). Memory type domain: `semantic` (rules/policies/facts) and `episodic` (Q&A/failures/history). OTel tracing: `shared/otel_tracer.py` (`build_tracer()` — private `TracerProvider`, no global state pollution). Token counting: `shared/token_counter.py` — priority order: LLM `usage.prompt_tokens` → POST `/tokenize` endpoint (llamacpp) → `chars // 4` fallback; warns once per session when `/tokenize` is unavailable.

Details: `docs/06_ref-agent-context.md`

### Slash Commands

`CommandRegistry` (`agent/commands/registry.py`) dispatches to six command modules: `cmd_session.py` / `cmd_mcp.py` / `cmd_config.py` / `cmd_context.py` / `cmd_rag.py` / `cmd_ingest.py` (all under `agent/commands/`).

Details: `docs/06_ref-agent-commands.md`

### RAG Pipeline

Pipeline: MQE → vector search (`chunks_vec`) → FTS5 (`chunks_fts`) → RRF → rerank. `rag/pipeline.py` (`RagPipeline`) orchestrates the pipeline. Support layers: `rag/types.py` / `rag/repository.py` / `rag/llm.py`. Common types `RagHit` / `LLMMessage` are defined in `docs/06_common.md`; `LLMMessage` lives in `shared/types.py` and is re-exported from `rag/types.py`.

Details: `docs/06_ref-rag.md`

### Session Management

`agent/session.py` — session CRUD (create / list / load / delete) backed by SQLite. `agent/history.py` — per-session conversation history buffer with compaction hooks; consumed by `Orchestrator` each turn. `agent/commands/cmd_session.py` dispatches `/session` slash commands.

Details: `docs/06_ref-agent-session.md`

### DB Layer

`db/helper.py` — connection management (WAL / busy_timeout). `db/maintenance.py` — operational policies (`/db` command). `db/store.py` — Protocol abstraction. `db/tool_results.py` — tool result persistence (`/tool show <id>`).

Details: `docs/06_ref-sqlite.md`

### MCP Servers

Eleven servers in models/service/server layers under `mcp/`. Common base: `mcp/server.py`; protocol spec: `docs/06_common.md`. The seventh server (`rag-pipeline-mcp`, port 8010) exposes the RAG pipeline via `mcp/rag_pipeline/server.py` / `mcp/rag_pipeline/service.py` / `mcp/rag_pipeline/models.py`; see `docs/04_mcp-rag.md`. When adding a new MCP server, also add an entry to `config/agent.toml` under `[mcp_servers]`. When `_MCP_TOOLS` exceeds 400 lines, extract to `{server}/tools.py` and import via `from mcp.{server}.tools import _MCP_TOOLS`. Destructive operations (write/delete/move) support a `dry_run: bool = Field(default=False)` parameter — when `True` the service returns preview info without side effects; the `check_approval()` flow in `agent/repl_tool_exec.py` injects `dry_run=True` automatically for tools listed in `approval_dry_run_tools`.

`MCPServer` base class provides `list_tools() -> list[str]` (from `mcp_tools` class attribute) and `health() -> dict[str, str]`. `run_stdio()` handles line-delimited JSON-RPC; intercepts `name == "__list_tools__"` before dispatching to `dispatch()`. `__` prefix is reserved — do not define tools with `__` prefix names. `attach_auth_middleware(app, token)` adds Bearer-token auth + `X-Request-Id` middleware to any FastAPI app; token `""` disables auth and only injects the header.

Details: `docs/04_mcp-servers.md`

### SQLite MCP (eighth server)

`mcp/sqlite/server.py` (port 8011) exposes read-only SELECT queries via `query_sqlite` tool. `mcp/sqlite/service.py` (`SqliteMCPService`) validates SQL (SELECT-only, no multiple statements), enforces `db_allowlist`, caps rows at `max_rows`, and connects with `PRAGMA query_only=ON`. Config: `config/sqlite_mcp_server.toml`.

### CI/CD MCP (ninth server)

`mcp/cicd/server.py` (port 8012) wraps GitHub Actions REST API via 4 tools: `trigger_workflow` / `get_workflow_runs` / `get_workflow_status` / `get_workflow_logs`. `mcp/cicd/service.py` (`CiCdService`) enforces `repo_allowlist` (empty = deny all, fail-closed) and `workflow_allowlist` (empty = allow all, fail-open). `CiBackend` is a `typing.Protocol` enabling future GitLab CI / Jenkins backends. `GitHubActionsBackend._token` is masked in `__repr__` and must never be passed to any logger. Log output is capped at `max_log_size_kb` KB (default 256). Config: `config/cicd_mcp_server.toml`. Details: `docs/04_mcp-cicd.md`.

### MDQ MCP (tenth server)

`mcp/mdq/` (port 8013) is the Markdown Context Compression Engine. `MdqService` indexes Markdown files into an in-process SQLite DB via `Indexer` (`mcp/mdq/indexer.py`) and exposes 7 tools: `search_docs` / `get_chunk` / `outline` / `index_paths` / `refresh_index` / `stats` / `grep_docs`. Parser: `mcp/mdq/parser.py`. Search: `mcp/mdq/search.py`. Config: `config/mdq_mcp_server.toml`. Note: `mcp/mdq/server.py` is not yet implemented — the server entry point is `scripts/mdq_mcp_server.py` at the repo root. Details: `docs/04_mcp-mdq.md`.

### Local git MCP (eleventh server)

`mcp/git/server.py` (port 8014) exposes local git operations via `GitService` (`mcp/git/service.py`). Security: `allowed_repo_paths` (empty = deny all, fail-closed); `read_only = true` (default) blocks all write tools. Write tools (`git_add` / `git_commit` / `git_checkout` / `git_pull` / `git_push`) all support `dry_run`. `git_push` and `git_checkout` are registered in `approval_dry_run_tools`. Config: `config/git_mcp_server.toml`. Details: `docs/04_mcp-git.md`.

### MCP Transport Layer

`shared/tool_executor.py` (`ToolExecutor`) is transport-agnostic: callers pass only `(tool_name, args)`. `ToolRouteResolver` (`shared/route_resolver.py`) maps tool names to server keys — config-driven (`tool_names` field) first, then static prefix fallback. `LifecycleProtocol` (typing.Protocol in `shared/tool_executor.py`) defines `ensure_ready(server_key)` — implemented by `ServerLifecycleManager`. `HttpTransport` reads `McpServerConfig.auth_token` and sends `Authorization: Bearer` header when non-empty.

`shared/tool_constants.py` — canonical `frozenset` definitions for tool classification: `READ_TOOLS` / `WRITE_TOOLS` / `DELETE_TOOLS` / `RAG_TOOLS` / `CICD_TOOLS`. Imported by `route_resolver.py` (static routing), `tool_executor.py` (side-effect detection), and `repl_tool_exec.py` (risk classification). Update this file when adding or removing tool names — do not duplicate the sets elsewhere.

`StdioTransport(cmd, server_key, working_dir="", env=None)` — `working_dir` が非空のとき `start()` 前に `Path.is_dir()` を確認し存在しなければ `ValueError`。`env` が非空のとき `{**os.environ, **env}` を `start()` 時にマージ。

`ServerLifecycleManager` (`agent/lifecycle.py`) manages MCP server lifecycle. Three modes via `McpServerConfig.startup_mode`: `persistent` (stdio only, start at init) / `ondemand` (stdio only, double-checked locking with per-server `asyncio.Lock`) / `subprocess` (HTTP only, spawns uvicorn via `start_http_subprocess()` and polls `/health` up to `startup_timeout_sec` sec). `shutdown_all()` stops all stdio transports and terminates HTTP subprocess procs. Wired in `agent/factory.py:_init_tool_executor()`; `AgentREPL._start_subprocess_servers()` handles all startup at agent init.

Details: `docs/04_mcp-protocol.md` (§2.3 デュアル起動モード)

### LLM Communication

`shared/llm_client.py` (`LLMClient`) handles all LLM HTTP communication. SSE streaming uses `RobustSSEParser` (incremental UTF-8 decoder + heartbeat tracking + malformed frame retry). `stream()` reconnects up to `sse_reconnect_max` times on retryable errors with no partial output; when partial output exists it raises `LLMTransportError(partial_text=...)` and `agent/orchestrator.py` saves an `[INCOMPLETE]` assistant message. `LLMTransportError` is the canonical exception for all LLM transport failures — catch it explicitly in `agent/orchestrator.py` (do not use bare `except Exception` for LLM errors). `format_transport_error()` in `shared/tool_executor.py` produces the shared `{"summary", "detail"}` dict for both LLM and tool failures.

Details: `docs/06_ref-agent-llm.md`

### Config

All configuration in `AgentConfig` dataclass (`agent/config.py`); access via `ctx.cfg.field_name`. `McpServerConfig` dataclass lives in `shared/mcp_config.py` and is re-exported from `agent/config.py`; its key fields include `auth_token: str` (Bearer token; `""` = disabled), `role: str` (label in `/mcp status`), `startup_mode: str` (`"persistent"` / `"ondemand"` / `"subprocess"`), `startup_timeout_sec: int = 30` (subprocess /health poll timeout). No module-level constant imports from `agent.config` into other modules — path constants (`_CONFIG_DIR`, `_SCRIPTS_DIR`) must be imported inside the function body with `# noqa: PLC0415`. Hot-reloadable via `/reload`; when adding a hot-reloadable field to `AgentConfig`, also add a reload line to `_apply_config_params()` in `agent/commands/cmd_config.py`. When adding a module under `scripts/`, add a `cp` line to `deploy/deploy.sh`.

`shared/git_helper.py` — utility called by `agent/commands/cmd_context.py` to display branch/commit info in `/context` output. Uses GitPython with a lazy import and `search_parent_directories=True`; returns `None` silently outside a git repo.

Details: `docs/06_ref-agent-config.md`

### Ingestion Pipeline

Three-script pipeline: `rag/ingestion/crawler.py` → `rag/ingestion/chunk_splitter.py` → `rag/ingestion/ingester.py`. Satellite helpers: `crawler_utils.py` / `chunk_utils.py` / `chunk_english.py` / `chunk_japanese.py` (all under `rag/ingestion/`). Processed files move to `rag-src/registered/` (idempotency guard).

Details: `docs/03_ref-ingestion.md`

### Plugin Architecture

`shared/plugin_registry.py` provides three decorators: `@register_command` / `@register_tool` / `@register_pipeline_stage`. Plugin files live in `plugins/*.py`. Tool handler return type convention `tuple[str, bool]`: see `docs/06_common.md`. Test helper: `plugin_registry._reset_for_testing()`.

Details: `docs/06_ref-agent-repl.md`

## Skills (`skills/`)

Skills are registered as Claude Code slash commands in `.claude/commands/`. Invoke with `/skill-name [task]` or via `Skill("skill-name")`.

| Slash command | When to use |
|---|---|
| `/python-implementation` | feature / bug fix / new module / business logic |
| `/python-lint-typecheck` | lint / type error / suppression / CI failure |
| `/python-test-and-fix` | test add/repair / flaky / mutation |
| `/python-debug-root-cause` | root cause / log / profiling / tracing |
| `/python-issue-to-plan` | ticket → implementation plan |
| `/python-refactoring` | behavior-preserving restructure (6-phase) |
| `/mcp-server-add` | new MCP server (proactively activated) |
| `/deploy` | deploy to `/opt/llm/` (proactively activated) |

Each command reads its `skills/*/SKILL.md` guide automatically. The guide declares `Composes with` and `Called by` sections — use these to chain skills across multi-phase tasks.

See `routing.md` for task-to-skill and task-to-docs mapping.

Skill design principles (when creating or improving a SKILL): `skills/DESIGN.md`
