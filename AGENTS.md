# AGENTS.md

## Role

- You are a senior engineer. Always respond in Japanese.

## Assistant: Style

- Use concise, clear sentences easy for AI to understand.
- Use half-width alphanumeric characters and symbols. No emojis.
- Keep responses brief. Use bullet points when appropriate.

## Assistant: Policy

- Separate facts and assumptions clearly. Base answers only on information available in the given context.
- If any point is ambiguous or unknown, explicitly state "不明" and request additional information.
- Never use `rm -rf` or similar destructive commands without explicit confirmation from the user.

## Global Rules

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

- **OS:** Linux
- **Python:** 3.13 (production venv: `/opt/llm/venv/`; dev venv: `.venv/` managed by uv)
- **DB:** SQLite + `sqlite-vec` extension at `/opt/llm/sqlite-vec/vec0.so`

Full environment details, schema, config reference, and service ports: `rules/env.md`

## Development

```bash
uv sync --dev --system-certs    # create .venv/ and install all deps
uv run pytest                   # run any tool without activating venv
```

Full validation sequence: `rules/toolchain.md`

Key library choices and coding conventions: `rules/coding.md`

**Import layer contracts (enforced by `.importlinter`):** `shared` → external only · `db` → shared · `rag` → db, shared · `mcp` → db, shared · `agent` → all. Violations fail `lint-imports`. Never import from a higher layer into a lower one (e.g. `shared` must not import from `agent`, `rag`, `db`, or `mcp`).

**Execution policy:** Run **all local commands** directly without asking the user for confirmation first. This includes destructive local operations such as file deletion, `git reset`, and `git checkout`. The only exceptions that still require confirmation are actions that affect systems outside the local machine: pushing to remote repositories, modifying shared infrastructure, or sending messages to external services.

**Test coverage:** Unit tests exist for `agent/commands/cmd_config.py`, `agent/commands/cmd_mcp.py`, `agent/commands/cmd_tooling.py` (via `test_agent_rag.py`), `agent/session.py`, `agent/repl_tool_exec.py` (re-export layer; approval logic in `test_tool_approval.py`), `agent/tool_policy.py`, `agent/tool_audit.py`, `agent/tool_approval.py`, `agent/tool_runner.py`, `agent/tool_result_formatter.py`, `agent/tool_loop_guard.py`, `agent/llm_turn_runner.py`, `agent/factory.py`, `agent/cli_view.py`, `mcp/file/delete_service.py`, `mcp/file/write_service.py`, `mcp/file/read_server.py` (models), `mcp/github/service.py`, `mcp/git/service.py`, `agent/history.py`, `shared/llm_client.py`, `shared/token_counter.py`, `shared/mcp_config.py`, `shared/config_loader.py`, `agent/memory/layer.py`, `agent/memory/store.py`, `agent/memory/extract.py`, `agent/memory/retriever.py`, `agent/memory/jsonl_store.py`, `agent/memory/embedding_client.py`, `agent/memory/ingestion.py`, `agent/memory/injection.py`, `agent/orchestrator.py`, `shared/otel_tracer.py`, `shared/plugin_registry.py`, `rag/utils.py`, `rag/pipeline.py`, `mcp/shell/service.py`, `mcp/rag_pipeline/service.py`, `mcp/sqlite/service.py`, `mcp/cicd/service.py`, `shared/route_resolver.py`, `agent/lifecycle.py`, `agent/http_lifecycle.py`, `agent/stdio_lifecycle.py`, `mcp/server.py` (base class), `shared/tool_executor.py` (routing paths), `db/helper.py`, `db/maintenance.py`, `db/tool_results.py`. Any refactoring task that touches this module must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting work.

## Skills (`skills/`)

Skills are registered as slash commands in `.claude/commands/`. Invoke with `/skill-name [task]` or via `Skill("skill-name")`. Each SKILL.md declares `Composes with` / `Called by` — use these to chain skills across multi-phase tasks.

Task→skill and task→docs mapping: `routing.md` (canonical; do not duplicate here).
Skill design principles (when creating or improving a SKILL): `skills/DESIGN.md`.
