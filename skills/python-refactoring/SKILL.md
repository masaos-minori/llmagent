---
name: python-refactoring
description: |
  Use this skill when refactoring existing Python code without changing external behavior.
  Covers the full 6-phase tool chain: dependency mapping, behavior lock, semantic
  transformation, semantic validation, incremental migration, and CI gate.
  Apply when splitting modules, resolving import cycles, renaming symbols across files,
  restructuring class hierarchies, or migrating public APIs.
  Do NOT use when adding new features — use python-implementation instead.
---

# Python Refactoring Skill

## Purpose

Restructure Python code safely and verifiably across six sequential phases.
Every phase produces a gate condition that must pass before the next phase begins.

## Primary goals

- preserve observable behavior across all refactoring steps (characterization guarantee)
- detect import cycles and blast radius before writing a single line (blast radius guarantee)
- apply code transforms at the syntax tree level, not with regex (semantic safety guarantee)
- land each change as a small, bisect-safe, independently-revertable commit (migration safety guarantee)

## Guarantees

| Guarantee | Enforced by |
|---|---|
| **Blast radius** | Phase 1: pydeps + import-linter map every affected module before changes begin |
| **Characterization** | Phase 2: pytest + hypothesis + mutmut lock existing behavior before any code change |
| **Semantic safety** | Phase 3+4: libcst/bowler transform + mypy/pyright/ast-grep verify no meaning change |
| **Migration safety** | Phase 5+6: one-step-one-commit via lazygit; CI gate blocks incomplete migrations |

---

## Toolchain

| Tool | Phase | Role |
|---|---|---|
| `pydeps` | Dependency Mapping | Visualize import graph; surface cycles and blast radius |
| `import-linter` | Dependency Mapping / CI Gate | Enforce and verify module boundary contracts |
| `rg` | Dependency Mapping | Symbol usages, log strings, config keys |
| `ast-grep` | Dependency Mapping / Semantic Validation | Structural search and post-transform call-site verification |
| `pytest` | Behavior Lock / CI Gate | Run and lock existing behavior |
| `pytest-cov` | Behavior Lock | Coverage baseline before touching code |
| `hypothesis` | Behavior Lock | Property-based tests for parsers/validators |
| `mutmut` | Behavior Lock | Validate test suite strength before trusting it |
| `diff-cover` | Behavior Lock / CI Gate | Coverage scoped to changed lines |
| `libcst` | Semantic Transformation | CST-preserving transforms: rename, signature change |
| `bowler` | Semantic Transformation | Query-based bulk refactoring with dry-run |
| `mypy` | Semantic Validation | Primary type checker after structural changes |
| `pyright` | Semantic Validation | Cross-validation type checker |
| `ruff` | Semantic Validation | Format normalization and lint after transforms |
| `git` | Incremental Migration | Atomic commits per step; bisect-safe history |
| `lazygit` | Incremental Migration | Hunk-level staging, stash management |
| `pre-commit` | CI Gate | Final gate: ruff + mypy before each commit |

---

## Phase overview

| Phase | Name | Gate condition |
|---|---|---|
| 1 | Dependency Mapping | blast radius documented; no unknown affected modules |
| 2 | Behavior Lock | coverage ≥ 80%; 0 surviving mutants on refactored paths; diff-cover baseline recorded |
| 3 | Semantic Transformation | ruff clean; transformed files parse; no old symbol names remain |
| 4 | Semantic Validation | mypy error count unchanged; pyright clean; characterization tests pass |
| 5 | Incremental Migration | every commit passes pytest + ruff + mypy; no broken intermediate state |
| 6 | CI Gate | pre-commit passes; lint-imports passes; diff-cover ≥ 90% |

---

See `workflow.md` for detailed phase content.

## Composes with

- `deploy` — run after Phase 6 if scripts/ files were added, removed, or renamed
- `python-implementation` — if the refactor reveals a feature gap that must be filled separately

## Called by

- `python-debug-root-cause` — when root cause is a structural issue requiring refactor
- `python-issue-to-plan` — when a plan's implementation steps include structural changes

## Improvement feedback

After running this skill, if a phase gate condition was too strict or a recovery path was missing:
update the phase overview gate conditions or add to workflow.md.
