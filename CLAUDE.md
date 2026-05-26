# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Global Rules

- Read only necessary skills and docs (minimal context)
- **Always read `routing.md` immediately after this file** — it maps task type → skills to load AND docs to load
- Do NOT load all `docs/*.md`; load only what `routing.md`'s "Docs → task mapping" specifies
- **Do not proceed speculatively on code generation, documentation, or any other task — stop and ask when anything is unclear.**

## Context Loader Pattern

```
Task → routing.md → Minimal Skills + Shared Rules → Relevant docs → Execution
```

Always-load alongside any skill:
- `rules/coding.md` — coding conventions and prohibited patterns
- `rules/toolchain.md` — validation sequence (format → lint → type → arch → security → test → coverage)

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

1. Group sections/functions by responsibility and record the split proposal in `04_split_plan.md`
2. Review the plan before touching any file
3. After splitting, convert the original file to an index (link list) or remove its content
4. Apply ripple-effect changes in the same pass: `routing.md`, `rules/env.md`, skill references, `docs/00_llm-implementation-guide.md`
5. For code files, confirm `ruff` / `mypy` / `pytest` pass before closing the task

## Target environment

- **OS:** Gentoo Linux + OpenRC
- **Python:** 3.13 (production venv: `/opt/llm/venv/`; dev venv: `.venv/` managed by uv)
- **DB:** SQLite + `sqlite-vec` extension at `/opt/llm/sqlite-vec/vec0.so`

Full environment details, schema, config reference, and service ports: `rules/env.md`

## Development

```bash
uv sync --dev --system-certs    # create .venv/ and install all deps
source .venv/bin/activate       # activate dev venv

pytest tests/test_<module>.py -v   # single module
pytest -v                           # full suite

ruff check scripts/ tests/ && mypy scripts/ tests/   # lint + type check (pre-commit runs both)
pre-commit run --all-files             # full gate (run before commit)

# CST-based bulk refactoring (bowler v0.9.0 confirmed installed)
bowler rename_func old_name new_name --write --dry-run   # always dry-run first
```

Full validation sequence: `rules/toolchain.md`

**mypy 注意:** `pyproject.toml` に `warn_unused_ignores = true` が設定されているため、mypy がエラーを検出しない行への `# type: ignore` はそれ自体がエラーになる。tests/ も pre-commit の mypy 対象なので同様に適用される。

**テストカバレッジ:** 現状のユニットテストは `tests/test_plugin_registry.py` と `tests/test_rag_utils.py` のみ。`agent_repl.py` / `tool_executor.py` / `history_manager.py` 等コア層はテストなし。これらを変更するリファクタリングタスクでは、着手前に behavior lock テスト (`python-test-and-fix` スキル) を取ること。

## Architecture

### Agent REPL

Entry point: `agent.py` → `asyncio.run(AgentREPL().run())`.

`AgentREPL` (`agent_repl.py`) wires all components into `AgentContext` via `_init_components()` and drives the input/command dispatch loop in `_repl_loop()`. MCP subprocess lifecycle, health checks, and watchdog are also owned here. Turn-level logic is delegated to `Orchestrator`.

`Orchestrator` (`orchestrator.py`) handles one conversation turn end-to-end: RAG augmentation → history compression → LLM streaming loop → tool dispatch. Owns `_run_turn()` with duplicate tool call detection (`tool_dedup_max_repeats`) and consecutive all-error guard (`tool_error_max_consecutive`). All terminal output is routed via callbacks (`on_turn_start`, `on_turn_end`, `on_error`) — no `print()` in this module.

Heavy subsystems live in satellite modules:

- `agent_repl_health.py` — MCP health checks and watchdog loop
- `agent_repl_tool_exec.py` — tool call approval and parallel execution
- `agent_repl_debug.py` — RAG debug printers (pure functions, no side effects)

**CLIView callback pattern**: UI output from library modules is routed via callbacks injected in `_init_components()`. `LLMClient` receives `on_token=self._view.write_token`; `HistoryManager` receives `on_compress=self._view.write_compress_notice`; `Orchestrator` receives `on_turn_start`, `on_turn_end`, `on_error`. None of these modules calls `print()` directly. `CLIView` owns all terminal output APIs.

Key library modules (all injected via `_init_components()`):

- `llm_client.py` — SSE streaming, retry with exponential backoff, payload builder; receives `on_token` callback
- `history_manager.py` — compresses old turns via LLM summary when context char limit is exceeded; receives `on_compress` callback
- `agent_session.py` — SQLite-backed session/message persistence (`ctx.session`); `save(role, content)` appends to `messages` table
- `cli_view.py` — readline setup, multiline continuation, RAG progress display; owns all terminal output APIs


### Shared State

`AgentContext` (`agent_context.py`) is the DI hub — per-session mutable state and config live here. Both `AgentREPL` and `CommandRegistry` operate on the same instance.

Two internal namespaces:
- `ctx.services` (`ServiceContainer`) — service references: `http`, `llm`, `tools`, `hist_mgr`, `rag`, `stdio_procs`. All None until `_init_components()` runs. **Access always via `ctx.services.llm` etc.; no property shims exist.**
- Flat fields on `AgentContext` — conversation state (`history`, `llm_url`, `debug_mode`, `plan_mode`), session stats (`stat_*`), `cfg`, `session`, `tool_result_store` (`ToolResultStore` instance — persists full tool output to the `tool_results` SQLite table; `/tool show <id>` retrieves by DB id).

### Slash Commands

`CommandRegistry` (`agent_commands.py`) delegates to six mixin classes, each in its own file:

| File | Mixin | Commands |
|---|---|---|
| `agent_cmd_session.py` | `_SessionMixin` | `/session` |
| `agent_cmd_mcp.py` | `_McpMixin` | `/mcp` |
| `agent_cmd_config.py` | `_ConfigMixin` | `/config`, `/stats`, `/set`, `/reload` |
| `agent_cmd_context.py` | `_ContextMixin` | `/context`, `/clear`, `/undo`, `/history`, `/system`, `/db` |
| `agent_cmd_rag.py` | `_RagMixin` | `/rag`, `/tool`, `/note`, `/plan`, `/debug` |
| `agent_cmd_ingest.py` | `_IngestMixin` | `/ingest`, `/export`, `/compact` |

### RAG Pipeline

`agent_rag.py` contains only `RagPipeline`. Supporting layers are split:

- `rag_types.py` — `RagHit` and `LLMMessage` TypedDicts (lightweight, no heavy imports)
- `rag_repository.py` — `RagRepository`, `RagScorer`, `SemanticCache`, FTS helpers, standalone search functions
- `rag_llm.py` — `RagLLM`, `get_embedding()`, `summarize_tool_result()`

Pipeline flow: MQE → vector search (`chunks_vec`) → FTS5 (`chunks_fts`) → RRF → rerank. Context is injected into the system prompt before each LLM turn.

### DB Layer

`sqlite_helper.py` — `SQLiteHelper` connection manager. All connections apply WAL / `synchronous=NORMAL` / `busy_timeout` unconditionally via `_apply_connection_pragmas()`. Use `begin_immediate()` / `begin_exclusive()` context managers for multi-statement write transactions. `health_check()` returns journal mode, integrity, and page stats. `checkpoint(mode)` flushes the WAL; `vacuum()` rebuilds the DB file in place.

`db_maintenance.py` — operational policy layer above `SQLiteHelper`. Provides `checkpoint_wal()`, `vacuum_db()`, `purge_old_sessions()`, `rotate_db()`, `recover_corruption()`, and `RetentionConfig` (session retention policy). All maintenance parameters (`sqlite_wal_checkpoint_mode`, `sqlite_retention_max_sessions`, `sqlite_retention_max_age_days`, `sqlite_archive_dir`) are read from `config/common.json`. Exposed via `/db health|checkpoint|vacuum|purge|recover` slash commands in `agent_cmd_context.py`.

`db_store.py` — abstract `Protocol` classes (`VectorStore`, `DocumentStore`, `SessionStore`) with SQLite-backed implementations (`SQLiteVectorStore`, `SQLiteDocumentStore`, `SQLiteSessionStore`). Also exports `validate_embedding_blob()` and `EMBEDDING_DIMS / EMBEDDING_BYTES` constants. The existing `RagRepository` in `rag_repository.py` structurally satisfies these Protocols.

`tool_result_store.py` — `ToolResultStore` persists full tool execution output to the `tool_results` table. LLM history receives only summaries/truncations; the full text is stored with a row id so `/tool show <id>` can retrieve it. Falls back silently on DB errors so the REPL continues without a DB.

Schema (`create_schema.py`): `chunks_vec_ad` trigger keeps `chunks_vec` in sync when `chunks` rows are deleted. `tool_results` table stores per-session tool output with `session_id`, `turn`, `tool_name`, `args_json`, `full_text`, `summary`, `is_error`.

### MCP Servers

各 MCP サーバは models / service / server の 3 層構成を踏襲する。共通セキュリティヘルパー (`resolve_safe`, `require_file`, `require_dir` 等) は `file_mcp_common.py` に集約。

| Server | Port | Models | Service | Server |
|---|---|---|---|---|
| file-read-mcp (読み取り専用) | 8005 | `file_read_mcp_models.py` | `file_read_mcp_service.py` | `file_read_mcp_server.py` |
| file-write-mcp (作成・編集・移動) | 8007 | `file_write_mcp_models.py` | `file_write_mcp_service.py` | `file_write_mcp_server.py` |
| file-delete-mcp (削除 + audit log) | 8008 | `file_delete_mcp_models.py` | `file_delete_mcp_service.py` | `file_delete_mcp_server.py` |
| shell-mcp (サンドボックスコマンド実行) | 8009 | `shell_mcp_models.py` | `shell_mcp_service.py` | `shell_mcp_server.py` |
| github-mcp | 8006 | `github_mcp_models.py` | `github_mcp_service.py` | `github_mcp_server.py` |
| web-search-mcp | 8004 | — | — | `web_search_mcp_server.py` |

**共通基盤**: `mcp_server.py` — 全 MCP サーバが継承するベースクラス。FastAPI アプリ起動・`/v1/call_tool` エンドポイント・`/health` を提供。`mcp_models.py` — `/v1/call_tool` の `CallToolRequest` / `CallToolResponse` Pydantic モデル。`formatters.py` — LLM context 向けとターミナル向けの 2 系統フォーマット関数。

**ツールルーティング** (`tool_executor.py`): モジュールレベルの `_READ_TOOLS` / `_WRITE_TOOLS` / `_DELETE_TOOLS` frozenset で振り分け。`shell_run` → `shell`、`search_web` → `web_search`、`github_*` → `github`。`HttpTransport` (HTTP/JSON-RPC) または `StdioTransport` (subprocess `--stdio`) で実行。結果は TTL キャッシュ。

**MCP インストーラ**: `mcp_installer.py` — `/mcp install <name>` から呼び出されるスケルトン生成ツール。`scripts/<name>_mcp_server.py` / `config/<name>_mcp_server.json` / `init.d/<name>` / `conf.d/<name>` を自動生成する。ポート 8007 以降を自動採番し、予約済みポート (8001–8006) への衝突を防ぐ。

**shell-mcp セキュリティ仕様**: `argv[0]` をホワイトリスト照合 (`shlex.split` → basename)、`shell=False` 固定、`start_new_session=True` でプロセスグループ管理、`resource.setrlimit()` で CPU/メモリ/fd/プロセス数を制限、タイムアウト時は SIGTERM → SIGKILL の順でグループ終了。全実行を `/opt/llm/logs/shell_audit.log` に記録。

**file-delete-mcp**: 全削除操作を `/opt/llm/logs/delete_audit.log` に記録。`agent.json` の `require_approval_tools` に `delete_file` / `delete_directory` / `shell_run` を登録し、実行前に y/N 確認を強制。

### Config

`config/agent.json`: `mcp_servers` drives transport selection; `use_mqe/use_search/use_rrf/use_rerank` toggle RAG steps; `masked_fields` redacts sensitive tool args from logs.

All config values (URLs, `tool_definitions`, `system_prompts`, RAG flags, LLM params, etc.) live exclusively in the `AgentConfig` dataclass (`agent_config.py`). There are no module-level constants; every field is hot-reloadable via `/reload`. Use `ctx.cfg.field_name` — never import constants from `agent_config`.

Key tool-result budget fields: `tool_result_max_llm_chars` (per-result truncation limit) and `tool_results_turn_max_chars` (per-turn total budget; results exceeding the budget are replaced with a `/tool show <id>` retrieval hint in LLM history).

Tool loop guard fields: `tool_dedup_max_repeats` (同一 tool+args の繰り返しをこの回数でブロック) and `tool_error_max_consecutive` (全ツールがエラーを返したターンが連続してこの回数に達したら打ち切り; 0 で無効).

`config/github_mcp_server.json`: `protected_branches` (fnmatch glob のリスト; 該当 branch への write 操作を 403 でブロック), `allow_force_push` (false のとき rebase merge を禁止), `require_pr_review` (将来拡張用).

When adding a new `scripts/*.py` module, also add a `cp` line to `deploy/deploy.sh`.

### Ingestion Pipeline

One-shot scripts for document collection and RAG indexing (run in sequence, not part of the REPL):

```
web_crawler.py → chunk_splitter.py → rag_ingester.py
```

- `web_crawler.py` — fetches URLs listed in `config/rag_pipeline.json`; saves raw text under `rag-src/`
- `chunk_splitter.py` — splits raw text into fixed-size chunks; writes JSON files under `rag-src/chunk/`
- `rag_ingester.py` — embeds chunks via the embed-llm service and upserts into `chunks` / `chunks_vec` / `chunks_fts`
- `pipeline_utils.py` — shared I/O: JSON file reading, source file enumeration, idempotency sentinel check
- `rag_utils.py` — shared text utilities (unicode normalization, tokenization) used by both ingestion and `agent_rag.py`

Processed files are moved to `rag-src/registered/` as an idempotency guard; re-running is safe.

### Plugin Architecture

`plugin_registry.py` — central registry for extending the agent without modifying core files. Provides three decorators:

| Decorator | Extension point | Handler signature |
|---|---|---|
| `@register_command("/name", prefix=False)` | New slash command | `async def fn(ctx: AgentContext, args: str) -> None` |
| `@register_tool("tool_name")` | Local Python tool (bypasses MCP) | `async def fn(args: dict) -> tuple[str, bool]` |
| `@register_pipeline_stage(when="post")` | Post-rerank RAG hook | `async def fn(hits: list[RagHit], query: str) -> list[RagHit]` |

Plugin files live in `plugins/*.py`. `AgentREPL._init_components()` calls `plugin_registry.load_plugins(plugins/)` at startup; each file's decorators run at import time. Broken plugin files are logged and skipped (fail-open).

Execution order: plugin tools are checked before MCP routing in `ToolExecutor.execute()`; plugin commands are checked after built-in commands in `CommandRegistry.dispatch()`; pipeline stages run after cross-encoder reranking in `RagPipeline.run()`.

Test helper: `plugin_registry._reset_for_testing()` clears all registries — call it from pytest fixtures to prevent cross-test pollution. See `plugins/example.py` for a working template.

### Documentation layout

- `docs/06_ref-agent.md` — index only; sub-files cover each module (`06_ref-agent-session.md`, `06_ref-agent-repl.md`, `06_ref-agent-config.md`, `06_ref-agent-context.md`, `06_ref-agent-view.md`, `06_ref-agent-commands.md`, `06_ref-agent-llm.md`, `06_ref-agent-history.md`)
- `docs/06_ref-rag.md` — RAG pipeline internals (`rag_types`, `rag_repository`, `rag_llm`, `agent_rag`)
- `docs/06_ref-mcp.md` — MCP server module APIs
- `docs/06_ref-infra.md` — config, DB, logger, formatters
- `docs/05_agent-impl.md` — REPL pipeline internals

## Skills (`skills/`)

| Skill | Trigger |
|---|---|
| `skills/python-implementation/` | Adding features, changing business logic, creating modules, writing production Python |
| `skills/python-lint-typecheck/` | Fixing lint errors, type errors, suppression governance, CI failures |
| `skills/python-test-and-fix/` | Adding/repairing tests, reproducing bugs, flaky detection, mutation testing |
| `skills/python-debug-root-cause/` | Root cause analysis, log inspection, profiling, tracing, service debugging |
| `skills/python-issue-to-plan/` | Converting a ticket or vague task into a concrete implementation plan |
| `skills/python-refactoring/` | Refactoring modules — 6-phase tool chain (dependency mapping → behavior lock → CST transform → semantic validation → incremental migration → CI gate) |
| `skills/mcp-server-add/` | Adding a new MCP server to the project (proactively activated) |
| `skills/deploy/` | Deploying changes to the production environment at `/opt/llm/` (proactively activated) |

Each skill file (`SKILL.md`) declares `Composes with` and `Called by` sections — read them to determine chaining order when a task spans multiple skills.

See `routing.md` for task-to-skill and task-to-docs mapping.

## Skill Design Principles

**Essential definition:** A SKILL is a formalized, re-executable encoding of a work procedure.

**Design principles** — every SKILL must satisfy all of these:

| Principle | What it means |
|---|---|
| Write the minimum necessary | Include only what cannot be inferred from the code or context; omit obvious steps |
| Spell out the procedure | List concrete, ordered steps — no ambiguous verbs like "handle" or "deal with" |
| Reduce judgment | Pre-decide branching logic so the executor never has to improvise |
| Define the deliverable | State exactly what artifact or state change marks the SKILL complete |
| Include verification | Provide a concrete check command or assertion that confirms success |
| Compose with other SKILLs | Design so the SKILL can be chained; avoid re-encoding what another SKILL already covers |
| Optimize for token efficiency | Front-load critical rules; cut prose that does not constrain behavior |
| Design to prevent failure | Anticipate common error modes and encode the guard or recovery inline |

**Evaluation criteria** — a SKILL is good when it:

- Runs autonomously end-to-end without human intervention
- Produces the same result on every execution (idempotent)
- Requires no judgment calls from the executor beyond reading the input
- Can be improved incrementally without breaking existing callers
- Contains an `## Improvement feedback` section — after running, update that section when a phase gate was wrong or a recovery path was missing
