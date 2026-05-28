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
pytest tests/test_<module>.py -v                     # single module
pytest -v                                            # full suite

pre-commit run --all-files             # full gate (run before commit)

# CST-based bulk refactoring (bowler v0.9.0 confirmed installed)
bowler rename_func old_name new_name --write --dry-run   # always dry-run first
```

Full validation sequence: `rules/toolchain.md`

**Validation policy:** Run `ruff`, `mypy`, and `pytest` directly without asking the user for confirmation first. These are always safe to execute.

**mypy note:** `warn_unused_ignores = true` is set in `pyproject.toml`, so any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run, so the same rule applies there.

**Key library choices:** Use `orjson` (not stdlib `json`) for all JSON serialization — `orjson.dumps()` returns `bytes`; call `.decode()` when a `str` is required; use `option=orjson.OPT_SORT_KEYS` / `OPT_INDENT_2` instead of `sort_keys=True` / `indent=2`. Use `httpx` (not `requests`) for HTTP — `httpx.Client` for sync, `httpx.AsyncClient` for async.

**Test coverage:** Unit tests exist for `agent_session.py`, `cli_view.py`, `history_manager.py`, `memory_layer.py`, `memory_store.py`, `otel_tracer.py`, `plugin_registry.py`, `rag_utils.py`. Core modules `agent_repl.py`, `orchestrator.py`, `tool_executor.py` have no tests. Any refactoring task that touches these modules must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting work.

## Architecture

→ For details, find the relevant `docs/` file via the "Docs → task mapping" table in `routing.md`.

### Agent REPL

`agent_repl.py` (`AgentREPL`) injects all components into `AgentContext` and drives the REPL loop. Turn-level logic (RAG → compression → LLM loop → tool dispatch) is delegated to `Orchestrator` (`orchestrator.py`). Satellite modules: `agent_repl_health.py` / `agent_repl_tool_exec.py` / `agent_repl_debug.py`. UI output goes through `CLIView` callbacks — no library module calls `print()` directly.

Details: `docs/05_agent-impl.md` / `docs/06_ref-agent-repl.md`

### Shared State

`AgentContext` (`agent_context.py`) owns per-session mutable state and acts as the DI hub. All services via `ctx.services.<key>` (no property shims); `ServiceContainer.audit_logger: Logger | None` provides structured audit logging; `ServiceContainer.memory: MemoryLayer | None` is the 4-tier memory facade (enabled by `use_memory_layer=True`). Per-turn trace IDs and token stats managed by `Orchestrator`. Memory implementation: `memory_store.py` (SQLite CRUD + vec0 KNN) / `memory_layer.py` (high-level facade). OTel tracing: `otel_tracer.py` (`build_tracer()` — private `TracerProvider`, no global state pollution).

Details: `docs/06_ref-agent-context.md`

### Slash Commands

`CommandRegistry` (`agent_commands.py`) dispatches to six mixin classes: `_SessionMixin` / `_McpMixin` / `_ConfigMixin` / `_ContextMixin` / `_RagMixin` / `_IngestMixin`.

Details: `docs/06_ref-agent-commands.md`

### RAG Pipeline

Pipeline: MQE → vector search (`chunks_vec`) → FTS5 (`chunks_fts`) → RRF → rerank. `agent_rag.py` (`RagPipeline`) orchestrates the pipeline. Support layers: `rag_types.py` / `rag_repository.py` / `rag_llm.py`. Common types `RagHit` / `LLMMessage` are defined in `docs/06_common.md`.

Details: `docs/06_ref-rag.md`

### DB Layer

`sqlite_helper.py` — connection management (WAL / busy_timeout). `db_maintenance.py` — operational policies (`/db` command). `db_store.py` — Protocol abstraction. `tool_result_store.py` — tool result persistence (`/tool show <id>`).

Details: `docs/06_ref-sqlite.md`

### MCP Servers

Seven servers in models/service/server layers. Common base: `mcp_server.py`; protocol spec: `docs/06_common.md`. When `_MCP_TOOLS` exceeds 400 lines, extract to `{server}_tools.py` and import via `from {server}_tools import _MCP_TOOLS`.

Details: `docs/04_mcp-servers.md`

### Config

All configuration in `AgentConfig` dataclass (`agent_config.py`); access via `ctx.cfg.field_name`. No module-level constant imports from `agent_config` into other modules — path constants (`_CONFIG_DIR`, `_SCRIPTS_DIR`) must be imported inside the function body with `# noqa: PLC0415`. Hot-reloadable via `/reload`; when adding a hot-reloadable field to `AgentConfig`, also add a reload line to `_apply_config_params()` in `agent_cmd_config.py`. When adding a `scripts/*.py` module, add a `cp` line to `deploy/deploy.sh`.

`git_helper.py` — utility called by `agent_cmd_context.py` to display branch/commit info in `/context` output. Uses GitPython with a lazy import and `search_parent_directories=True`; returns `None` silently outside a git repo.

Details: `docs/06_ref-agent-config.md`

### Ingestion Pipeline

Three-script pipeline: `web_crawler.py` → `chunk_splitter.py` → `rag_ingester.py`. Satellite helpers: `crawler_utils.py` / `chunk_utils.py` / `chunk_english.py` / `chunk_japanese.py`. Processed files move to `rag-src/registered/` (idempotency guard).

Details: `docs/03_ref-ingestion.md`

### Plugin Architecture

`plugin_registry.py` provides three decorators: `@register_command` / `@register_tool` / `@register_pipeline_stage`. Plugin files live in `plugins/*.py`. Tool handler return type convention `tuple[str, bool]`: see `docs/06_common.md`. Test helper: `plugin_registry._reset_for_testing()`.

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
