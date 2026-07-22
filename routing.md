# Context Loading Reference

Maps task type to files that must be loaded. Read this immediately after AGENTS.md.

## Task → skill mapping

Skills can be invoked as slash commands (e.g. `/python-implementation`) or via `Skill("python-implementation")`. The command reads `skills/*/SKILL.md` automatically.
`/skill <name> [args]` is the equivalent runtime-invocable form inside AgentREPL; `/skill` with no argument lists available skill names.

| Task type | Keywords | Load |
|---|---|---|
| Feature / bug fix / new module | add, implement, fix, create, modify | `skills/python-implementation/SKILL.md` |
| Debug / root cause | debug, error, exception, crash, trace, log, slow, hang | `skills/python-debug-root-cause/SKILL.md` |
| Lint / type errors / CI fix | lint, ruff, mypy, pyright, type error, CI, pre-commit | `skills/python-lint-typecheck/SKILL.md` |
| Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression | `skills/python-test-and-fix/SKILL.md` |
| Refactor / rename / CST | refactor, rename, restructure, split, move, import cycle | `skills/python-refactoring/SKILL.md` |
| Plan / design / ticket | plan, design, analyze, assess, spec, ticket | `skills/python-issue-to-plan/SKILL.md` + `skills/python-issue-to-plan/workflow.md` |
| Architecture / module design | architecture, module, interface, data model, component | `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `rules/env.md` + `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/04_mcp_06_02_configuration-file-inventory.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `rules/env.md` + `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` |
| Event Bus implementation / debug | eventbus, event bus, dlq, sse subscribe, replay | `skills/python-implementation/SKILL.md` + `rules/env.md` |
| Documentation / docs | document, doc, write docs, readme, changelog | `skills/python-documentation/SKILL.md` |
| Git commit / sync | commit, stage, push, pull, git sync, conflict, git workflow | `skills/git-commit-and-sync/SKILL.md` |

## Workflow files

Invoke directly by filename. Not triggered by routing.

| Workflow | File |
|---|---|
| Issue → requirement (raw issue → formal require doc) | `00_issue-to-require.md` |
| Plan (requirement → work plan) | `01_require-to-plan.md` |
| Implementation procedure (work plan → file-level implementation procedure docs) | `02_plan_to_implementation_procedure.md` |
| Implementation (implementation procedure doc → code, tests, docs) | `03_implementation.md` |

The full pipeline: issue file → requirement document → work plan document → file-level
implementation procedure document → implementation, tests, and documentation updates.
There is no separate "design" phase — `02_plan_to_implementation_procedure.md` produces the
implementation procedure, not an architecture design document.

## Document workflow directories

`requires/` holds the full issue-to-requirement pipeline in one place:

| Directory | Contents |
|---|---|
| `requires/inbox/` | Raw, unformatted issues — the entry point. Populated manually (code review findings, proposals, audit results). |
| `requires/ready/` | Formal requirement docs ready for `01_require-to-plan.md`, in the `Title/Priority/Target files/...` template. |
| `requires/derived/` | Unknowns and risks generated as a byproduct of `01_require-to-plan.md` Steps 5-6. Not a workflow entry point. |
| `requires/done/` | Completed items from any of the above — issues resolved via `00_issue-to-require.md`, or requirements consumed by `01_require-to-plan.md`. |

## Docs → task mapping

Load only the docs relevant to the specific task. Do NOT load all `docs/*.md`.

Full task-scope → doc mapping (Domain specs, System overview, Agent, MCP, RAG, DB/Shared, Event Bus): see `docs/00_index.md` §「タスク別ドキュメント参照」.

## Always load alongside the skill

- `rules/coding.md` — coding conventions and prohibited patterns
- `rules/toolchain.md` — validation sequence (format → lint → type → arch → security → test → coverage)

## Conditional load

Load in addition to the skill when the task involves:

- `skills/DESIGN.md` — any task that touches module boundaries, interfaces, or data models
- `rules/env.md` — service ports, DB schema, config files, or deployment

## Multiple task types

If a task spans multiple types, load the union of all required skills and docs.
