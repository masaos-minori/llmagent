---
name: python-lint-typecheck
description: |
  Use this skill PROACTIVELY when fixing Python code quality issues.
  Covers: repository convention enforcement, architecture integrity, suppression governance,
  semantic refactor safety, type flow analysis, static security validation,
  diff scope enforcement, CI consistency validation, and repository knowledge compression.
  Use when resolving lint errors, type errors, security findings, CI failures,
  or performing safe structural refactors.
---

# Lint Typecheck Skill

## Purpose

Resolve Python code quality issues using the project's full toolchain while preserving
correctness, readability, and minimal change scope.

## Primary goals

- fix root causes, not suppress warnings
- maintain minimal diff scope
- preserve behavior unless explicitly required to change
- keep all static checks fully passing
- ensure consistency across multiple type checkers

---

## Toolchain

| Tool | Goal | Role |
|---|---|---|
| `ruff` | repository convention enforcement | Format and lint; auto-fix safe violations |
| `ast-grep` | convention enforcement, architecture integrity | Structural search and pattern enforcement |
| `mypy` | type flow analysis | Primary static type checker |
| `pyright` | type flow analysis | Alternate type checker; cross-validates mypy |
| `pyre` | type flow analysis | Strict inference on protocols/TypedDict |
| `bandit` | static security validation | Vulnerability scan |
| `diff-cover` | diff scope enforcement | Coverage gate scoped to changed lines |
| `tox` | CI consistency validation | Runs full check suite in isolated envs |
| `libcst` | semantic refactor safety | CST-based transforms preserving comments |
| `pre-commit` | — | Aggregated hook runner; final gate |

---

## Phase overview

| Step | Name | Goal |
|---|---|---|
| 1 | Identify failure source | run tools to determine which is failing; use fast path if source is known |
| 2 | Repository convention enforcement | ruff format + lint; ast-grep structural checks |
| 3 | Architecture integrity | lint-imports; cross-reference with ast-grep |
| 4 | Suppression governance | audit noqa / type: ignore / nosec with justification |
| 5 | Semantic refactor safety | LibCST for comment/formatting-preserving transforms |
| 6 | Type flow analysis | mypy + pyright; pyre only for Protocol/TypedDict-heavy modules |
| 7 | Static security validation | bandit; address B105/B608 before merge |
| 8 | Diff scope enforcement | diff-cover ≥ 90% on changed lines |
| 9 | CI consistency validation | tox in all envs |
| 10 | Minimal change principle | stage individually; no broad reformat of unrelated code |
| 11 | Repository knowledge compression | CLAUDE.md, .importlinter, pyproject.toml, .pre-commit-config.yaml |

**Fast path** — if the failing tool is already known from the error message:
- `ruff` error → start at Step 2
- `mypy` error → start at Step 6
- `lint-imports` violation → start at Step 3
- `bandit` finding → start at Step 7

**Execution policy** — run non-destructive commands (file reads, grep, lint, type checks, tests) directly without asking for user confirmation. These are always safe to execute; user approval before each run is explicitly not required.

---

See `workflow.md` for detailed phase content.
See `rules/coding.md` for prohibited behavior and conventions.
See `rules/toolchain.md` for the standard validation sequence.

## Composes with

- `python-implementation` — run if the fix requires adding new code beyond the lint/type fix
- `python-refactoring` — run if the fix requires restructuring to eliminate an import cycle

## Improvement feedback

After running this skill, if a step was unnecessary for the task type or a recovery path was missing:
update the phase overview skip criteria or add to workflow.md.
