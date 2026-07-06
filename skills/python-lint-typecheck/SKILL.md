---
name: python-lint-typecheck
description: |
  Use this skill PROACTIVELY when fixing Python code quality issues, lint errors,
  type mismatches, static security findings, or CI pipeline failures.
  Covers: repository convention enforcement, architecture integrity, suppression governance,
  semantic refactor safety, type flow analysis, static security validation,
  diff scope enforcement, CI consistency validation, and repository knowledge compression.
  Do NOT add broad suppression comments unless explicitly justified.
---

# Lint Typecheck Skill

## Purpose

Resolve Python code quality issues; fix root causes rather than suppressing warnings; maintain a minimal, clean diff scope.

---

## Core Quality Rules (Strictly Enforced for AI)

- **Fix the Root Cause, Do Not Ignore**: Resolving a type/lint error by blindly adding `# type: ignore` or `# noqa` is considered a failure. You must attempt to fix the underlying type signature or code structure first.
- **No Tool Hallucination**: If advanced tools (e.g., `ast-grep`, `LibCST`, `lint-imports`) are not installed in the current environment, **do not invent their success messages**. Document "Tool [name] not available" and fallback to standard verification (`ruff`, `mypy`, or manual static analysis).
- **Strict Diff Isolation**: When running automated formatters or fixers (`ruff check --fix`), ensure you only stage and commit changes strictly relevant to the target issue. Do not reformat unrelated codeblocks.

---

## Routing (Fast Path Assessment)

Before running the full sequence, look at the error log and check if the failure source is already known. If known, you may fast-track the execution:

- [ ] **Ruff Error / Formatting Issue** → Start directly at **Step 2**
- [ ] **Import / Layering Violation (`lint-imports`)** → Start directly at **Step 3**
- [ ] **Type Error (`mypy` / `pyright`)** → Start directly at **Step 6**
- [ ] **Security Finding (`bandit`)** → Start directly at **Step 7**

*If multiple tools are failing or the source is ambiguous, you must run the full sequence from Step 1.*

---

## Phase overview

| Step | Name | Goal / AI Action |
|---|---|---|
| 1 | Identify failure source | Run validation tools or inspect logs to pinpoint which check is failing. |
| 2 | Repository convention enforcement | Run `ruff format` first (formatting), then `ruff check` (lint). Use `ast-grep` for structural pattern checks if available. |
| 3 | Architecture integrity | Validate layering with `uv run lint-imports` (config: `.importlinter`). Layer contract: `shared → db → rag/mcp → agent`; violations must be fixed structurally, not suppressed. Also run `python tools/check_no_compat.py` to detect backward compatibility leftovers in source and docs. |
| 4 | Suppression governance | **Audit step**: If any `# noqa`, `# type: ignore`, or `# nosec` is absolutely necessary, you must provide a rigorous, comments-based justification directly above the line. |
| 5 | Semantic refactor safety | Use `LibCST` or structural modifiers when performing comment/formatting-preserving transformations. |
| 6 | Type flow analysis | Run `mypy` and `pyright` to ensure zero type errors. Ensure strict type flow in public interfaces. |
| 7 | Static security validation | Run `bandit`. Address high/medium severity issues (especially B105/B608) before proceeding. |
| 8 | Diff scope enforcement | Check your changes against git diff. Ensure `diff-cover ≥ 90%` on newly changed or added lines. |
| 9 | CI consistency validation | Run `tox` or execution environment tests across all target Python environments. |
| 10 | Minimal change principle | Stage changes individually. Ensure no broad or automated reformats bleed into unrelated code. |
| 11 | Repository knowledge compression | If configuration patterns or rule exclusions were updated, update `CLAUDE.md`, `pyproject.toml`, or `.pre-commit-config.yaml`. |

---

## Mandatory Audit Log Template for Step 4 (Suppression Governance)

If you must suppress a lint, type, or security warning because a proper fix is technically impossible or introduces a breaking change, you must document it in your final response using the following format:

### Suppression Audit Record
- **File Path**: `path/to/file.py`
- **Line Number / Code Snippet**: `...  # type: ignore[attr-defined]`
- **Tool & Rule ID**: (e.g., Mypy `attr-defined` / Ruff `F401`)
- **Technical Justification**: [Explain exactly why this cannot be fixed safely using native type structures or architectural adjustments]

---

## See Also
See `workflow.md` for detailed phase content, commands, and options.

## Composes with

- `python-implementation` — run if the quality fix requires adding new feature code beyond the lint/type alignment.
- `python-refactoring` — run if the quality fix requires restructuring modules to eliminate architectural or import cycle violations.

## Improvement feedback

After running this skill, if a step was unnecessary for the task type or a recovery path was missing:
update the routing rules in this file or add the specific tool recovery commands to `workflow.md`.
