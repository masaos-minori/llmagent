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
- removing import cycles cleanly without resorting to anti-patterns
- renaming symbols across files safely
- restructuring class hierarchies and modernizing design patterns
- migrating public APIs while preserving backward compatibility
- improving internal design and maintainability without changing externally visible behavior

Do not use for: adding features, changing expected behavior, introducing business logic, or fixing bugs by changing outputs. Use `python-implementation` instead.

---

## Phase overview

| Phase | Name | Gate |
|---|---|---|
| 1 | Dependency Mapping | Blast radius documented; all affected modules, internal/external imports, and public API impact identified |
| 2 | Behavior Lock | Test coverage ≥ 80%; 0 surviving mutants on refactored paths (via `mutmut` if installed, else skip mutation check and note it); characterization/snapshot tests recorded |
| 3 | Semantic Transformation | Ruff clean; all transformed files parse correctly; no old symbol names remain; AST-safe transformations applied |
| 4 | Semantic Validation | Mypy error count unchanged or decreased; Pyright clean; all characterization and regression tests pass |
| 5 | Incremental Migration | Every commit passes pytest + ruff + mypy; no broken intermediate state; backward compatibility layers functional |
| 6 | CI Gate | Pre-commit passes; lint-imports passes; diff-cover ≥ 90% |

See `workflow.md` for detailed phase content including commands, tools, and failure recovery.

---

## Mandatory refactoring constraints

These apply regardless of the refactor type. Do not violate.

### Code Correctness & Safety
- Do not use `assert` in business logic — use explicit exceptions
- Do not use `except Exception` — catch only specific types
- Do not use `dict[str, Any]` outside external boundaries — convert to typed structures (e.g., `dataclasses`, `Pydantic`, or `TypedDict`) immediately
- Do not perform unconditional string conversion (`str(args.get(...))`) — validate types first
- Do not treat `None`, empty strings, and unset values as equivalent — handle each explicitly
- Do not output directly with `print` — route through logging framework or a UI/CLI output interface
- Do not use fail-open behavior for unknown tool names, tiers, or metadata — use fail-fast

### Refactoring & Python Architecture Standards
- **Maintain Backward Compatibility**: When migrating public APIs, do not abruptly delete old symbols. Retain them as deprecated aliases using `warnings.warn(..., DeprecationWarning)` until the migration is fully deprecated.
- **Clean Import Cycle Resolution**: Avoid heavy reliance on local/lazy imports inside functions to fix import cycles. Instead, resolve them by extracting interfaces (`typing.Protocol`), introducing abstract base classes, or isolating type-only hints inside `if TYPE_CHECKING:` blocks.
- **Synchronize Documentation**: When renaming or shifting symbols, classes, or modules, immediately update all corresponding docstrings (PEP 257), type annotations, and inline comments to reflect the new structure.
- **Favor Modern Python Features**: Where appropriate, refactor redundant conditional logic or rigid class hierarchies into modern constructs like structural pattern matching (`match-case`), structural typing (`Protocol`), or structural configuration.

### Domain Models & Data Integrity
- Define dedicated DTOs for audit logs, approval decisions, and execution results
- Validate all LLM-derived JSON immediately after decoding; fail immediately on schema violation
- Apply strict typing and strict conversion throughout

---

## Composition rules

### Run after this skill
- `deploy` — if scripts/ files were added, removed, or renamed
- `python-documentation` — if public interfaces or module names changed, update corresponding docs

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
