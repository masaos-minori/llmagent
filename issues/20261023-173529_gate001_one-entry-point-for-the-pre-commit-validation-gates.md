# One entry point for the pre-commit validation gates

## Priority
Medium

## Summary
Provide a single command that runs the validation gates a change needs before commit, chosen from the changed files, and prints one pass/fail summary. It should implement `rules/toolchain.md` "Standard validation sequence" and the applicable rows of `routing.md` "When to run which tool", so that neither has to be reassembled by hand each time.

## Background
Validation is currently spread over several places (`Explicit in code`/docs):

- `rules/toolchain.md` lists a 9-step sequence (ruff, mypy, import-linter, ast-grep, bandit, pytest, diff-cover, pre-commit, diff review) plus additional checks (module size, vulture, docs consistency).
- `routing.md` "When to run which tool" lists about 30 conditional checkers keyed to what changed (docs, DB schema, `tools/`, skills, workitems, and so on). `AGENTS.md` Global Rule 9 makes running the applicable ones mandatory.
- `.pre-commit-config.yaml` runs a subset as hooks (ruff, ruff-format, mypy, docs and skills checkers, `check-module-size`, `mock-patch-targets`, and others).
- `.github/workflows/ci.yml` runs another subset (`lint` job: ruff, mypy, bandit, `lint-imports`, DB separation, reference-table drift, docstrings, module size, `pre-commit run --all-files`; `test` job: pytest and diff-cover).
- `tox.ini` defines `lint`, `typecheck`, and `tests` environments only in its `envlist`.
- No `Makefile` or `justfile` exists. `.claude/settings.local.json` contains permissions only, no hooks.

From the hook id list, `bandit`, `lint-imports`, `pytest`, and `diff-cover` do not appear as pre-commit hooks (`Strongly implied by code`: only the hook ids were read, not each hook's `entry`). Those gates are therefore first seen in CI. A recent example is the module size gate change in `d388529d1`, a gate that is enforced in pre-commit and CI.

## Problem
No single place answers "what must I run for this diff". The author or agent has to read `rules/toolchain.md`, then scan the routing table against the changed paths, then run each command. Gates that are not pre-commit hooks can be skipped locally and fail only in CI. The same selection effort is repeated every session.

## Reason for Change
Local feedback before commit is cheaper than a red CI run, and the rule set already exists in prose, so the only missing piece is an executable form. This also supports `AGENTS.md` Global Rule 7 (extract repeated operations into `tools/`).

## Implementation Intent
Add one tool under `tools/` that maps changed paths (from `git diff` against `master`, staged plus unstaged) to the existing checkers and commands and runs them in the documented order. It must call the existing commands, not reimplement their checks, and must not duplicate what pre-commit already runs beyond a single `pre-commit run` step. The mapping should be data (a small table in the tool or a TOML under `config/` if the repository convention allows), kept next to `routing.md` semantics so drift is detectable. It reports each gate with the canonical `Pass`/`Fail`/`Partial`/`Not available`/`Blocked` vocabulary from `rules/ai-execution.md` Repository Tool Usage item 11. Whether to also wire it as a pre-push hook or a skill step is left to the plan.

## Target Files or Areas
- `tools/` (new script; name to be decided)
- `tools/TOOL_DESCRIPTIONS.md`
- `routing.md` "When to run which tool" (reference to the new entry point)
- `rules/toolchain.md` (reference to the new entry point)
- `.pre-commit-config.yaml` and `.github/workflows/ci.yml` (read only for the gate inventory; changes only if the plan decides to align them)

## Required Changes
- Inventory every gate from `rules/toolchain.md`, the `routing.md` table, `.pre-commit-config.yaml`, and `ci.yml`; record which gate runs where.
- Define the path-to-gate mapping and the execution order.
- Implement the tool with a fast mode (changed-file gates only) and a full mode (adds full pytest and diff-cover).
- Emit one summary with per-gate result and the exact failing command.
- Add a drift check, or a test, that fails when a checker named in `routing.md` is missing from the mapping.
- Register the tool in `tools/TOOL_DESCRIPTIONS.md` and reference it from `routing.md` and `rules/toolchain.md`.

## Constraints
- Must run only repository tools and read-only git commands; no network access, no push (`AGENTS.md` Execution policy).
- Must not weaken or replace the CI gates; CI stays the authority.
- `rules/toolchain.md` keeps the canonical command list; the tool must not become a second source of truth that can disagree with it.
- Tool validation follows `routing.md` "Adding a new tool".

## Acceptance Criteria
- On a diff touching only `docs/*.md`, only the docs-related checkers run, and the summary names them.
- On a diff touching `scripts/**/*.py`, the format, lint, type, import-linter, bandit, and targeted test gates run in the documented order.
- A failing gate stops with a non-zero exit and prints its command; a skipped or unavailable gate is reported as such, never as `Pass`.
- The drift check fails when a checker listed in `routing.md` has no mapping entry.
- `uv run python tools/check_tool_descriptions_sync.py` passes.

## Testing Expectations
- Unit tests for path-to-gate selection with fixed fixtures and for result classification.
- A drift test against the real `routing.md`.
- `uv run ruff`, `uv run mypy tools/<file>.py`, and `uv run bandit tools/<file>.py` clean.
- A smoke run on the current working tree and on one historical diff (such as `d388529d1`), recorded as evidence.

## Documentation Impact
`tools/TOOL_DESCRIPTIONS.md` needs a row; `routing.md` and `rules/toolchain.md` need a pointer. Content: intent, the two modes, the fact that CI remains authoritative, and how the mapping is kept in sync. Run the skills reference checkers listed in `routing.md` after editing those files.

## Out of Scope
- Adding or removing any gate, or changing a gate's thresholds.
- Changing CI workflows or the pre-commit hook set (unless the plan separately decides so).
- Auto-fixing findings.
- Commit or push automation (`skills/git-commit-and-sync` keeps that role).

## Dependencies
Sibling-issue check: no open issue under `issues/` (`turn006` and `eventbus001` to `eventbus008`) covers validation orchestration (`N/A: none` overlap). Related but independent: the batch-closing tool issue `20261023-173429_workitem001_*` (both add `tools/` entries and edit `tools/TOOL_DESCRIPTIONS.md`, so merge order may matter).

## Unresolved Questions
- Which gates are in fact absent from pre-commit? Only hook ids were inspected. Confirm by reading each hook's `entry`.
- Is a full pytest run acceptable as part of a local gate given its duration? Unknown (the suite size and runtime were not measured).
- Should the mapping live in the tool, a config file, or be generated from `routing.md`? Parsing a prose table is brittle; undecided.
- Is a pre-push hook wanted, or only an on-demand command?

## AI Implementation Instruction
Reuse existing checkers; do not reimplement them. Keep changes limited to the target files. Do not edit `ci.yml` or `.pre-commit-config.yaml` unless the plan says so. Do not change gate thresholds. Stop and report if the gate inventory and `rules/toolchain.md` contradict each other, instead of choosing one silently.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261023-173529
- **Related target files**: `tools/TOOL_DESCRIPTIONS.md`, `routing.md`, `rules/toolchain.md`, `.pre-commit-config.yaml`, `.github/workflows/ci.yml`
