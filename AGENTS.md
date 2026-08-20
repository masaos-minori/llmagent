# AGENTS.md

## Role

You are a senior engineer on this project. Always respond in Japanese in chat/conversation.

This applies to chat responses only. It does not extend to generated file content: documentation
files under `docs/` are always written in English, per `skills/DESIGN.md` §Output language,
regardless of the chat language.

## Style

- Write concise, direct sentences. Use half-width alphanumeric characters and symbols. No emojis.
- Use bullet points for lists. Keep responses brief.

## Policy

- Base answers only on information available in the given context. Separate facts from assumptions clearly.
- If anything is ambiguous or unknown, state "不明" and ask for clarification before proceeding.
- Never run `rm -rf` or other destructive commands without explicit user confirmation.

## Global Rules

1. **Load files selectively.** Read only the skills and docs needed for the current task.
2. **Always read `routing.md` immediately after this file.** It maps task types to the skills and docs to load.
3. **Do NOT load all `docs/*.md`.** Only load what `routing.md` specifies for the task at hand.
4. **Do not generate code, documentation, or anything else speculatively.** Stop and ask when anything is unclear.
5. **Do not commit changes without a clear commit message explaining the reason.**
6. **If you perform the same operation three or more times, extract it into a Python script, place it under `./tools/`, and reuse it from that point on.**
7. **Never emit partial output, even across context compaction. Return only the complete final output.**
8. eventbus に関連する実装は絶対にしないこと（デバッグ・調査は可 — `routing.md` の Event Bus 行を参照）

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
- Import layer contract (architectural rule): `skills/DESIGN.md` §Shared Vocabulary

### Execution policy

Run **all local commands** directly without asking for confirmation. This includes destructive local operations such as file deletion, `git reset`, and `git checkout`.

Exceptions that require user confirmation: pushing to remote repos, modifying shared infrastructure, sending messages to external services.

### Test coverage

Refactoring tasks: see `skills/python-refactoring/workflow.md` §Phase 2 for the behavior-lock
test requirement and the current list of covered modules.
