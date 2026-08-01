# Context Loading Reference

Maps task type to files that must be loaded. Read this immediately after AGENTS.md.

## Task → skill mapping

Skills can be invoked as slash commands (e.g. `/python-implementation`) or via `Skill("python-implementation")`. The command reads `skills/*/SKILL.md` automatically.
`/skill <name> [args]` is the equivalent runtime-invocable form inside AgentREPL; `/skill` with no argument lists available skill names.

| Task type | Keywords | Load |
|---|---|---|
| Feature / bug fix / new module | add, implement, fix, create, modify | `skills/python-implementation/SKILL.md` + `skills/python-implementation/workflow.md` |
| Debug / root cause | debug, error, exception, crash, trace, log, slow, hang | `skills/python-debug-root-cause/SKILL.md` + `skills/python-debug-root-cause/workflow.md` |
| Lint / type errors / CI fix | lint, ruff, mypy, pyright, type error, CI, pre-commit | `skills/python-lint-typecheck/SKILL.md` + `skills/python-lint-typecheck/workflow.md` |
| Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression | `skills/python-test-and-fix/SKILL.md` + `skills/python-test-and-fix/workflow.md` |
| Refactor / rename / CST | refactor, rename, restructure, split, move, import cycle | `skills/python-refactoring/SKILL.md` + `skills/python-refactoring/workflow.md` |
| Code review / PR review | review, code review, PR review, findings | `skills/python-code-review/SKILL.md` + `skills/python-code-review/workflow.md` |
| Issue -> requirement | issue, raw issue, issue-to-require | `skills/issue-to-require/SKILL.md` + `skills/issue-to-require/workflow.md` |
| Plan / design / ticket | plan, design, analyze, assess, spec, ticket | `skills/require-to-plan/SKILL.md` + `skills/require-to-plan/workflow.md` |
| Architecture / module design | architecture, module, interface, data model, component | `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `skills/mcp-server-add/workflow.md` + `rules/env.md` + `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/04_mcp_06_02_configuration-file-inventory.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `skills/deploy/workflow.md` + `rules/env.md` + `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` |
| Event Bus debug / investigation only — **implementation forbidden, see AGENTS.md Global Rule 8** | eventbus, event bus, dlq, sse subscribe, replay | `skills/python-debug-root-cause/SKILL.md` + `skills/python-debug-root-cause/workflow.md` + `rules/env.md` |
| Documentation / docs | document, doc, write docs, readme, changelog | `skills/python-documentation/SKILL.md` + `skills/python-documentation/workflow.md` |
| Issue creation / GitHub issue | issue, github issue, create issue, convert findings to issue | `skills/issue-creator/SKILL.md` + `skills/issue-creator/workflow.md` |
| Git commit / sync | commit, stage, push, pull, git sync, conflict, git workflow | `skills/git-commit-and-sync/SKILL.md` + `skills/git-commit-and-sync/workflow.md` |

## Source code layout

Source code lives under `scripts/` (e.g. `scripts/agent/`, `scripts/mcp/`, `scripts/rag/`, `scripts/shared/`, `scripts/eventbus/`, `scripts/db/`). Feature/bug fix, refactor, and debug tasks operate on files under this directory.

Test scripts live under `tests/` (mirroring `scripts/` structure, e.g. `tests/agent/`, `tests/shared/`, `tests/integration/`). Test / pytest / flaky tasks operate on files under this directory.

## Tools

Scripts in `tools/` for one-off operations on source code or documentation. Not triggered by routing; AI invokes these during investigation or refactoring tasks. See `tools/TOOL_DESCRIPTIONS.md` for details.

## Workflow files

Invoke directly by filename. Not triggered by routing.

| Workflow | File |
|---|---|
| Issue → requirement (raw issue → formal require doc) | `prompts/00_issue-to-require.md` |
| Plan (requirement → work plan) | `prompts/01_require-to-plan.md` |
| Implementation procedure (work plan → file-level implementation procedure docs) | `prompts/02_plan-to-implementation-procedure.md` |
| Implementation (implementation procedure doc → code, tests, docs) | `prompts/03_implementation.md` |
| Refactor (direct refactor execution on named source files) | `prompts/04_refactor.md` |
| Skills/routing reorganization (Context Loader Pattern restructuring of skills and routing.md) | `prompts/05_skills.md` |
| Documentation restructuring (reorganize `docs/` against current source code) | `prompts/06_documentation.md` |
| Test suite review (run tests, find coverage/validation gaps, produce improvement plan) | `prompts/07_test-refactor.md` |
| Design docs refactor (add implementation intent to design docs, supported by code) | `prompts/08_document-refactor.md` |

The full pipeline: issue file → requirement document → work plan document → file-level
implementation procedure document → implementation, tests, and documentation updates.
There is no separate "design" phase — `prompts/02_plan-to-implementation-procedure.md` produces the
implementation procedure, not an architecture design document.
`prompts/04`–`08` are auxiliary maintenance workflows outside this pipeline — invoked directly
by filename when the situation applies (ad-hoc refactor, skill/doc reorganization, test audit),
not staged through `issues/` -> `requires/` -> `plans/` -> `implementations/`.

## Document workflow directories

The full pipeline runs across four top-level directories, in order:
`issues/` -> `requires/` -> `plans/` -> `implementations/` -> code.

| Directory | Contents |
|---|---|
| `issues/` | Raw, unformatted issues — the pipeline entry point. Populated manually (code review findings, proposals, audit results), and automatically by `prompts/01_require-to-plan.md` Steps 5-6 (unresolved unknowns and risks, filed as issues). Consumed by `prompts/00_issue-to-require.md`. |
| `issues/done/` | Issue files consumed by `prompts/00_issue-to-require.md` — either converted into a requirement doc, or found already resolved/no longer applicable. |
| `requires/` | Formal requirement docs ready for `prompts/01_require-to-plan.md`, in the `Title/Priority/Target files/...` template. |
| `requires/done/` | Requirement docs consumed by `prompts/01_require-to-plan.md`. |
| `plans/` | Work plan docs produced by `prompts/01_require-to-plan.md`, ready for `prompts/02_plan-to-implementation-procedure.md`. |
| `plans/done/` | Plan docs consumed by `prompts/02_plan-to-implementation-procedure.md`. |
| `implementations/` | File-level implementation procedure docs produced by `prompts/02_plan-to-implementation-procedure.md`, ready for `prompts/03_implementation.md`. |
| `implementations/done/` | Implementation procedure docs consumed by `prompts/03_implementation.md`. |

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
