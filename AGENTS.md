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

- Read only the skills and docs needed for the task.
- **Always read `routing.md` immediately after this file.** It maps task types to both skills and docs to load.
- Do NOT load all `docs/*.md`. Load only what `routing.md`'s Docs → task mapping specifies.
- **Do not generate code, documentation, or anything else speculatively. Stop and ask when anything is unclear.**
- **Do not commit changes without a clear commit message explaining the reason for them.**

## Context Loader Pattern

```
Task → routing.md → Minimal Skills + Shared Rules → Relevant docs → Execution
```

- Task routing rules: AGENTS.md
- Shared design and architectural rules: `skills/DESIGN.md`
- Task-specific procedures: `skills/<task>/SKILL.md` + `skills/<task>/workflow.md`
- Always-load rules are in `routing.md` (`## Always load alongside the skill`)

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

**Test coverage:** Unit tests exist for the following modules. Any refactoring that touches these must acquire behavior-lock tests (using the `python-test-and-fix` skill) before starting.

- **agent/**: cmd_config, cmd_mcp, cmd_tooling (via `test_agent_rag.py`), session, repl_tool_exec (approval logic in `test_tool_approval.py`), tool_policy, tool_audit, tool_approval, tool_runner, tool_result_formatter, tool_loop_guard, llm_turn_runner, factory, cli_view, history, memory (layer, store, extract, retriever, jsonl_store, embedding_client, ingestion, injection), orchestrator, lifecycle, http_lifecycle, stdio_lifecycle
- **shared/**: llm_client, token_counter, mcp_config, config_loader, otel_tracer, plugin_registry, route_resolver, tool_executor (routing paths)
- **mcp/**: file (delete_service, write_service, read_server models), github/service, git/service, shell/service, rag_pipeline/service, sqlite/service, cicd/service, server (base class)
- **rag/**: utils, pipeline, repository (FTS5 via `test_fts_japanese.py`)
- **db/**: helper, maintenance, tool_results

## Skills (`skills/`)

Skills are registered as slash commands in `.claude/commands/`. Invoke with `/skill-name [task]` or via `Skill("skill-name")`. Each SKILL.md declares `Composes with` / `Called by` — use these to chain skills across multi-phase tasks.

Task→skill and task→docs mapping: `routing.md` (canonical; do not duplicate here).
Skill design principles and file-split rules: `skills/DESIGN.md`.
