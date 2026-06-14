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
- structural refactoring with no behavior change → use `python-refactoring` instead

---

## Phase overview

| Phase | Name | Goal |
|---|---|---|
| 1 | Task Classification | task type; interface / runtime / security impact |
| 2 | Repository Intelligence | modules, entry points, tests, downstream dependencies |
| 3 | Architecture Boundary Analysis | layer boundaries, dependency direction violations |
| 4 | Convention Extraction | naming, typing, error handling, test style |
| 5 | Semantic Safe Modification | smallest change; preserve unrelated behavior |
| 6 | Runtime Contract Validation | request/response contracts, MCP endpoint compatibility (MCP changes only) |
| 7 | Observability Injection | structured logging / tracing (skip unless project-wide pattern exists) |
| 8 | Security Validation | file I/O, subprocess, SQL, shell, credentials, serialization |
| 9 | Validation Orchestration | tests, lint, type checks; separate task-caused from pre-existing failures |
| 10 | Scope Control | diff proportional to task; diff-cover; benchmark only on hot paths |
| 11 | Production Readiness | code/tests/typing/config consistent; no placeholders or debug leftovers |
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

---

## Core implementation rules

- Prefer existing repository patterns over new local inventions
- Prefer typed, explicit, maintainable code
- Prefer small, reviewable diffs
- Do not widen scope without clear necessity
- Do not change unrelated behavior
- Do not treat uncertainty as approval; inspect the repository first
- Do not assume conventions; extract them from nearby code
- Do not consider the task complete until validation is finished

---

## Composition rules

- `python-lint-typecheck` — Phase 9 reveals lint/type errors not caused by the task
- `python-test-and-fix` — Phase 9 reveals test failures not caused by the task
- `deploy` — after Phase 11 if `scripts/` or `config/` changed

---

## Improvement feedback

After using this skill:
- if a phase was unnecessary, update the mandatory or skip conditions
- if a needed step was missing, add it
- if the fast path was too broad or too narrow, refine its conditions

Update the phase definitions in this file and the detailed procedures in `workflow.md` as needed.
