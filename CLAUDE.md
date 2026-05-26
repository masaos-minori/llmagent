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
4. Apply ripple-effect changes in the same pass: `routing.md`, `rules/env.md`, skill references, `docs/00_llm-implementation-guide.md`, `docs/06_common.md`
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

**mypy note:** `warn_unused_ignores = true` is set in `pyproject.toml`, so any `# type: ignore` on a line where mypy finds no error is itself an error. `tests/` is also covered by pre-commit's mypy run, so the same rule applies there.

**Test coverage:** Current unit tests are only `tests/test_plugin_registry.py` and `tests/test_rag_utils.py`. Core modules such as `agent_repl.py`, `orchestrator.py`, `tool_executor.py`, and `history_manager.py` have no tests. Any refactoring task that touches these modules must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting work.

## Architecture

→ 詳細は `routing.md` の "Docs → task mapping" から該当 `docs/` ファイルを参照。

### Agent REPL

`agent_repl.py` (`AgentREPL`) が全コンポーネントを `AgentContext` に注入し REPL ループを駆動する。ターンレベルのロジックは `Orchestrator` (`orchestrator.py`) に委譲。サテライトモジュール: `agent_repl_health.py` / `agent_repl_tool_exec.py` / `agent_repl_debug.py`。UI 出力は `CLIView` コールバックパターン経由 — いずれのライブラリモジュールも `print()` を直接呼ばない。

詳細: `docs/05_agent-impl.md` / `docs/06_ref-agent-repl.md`

### Shared State

`AgentContext` (`agent_context.py`) が per-session 可変状態と DI ハブを担当。サービス参照は `ctx.services.llm` 等 `ctx.services.<key>` でアクセスすること — property shim は存在しない。

詳細: `docs/06_ref-agent-context.md`

### Slash Commands

`CommandRegistry` (`agent_commands.py`) が `_SessionMixin` / `_McpMixin` / `_ConfigMixin` / `_ContextMixin` / `_RagMixin` / `_IngestMixin` の 6 ミックスインクラスにディスパッチ。

詳細: `docs/06_ref-agent-commands.md`

### RAG Pipeline

MQE → vector search (`chunks_vec`) → FTS5 (`chunks_fts`) → RRF → rerank のパイプライン。`agent_rag.py` (`RagPipeline`) がオーケストレーション。補助層: `rag_types.py` / `rag_repository.py` / `rag_llm.py`。共通型 `RagHit` / `LLMMessage` の定義は `docs/06_common.md` 参照。

詳細: `docs/06_ref-rag.md`

### DB Layer

`sqlite_helper.py` — 接続管理 (WAL / busy_timeout)。`db_maintenance.py` — 運用ポリシー (`/db` コマンド)。`db_store.py` — Protocol 抽象。`tool_result_store.py` — ツール結果永続化 (`/tool show <id>`)。

詳細: `docs/06_ref-sqlite.md`

### MCP Servers

7 本のサーバが models / service / server の 3 層構造で実装。共通基底: `mcp_server.py`。ツールルーティング・TTL キャッシュ: `tool_executor.py`。共通プロトコル仕様 (`/v1/call_tool` フォーマット) は `docs/06_common.md` 参照。

詳細: `docs/04_mcp-servers.md`

### Config

全設定値は `AgentConfig` dataclass (`agent_config.py`) に集約。`ctx.cfg.field_name` でアクセス。モジュールレベル定数への import は禁止。`/reload` でホットリロード可能。新規 `scripts/*.py` モジュール追加時は `deploy/deploy.sh` にも `cp` 行を追加すること。

詳細: `docs/06_ref-agent-config.md`

### Ingestion Pipeline

`web_crawler.py` → `chunk_splitter.py` → `rag_ingester.py` の 3 スクリプトによるファイルパイプライン。`pipeline_utils.py` / `rag_utils.py` が共有ユーティリティを提供。処理済みファイルは `rag-src/registered/` へ移動 (冪等性ガード)。

詳細: `docs/03_ref-ingestion.md`

### Plugin Architecture

`plugin_registry.py` が `@register_command` / `@register_tool` / `@register_pipeline_stage` の 3 デコレータを提供。プラグインファイルは `plugins/*.py`。ツールハンドラの戻り値規約 `tuple[str, bool]` は `docs/06_common.md` 参照。テストヘルパー: `plugin_registry._reset_for_testing()`。

詳細: `docs/06_ref-agent-repl.md`

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
