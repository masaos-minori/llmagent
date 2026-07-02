---
name: python-design
description: |
  Design Python programs before implementation. Define architecture, modules,
  interfaces, data models, error handling, configuration, tests, and phased implementation plans.
  Focus heavily on Pythonic architecture, type safety, and preventing common dynamic language pitfalls.
  Do not implement unless explicitly requested.
---

# Python Program Design Skill

## Rule
Design first. Do not implement unless the user explicitly asks for implementation.

Your output must be:
- clear & structured
- minimal & YAGNI-compliant (No over-engineering)
- type-safe (Mypy/Pyright compliant)
- testable & loosely coupled
- maintainable & implementation-ready

Prefer explicit design decisions and type contracts over vague conceptual ideas.

## Use This Skill When
Use this skill for:
- Python architecture design (e.g., Clean Architecture, Hexagonal, or simple Layered)
- module and package layout design (including sub-packages and `src/` layout consideration)
- interface and API design (using standard typing, `Protocol`, or `abc`)
- data model and domain entity design
- error handling, resource lifecycle, and logging design
- configuration and environment management design
- test planning and testability matrix
- implementation sequencing and planning
- design review of an existing Python codebase

## Do Not Use This Skill When
Do not use this skill for:
- direct implementation-only requests
- tiny one-off code snippets
- isolated syntax/debug fixes
- pure documentation-only edits with no architectural design work

If the task mixes design and implementation, do the design first and lock the contract.

---

## Phase overview

| Step | Name | Goal |
|------|------|------|
| 1 | Understand the task | clarify goals, performance characteristics, constraints, and context |
| 2 | Extract requirements | functional, non-functional, edge cases, type safety guarantees, assumptions |
| 3 | Define architecture | components, responsibility boundaries, data/control flow, **async/sync boundaries** |
| 4 | Design modules & packages | package layout, module responsibilities, **strict dependency direction (preventing cycles)** |
| 5 | Design data & validation | entities, DTOs, validation boundaries, storage ownership, immutability strategy |
| 6 | Define error & resource policy | failure modes, exception/retry policy, **context manager (`with`) lifecycles** |
| 7 | Define test strategy | unit, integration, mocking strategy for external dependencies, testability hooks |
| 8 | Produce an implementation plan | ordered phases, dependency-aware task order, migration path if applicable |
| 9 | Review the design | verify completeness, consistency, Mypy feasibility, and testability |

---

## Required Output
When relevant, produce these sections:

1. Goal
   - what the program does
   - what problem it solves

2. Scope
   - in scope
   - out of scope

3. Requirements
   - functional & non-functional requirements
   - python-specific constraints (e.g., Python version compatibility, GIL bottlenecks if multi-threaded)
   - assumptions & external dependencies

4. Architecture
   - main components & responsibility boundaries
   - control flow & data flow
   - **Concurrency Model**: Explicitly state if the system is synchronous, asynchronous (`asyncio`), or multi-processed, and define the boundaries between them.

5. Module Design
   - package layout (clear folder/file structures, e.g., adhering to `src/` layout if necessary)
   - module responsibilities
   - **Dependency Graph**: Explicitly state dependency direction to ensure zero circular imports.

6. Interface Design
   - public classes, functions, and decorators
   - input/output type contracts (using Python typing hints)
   - **Abstractions**: Define explicit use of `typing.Protocol` (structural typing) or `abc.ABC` (nominal typing). Do not introduce abstractions without clear justification.

7. Data Model & Serialization
   - key domain entities and DTOs
   - technology choices (`dataclasses(frozen=True)` for immutability vs `Pydantic` for strict external validation)
   - validation rules at data boundaries

8. Error Handling & Resource Lifecycle
   - failure modes and application-specific exceptions
   - retry policies and logging context strategy
   - **Resource Management**: Explicitly design context managers (`with` / `async with`) for files, sockets, or database connections.

9. Configuration
   - config sources (env vars, TOML, JSON) and type-safe configuration parsing
   - runtime vs startup-only settings

10. Test Strategy
    - unit & integration test mapping
    - mocking strategy (how to isolate external APIs or database layers cleanly using `pytest` fixtures)

11. Implementation Plan
    - ordered phases with measurable milestones

12. Risks / Open Questions
    - risk descriptions with mitigations (e.g., dynamic typing risks, third-party library stability)

---

## Rules

- **Keep modules small and explicit.** Avoid monolithic files or dumping everything into `utils.py`.
- **Enforce strict one-way dependency direction.** Design your modules to prevent circular imports (`ImportError`) at the design stage, not during implementation.
- **Isolate Async and Sync code.** Do not mix synchronous blocking operations inside `async def` pipelines without an explicit thread/process pool executor design.
- **Design for Immutability by default.** Prefer immutable data structures (`frozen=True` dataclasses, `Mapping`) for core business domain data to prevent accidental state mutations.
- **Separate input validation from domain logic.** Validate external data strictly at the system boundaries (API/CLI/File entry points) and pass fully trusted, type-safe objects into internal services.
- **No speculative over-engineering.** Do not add abstract factories or complex design patterns unless there is an immediate, proven requirement for them. Prefer simple, stable functions over classes when state is not required.
- **Include failure paths explicitly.** A design is incomplete if it only describes the happy path. Design for timeouts, disconnected states, and malformed inputs.
- **Do not write production code blocks.** Use pseudocode or minimal signature definitions with type hints to illustrate interfaces. Do not hide lack of design behind large walls of implementation code.

---

See `workflow.md` for detailed phase content.

## Composes with
- `python-issue-to-plan` — called when a plan identifies that architecture/design work is needed before implementation

## Called by
- `python-issue-to-plan` — during planning phase when design decisions or architecture analysis is required

## Default Template
Use this order unless the user requests another format:
1. Goal
2. Scope
3. Requirements
4. Architecture (including Concurrency Model)
5. Module Design (including Layout & Dependency Graph)
6. Interface Design (including Typing Abstractions)
7. Data Model & Serialization
8. Error Handling & Resource Lifecycle
9. Configuration
10. Test Strategy
11. Implementation Plan
12. Risks / Open Questions

## Improvement feedback

After running this skill:
- if a required section was unnecessary for the task type, note the condition and update the phase overview
- if a design rule conflicted with project-specific constraints, add a project exception to the Rules section
- if the Do Not Use conditions were too broad or too narrow, refine them here
