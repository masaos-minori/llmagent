---
name: python-refactoring
description: |
  Use this skill only when refactoring existing Python code without changing external behavior.
  Execute the refactor through a mandatory 6-phase process with strict gates between phases.
  Use this skill for structural changes only: module splits, import-cycle removal, cross-file renames,
  class hierarchy restructuring, and public API migration.
  Do NOT use this skill for feature development or intentional behavior changes.
---

# Python Refactoring Skill

## Scope

Use this skill only for structural refactoring, including:
- splitting or merging modules
- removing import cycles
- renaming symbols across files
- restructuring class hierarchies
- migrating public APIs
- improving internal design without changing externally visible behavior

Do not use for: adding features, changing expected behavior, introducing business logic, or fixing bugs by changing outputs. Use `python-implementation` instead.

---

## Phase overview

| Phase | Name | Gate |
|---|---|---|
| 1 | Dependency Mapping | blast radius documented; all affected modules and imports identified |
| 2 | Behavior Lock | coverage ≥ 80%; 0 surviving mutants on refactored paths; diff-cover baseline recorded |
| 3 | Semantic Transformation | ruff clean; all transformed files parse; no old symbol names remain |
| 4 | Semantic Validation | mypy error count unchanged; pyright clean; all characterization tests pass |
| 5 | Incremental Migration | every commit passes pytest + ruff + mypy; no broken intermediate state |
| 6 | CI Gate | pre-commit passes; lint-imports passes; diff-cover ≥ 90% |

See `workflow.md` for detailed phase content including commands, tools, and failure recovery.

---

## Mandatory refactoring constraints

These apply regardless of the refactor type. Do not violate.

- Do not use `assert` in business logic — use explicit exceptions
- Do not use `except Exception` — catch only specific types
- Do not use `dict[str, Any]` outside external boundaries — convert to typed structures immediately
- Do not perform unconditional string conversion (`str(args.get(...))`) — validate types first
- Do not treat `None`, empty strings, and unset values as equivalent — handle each explicitly
- Do not output directly with `print` — route through a UI or CLI output interface
- Do not use fail-open behavior for unknown tool names, tiers, or metadata — use fail-fast
- Define dedicated DTOs for audit logs, approval decisions, and execution results
- Validate all LLM-derived JSON immediately after decoding; fail immediately on schema violation
- Apply strict typing and strict conversion throughout

---

## Composition rules

### Run after this skill
- `deploy` — if scripts/ files were added, removed, or renamed

### Use separately if needed
- `python-implementation` — only if the refactor reveals a feature gap requiring new code

### This skill may be triggered by
- `python-debug-root-cause`
- `python-issue-to-plan`

---

## Improvement feedback

After running this skill:
- if a gate condition was too strict or too loose, update the phase overview gate column
- if a recovery path was missing for a common failure mode, add it to `workflow.md`

Do not weaken safety requirements without explicit justification.
