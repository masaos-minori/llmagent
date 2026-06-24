# AGENTS.md

## Role

Senior engineer working on this project. Always respond in Japanese.

## Style

- Concise, direct sentences. Use half-width alphanumeric characters and symbols. No emojis.
- Use bullet points for lists. Keep responses brief.

## Policy

- Base answers only on information available in the given context. Separate facts from assumptions clearly.
- If anything is ambiguous or unknown, state "不明" and ask for clarification.
- Never run `rm -rf` or other destructive commands without explicit user confirmation.

## Global Rules

1. **Load files selectively.** Read only the skills and docs needed for the current task.
2. **Always read `routing.md` immediately after this file.** It maps task types to the skills and docs to load.
3. **Do NOT load all `docs/*.md`.** Only load what `routing.md` specifies for the task at hand.
4. **Do not generate code, documentation, or anything else speculatively.** Stop and ask when anything is unclear.
5. **Do not commit changes without a clear commit message explaining the reason.**

## Context Loading Flow

```
Task → routing.md → skill + shared rules → relevant docs → execute
```

- Task→skill/docs mapping: `routing.md` (canonical source)
- Shared design/architecture rules: `skills/DESIGN.md`
- Task-specific procedures: `skills/<task>/SKILL.md` + `skills/<task>/workflow.md`
- Always-loaded rules: listed in `routing.md` under "Always load alongside the skill"

## Environment

- **OS:** Linux
- **Python:** 3.13 (production venv: `/opt/llm/venv/`; dev venv: `.venv/` managed by uv)
- **DB:** SQLite + `sqlite-vec` extension at `/opt/llm/sqlite-vec/vec0.so`

Full details (schema, config reference, service ports): `rules/env.md`

## Development

```bash
uv sync --dev --system-certs    # create .venv/ and install all deps
uv run pytest                   # run tests without activating venv
```

- Full validation sequence: `rules/toolchain.md`
- Library choices and coding conventions: `rules/coding.md`

### Import layer contract (enforced by `.importlinter`)

Layers may only import from themselves and layers below:

```
shared → external only
db     → shared
rag    → db, shared
mcp    → db, shared
agent  → all layers
```

Violations fail `lint-imports`. Never import a lower layer from a higher one (e.g. `shared` must not import from `agent`, `rag`, `db`, or `mcp`).

### Execution policy

Run **all local commands** directly without asking for confirmation. This includes destructive local operations such as file deletion, `git reset`, and `git checkout`.

Exceptions that require user confirmation: pushing to remote repos, modifying shared infrastructure, sending messages to external services.

### Test coverage

Unit tests exist for these modules. Refactoring that touches them must first acquire behavior-lock tests (using the `python-test-and-fix` skill).

- **agent/**: cmd_config, cmd_mcp, cmd_tooling (via `test_agent_rag.py`), session, tool_policy, tool_audit, tool_approval, tool_runner, tool_result_formatter, tool_loop_guard, llm_turn_runner, factory, cli_view, history, memory (layer, store, extract, retriever, jsonl_store, embedding_client, ingestion, injection), orchestrator, lifecycle, http_lifecycle, stdio_lifecycle
- **shared/**: llm_client, token_counter, mcp_config, config_loader, otel_tracer, plugin_registry, route_resolver, tool_executor (routing paths)
- **mcp/**: file (delete_service, write_service, read_server models), github/service, git/service, shell/service, rag_pipeline/service, sqlite/service, cicd/service, server (base class)
- **rag/**: utils, pipeline, repository (FTS5 via `test_fts_japanese.py`)
- **db/**: helper, maintenance, tool_results

## Skills (`skills/`)

Skills are registered as slash commands in `.claude/commands/`. Invoke with `/skill-name [task]` or via `Skill("skill-name")`. Each SKILL.md declares `Composes with` / `Called by` — use these to chain skills across multi-phase tasks.

- Task→skill and task→docs mapping: `routing.md` (canonical; do not duplicate here)
- Skill design principles and file-split rules: `skills/DESIGN.md`
