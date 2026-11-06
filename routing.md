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

### When to run which tool

Run the applicable checker below instead of relying on manual review alone — these scripts already
encode the project's structural/consistency rules. Run before finishing the task, not only when a
problem is suspected; several of these gaps (stale claims, unregistered NC markers, drifted
descriptions) are invisible from reading the changed file alone.

| Situation | Run | Notes |
|---|---|---|
| Any `docs/*.md` file was added or edited | `uv run python tools/check_docs_quality.py` | Structural/formatting rules (headings, tables, code fences, Migration Notes placement) |
| Any `docs/*.md` file was added or edited | `uv run python tools/check_docs_structure.py [glob ...]` | File size, H1 count, Front Matter, Keywords section, body `Related Documents`/`Related Docs`/`Related Chapters` headings at ANY level in any document, front matter `related:` format (`.md` basenames) and coverage of documents referenced by ADR bodies, internal link reachability |
| A DB schema DDL (`scripts/db/schema_sql.py`, `scripts/eventbus/schema.sql`), a `*_db_path` config key, or an `ATTACH`/`load_vec` usage was added or changed | `uv run python tools/check_db_separation.py` | Verifies ADR-008 4DB separation: table ownership inventory, cross-DB FK, distinct DB paths, sqlite-vec scope, no `ATTACH`/schema-qualified access; also runs in CI (`lint` job) and in the deploy pre-deploy check |
| A `scripts/**/*.py` module was added, or an existing module grew | `uv run python tools/check_module_size.py` | Exits 1 past the 24576 B size gate for `scripts/`. `tools/check_module_size_baseline.txt` grandfathers the modules already over the limit at their recorded byte size, so growth past that size, a new oversize module, and stale baseline entries all fail; split with `module_nodes.py measure` and `module_nodes.py extract`. Also runs as the `check-module-size` pre-commit hook and in CI (`lint` job) |
| A `tools/*.py` module was added, or an existing tool grew | `uv run python tools/check_module_size.py --scripts-dir tools --baseline tools/check_module_size_tools_baseline.txt` | Exits 1 past the 24576 B size gate for `tools/`. `tools/check_module_size_tools_baseline.txt` is the separate baseline for `tools/` and only shrinks: growth past a recorded size, a new oversize tool, and stale entries all fail; split with `module_nodes.py measure` and `module_nodes.py extract`. Also runs as the `check-module-size-tools` pre-commit hook and in CI (`lint` job) |
| Any `docs/*.md` file was added or edited | `uv run python tools/check_docs_content_policy.py` | Detection of implementation-detail content (Warnings; `--strict` exits 1 on any warning and is what CI runs, so a finding blocks the PR) that should point to a canonical source instead — see `skills/DESIGN.md` Docs content policy — remove |
| Docs touched a specific domain (`agent`\|`mcp`\|`rag`\|`deployment`\|`overview`\|`eventbus`\|`shared`\|`db`) | `uv run python tools/check_docs_consistency.py --domain <domain>` | Cross-checks doc claims (ports, config keys, symbol references) against `config/agent.toml` and `scripts/` |
| A "Needs confirmation" marker was added, resolved, or removed anywhere under `docs/` | `uv run python tools/check_needs_confirmation_inventory.py` | Register new markers in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; remove the inline marker from the source doc once an entry is marked resolved |
| A file was added to or removed from `tools/` | `uv run python tools/check_tool_descriptions_sync.py` | Update `tools/TOOL_DESCRIPTIONS.md` in the same change — do not leave a tool undocumented or a description referring to a deleted file; also fails when a CI workflow, pre-commit hook, or `tox.ini` still references a tool that was renamed or deleted |
| Need to run the gates a specific diff/set of changed files requires | `uv run python tools/run_validation_gates.py` | Discovers changed files (staged+unstaged, base overridable via `--base`), maps them to the gates each change needs from the two-source mapping (`rules/toolchain.md` + `routing.md`), runs fast/full modes, prints one `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` summary, and exposes a drift check against `routing.md` |
| A `docs/*.md` file is to be renamed or moved | `uv run python tools/rename_doc.py <old> <new>` (dry-run first, then `--apply`) | Rewrites docs links/`related:` and reports stale old-name mentions outside `docs/` (code, tests, skills, tools) — fix those by hand, then re-run the dry-run for the old path to confirm none remain |
| A `skills/*.md`, `rules/*.md`, or `prompts/*.md` file was added, edited, renamed, or removed | `uv run python tools/check_skills_references.py` | Verifies every backtick-quoted `rules/`/`skills/`/`templates/` (or `AGENTS.md`/`routing.md`) file reference still resolves to a file that exists — catches a dangling reference left behind by a rename, split, or deletion |
| A cross-reference from `AGENTS.md`, `routing.md`, `skills/DESIGN.md`, `rules/*.md`, `skills/**/*.md`, or `prompts/*.md` to another file's section was added or changed | `uv run python tools/check_skills_heading_cycles.py` | Exits 1 when sections of different files reference each other (heading-level cycle). Only references that resolve to a heading are checked; bare file references and same-file references are not |
| A `plans/*.md`, `issues/*.md`, or `implementations/*.md` document is about to be read as a workflow's input, or was just generated as its output (`issue-creator`, `issue-to-plan`, `plan-to-implementation-procedure`, `code-implementation`) | `uv run python tools/check_workitem_structure.py --file <path>` | Verifies every `## ` section required by the matching canonical template (`templates/issue.md`/`templates/plan.md`/`templates/implementation-procedure.md`) is present — catches a structurally incomplete document (e.g. a missing `Implementation Target Files` or `Traceability` section) before a workflow proceeds on it |
| A diff mixes groups (code, tests, tools, docs, workflow artifacts) and the user chose a split commit (`skills/git-commit-and-sync/workflow.md`) | `uv run python tools/classify_changes.py [--status-file <path>]` | Read-only; prints per-group pathspec lists with both names of every rename; exit 1 on partly staged or unmerged paths. `<path>` is a runtime placeholder, so `run_validation_gates.py` reports it `Not available` |
| A Plan is being written for a change to persisted schema, a public API, or a shared constant (`issue-to-plan` Step 3) | `uv run python tools/scan_change_consumers.py --seed <seed>` | One `--seed` per changed symbol, name, constant, or file. Lists candidate consumers only: record each as a target row, a reference row, or a stated "not affected" reason; absence is not evidence; not a gate. `<seed>` is a runtime placeholder, so `run_validation_gates.py` reports it `Not available` |
| Need to check whether any `plans/*.md`/`implementations/*.md` workitem has sat `In Progress`/`Pending` too long | `uv run python tools/manage_workitem_stage.py detect-stale --days <N>` | Flags workitems whose file mtime is older than `--days` (default 7) and whose `### Execution Status` table still shows `In Progress`/`Pending` — a candidate for follow-up, not an automatic `Blocked` |
| A Frozen Plan needs a target file added after freeze (an additional target file discovery in `plan-to-implementation-procedure` Step 3c or `code-implementation`) | `uv run python tools/amend_plan.py <plan> --file <path>` | Add `--responsibility`, `--reason`, `--requirement`, `--evidence`, `--tests`, `--step`, `--class` (fallout or scope; recorded, never decided by the tool), and optionally `--procedure`; run with `--dry-run` first. Refuses an archived Plan and a file already a target or reference row; sets `Draft` when a Freeze criterion fails; prints the structure, path-audit, and overlap checks. `<plan>` and `<path>` are runtime placeholders, so `run_validation_gates.py` reports it `Not available` |
| Need the current list of in-flight `plans/*.md`/`implementations/*.md` workitems, or a single one's `### Execution Status` table | `uv run python tools/manage_workitem_stage.py list --kind <kind> --status <status>` / `... show <kind> <path>` | Read-only status inspection — `list` filters across all workitems of a kind, `show` prints one file's table |
| A Plan is about to be converted to procedures, a procedure is about to be executed, or the order of the open Plans is in question | `uv run python tools/plan_dependency_order.py --plan <path>` | Read-only. Recommends an order and reports each open Plan as `ready` or `gated` with the blocking item; the owner decides the order. Omit `--plan` to list every open Plan |
| The Canonical Source Registry (`config/documentation_canonical_sources.toml`) was added to or modified | `uv run python tools/check_canonical_source_registry.py` | Validates schema conformance, confirms every registered source path exists, enforces the single-normative-source-per-claim-type constraint, and checks Accepted status for ADR-sourced entries |
| Claiming no backward-compat shims remain in `scripts/`, `docs/`, `tests/`, or `tools/` | `uv run python tools/check_compat_shims.py` | |
| A `patch("module.Symbol")` call was added or changed in `tests/`, or a symbol import in `scripts/` moved | `uv run python tools/check_mock_patch_targets.py` | Exits 1 when a patch targets the origin module while the code under test imports the symbol at module level (the mock never takes effect). A false positive is dismissed with `# mock-patch-ok: <reason>` right after the `patch(` open paren; also runs as the `mock-patch-targets` pre-commit hook |
| A `# noqa` / `# type: ignore` / `# nosec` suppression was added | `uv run python tools/check_suppression_justification.py` | Requires a rule/error code plus an em-dash-separated justification |
| Code under a generated-reference domain (`scripts/agent/`, `scripts/eventbus/`, `scripts/agent/memory/`, `scripts/mcp_servers/`, `scripts/db/config.py`, `config/agent.toml`) changed | `uv run python tools/generate_reference_table.py --check` | Exits 1 when a guarded `AUTO-GENERATED` block drifted (ADR-015 INV-01); fix by running the generator with `--type <domain>` and committing the result; also runs in CI (`lint` job) |
| Need the current MCP port/tool reference table | `uv run python tools/generate_reference_table.py --type mcp` | Add `--dry-run` to preview without writing; omit it to refresh the `<!-- AUTO-GENERATED -->` block in place |
| Need the current RAG config reference table | `uv run python tools/generate_reference_table.py --type rag` | Same `--dry-run` behavior as above |
| Need the current DB path/config-key reference table | `uv run python tools/generate_reference_table.py --type deployment` | Same `--dry-run` behavior as above |
| Need the current MCP server inventory (transport, startup mode, tool names) | `uv run python tools/generate_mcp_inventory.py --format json\|csv` | Reads live `config/agent.toml`, not a doc snapshot |
| A module-level docstring header path may be stale after a file move | `uv run python tools/fix_docstring_paths.py --dry-run` | Add `--apply` only after reviewing the dry-run diff |
| Docstring format needs verification (not repair) after touching `scripts/` | `uv run python tools/check_docstrings.py` | Read-only — does not add or fix docstrings |
| Front Matter is missing or a list field has duplicate entries in `docs/*.md` | `uv run python tools/manage_frontmatter.py add-missing` | Report-only (dry-run); `--fix` not passed in the gate |
| A doc or workitem adds Metadata/Status fields or workitem sections outside the sanctioned set | `uv run python tools/check_metadata_field_policy.py` | GV-016; warning (non-blocking, exits 0); runs by pre-commit and CI; scans `docs/` front matter and issues/plans/implementations workitems, skipping `done/` |
| A `docs/10_adr/*.md` file was shortened or reworded without intending to change its decisions | `uv run python tools/check_adr_preservation.py` | Compares against `HEAD` (`--base <ref>` for another ref): ERROR when an invariant, reference, test citation, Known Deviations, or Approval text changed; WARNING when a Decision, Failure Policy, or normative keyword count changed. Token counts are not measured |
| An ADR was added, its front matter `related` changed, or `config/adr_authority.toml` changed | `uv run python tools/check_adr_authority.py` | GV-024; reports `DUP_PRIMARY`/`DANGLING_ADR`/`AUTHORITY_CYCLE`/`ASSUMPTION_DRIFT`/`EDGE_UNKNOWN_TYPE` findings; the front matter/model cross-check (`FRONTMATTER_DIVERGENCE`) runs inside `tools/check_adr_reference.py` via the `adr-reference-scoped` pre-commit hook; also runs in CI (`lint` job) |
| ADR index graph sections need regeneration after a model change | `uv run python tools/generate_adr_authority.py` | GV-025; refreshes the three guarded sections in `docs/10_adr/adr_01_index.md`; add `--check` for the read-only drift gate (exits 1 on drift); also runs in CI (`lint` job) |
| Japanese text may remain in `docs/*.md` (violates `skills/DESIGN.md` Output language) | `uv run python tools/check_docs_japanese.py` | Exits 1 when any is found; also runs as the `docs-japanese` pre-commit hook |
| A test cited by `docs/10_adr/adr_01_index.md` may have been removed or renamed (or the ADR or a source file was) | `uv run python tools/check_adr_invariant_matrix.py` | Hook `adr-invariant-matrix`; fails when a cited test path or node no longer exists |
| A source file cited by an ADR may lack its `# ADR-NNN` marker | `uv run python tools/check_adr_reference.py` | Hook `adr-reference-scoped`; checks `scripts/*.py` files named by the ADR Invariant Matrix |
| An ADR `## Known Deviations` heading or Implementation Notes/References may have drifted | `uv run python tools/check_adr_structure.py` | Hook `adr-structure` |
| A `docs/*.md` file's Known Deviations entry was added or changed | `uv run python tools/check_known_deviation_sync.py` | Hook `known-deviation-sync`; ADR Known Deviations must stay in sync with the governance issue list |
| A `plans/*.md` file was added or its `Implementation Target Files` changed | `uv run python tools/check_plan_target_overlaps.py` | Hook `plan-target-overlaps`; report-only overlap candidates, never a verdict (`skills/plan-to-implementation-procedure/workflow.md` Step 2) |
| A `tests/**/conftest*` file was changed | `uv run python tools/check_conftest_integrity.py` | Hook `conftest-integrity`; verifies the root conftest module exists and keeps its required autouse fixtures |
| A work item under `issues/`, `plans/`, or `implementations/` was added or changed | `uv run python tools/check_workitem_traceability.py --active-only` | Hook `workitem-traceability`; archived items are excluded; about 6.5 seconds, so `run_validation_gates.py` runs it in full mode only |

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
- `rules/persisted-schema-change.md` — persisted SQLite schema, DDL, schema version, or migration changes

## Multiple task types

If a task spans multiple types, load the union of all required skills and docs.
