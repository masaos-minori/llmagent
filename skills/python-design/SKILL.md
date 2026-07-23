---
name: python-design
description: |
  Design Python programs before implementation. Define architecture, responsibility boundaries,
  public contracts, data ownership, error handling, configuration boundaries, tests,
  and phased implementation plans.
  Focus on Pythonic architecture, type safety, maintainability, and preventing common
  dynamic language pitfalls.
  Do not implement unless explicitly requested.
---

# Python Program Design Skill

## Rule

Design first. Do not implement unless the user explicitly asks for implementation.

Your output must be:

- clear and structured
- minimal and YAGNI-compliant
- type-safe and feasible for Mypy/Pyright
- testable and loosely coupled
- maintainable and ready for implementation planning
- focused on design decisions, responsibility boundaries, constraints, and operational risks

Prefer explicit design decisions and type contracts over vague conceptual ideas.

Do not turn design documents into exhaustive implementation references.

---

## Documentation Language

Write design documentation in Japanese unless the target repository or user explicitly requires another language.

Keep file names, module names, symbols, commands, configuration keys, type names, and evidence labels in their original form.

---

## Use This Skill When

Use this skill for:

- Python architecture design, such as Clean Architecture, Hexagonal Architecture, or simple layered architecture
- package responsibility and module boundary design, without exhaustive file-by-file listings
- public contract design using standard typing, `typing.Protocol`, or `abc.ABC` where justified
- domain model ownership, validation boundaries, and persistence or serialization constraints
- error handling, resource lifecycle, and logging design
- configuration ownership and runtime behavior design
- test planning and testability matrix design
- implementation sequencing and phased planning
- design review of an existing Python codebase
- refactoring design where responsibility boundaries or dependency direction must be clarified

## Do Not Use This Skill When

Do not use this skill for:

- direct implementation-only requests
- tiny one-off code snippets
- isolated syntax or debugging fixes
- pure documentation-only edits with no architectural design work
- marketing or end-user content
- speculative designs that are not requested by the user

If the task mixes design and implementation, perform the design first and lock the contract before implementation starts.

---

## Phase Overview

| Step | Name | Goal |
|---|---|---|
| 1 | Understand the task | Clarify goals, constraints, performance characteristics, and context |
| 2 | Extract requirements | Identify functional requirements, non-functional requirements, edge cases, type-safety guarantees, assumptions, and external dependencies |
| 3 | Define architecture | Define components, responsibility boundaries, data flow, control flow, and async/sync boundaries |
| 4 | Design modules and packages | Define package responsibilities, module boundaries, dependency direction, and import constraints |
| 5 | Design data and validation | Define data ownership, domain entities, DTO boundaries, validation boundaries, storage ownership, and immutability strategy |
| 6 | Define error and resource policy | Define failure modes, exception policy, retry policy, logging context, and context-manager lifecycle |
| 7 | Define test strategy | Define unit tests, integration tests, mocking strategy, fixtures, and testability hooks |
| 8 | Produce an implementation plan | Define ordered phases, dependency-aware task order, migration path, and measurable milestones |
| 9 | Review the design | Verify completeness, consistency, type-checking feasibility, testability, and YAGNI compliance |

See `workflow.md` for detailed phase content.

---

## Required Output

When relevant, produce these sections.

Omit sections that do not apply to the task. Do not fill irrelevant sections just to satisfy the template.

### 1. Goal

Describe:

- what the program or change is intended to do
- what problem it solves
- what value the design provides

### 2. Scope

Describe:

- in scope
- out of scope
- assumptions
- explicit non-goals

### 3. Requirements

Describe:

- functional requirements
- non-functional requirements
- edge cases
- Python-specific constraints
- Python version compatibility when relevant
- performance characteristics where relevant
- external dependencies
- assumptions that must be verified later

### 4. Architecture

Describe:

- main components
- responsibility boundaries
- ownership boundaries
- control flow
- data flow
- dependency direction
- operational or runtime constraints

Include a concurrency model when relevant:

- synchronous
- asynchronous with `asyncio`
- threaded
- multi-processed
- hybrid

Explicitly state boundaries between sync and async code when applicable.

### 5. Module Design

Describe:

- package layout at responsibility level
- module responsibilities
- allowed dependency direction
- forbidden dependency direction
- import boundaries
- important constraints that prevent circular imports
- important exceptions, if any

Do not list every planned file unless the file boundary itself is a design decision.

### 6. Interface Design

Describe:

- externally relevant public contracts only
- caller-visible behavior
- input and output type boundaries for major use cases
- protocol or abstract base class usage only when justified
- stability expectations for public interfaces

Do not list every public function, every method, or every decorator unless it is necessary to explain a design decision.

### 7. Data Model and Serialization

Describe:

- key domain entities and their ownership
- data lifecycle
- validation boundaries
- persistence ownership
- serialization boundaries
- immutability strategy
- compatibility-sensitive fields only when needed
- security-sensitive or persistence-sensitive fields only when needed

Avoid exhaustive DTO, dataclass, TypedDict, Pydantic model, or schema field listings unless the fields are required to explain a design decision.

### 8. Error Handling and Resource Lifecycle

Describe:

- failure modes
- application-specific exceptions
- retry policy
- timeout policy
- disconnected-state behavior
- malformed-input behavior
- logging context strategy
- resource lifecycle

Explicitly design context managers for resources such as:

- files
- sockets
- database connections
- HTTP clients
- async clients

Use `with` or `async with` as a design requirement where appropriate.

### 9. Configuration

Describe:

- configuration ownership
- configuration source boundaries
- environment variables, TOML, JSON, or other sources
- startup-only settings
- runtime-changeable settings
- restart requirements
- hot-reload boundaries
- security-sensitive settings
- persistence-sensitive settings

Avoid exhaustive configuration key tables unless the keys are required for a design decision.

### 10. Test Strategy

Describe:

- unit test targets
- integration test targets
- contract tests where relevant
- mocking strategy
- fixture strategy
- external dependency isolation
- database or filesystem test isolation
- type-checking expectations
- regression tests for failure paths

### 11. Implementation Plan

Describe:

- ordered phases
- measurable milestones
- dependency-aware task order
- migration path if applicable
- rollback or compatibility strategy if relevant
- documentation update points if relevant

### 12. Risks and Open Questions

Describe:

- risks and mitigations
- dynamic typing risks
- third-party library risks
- concurrency risks
- operational risks
- unresolved design decisions
- assumptions that require confirmation
- implementation verification items
- items that must be revisited after implementation

---

## Evidence and Assumptions

### Existing Codebase Design Review

When reviewing or redesigning an existing Python codebase:

- use the repository's existing evidence labels when describing current behavior
- do not introduce a competing evidence label system
- do not present unverified behavior as fact
- mark unclear implementation behavior as `Needs confirmation`
- distinguish implemented behavior from desired design
- preserve known issues and unresolved documentation/code mismatches

Use established evidence labels when available, such as:

- `Explicit in code`
- `Strongly implied by code`
- `Documentation only`
- `Needs confirmation`
- `Deprecated`
- `Verified by test`
- `Operationally observed`

### New Design Work

When designing new behavior before implementation:

- clearly distinguish proposed decisions from implemented behavior
- clearly mark assumptions
- clearly mark constraints
- clearly mark open questions
- list implementation verification items
- do not describe proposed behavior as if it already exists

Use these concepts when helpful:

- Proposed Decision
- Assumption
- Constraint
- Open Question
- Verification Item

---

## Rules

- **Design first.**
  Do not implement unless the user explicitly asks for implementation.

- **Focus on decisions, boundaries, and constraints.**
  A design document should explain why the architecture is shaped this way, what each component owns, what it must not own, what constraints must be preserved, and what operational risks exist.

- **Avoid implementation-reference duplication.**
  Do not produce exhaustive file lists, method catalogs, DTO field tables, configuration key tables, command examples, or JSON payload examples unless they are necessary for a design decision.

- **Keep modules small and explicit.**
  Avoid monolithic files or dumping unrelated behavior into `utils.py`.

- **Design package layout at responsibility level.**
  Describe package responsibilities and dependency direction. Do not list every planned file unless the file boundary itself is a design decision.

- **Enforce strict one-way dependency direction.**
  Design modules to prevent circular imports at the design stage, not during implementation.

- **Isolate async and sync code.**
  Do not mix synchronous blocking operations inside `async def` pipelines without an explicit thread-pool or process-pool boundary.

- **Design for immutability by default.**
  Prefer immutable data structures such as frozen dataclasses, tuples, and `Mapping` for core domain data unless mutation is justified.

- **Separate input validation from domain logic.**
  Validate external data strictly at system boundaries such as API, CLI, file, database, and message boundaries. Pass trusted, type-safe objects into internal services.

- **Use abstractions only when justified.**
  Do not introduce abstract factories, complex inheritance, `Protocol`, or `abc.ABC` unless there is a concrete requirement.

- **Prefer simple functions over classes when state is not required.**
  Use classes when they represent state, lifecycle, dependency injection, polymorphism, or a stable public concept.

- **Keep interface design at contract level.**
  Describe public contracts and caller-visible behavior. Do not list every function or method.

- **Keep data model design at semantic level.**
  Describe ownership, lifecycle, validation boundaries, compatibility constraints, serialization boundaries, and invariants. Do not list every field unless it affects a design decision.

- **Include failure paths explicitly.**
  A design is incomplete if it only describes the happy path. Design for timeouts, disconnected states, partial failures, malformed inputs, invalid configuration, and resource cleanup.

- **Include resource lifecycle explicitly.**
  Define ownership and cleanup for files, sockets, database connections, HTTP clients, subprocesses, and async resources.

- **Do not write production code blocks.**
  Use pseudocode or minimal signature definitions with type hints to illustrate interfaces. Do not hide lack of design behind large implementation code blocks.

- **Do not over-specify generated or mechanically discoverable details.**
  Avoid exhaustive descriptions of CLI help, configuration schemas, DTO fields, and file trees that can be mechanically confirmed from implementation.

- **Keep proposed design separate from implemented behavior.**
  For new design, mark assumptions and open questions clearly. For existing codebase review, use evidence labels and mark unclear behavior as `Needs confirmation`.

- **Respect project-specific constraints.**
  If a general rule conflicts with a project-specific convention or existing design principle, document the exception and explain why it is acceptable.

---

## Python-specific Design Checks

Use these checks before finalizing the design:

- Are import directions one-way?
- Are circular imports avoided?
- Are type boundaries explicit?
- Are `Any` and untyped dictionaries avoided or isolated?
- Are external inputs validated before reaching domain logic?
- Are sync and async boundaries explicit?
- Are blocking calls kept out of async pipelines or isolated behind executors?
- Are resource lifecycles explicit?
- Are retries bounded?
- Are errors classified?
- Are logs useful without exposing secrets?
- Are tests feasible without real external services?
- Are abstractions justified?
- Is the design smaller than the problem requires, not larger?
- Is every detailed artifact included because it supports a design decision?

---

## Before Finalizing

Review the design for:

- correctness
- responsibility boundaries
- dependency direction
- type-checking feasibility
- YAGNI compliance
- testability
- operational safety
- failure behavior
- resource lifecycle
- open questions
- assumptions
- implementation verification items

If a section is not relevant, omit it instead of filling it with generic text.

---

## Composes With

- `python-issue-to-plan` — called when a plan identifies that architecture or design work is needed before implementation
- `python-documentation` — used when the design task requires reviewing or updating existing Python documentation

## Called By

- `python-issue-to-plan` — during planning phase when design decisions or architecture analysis are required

---

## Default Template

Use this order when relevant. Omit sections that do not apply to the task.

1. Goal
2. Scope
3. Requirements
4. Architecture, including concurrency model when relevant
5. Module Design, including responsibility-level layout and dependency direction
6. Interface Design, including public contracts and justified abstractions
7. Data Model and Serialization, including ownership and validation boundaries
8. Error Handling and Resource Lifecycle
9. Configuration
10. Test Strategy
11. Implementation Plan
12. Risks and Open Questions

---

## Improvement Feedback

After running this skill:

- if a required section was unnecessary for the task type, note the condition and refine the default template
- if a design rule conflicted with project-specific constraints, add a project exception to the Rules section
- if the Do Not Use conditions were too broad or too narrow, refine them
- if the design produced too much implementation-reference detail, tighten the rule against exhaustive implementation-derived descriptions
- if the design omitted important operational constraints, strengthen the error handling, configuration, or resource lifecycle guidance

---

## Final Rule

You are not implementing.

You are producing a small, explicit, type-safe, testable, and maintainable Python design.

When in doubt, prioritize:

1. correctness
2. simplicity
3. explicit responsibility boundaries
4. type safety
5. testability
6. operational safety
7. maintainability
