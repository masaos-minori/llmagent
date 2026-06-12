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

You are performing a Python refactor.
Your task is to change structure without changing external behavior.

Follow all instructions below exactly.

---

## Scope

Use this skill only for structural refactoring, including:
- splitting or merging modules
- removing import cycles
- renaming symbols across files
- restructuring class hierarchies
- migrating public APIs
- improving internal design without changing externally visible behavior

Do not use this skill for:
- adding features
- changing expected behavior
- introducing new business logic
- fixing bugs by intentionally changing outputs or semantics

If the task requires new functionality, use `python-implementation` instead.

---

## Primary rules

You must obey all of the following:

- Preserve external behavior.
- Perform structural change only.
- Execute the refactor in six sequential phases.
- Do not skip phases.
- Do not skip gate checks.
- Do not proceed to the next phase until the current phase gate passes.
- If a gate fails, stop immediately, fix the issue, and rerun the gate.
- Never leave the repository in a broken intermediate state.

---

## Required phase order

Execute the refactor in this exact order:

1. Dependency Mapping
2. Behavior Lock
3. Semantic Transformation
4. Semantic Validation
5. Incremental Migration
6. CI Gate

Do not reorder these phases.

---

## Phase 1 — Dependency Mapping

### Objective
Identify the full blast radius before making any code changes.

### You must
- map all affected modules
- map all imports and reverse dependencies
- identify import cycles
- identify all symbols to be moved, renamed, or removed
- identify all directly and indirectly affected files
- document the blast radius before editing code

### Recommended tools
- `pydeps`
- `import-linter`

### Gate
Do not proceed until:
- the blast radius is documented
- all affected modules are identified
- all impacted imports are identified
- there are no unknown affected files or symbols

If any affected area is still unknown, stop and resolve it first.

---

## Phase 2 — Behavior Lock

### Objective
Lock current behavior before any refactoring begins.

### You must
- add or update characterization tests for current behavior
- measure coverage on refactored paths
- run mutation testing where applicable
- record a diff-cover baseline before structural changes

### Recommended tools
- `pytest`
- `hypothesis`
- `mutmut`
- `diff-cover`

### Gate
Do not proceed until:
- coverage on affected areas is >= 80%
- surviving mutants on refactored paths are 0
- characterization tests pass
- diff-cover baseline is recorded

If behavior is not locked, do not edit production code.

---

## Phase 3 — Semantic Transformation

### Objective
Apply structural changes without changing code meaning.

### You must
- perform controlled or automated transformations
- rename symbols consistently across all affected files
- remove obsolete references
- keep syntax valid after each transformation step
- ensure transformed files remain parseable

### Recommended tools
- `libcst`
- `bowler`
- `ruff`
- `ast-grep`

### Gate
Do not proceed until:
- all transformed files parse successfully
- `ruff` passes
- no obsolete symbol names remain where migration is intended to be complete
- no invalid syntax or broken intermediate transformation exists

If parsing fails or stale symbol references remain, stop and fix them first.

---

## Phase 4 — Semantic Validation

### Objective
Prove that the refactor did not change semantics or type correctness.

### You must
- run static type checks
- run semantic validation checks
- rerun all characterization tests
- compare type-checking results against the pre-refactor baseline

### Recommended tools
- `mypy`
- `pyright`
- `pytest`
- `ast-grep`

### Gate
Do not proceed until:
- characterization tests pass
- `pyright` is clean
- `mypy` error count does not increase
- no semantic regression is detected

If semantics cannot be proven safe, stop immediately.

---

## Phase 5 — Incremental Migration

### Objective
Land the refactor in small, safe, reversible steps.

### You must
- split the refactor into small commits
- keep every intermediate commit valid
- verify each step before creating the next one
- avoid large, unreviewable, multi-risk changesets

### Recommended tools
- `lazygit`
- `pytest`
- `ruff`
- `mypy`

### Gate
Every commit must:
- pass `pytest`
- pass `ruff`
- pass `mypy`
- leave no broken intermediate state

If any intermediate step is broken, do not continue.

---

## Phase 6 — CI Gate

### Objective
Block incomplete or unsafe refactors from being finalized.

### You must
- run full repository validation
- run all pre-commit hooks
- validate import rules
- validate diff coverage after the refactor
- confirm that no migration leftovers remain

### Recommended tools
- `pre-commit`
- `lint-imports`
- `diff-cover`

### Gate
Do not finish until:
- `pre-commit` passes
- `lint-imports` passes
- diff coverage is >= 90%
- no incomplete migration artifacts remain

If CI safety is not proven, the refactor is not complete.

---

## Behavioral guarantees

Your output must preserve all of the following guarantees:

- Blast radius control
  No refactor begins before affected modules and dependencies are fully mapped.

- Behavior preservation
  Existing behavior is locked before structural edits begin.

- Semantic safety
  Syntax, typing, and characterization tests prove semantic equivalence.

- Migration safety
  Every intermediate state remains valid.

- CI safety
  Finalization is blocked until all gates pass.

---

## Mandatory refactoring constraints

These constraints are mandatory. Do not violate them.

- Do not use `assert` in business logic.
  Replace all precondition checks with explicit exceptions.

- Do not use `except Exception`.
  Catch only specific exception types.

- Do not use `dict[str, Any]` outside external boundaries.
  Convert boundary input into typed structures immediately.

- Do not perform unconditional string conversion such as `str(args.get(...))`.
  Validate input types first. Raise explicit exceptions for unexpected types.

- Apply strict typing and strict conversion throughout the codebase.

- Do not treat `None`, empty strings, and unset values as equivalent.
  Handle them explicitly and separately.

- Define dedicated DTOs for:
  - audit logs
  - approval decisions
  - execution results

- Validate all LLM-derived JSON immediately after decoding.
  If the schema is invalid, fail immediately.

- Do not output directly with `print`.
  Route all output through a UI or CLI output interface.

- Do not use fail-open behavior for:
  - unknown tool names
  - unknown tiers
  - unknown metadata

  Use fail-fast behavior instead.

---

## Composition rules

### Run after this skill
- `deploy`
  Use after Phase 6 if scripts or files were added, removed, or renamed.

### Use separately if needed
- `python-implementation`
  Use only if the refactor reveals a true feature gap that requires new implementation.

### This skill may be triggered by
- `python-debug-root-cause`
- `python-issue-to-plan`

Use this skill when the required fix is structural rather than feature-oriented.

---

## Self-correction rule

If, during execution:
- a gate condition is too strict,
- a recovery path is missing,
- or an important validation step is absent,

then update:
- the phase gate definitions in this file
- and/or the detailed procedures in `workflow.md`

Do not weaken safety requirements without explicit justification.

---

## Final execution directive

Execute this refactor as a **behavior-preserving structural migration**.

You must:
- preserve external behavior
- follow all six phases in order
- enforce every gate strictly
- stop immediately on gate failure
- keep every intermediate state valid
- prefer typed, explicit, fail-fast changes
- reject ambiguous or semantically unsafe transformations

If semantic equivalence cannot be demonstrated, do not continue.
