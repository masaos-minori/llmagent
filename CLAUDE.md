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

pytest tests/test_<module>.py -v   # single module
pytest -v                           # full suite

ruff check scripts/ tests/ && mypy scripts/ tests/   # lint + type check (pre-commit runs both)
pre-commit run --all-files             # full gate (run before commit)

# CST-based bulk refactoring (bowler v0.9.0 confirmed installed)
bowler rename_func old_name new_name --write --dry-run   # always dry-run first
```

Full validation sequence: `rules/toolchain.md`

**mypy note:** `warn_unused_ignores = true` is set in `pyproject.toml`, so any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run, so the same rule applies there.

**Test coverage:** Unit tests exist for `agent_session.py`, `cli_view.py`, `history_manager.py`, `plugin_registry.py`, `rag_utils.py`. Core modules `agent_repl.py`, `orchestrator.py`, `tool_executor.py` have no tests. Any refactoring task that touches these modules must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting work.

## Architecture

→ For details, find the relevant `docs/` file via the "Docs → task mapping" table in `routing.md`.

### Agent REPL

`agent_repl.py` (`AgentREPL`) injects all components into `AgentContext` and drives the REPL loop. Turn-level logic is delegated to `Orchestrator` (`orchestrator.py`). Satellite modules: `agent_repl_health.py` / `agent_repl_tool_exec.py` / `agent_repl_debug.py`. UI output goes through `CLIView` callbacks — no library module calls `print()` directly.

Details: `docs/05_agent-impl.md` / `docs/06_ref-agent-repl.md`

### Shared State

`AgentContext` (`agent_context.py`) owns per-session mutable state and acts as the DI hub. Access services via `ctx.services.llm` etc. (`ctx.services.<key>`) — no property shims exist.

`ServiceContainer` holds all injected service references including `audit_logger: Logger | None` (initialized by `AgentREPL._init_components()`).

Per-turn trace IDs are set and cleared by `Orchestrator.handle_turn()`:
- `ctx.current_turn_id` — UUID4, set at `handle_turn()` entry; cleared in `finally`
- `ctx.current_rag_query_id` — UUID4, set in `_augment_with_rag()`; `None` when RAG is skipped
- `ctx.stat_input_tokens` / `ctx.stat_output_tokens` — `int | None`; `None` = LLM endpoint did not return `usage`

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

Seven servers implemented in a three-layer structure: models / service / server. Common base: `mcp_server.py`. Tool routing and TTL cache: `tool_executor.py`. Common protocol spec (`/v1/call_tool` format): `docs/06_common.md`.

When a `_MCP_TOOLS` list exceeds 400 lines, extract it to `{server}_tools.py` (e.g. `github_mcp_tools.py`, `file_read_mcp_tools.py`) and import it via `from {server}_tools import _MCP_TOOLS`.

Details: `docs/04_mcp-servers.md`

### Config

All configuration values are consolidated in the `AgentConfig` dataclass (`agent_config.py`). Access via `ctx.cfg.field_name`. Importing module-level constants is prohibited. Hot-reloadable via `/reload`. When adding a new `scripts/*.py` module, also add a `cp` line to `deploy/deploy.sh`.

Observability-related fields: `audit_log_file` (default `/opt/llm/logs/audit.log`) and `structured_log` (default `False`). The audit logger is constructed with `structured_log=True` unconditionally to write JSON-lines; the main agent logger uses `structured_log` from config.

Details: `docs/06_ref-agent-config.md`

### Ingestion Pipeline

Three-script file pipeline: `web_crawler.py` → `chunk_splitter.py` → `rag_ingester.py`. `pipeline_utils.py` / `rag_utils.py` provide shared utilities. Processed files are moved to `rag-src/registered/` (idempotency guard).

Satellite modules (extracted from their parents):
- `crawler_utils.py` — URL helpers, text extraction, language detection, target URL parsing (pure functions; extracted from `web_crawler.py`)
- `chunk_utils.py` — buffer accumulation helpers `start_next_buf` / `merge_text_items`
- `chunk_english.py` — `ChunkEnglishMixin` (4 English chunker methods)
- `chunk_japanese.py` — `ChunkJapaneseMixin` (4 Sudachi morphological-analysis-based Japanese chunker methods)

`ChunkSplitter(ChunkEnglishMixin, ChunkJapaneseMixin)` holds only orchestration and file I/O.

Details: `docs/03_ref-ingestion.md`

### Plugin Architecture

`plugin_registry.py` provides three decorators: `@register_command` / `@register_tool` / `@register_pipeline_stage`. Plugin files live in `plugins/*.py`. Tool handler return type convention `tuple[str, bool]`: see `docs/06_common.md`. Test helper: `plugin_registry._reset_for_testing()`.

Details: `docs/06_ref-agent-repl.md`

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

Skill design principles (when creating or improving a SKILL): `skills/DESIGN.md`
