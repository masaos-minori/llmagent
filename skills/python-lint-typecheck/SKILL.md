---
name: python-lint-typecheck
description: |
  Use this skill PROACTIVELY when fixing Python code quality issues, lint errors,
  type mismatches, static security findings, or CI pipeline failures.
  Covers: repository convention enforcement, architecture integrity, suppression governance,
  semantic refactor safety, type flow analysis, static security validation,
  diff scope enforcement, CI consistency validation, and repository knowledge compression.
  Add a suppression comment only with the Step 4 justification format; otherwise fix the
  underlying issue.
---

# Lint Typecheck Skill

## Purpose

Resolve Python code quality issues; maintain a minimal, clean diff scope (see Core
Quality Rules below for the root-cause-first requirement).

---

## Core Quality Rules (Strictly Enforced for AI)

- **Fix the Root Cause, Do Not Ignore**: Blindly adding `# type: ignore` or `# noqa` to resolve a type/lint error is a failure. You MUST first attempt to fix the underlying type signature or code structure.
- **No Tool Hallucination**: applies to every tool a Step runs — `ruff`, `mypy`, `pyright`, `pyre`, `bandit`, `ast-grep`, `LibCST`, `lint-imports`, `tox`, `diff-cover` — see `skills/DESIGN.md` Tool availability guard. Run Python tools through `uv run`, and test availability the same way (`uv run <tool> --version`): `pyright`, `pyre`, and `tox` are not on PATH here but work under `uv run`, so `command -v` gives a false "not installed".
- **Strict Diff Isolation**: When running automated formatters or fixers (`ruff check --fix`), keep changes scoped to the target issue — see `AGENTS.md` Global Rule 5. Review only your own changes with `git diff <path>`; MUST NOT `git stash` or reset in the working tree to isolate them (parallel sessions leave unstaged edits there), and revert an unwanted auto-fix hunk by editing the lines back.
- **CI Parity, Not Stricter**: fix what the project's CI and pre-commit configuration report. A stricter run (for example `mypy --strict`) is investigation only; its extra findings are recorded, not fixed.

---

## Routing (Fast Path Assessment)

Before running the full sequence, check the error log for a known failure source. If known, you may fast-track:

- [ ] **Ruff Error / Formatting Issue** → Start directly at **Step 2**
- [ ] **Import / Layering Violation (`lint-imports`)** → Start directly at **Step 3**
- [ ] **Type Error (`mypy` / `pyright`)** → Start directly at **Step 6**
- [ ] **Security Finding (`bandit`)** → Start directly at **Step 7**
- [ ] **Suppression without justification (`# noqa`/`# type: ignore`/`# nosec`)** → Start directly at **Step 4**
- [ ] **Other CI or pre-commit gate (DB separation, reference-table drift, docstring format, module size, a pre-commit hook, ADR tests)** → Start directly at **Step 9** (CI-only gates table in `workflow.md`)

*If multiple tools are failing or the source is ambiguous, you MUST run the full sequence from Step 1.* The list of CI steps lives in `.github/workflows/ci.yml` (the `lint` job); map the failing step name to a Step via the CI-step table in `workflow.md`.

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 1 | Identify failure source | Run validation tools or inspect logs to pinpoint the failing check. |
| 2 | Repository convention enforcement | Run `ruff format` first (formatting), then `ruff check` (lint). Use `ast-grep` for structural pattern checks if available. |
| 3 | Architecture integrity | Validate layering with `PYTHONPATH=scripts uv run lint-imports` (config: `.importlinter`) against the layer contract in `skills/DESIGN.md` Import layer contract; violations MUST be fixed structurally, not suppressed. Also run `uv run python tools/check_compat_shims.py` to detect backward compatibility leftovers in source and docs. |
| 4 | Suppression governance | **Audit step** (suppressions this task adds or touches): If any `# noqa`, `# type: ignore`, or `# nosec` is absolutely necessary, you MUST provide a rigorous, comments-based justification directly above the line. Report other unjustified suppressions; do not fix them. |
| 5 | Semantic refactor safety | Use `LibCST` or structural modifiers for comment/formatting-preserving transformations. |
| 6 | Type flow analysis | Run `mypy` (CI invocation) to zero errors, and `pyright` on the changed files as a cross-check (findings elsewhere are recorded, not fixed). Ensure strict type flow in public interfaces. `pyre` is not used unless asked (no `.pyre_configuration`; see `workflow.md` Step 6). |
| 7 | Static security validation | Run `bandit`. Address high/medium severity issues (see `rules/coding.md` Bandit priority findings) before proceeding. |
| 8 | Diff scope enforcement | Confirm the diff contains only the target fixes (`git diff <path>`); run diff-scoped coverage (`rules/toolchain.md` §7) only when a fix changed runtime behavior. |
| 9 | CI consistency validation | Run the CI `lint` job's commands and `pre-commit run --files <changed files>` (never `--all-files`) (or `uv run tox` where the `tox.ini` envs `lint`, `typecheck`, `tests` apply); fix the CI-only gates in the table in `workflow.md`. |
| 10 | Minimal change principle | Review your diff only (no stash/reset); unrelated-reformat prohibition: `AGENTS.md` Global Rule 5. Commits go through `git-commit-and-sync`. |
| 11 | Repository knowledge compression | If configuration patterns or rule exclusions were updated, record the needed `pyproject.toml`/`.pre-commit-config.yaml`/`.importlinter` change as part of the task (it is the fix itself) and propose any documentation updates instead of editing docs unprompted. |

---

## Mandatory Audit Log Template for Step 4 (Suppression Governance)

If you must suppress a lint, type, or security warning because a proper fix is technically impossible or introduces a breaking change, you MUST document it in your final response using the audit record format in `rules/coding.md` Suppression governance.

---

## See Also
See `workflow.md` for detailed phase content, commands, and options.

## Called by

- `code-implementation` — Step 3e's validation guidance.
- `git-commit-and-sync` — when lint or type gates fail in pre-commit or post-sync validation.

## Final response

Report: the failing check and its cause; the fix; the check-only commands run and their results (confirming each examined a non-empty target); every suppression added, in the audit record format; the Step 8 result or `diff-cover: not applicable`; the findings recorded instead of fixed (stricter-run findings, unjustified suppressions elsewhere, low-severity bandit findings, unrelated gate failures); and that the changes are uncommitted, so `git-commit-and-sync` commits them on request.

## Composes with

- `python-implementation` — run if the quality fix requires adding new feature code beyond the lint/type alignment.
- `python-refactoring` — run if the quality fix requires restructuring modules to eliminate architectural or import cycle violations.
- `python-test-and-fix` — if a type or lint fix makes a test fail, or Step 8 needs a test for a behavior-changing fix.
- `python-code-review` — when the user asks for a review of the quality fix.
- `git-commit-and-sync` — to stage, commit, and push the result on request; this skill never commits on its own.
- `deploy` — only if the fix is meant to reach `/opt/llm`.

## Improvement feedback

If a step was unnecessary for the task type or a recovery path was missing: update the routing rules here or add the tool recovery commands to `workflow.md`.
