---
name: python-implementation
description: |
  Use this skill proactively whenever implementing or modifying Python code.
  Apply it to feature development, business logic changes, module creation,
  production code updates, and refactoring that changes implementation behavior.
  This skill enforces architecture boundaries, dependency awareness, repository
  conventions, semantic safety, runtime contract validation, observability,
  security checks, validation orchestration, scope control, production readiness,
  and repository knowledge compression.
---

# Python Implementation Skill

You are implementing or modifying Python code.
Follow this skill proactively unless the task is clearly unrelated to Python implementation.

---

## When to use

Use this skill when the task includes any of the following:
- adding features
- changing business logic
- creating new Python modules
- modifying existing production Python code
- refactoring that changes implementation details
- extending existing interfaces or behaviors
- integrating with repository-specific conventions

Use this skill by default for production Python work.

---

## When not to use

Do not use this skill when:
- the task is only documentation-only work
- the task is only configuration explanation with no code change
- the task is only deployment execution with no Python implementation change

If the task is only structural refactoring with no behavior change, prefer `python-refactoring`.

---

## Primary objective

Implement Python code safely, consistently, and in alignment with the repository.

You must:
- follow existing project conventions before introducing new patterns
- prefer small, verifiable changes
- understand repository structure before editing code
- validate behavior before considering the task complete
- keep the implementation inside the approved scope

---

## Execution rule

Execute the phases in order.

Do not skip mandatory phases.
Skip optional phases only when the defined skip condition applies.
If a phase reveals missing information or blocking issues, stop, resolve them, and continue only after the issue is understood.

---

## Phase 1 — Task Classification

### Objective
Determine exactly what kind of implementation task this is.

### You must
- classify the task as one or more of:
  - feature addition
  - business logic change
  - bug fix
  - module creation
  - interface change
  - refactor with behavior impact
- determine whether the task changes:
  - public interfaces
  - runtime contracts
  - data models
  - external integrations
  - security-sensitive behavior

### Mandatory
Yes

### Skip condition
Do not skip.

---

## Phase 2 — Repository Intelligence

### Objective
Understand the repository before changing code.

### You must
- identify the relevant modules, entry points, tests, and configuration
- inspect nearby implementations before writing new patterns
- identify existing utilities, abstractions, and shared helpers
- identify impacted files and likely downstream dependencies

### Mandatory
Yes

### Skip condition
Do not skip.

---

## Phase 3 — Architecture Boundary Analysis

### Objective
Ensure the implementation respects module and layer boundaries.

### You must
- identify architectural boundaries relevant to the change
- check whether the task crosses application, domain, infrastructure, API, or adapter boundaries
- avoid introducing dependency direction violations
- avoid leaking internal concerns across layers

### Mandatory
Yes

### Skip condition
Do not skip, except in the fast path.

---

## Phase 4 — Convention Extraction

### Objective
Match the repository’s existing coding and design conventions.

### You must
- infer naming conventions, typing style, error-handling style, DTO usage, logging style, and test style from the repository
- follow existing patterns unless there is a strong reason not to
- prefer consistency over inventing a new local pattern

### Mandatory
Yes

### Skip condition
Do not skip.

---

## Phase 5 — Semantic Safe Modification

### Objective
Modify or add code without introducing unnecessary semantic risk.

### You must
- make the smallest change that fully solves the task
- preserve unrelated behavior
- keep edits localized where possible
- avoid opportunistic rewrites outside the task scope
- maintain compatibility with surrounding code unless an intentional interface change is required

### Mandatory
Yes

### Skip condition
Do not skip.

---

## Phase 6 — Runtime Contract Validation

### Objective
Validate runtime contracts for integration-facing changes.

### You must
- validate request/response contracts
- validate input/output schema assumptions
- validate endpoint or tool interface compatibility
- validate MCP behavior if MCP endpoints are involved

### Mandatory
Yes, only when MCP-related interfaces are changed

### Skip condition
Skip only when the task does not touch MCP endpoints or equivalent runtime-facing contracts.

---

## Phase 7 — Observability Injection

### Objective
Add or improve observability when the project expects it.

### You should
- add structured logging, metrics, tracing hooks, or operational diagnostics
- align any observability additions with existing project-wide patterns
- avoid introducing one-off observability styles

### Mandatory
No

### Skip condition
Skip unless:
- the project already adopts observability patterns project-wide, or
- the task explicitly requests observability changes

---

## Phase 8 — Security Validation

### Objective
Check for security impact when the code interacts with sensitive operations.

### You must
perform security validation if the task changes any of the following:
- file I/O
- subprocess execution
- SQL generation or execution
- shell command construction
- external service calls with credentials
- serialization or deserialization boundaries
- permission or approval logic

### Mandatory
Yes, when security-relevant code is affected

### Skip condition
Skip only for pure business logic changes with no security-sensitive surface.

---

## Phase 9 — Validation Orchestration

### Objective
Run the required validation steps for the implemented change.

### You must
- run tests relevant to the task
- run lint checks
- run type checks
- validate changed behavior and unchanged expected behavior
- distinguish task-caused failures from pre-existing failures

### Mandatory
Yes

### Skip condition
Do not skip.

### Composition rule
- If lint or type errors are revealed and are not caused by the task, use `python-lint-typecheck`.
- If test failures are revealed and are not caused by the task, use `python-test-and-fix`.

---

## Phase 10 — Scope Control

### Objective
Keep the change set proportional and justified.

### You must
- confirm that the diff is limited to the actual task scope
- avoid unrelated cleanup unless required for correctness
- verify diff coverage for changed code
- benchmark only if the task affects a known hot path or performance-critical logic

### Mandatory
- diff-cover: Yes
- benchmark: Optional

### Skip condition
- Do not skip diff-cover
- Skip benchmark unless the task affects a known hot path

---

## Phase 11 — Production Readiness

### Objective
Ensure the implementation is ready to merge or deploy.

### You must
- confirm that code, tests, typing, and configuration are in a consistent state
- ensure there are no placeholder implementations, debug leftovers, or partial migrations
- ensure the implementation is understandable and maintainable
- confirm that operational impact is acceptable

### Mandatory
Yes

### Skip condition
Do not skip.

### Composition rule
- If `scripts/` or `config/` files changed, run `deploy` after this phase.

---

## Phase 12 — Knowledge Compression

### Objective
Capture the essential repository knowledge learned during implementation.

### You must
- summarize the repository conventions used
- summarize architectural assumptions discovered
- summarize important implementation decisions
- summarize any non-obvious constraints, risks, or follow-up items
- compress this knowledge so future work can reuse it efficiently

### Mandatory
Yes

### Skip condition
Do not skip.

---

## Fast path

Use the fast path only for a small, self-contained bug fix that satisfies all of the following:
- touches 2 files or fewer
- does not change any public or runtime-facing interface
- does not change architecture boundaries
- does not affect MCP endpoints
- does not require performance benchmarking

If all fast-path conditions are true, run only:
- Phase 1 — Task Classification
- Phase 2 — Repository Intelligence
- Phase 4 — Convention Extraction
- Phase 5 — Semantic Safe Modification
- Phase 8 — Security Validation
- Phase 9 — Validation Orchestration
- Phase 11 — Production Readiness
- Phase 12 — Knowledge Compression

In the fast path:
- skip Phase 3
- skip Phase 6
- skip Phase 7
- skip Phase 10 benchmark work

Do not use the fast path if the task touches interfaces, architecture, or integration contracts.

---

## Core implementation rules

You must follow these rules throughout execution:

- Prefer existing repository patterns over new local inventions.
- Prefer typed, explicit, maintainable code.
- Prefer small, reviewable diffs.
- Do not widen scope without clear necessity.
- Do not change unrelated behavior.
- Do not treat uncertainty as approval; inspect the repository first.
- Do not assume conventions; extract them from nearby code.
- Do not consider the task complete until validation is finished.

---

## Composition rules

### Composes with
- `python-lint-typecheck`
  Run if Phase 9 reveals lint or type errors not caused by the task.

- `python-test-and-fix`
  Run if Phase 9 reveals test failures not caused by the task.

- `deploy`
  Run after Phase 11 if `scripts/` or `config/` changed.

---

## Improvement feedback

After using this skill:
- if a phase was unnecessary, update the mandatory or skip conditions
- if a needed step was missing, add it
- if the fast path was too broad or too narrow, refine its conditions

Update the phase definitions in this file and the detailed procedures in `workflow.md` as needed.

---

## Final execution directive

Implement the requested Python change in a way that is:
- repository-consistent
- architecture-aware
- semantically safe
- validated
- production-ready
- scoped correctly
- easy for future work to build upon

When in doubt:
- inspect the repository first
- follow existing conventions
- make the smallest correct change
- validate before finishing
