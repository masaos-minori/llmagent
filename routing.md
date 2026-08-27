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
| Issue -> plan | issue, raw issue, plan, design, analyze, assess, spec, ticket | `skills/issue-to-plan/SKILL.md` + `skills/issue-to-plan/workflow.md` |
| Plan -> implementation procedure | plan, approved plan, implementation procedure, file-level steps | `skills/plan-to-implementation-procedure/SKILL.md` + `skills/plan-to-implementation-procedure/workflow.md` |
| Implementation procedure -> code | implementation procedure, execute procedure, implement from procedure | `skills/code-implementation/SKILL.md` + `skills/code-implementation/workflow.md` |
| Architecture / module design | architecture, module, interface, data model, component | `skills/python-design/SKILL.md` + `skills/python-design/workflow.md` |
| MCP server / new server | mcp server, new server, install server | `skills/mcp-server-add/SKILL.md` + `skills/mcp-server-add/workflow.md` + `rules/env.md` + `docs/04_mcp_03_01_dispatch-and-routing.md` + `docs/04_mcp_06_02_configuration-file-inventory.md` |
| Deploy / production | deploy, /opt/llm, service restart, init.d | `skills/deploy/SKILL.md` + `skills/deploy/workflow.md` + `rules/env.md` + `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` |
| Event Bus implementation / debug | eventbus, event bus, dlq, sse subscribe, replay | `skills/python-implementation/SKILL.md` + `skills/python-implementation/workflow.md` + `rules/env.md` (add `skills/python-debug-root-cause/SKILL.md` + `workflow.md` for debug/investigation tasks) |
| Documentation / docs — also matches whenever a file under `docs/` or `skills/` will be created or edited, even with no documentation keyword in the request | document, doc, write docs, readme, changelog, editing `docs/*` or `skills/*` | `skills/python-documentation/SKILL.md` + `skills/python-documentation/workflow.md` |
| Issue creation / GitHub issue | issue, github issue, create issue, convert findings to issue | `skills/issue-creator/SKILL.md` + `skills/issue-creator/workflow.md` |
| Git commit / sync | commit, stage, push, pull, git sync, conflict, git workflow | `skills/git-commit-and-sync/SKILL.md` + `skills/git-commit-and-sync/workflow.md` |

## Source code layout

Source code lives under `scripts/` (e.g. `scripts/agent/`, `scripts/mcp/`, `scripts/rag/`, `scripts/shared/`, `scripts/eventbus/`, `scripts/db/`). Feature/bug fix, refactor, and debug tasks operate on files under this directory.

Test scripts live under `tests/` (mirroring `scripts/` structure, e.g. `tests/agent/`, `tests/shared/`, `tests/integration/`). Test / pytest / flaky tasks operate on files under this directory.

## Tools

Scripts in `tools/` for one-off operations on source code or documentation. Not triggered by routing; AI invokes these during investigation or refactoring tasks. See `tools/TOOL_DESCRIPTIONS.md` for details.

### When to run which tool

Run the applicable checker below instead of relying on manual review alone — these scripts already
encode the project's structural/consistency rules. Run before finishing the task, not only when a
problem is suspected; several of these gaps (stale claims, unregistered NC markers, drifted
descriptions) are invisible from reading the changed file alone.

| Situation | Run | Notes |
|---|---|---|
| Any `docs/*.md` file was added or edited | `uv run python tools/check_docs_quality.py` | Structural/formatting rules (headings, tables, code fences, Migration Notes placement) |
| Any `docs/*.md` file was added or edited | `uv run python tools/check_docs_structure.py [glob ...]` | File size, H1 count, Front Matter, Related Documents/Keywords sections, internal link reachability |
| Docs touched a specific domain (`agent`\|`mcp`\|`rag`\|`deployment`\|`overview`) | `uv run python tools/check_docs_consistency.py --domain <domain>` | Cross-checks doc claims (ports, config keys, symbol references) against `config/agent.toml` and `scripts/` |
| A "Needs confirmation" marker was added, resolved, or removed anywhere under `docs/` | `uv run python tools/check_needs_confirmation_inventory.py` | Register new markers in `docs/00_governance_03_issue-and-uncertainty-management.md`; remove the inline marker from the source doc once an entry is marked resolved |
| A file was added to or removed from `tools/` | `uv run python tools/check_tool_descriptions_sync.py` | Update `tools/TOOL_DESCRIPTIONS.md` in the same change — do not leave a tool undocumented or a description referring to a deleted file |
| Claiming no backward-compat shims remain in `scripts/`, `docs/`, `tests/`, or `tools/` | `uv run python tools/check_compat_shims.py` | |
| A `# noqa` / `# type: ignore` / `# nosec` suppression was added | `uv run python tools/check_suppression_justification.py` | Requires a rule/error code plus an em-dash-separated justification |
| Need the current MCP port/tool reference table | `uv run python tools/generate_reference_table.py --type mcp` | Add `--dry-run` to preview without writing; omit it to refresh the `<!-- AUTO-GENERATED -->` block in place |
| Need the current RAG config reference table | `uv run python tools/generate_reference_table.py --type rag` | Same `--dry-run` behavior as above |
| Need the current DB path/config-key reference table | `uv run python tools/generate_reference_table.py --type deployment` | Same `--dry-run` behavior as above |
| Need the current MCP server inventory (transport, startup mode, tool names) | `uv run python tools/generate_mcp_inventory.py --format json\|csv` | Reads live `config/agent.toml`, not a doc snapshot |
| A module-level docstring header path may be stale after a file move | `uv run python tools/fix_docstring_paths.py --dry-run` | Add `--apply` only after reviewing the dry-run diff |
| Docstring format needs verification (not repair) after touching `scripts/` | `uv run python tools/check_docstrings.py` | Read-only — does not add or fix docstrings |
| Front Matter is missing or a list field has duplicate entries in `docs/*.md` | `uv run python tools/manage_frontmatter.py add-missing\|dedupe-lists` | |
| Japanese text may remain in `docs/*.md` (violates `skills/DESIGN.md` Output language) | `uv run python tools/check_docs_japanese.py` | |

Do not write a new one-off script for something this list already covers — extend the existing tool
instead (see AGENTS.md Global Rule 7 for when a *new* script is warranted).

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
| `implementations/done/` | Implementation procedure docs consumed by `prompts/03_implementation.md`. |

## Docs → task mapping

Load only the docs relevant to the specific task. Do NOT load all `docs/*.md`.

Full task-scope → doc mapping (Domain specs, System overview, Agent, MCP, RAG, DB/Shared, Event Bus): see `docs/00_index.md` "Document References by Task".

## Always load alongside the skill

- `rules/coding.md` — coding conventions and prohibited patterns
- `rules/toolchain.md` — validation sequence (format → lint → type → arch → security → test → coverage)

## Conditional load

Load in addition to the skill when the task involves:

- `skills/DESIGN.md` — any task that touches module boundaries, interfaces, or data models
- `rules/env.md` — service ports, DB schema, config files, or deployment

## Multiple task types

If a task spans multiple types, load the union of all required skills and docs.
