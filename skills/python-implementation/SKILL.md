---
name: python-implementation
description: |
  Use this skill proactively whenever implementing or modifying Python code.
  Apply it to feature development, business logic changes, module creation,
  production code updates, and refactoring that changes implementation behavior.
---

# Python Implementation Skill

## When to use

- adding features, changing business logic, creating new Python modules
- modifying existing production Python code
- refactoring that changes implementation details
- extending existing interfaces or behaviors
- integrating with repository-specific conventions

Use this skill by default for production Python work.

## When not to use

- documentation-only or configuration-only work with no code change
- structural refactoring with no behavior change — see `routing.md` Task → skill
  mapping (Refactor / rename / CST row)

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Task Classification | task type; interface / runtime / security impact |
| 2 | Repository Intelligence | modules, entry points, tests, downstream dependencies |
| 3 | Architecture Boundary Analysis | layer boundaries, dependency direction violations |
| 4 | Convention Extraction | naming, typing (PEP 484/526), error handling, test style |
| 5 | Semantic Safe Modification | smallest change; preserve unrelated behavior; apply modern Python features |
| 6 | Runtime Contract Validation | request/response contracts, MCP endpoint compatibility (MCP changes only) |
| 7 | Observability Injection | structured logging (using `logging` framework) / tracing (skip unless project pattern exists) |
| 8 | Security Validation | Apply `skills/DESIGN.md` Pythonic safety constraints (dynamic execution); also check SQL injection, unvalidated serialization |
| 9 | Validation Orchestration | Run validation tools: `pytest`, `ruff check`, `mypy`/`pyright`; run `python tools/check_no_compat.py` to detect backward compatibility leftovers; separate task-caused from pre-existing failures |
| 10 | Scope Control | diff proportional to task; diff-cover ≥ 90%; benchmark only on hot paths |
| 11 | Production Readiness | Apply `skills/DESIGN.md` Pythonic safety constraints (no placeholders, no debug artifacts); strict typing; docstrings updated for non-obvious or public-facing APIs only (PEP 257) |
| 12 | Knowledge Compression | routing.md, docs/, deploy.sh updated |

See `workflow.md` for detailed phase content including commands and tools.

---

## Fast path

Use only for small, self-contained bug fixes satisfying ALL of:
- ≤ 2 files changed
- no public or runtime-facing interface change
- no architecture boundary change
- no MCP endpoint change
- no performance benchmarking needed

Run phases: 1 → 2 → 4 → 5 → 8 → 9 → 11 → 12. Skip 3, 6, 7, 10 benchmark.
*Note: Even in Fast Path, passing `ruff` and `mypy/pyright` checks in Phase 9 is mandatory.*

---

## Core implementation rules

### Code Correctness & Architecture
- Prefer existing repository patterns over new local inventions
- Prefer typed, explicit, maintainable code
- Prefer small, reviewable diffs
- Do not widen scope without clear necessity
- Do not change unrelated behavior
- Do not treat uncertainty as approval; inspect the repository first
- Do not assume conventions; extract them from nearby code
- Do not consider the task complete until validation (`pytest`, `ruff`, `mypy`) is finished
- Out-of-scope paths: see `skills/DESIGN.md` Out-of-scope paths.

### Pythonic Code Quality & Safety Constraints
See `skills/DESIGN.md` Pythonic safety constraints (mutable defaults, exception handling,
typed data, resource management, dynamic execution, async safety) — apply in full.

### Code Comments
Write a comment only for a non-obvious WHY: a hidden constraint, the reason for a
workaround, or behavior that would surprise a reader — information that cannot be
recovered by reading the code itself. Do not write:
- WHAT the code does (already visible from the code, e.g. `# get the user ID`)
- change history (e.g. "added X", "previously implemented as Y")
- task/ticket ID references (e.g. `(UZU-XXXX)`)

### Production Readiness
See `skills/DESIGN.md` Pythonic safety constraints (no placeholders, no debug artifacts) —
apply before moving to Phase 11.

---

## Composition rules

- `python-lint-typecheck` — Phase 9 reveals lint/type errors not caused by the task
- `python-test-and-fix` — Phase 9 reveals test failures not caused by the task
- `deploy` — after Phase 11 if `scripts/` or `config/` changed
- `issue-to-plan` — if implementation starts from an approved plan in `plans/`, verify scope against the plan before Phase 5
- `code-implementation` — calls this skill in its Step 3 (Implement the feature) when executing an approved implementation procedure from `implementations/*.md`; verify scope against that procedure document, not just the Plan, before Phase 5

---

## Improvement feedback

After using this skill:
- if a phase was unnecessary, update the mandatory or skip conditions
- if a needed step was missing, add it
- if the fast path was too broad or too narrow, refine its conditions

Update the phase definitions in this file and the detailed procedures in `workflow.md` as needed.
