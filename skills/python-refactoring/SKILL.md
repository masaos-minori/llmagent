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

Restructure Python code safely across six sequential phases without changing external behavior; every phase has a gate condition that must pass before the next begins.

## Guarantees

| Guarantee | Enforced by |
|---|---|
| **Blast radius** | Phase 1: pydeps + import-linter map every affected module before changes begin |
| **Characterization** | Phase 2: pytest + hypothesis + mutmut lock existing behavior before any code change |
| **Semantic safety** | Phase 3+4: libcst/bowler transform + mypy/pyright/ast-grep verify no meaning change |
| **Migration safety** | Phase 5+6: one-step-one-commit via lazygit; CI gate blocks incomplete migrations |

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
