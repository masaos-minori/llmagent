# Context Loading Reference

Maps task type to files that must be loaded. Read this immediately after AGENTS.md.

## Task → skill mapping

Skills can be invoked as slash commands (e.g. `/python-implementation`) or via `Skill("python-implementation")`. The command reads `skills/*/SKILL.md` automatically.

| Task type | Keywords | Load |
|---|---|---|
| Feature / bug fix / new module | add, implement, fix, create, modify | `skills/python-implementation/SKILL.md` + `skills/python-implementation/workflow.md` |
| Debug / root cause | debug, error, exception, crash, trace, log, slow, hang | `skills/python-debug-root-cause/SKILL.md` + `skills/python-debug-root-cause/workflow.md` |
| Lint / type errors / CI fix | lint, ruff, mypy, pyright, type error, CI, pre-commit | `skills/python-lint-typecheck/SKILL.md` + `skills/python-lint-typecheck/workflow.md` |
| Test / pytest / flaky | test, pytest, flaky, coverage, assertion, regression | `skills/python-test-and-fix/SKILL.md` + `skills/python-test-and-fix/workflow.md` |
| Test suite audit (whole-suite, not a single failing test) | test audit, test suite audit, coverage gap, test debt, stabilization plan, QA review | `skills/test-audit/SKILL.md` + `skills/test-audit/workflow.md` |
| Refactor / rename / CST | refactor, rename, restructure, split, move, import cycle | `skills/python-refactoring/SKILL.md` + `skills/python-refactoring/workflow.md` |
| Code review / PR review | review, code review, PR review, findings | `skills/python-code-review/SKILL.md` + `skills/python-code-review/workflow.md` + `skills/DESIGN.md` (Evidence labels, Confidence, Severity) |
| Issue -> plan | raw issue, existing issue file, issues/*.md, plan, design, analyze, assess, spec, ticket | `skills/issue-to-plan/SKILL.md` + `skills/issue-to-plan/workflow.md` |
| Plan -> implementation procedure | plan, approved plan, implementation procedure, file-level steps | `skills/plan-to-implementation-procedure/SKILL.md` + `skills/plan-to-implementation-procedure/workflow.md` |
| Implementation procedure -> code | implementation procedure, execute procedure, implement from procedure | `skills/code-implementation/SKILL.md` + `skills/code-implementation/workflow.md` |
| Architecture / module design | architecture, module, interface, data model, component | `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `skills/mcp-server-add/workflow.md` + `rules/env.md` + `docs/22_mcp/mcp_03_01_dispatch-and-routing.md` + `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` + `docs/22_mcp/mcp_06_12_new-mcp-server-addition-checklist.md` + `docs/22_mcp/mcp_03_05_lifecycle-and-new-server.md` + `docs/22_mcp/mcp_06_14_mcp-authentication-setup.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `skills/deploy/workflow.md` + `rules/env.md` + `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` |
| Event Bus implementation / debug | eventbus, event bus, dlq, sse subscribe, replay | `skills/python-implementation/SKILL.md` + `skills/python-implementation/workflow.md` + `rules/env.md` (add `skills/python-debug-root-cause/SKILL.md` + `workflow.md` for debug/investigation tasks) |
| Documentation / docs — also matches whenever a file under `docs/` or `skills/` will be created or edited, even with no documentation keyword in the request | document, doc, write docs, readme, changelog, editing `docs/*` or `skills/*` | `skills/python-documentation/SKILL.md` + `skills/python-documentation/workflow.md` |
| Issue creation / GitHub issue | issue, github issue, create issue, convert findings to issue | `skills/issue-creator/SKILL.md` + `skills/issue-creator/workflow.md` |
| Git commit / sync (also for committing/pushing a `tools/` script) | commit, stage, push, pull, fetch, rebase, git sync, conflict, git workflow, commit tool, push tool | `skills/git-commit-and-sync/SKILL.md` + `skills/git-commit-and-sync/workflow.md` |
| Tool addition / modification (structure, format, checks) | new tool, add script, tools/, one-off script | See "Tools" → "Adding a new tool" below — lighter validation than a `scripts/` change, not `python-implementation` |
| Tool logic / behavior change | change tool behavior, tool refactor logic | `skills/python-implementation/SKILL.md` + `skills/python-implementation/workflow.md` — only when the tool's runtime behavior changes materially; otherwise stay on the lighter validation above |
| Debug a failing tool | tool error, tool crash, tool slow, wrong tool output | `skills/python-debug-root-cause/SKILL.md` + `skills/python-debug-root-cause/workflow.md` |
| Fix lint / type / bandit findings in a tool | ruff, mypy, bandit, noqa, tool lint | `skills/python-lint-typecheck/SKILL.md` + `skills/python-lint-typecheck/workflow.md` |
| Refactor a tool (no behavior change) | refactor tool, rename tool, restructure tool | `skills/python-refactoring/SKILL.md` + `skills/python-refactoring/workflow.md` |
| Add / fix tests for a tool | tool test, tool pytest, flaky tool | `skills/python-test-and-fix/SKILL.md` + `skills/python-test-and-fix/workflow.md` |
| Review a tool | tool PR review, review tool | `skills/python-code-review/SKILL.md` + `skills/python-code-review/workflow.md` |
| Document a tool (incl. `tools/TOOL_DESCRIPTIONS.md`) | document tool, TOOL_DESCRIPTIONS | `skills/python-documentation/SKILL.md` + `skills/python-documentation/workflow.md` |

**Documentation row exception**: a `skills/*.md` edit that revises the *procedure
itself* (per that skill's own `## Improvement feedback` section — e.g. correcting a
Step's stop condition, adding a missing branch, fixing a false-positive check) does
not route through `python-documentation`. That skill's own "When to use"/"When not to
use" scope it to documenting existing Python code/architecture behavior, not to
revising workflow instructions — applying its Phase 1-10 procedure to a `workflow.md`
edit is a scope mismatch. This row still applies as normal to any `docs/*.md` edit,
and to a `skills/*.md` edit that documents actual code behavior (e.g. `rules/env.md`
Architecture changes reflected into a skill's evidence).

## Source code layout

Source code lives under `scripts/` (e.g. `scripts/agent/`, `scripts/mcp/`, `scripts/rag/`, `scripts/shared/`, `scripts/eventbus/`, `scripts/db/`). Feature/bug fix, refactor, and debug tasks operate on files under this directory.

Test scripts live under `tests/` (mirroring `scripts/` structure, e.g. `tests/agent/`, `tests/shared/`, `tests/integration/`). Test / pytest / flaky tasks operate on files under this directory.

## Tools

Scripts in `tools/` for one-off operations on source code or documentation. Not triggered by routing; AI invokes these during investigation or refactoring tasks. See `tools/TOOL_DESCRIPTIONS.md` for details.

### Adding a new tool

A new or modified `tools/*.py` script does not route through `python-implementation`
— that skill's scope is `scripts/` (see "Source code layout" above). Apply this
lighter validation sequence instead, then consider the tool done:

1. `uv run ruff format tools/<file>.py` and `uv run ruff check tools/<file>.py --fix`,
   then confirm clean with `uv run ruff check tools/<file>.py`.
2. `uv run mypy tools/<file>.py` — pass the file path explicitly as the narrowest check;
   `pyproject.toml`'s mypy `files` scope covers `scripts/`, `tests/eventbus`, and `tools/`, so a bare
   `uv run mypy` (no path) also checks this file but reports every file's findings.
3. `uv run bandit tools/<file>.py`.
4. A manual smoke-test invocation against real repository data (not only a
   hand-crafted fixture) — confirm the tool's actual output on live
   `issues/`/`plans/`/`implementations/`/`docs/` content before trusting it as
   evidence elsewhere.
5. Apply `AGENTS.md` Global Rule 7 (script-worthiness) and Global Rule 9: run
   `uv run python tools/check_tool_descriptions_sync.py` and add the new tool's row to
   `tools/TOOL_DESCRIPTIONS.md` in the same change. If the tool should run
   automatically at a defined trigger point rather than only ad hoc, add it to "When
   to run which tool" below too.

### Checkers by situation

The table of checkers to run, by situation, is `rules/tool-gates.md` "When to run which tool".
Load it before finishing a task that added, edited, or removed a file; `AGENTS.md` Global Rule 9
requires it for `docs/` and `tools/` changes, and `uv run python tools/run_validation_gates.py`
runs the path-keyed rows for the changed files.

## Workflow files

Invoke directly by filename. Not triggered by routing.

| Workflow | File |
|---|---|
| Issue → plan (raw issue → work plan, no standalone requirement doc) | `prompts/01_issue-to-plan.md` |
| Implementation procedure (work plan → file-level implementation procedure docs) | `prompts/02_plan-to-implementation-procedure.md` |
| Implementation (implementation procedure doc → code, tests, docs) | `prompts/03_implementation.md` |
| Refactor (direct refactor execution on named source files) | `prompts/04_refactor.md` |
| Skills/routing reorganization (Context Loader Pattern restructuring of skills and routing.md) | `prompts/05_skills.md` |
| Test suite audit (run tests, find coverage/validation gaps, produce improvement plan) | `prompts/07_test-audit.md` |
| Design docs refactor (add implementation intent to design docs, supported by code) | `prompts/08_document-sync.md` |

The full pipeline: issue file → work plan document → file-level implementation
procedure document → implementation, tests, and documentation updates. There is no
standalone requirement-document stage, and no separate "design" phase —
`prompts/02_plan-to-implementation-procedure.md` produces the implementation
procedure, not an architecture design document.
`prompts/04`–`08` are auxiliary maintenance workflows outside this pipeline — invoked directly
by filename when the situation applies (ad-hoc refactor, skill/doc reorganization, test audit),
not staged through `issues/` -> `plans/` -> `implementations/`.

## Document workflow directories

The full pipeline runs across three top-level directories, in order:
`issues/` -> `plans/` -> `implementations/` -> code.

| Directory | Contents |
|---|---|
| `issues/` | Raw, unformatted issues — the pipeline entry point. Populated manually (code review findings, proposals, audit results), and automatically by `prompts/01_issue-to-plan.md` Step 6 (unresolved unknowns and risks, filed as issues). Consumed by `prompts/01_issue-to-plan.md`. |
| `issues/done/` | Issue files consumed by `prompts/01_issue-to-plan.md` — either converted into a work plan, or found already resolved/no longer applicable. |
| `plans/` | Work plan docs produced by `prompts/01_issue-to-plan.md`, ready for `prompts/02_plan-to-implementation-procedure.md`. |
| `plans/done/` | Plan docs consumed by `prompts/02_plan-to-implementation-procedure.md`. |
| `implementations/` | File-level implementation procedure docs produced by `prompts/02_plan-to-implementation-procedure.md`, ready for `prompts/03_implementation.md`. |
| `implementations/done/` | Implementation procedure docs consumed by `prompts/03_implementation.md`. Only executed procedures are stored here; a procedure reaches this directory only via the `code-implementation` Step 7 archival move, never by an earlier phase. |

## Docs → task mapping

Load only the docs relevant to the specific task. Do NOT load all `docs/*.md`.

Full task-scope → doc mapping (Domain specs, System overview, Agent, MCP, RAG, DB/Shared, Event Bus): see `docs/00_index.md` "Document References by Task".

## Always load alongside the skill

- `rules/coding.md` — coding conventions and prohibited patterns
- `rules/toolchain.md` — validation sequence (format → lint → type → arch → security → test → coverage)

Exception: `issue-to-plan` and `plan-to-implementation-procedure` produce documents only, so
each loads these two files at the step its own Step 0 names (a Plan or procedure row that
changes code or tests), not at the start.

## Conditional load

Load in addition to the skill when the task involves:

- `skills/DESIGN.md` — any task that touches module boundaries, interfaces, or data models
- `rules/env.md` — service ports, DB schema, config files, or deployment
- `rules/persisted-schema-change.md` — persisted SQLite schema, DDL, schema version, or migration changes
- `rules/tool-gates.md` — before finishing any task that added, edited, or removed a file: the checkers to run, by situation

## Multiple task types

If a task spans multiple types, load the union of all required skills and docs.
