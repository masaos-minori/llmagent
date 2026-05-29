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
PYTHONPATH=scripts lint-imports                      # architecture boundary check
pytest tests/test_<module>.py -v                     # single module
pytest -v                                            # full suite

# coverage gate — new/changed lines must hit 90%
coverage run -m pytest tests/ && coverage xml
diff-cover coverage.xml --compare-branch=main --fail-under=90

pre-commit run --all-files             # full gate (run before commit)

# CST-based bulk refactoring (bowler v0.9.0 confirmed installed)
bowler rename_func old_name new_name --write --dry-run   # always dry-run first
```

Full validation sequence: `rules/toolchain.md`

**Validation policy:** Run `ruff`, `mypy`, `pytest`, `sed`, and `source .venv/bin/activate` directly without asking the user for confirmation first. These are always safe to execute.

**mypy note:** `warn_unused_ignores = true` is set in `pyproject.toml`, so any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run, so the same rule applies there.

**Key library choices:** Use `orjson` (not stdlib `json`) for all JSON serialization — `orjson.dumps()` returns `bytes`; call `.decode()` when a `str` is required; use `option=orjson.OPT_SORT_KEYS` / `OPT_INDENT_2` instead of `sort_keys=True` / `indent=2`. Use `httpx` (not `requests`) for HTTP — `httpx.Client` for sync, `httpx.AsyncClient` for async.

**Test coverage:** Unit tests exist for `agent/commands/cmd_config.py`, `agent/session.py`, `agent/repl_tool_exec.py`, `agent/cli_view.py`, `mcp/file/delete_service.py`, `mcp/file/write_service.py`, `mcp/github/service.py`, `agent/history.py`, `shared/llm_client.py`, `agent/memory/layer.py`, `agent/memory/store.py`, `agent/orchestrator.py`, `shared/otel_tracer.py`, `shared/plugin_registry.py`, `rag/utils.py`, `mcp/shell/service.py`, `mcp/rag_pipeline/service.py`, `rag/pipeline.py`. Core modules `agent/repl.py` and `shared/tool_executor.py` have no tests. Any refactoring task that touches these modules must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting work.

## Architecture

→ For details, find the relevant `docs/` file via the "Docs → task mapping" table in `routing.md`.

### Agent REPL

`agent/repl.py` (`AgentREPL`) injects all components into `AgentContext` and drives the REPL loop. Turn-level logic (RAG → compression → LLM loop → tool dispatch) is delegated to `Orchestrator` (`agent/orchestrator.py`). Satellite modules: `agent/repl_health.py` / `agent/repl_tool_exec.py` (risk-based tool approval, audit logging) / `agent/repl_debug.py`. UI output goes through `CLIView` callbacks — no library module calls `print()` directly.

Details: `docs/05_agent-impl.md` / `docs/06_ref-agent-repl.md`

### Shared State

`AgentContext` (`agent/context.py`) owns per-session mutable state and acts as the DI hub. All services via `ctx.services.<key>` (no property shims); `ServiceContainer.audit_logger: Logger | None` provides structured audit logging; `ServiceContainer.memory: MemoryLayer | None` is the 4-tier memory facade (enabled by `use_memory_layer=True`). Per-turn trace IDs and token stats managed by `Orchestrator`. Memory implementation: `agent/memory/store.py` (SQLite CRUD + vec0 KNN) / `agent/memory/layer.py` (high-level facade). OTel tracing: `shared/otel_tracer.py` (`build_tracer()` — private `TracerProvider`, no global state pollution).

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

Seven servers in models/service/server layers under `mcp/`. Common base: `mcp/server.py`; protocol spec: `docs/06_common.md`. The seventh server (`rag-pipeline-mcp`, port 8010) exposes the RAG pipeline via `mcp/rag_pipeline/server.py` / `mcp/rag_pipeline/service.py` / `mcp/rag_pipeline/models.py`; see `docs/04_mcp-rag.md`. When `_MCP_TOOLS` exceeds 400 lines, extract to `{server}/tools.py` and import via `from mcp.{server}.tools import _MCP_TOOLS`. Destructive operations (write/delete/move) support a `dry_run: bool = Field(default=False)` parameter — when `True` the service returns preview info without side effects; the `check_approval()` flow in `agent/repl_tool_exec.py` injects `dry_run=True` automatically for tools listed in `approval_dry_run_tools`.

Details: `docs/04_mcp-servers.md`

### LLM Communication

`shared/llm_client.py` (`LLMClient`) handles all LLM HTTP communication. SSE streaming uses `RobustSSEParser` (incremental UTF-8 decoder + heartbeat tracking + malformed frame retry). `stream()` reconnects up to `sse_reconnect_max` times on retryable errors with no partial output; when partial output exists it raises `LLMTransportError(partial_text=...)` and `agent/orchestrator.py` saves an `[INCOMPLETE]` assistant message. `LLMTransportError` is the canonical exception for all LLM transport failures — catch it explicitly in `agent/orchestrator.py` (do not use bare `except Exception` for LLM errors). `format_transport_error()` in `shared/tool_executor.py` produces the shared `{"summary", "detail"}` dict for both LLM and tool failures.

Details: `docs/06_ref-agent-llm.md`

### Config

All configuration in `AgentConfig` dataclass (`agent/config.py`); access via `ctx.cfg.field_name`. `McpServerConfig` dataclass lives in `shared/mcp_config.py` and is re-exported from `agent/config.py`. No module-level constant imports from `agent.config` into other modules — path constants (`_CONFIG_DIR`, `_SCRIPTS_DIR`) must be imported inside the function body with `# noqa: PLC0415`. Hot-reloadable via `/reload`; when adding a hot-reloadable field to `AgentConfig`, also add a reload line to `_apply_config_params()` in `agent/commands/cmd_config.py`. When adding a module under `scripts/`, add a `cp` line to `deploy/deploy.sh`.

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
| `/python-implementation` | Adding features, changing business logic, creating modules, writing production Python |
| `/python-lint-typecheck` | Fixing lint errors, type errors, suppression governance, CI failures |
| `/python-test-and-fix` | Adding/repairing tests, reproducing bugs, flaky detection, mutation testing |
| `/python-debug-root-cause` | Root cause analysis, log inspection, profiling, tracing, service debugging |
| `/python-issue-to-plan` | Converting a ticket or vague task into a concrete implementation plan |
| `/python-refactoring` | Refactoring modules — 6-phase tool chain (dependency mapping → behavior lock → CST transform → semantic validation → incremental migration → CI gate) |
| `/mcp-server-add` | Adding a new MCP server to the project (proactively activated) |
| `/deploy` | Deploying changes to the production environment at `/opt/llm/` (proactively activated) |

Each command reads its `skills/*/SKILL.md` guide automatically. The guide declares `Composes with` and `Called by` sections — use these to chain skills across multi-phase tasks.

See `routing.md` for task-to-skill and task-to-docs mapping.

Skill design principles (when creating or improving a SKILL): `skills/DESIGN.md`
