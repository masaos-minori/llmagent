---
name: python-design
description: |
  Design Python programs before implementation. Define architecture, responsibility boundaries,
  public contracts, data ownership, error handling, configuration boundaries, tests,
  and phased implementation plans.
  Do not implement unless explicitly requested.
---

# Python Program Design Skill

## Purpose

Design first. Do not implement unless the user explicitly asks for implementation.

Produce output that is clear and structured, minimal and YAGNI-compliant, type-safe,
testable, and focused on design decisions, responsibility boundaries, constraints, and
operational risks — not on exhaustive implementation-reference detail.

---

## Documentation Language

Write design documentation in Japanese unless the target repository or user explicitly
requires another language.

Keep file names, module names, symbols, commands, configuration keys, type names, and
evidence labels in their original form.

---

## When to use

- Python architecture design (Clean Architecture, Hexagonal, or simple layered)
- package/module responsibility and dependency-direction design
- public contract design using standard typing, `Protocol`, or `abc.ABC` where justified
- domain model ownership, validation boundaries, and persistence/serialization constraints
- error handling, resource lifecycle, and configuration ownership design
- test strategy and phased implementation planning
- design review of an existing Python codebase
- refactoring design where responsibility boundaries or dependency direction must be clarified

## When not to use

- direct implementation-only requests, tiny snippets, or isolated syntax/debugging fixes
- pure documentation-only edits with no architectural design work
- marketing or end-user content
- speculative designs not requested by the user

If the task mixes design and implementation, design first and lock the contract before
implementation starts.

---

## Phase overview

| Step | Name | Goal |
|---|---|---|
| 1 | Understand the task | Clarify goals, constraints, performance characteristics, and context |
| 2 | Extract requirements | Functional/non-functional requirements, edge cases, assumptions, dependencies |
| 3 | Define architecture | Components, responsibility boundaries, data flow, control flow, sync/async boundaries |
| 4 | Design modules and packages | Package responsibilities, dependency direction, import constraints |
| 5 | Design data and validation | Data ownership, domain entities, validation boundaries, immutability |
| 6 | Define error and resource policy | Failure modes, exception/retry policy, logging context, resource lifecycle |
| 7 | Define test strategy | Unit/integration tests, mocking strategy, fixtures, testability hooks |
| 8 | Produce an implementation plan | Ordered phases, dependency-aware task order, migration path, milestones |
| 9 | Review the design | Completeness, consistency, type-checking feasibility, testability, YAGNI compliance |

See `workflow.md` for detailed phase content and the required output template.

---

## Core Design Rules (Strictly Enforced for AI)

- **Design first**: do not implement unless explicitly requested.
- **Avoid implementation-reference duplication**: no exhaustive file lists, method catalogs, DTO field tables, config key tables, or command/JSON examples unless required for a design decision.
- **Enforce one-way dependency direction**: prevent circular imports at the design stage, not during implementation.
- **Isolate async and sync code**: no blocking calls inside `async def` pipelines without an explicit executor boundary.
- **Design for immutability by default**: prefer frozen dataclasses, tuples, and `Mapping` for core domain data unless mutation is justified.
- **Validate only at system boundaries**: pass trusted, type-safe objects into internal services.
- **Use abstractions only when justified**: no abstract factories, `Protocol`, or `abc.ABC` without a concrete requirement.
- **Include failure paths and resource lifecycle explicitly**: a design is incomplete if it only describes the happy path.
- **Do not write production code blocks**: use pseudocode or minimal typed signatures to illustrate interfaces.
- **Keep proposed design separate from implemented behavior**: for existing-codebase review, use evidence labels and mark unclear behavior `Needs confirmation`; for new design, mark assumptions and open questions clearly.

See `workflow.md` for the full rule set, evidence-label usage, and the Python-specific
design checklist.

---

## Composes with

- `python-issue-to-plan` — called when a plan identifies that architecture or design work is needed before implementation
- `python-documentation` — used when the design task requires reviewing or updating existing Python documentation

## Called by

- `python-issue-to-plan` — during planning phase when design decisions or architecture analysis are required

---

## Improvement feedback

After running this skill:
- if a required section was unnecessary for the task type, note the condition and refine the output template in `workflow.md`
- if a design rule conflicted with a project-specific constraint, document the exception
- if the When Not To Use conditions were too broad or too narrow, refine them
- if the design produced too much implementation-reference detail, tighten the rule against exhaustive implementation-derived descriptions

---

## Final Rule

You are not implementing. You are producing a small, explicit, type-safe, testable, and
maintainable Python design.

When in doubt, prioritize: correctness, simplicity, explicit responsibility boundaries,
type safety, testability, operational safety, maintainability.
