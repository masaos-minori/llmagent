---
name: python-design
description: |
  Design Python programs before implementation. Define architecture, responsibility boundaries,
  public contracts, data ownership, error handling, configuration boundaries, tests,
  and phased implementation plans.
  MUST NOT implement unless explicitly requested.
---

# Python Program Design Skill

## Purpose

Design first: produce design output only; implement only when the user explicitly
requests it (see `skills/DESIGN.md` Analysis-only phase constraint).

Produce output that is clear, structured, minimal (YAGNI), type-safe, testable, and focused on design
decisions, responsibility boundaries, constraints, and operational risks — not
exhaustive implementation-reference detail.

---

## Documentation Language

See `skills/DESIGN.md` Output language.

## Deliverable

The deliverable is the design written to the `workflow.md` Final Output template, as an English
design document (`skills/DESIGN.md` Output language). Default delivery: present it in the chat
response as a Markdown document, with a short Japanese summary and the open questions in the
conversation language (`AGENTS.md` Role). Write it to a file only when the user asks; if they ask
for a file without a location, ask where. A change under `docs/` is a documentation update:
make it only on explicit instruction (then via `python-documentation`). Writing the design
document is this skill's designated output, not a violation of the analysis-only rule; no
source code, tests, or configuration are changed.

For an existing-codebase review or a refactoring design, say so in Step 1 (mode:
`existing`), and apply Evidence labels in every step (`workflow.md` Evidence and Assumptions).

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
| 1 | Understand the task | Clarify goals, constraints, performance characteristics, context, and mode (new design or `existing` codebase review/refactoring design) |
| 2 | Extract requirements | Scope and non-goals, functional/non-functional requirements, edge cases, assumptions, dependencies |
| 3 | Define architecture | Existing docs and ADRs, components, responsibility boundaries, process separation, data flow, control flow, sync/async boundaries |
| 4 | Design modules and interfaces | Package responsibilities, dependency direction, import constraints, decisions with alternatives and compatibility impact |
| 5 | Design data, persistence, configuration, and security | Data ownership, entities, validation boundaries, immutability (5a); configuration ownership and reload boundaries (5b); trust boundaries, approval paths, secrets (5c) |
| 6 | Define error handling | Failure modes, exception/retry policy, logging context, resource lifecycle |
| 7 | Define test strategy | Unit/integration tests, mocking strategy, fixtures, production isolation, testability hooks |
| 8 | Produce an implementation plan | Ordered phases, dependency-aware task order, migration path, milestones |
| 9 | Review the design | Completeness, consistency, ADR consistency, type-checking feasibility, testability, YAGNI compliance |

See `workflow.md` for detailed phase content and the required output template.

---

## Core Design Rules (Strictly Enforced for AI)

- **Avoid implementation-reference duplication**: see `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content policy — remove.
- **Enforce one-way dependency direction**: apply `skills/DESIGN.md` Import layer contract at the design stage, not during implementation.
- **Isolate async and sync code**: design so the implementation can satisfy `skills/DESIGN.md` Pythonic safety constraints (async safety); this skill designs to that constraint, which binds `python-implementation`/`python-refactoring` directly.
- **Design for immutability by default**: prefer frozen dataclasses, tuples, and `Mapping` for core domain data unless mutation is justified.
- **Validate only at system boundaries**: pass trusted, type-safe objects into internal services.
- **Use abstractions only when justified**: no abstract factories, `Protocol`, or `abc.ABC` without a concrete requirement.
- **Include failure paths and resource lifecycle explicitly**: a design is incomplete if it only describes the happy path.
- **MUST NOT write production code blocks**: use pseudocode or minimal typed signatures to illustrate interfaces. Refer to a repository convention (for example the logging format) by name instead of copying code.
- **Respect accepted decisions**: the design MUST NOT contradict an accepted ADR under `docs/10_adr/` or the layer rules; a needed deviation is stated as a proposed ADR change, never silently applied.
- **Keep proposed design separate from implemented behavior**: for existing-codebase review, apply `skills/DESIGN.md` Evidence labels; for new design, mark assumptions and open questions.

See `workflow.md` for the full rule set, evidence-label usage, and the design checklist.

---

## Composes with

- `issue-to-plan` — called when a plan identifies that architecture or design work is needed before implementation
- `python-documentation` — used when the design task requires reviewing or updating existing Python documentation
- `python-implementation` — hand-off once the design's contracts are locked and the user asks for implementation (design first, then implement)
- `python-code-review` — for an existing-codebase design review, use it for the evidence-based review of the current code
- `python-refactoring` — hand-off for a refactoring design that is approved for execution (Path A/B/C rules apply there)
- `mcp-server-add` — when the design adds an MCP server, its flow and checklist own the addition steps

## Called by

- `issue-to-plan` — during planning phase when design decisions or architecture analysis are required
- `plan-to-implementation-procedure` — narrow usage only: draws a few relevant bullets for its "Design decisions" / "Alternatives considered" / "Compatibility considerations" / "Security considerations" / "Rollback considerations" fields (produced by this skill's Decisions and Alternatives, Compatibility, Security, and Implementation Plan sections), not a full invocation of this skill's multi-section output

---

## Improvement feedback

After running this skill:
- if a required section was unnecessary for the task type, note the condition and refine the output template in `workflow.md`
- if a design rule conflicted with a project-specific constraint, document the exception
- if the When Not To Use conditions were too broad or too narrow, refine them
- if the design had too much implementation-reference detail, tighten the rule against exhaustive implementation-derived descriptions

---

## Final Rule

You are producing a small, explicit, type-safe, testable, maintainable Python design (analysis-only per Purpose).

When in doubt, prioritize: correctness, simplicity, explicit responsibility boundaries,
type safety, testability, operational safety, maintainability.
