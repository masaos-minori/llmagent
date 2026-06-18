---
name: python-program-design
description: Design Python programs before implementation. Define architecture, modules, interfaces, data models, error handling, configuration, tests, and phased implementation plans. Do not implement unless explicitly requested.
---

# Python Program Design Skill

## Rule
Design first. Do not implement unless the user explicitly asks for implementation.

Your output must be:
- clear
- structured
- minimal
- testable
- maintainable
- implementation-ready

Prefer explicit decisions over vague ideas.

## Use This Skill When
Use this skill for:
- Python architecture design
- module and package design
- interface and API design
- data model design
- error handling design
- configuration design
- test planning
- implementation planning
- design review of an existing Python codebase

## Do Not Use This Skill When
Do not use this skill for:
- direct implementation-only requests
- tiny one-off code snippets
- isolated syntax/debug fixes
- pure documentation-only edits with no design work

If the task mixes design and implementation, do the design first.

## Phase overview

| Step | Name | Goal |
|------|------|------|
| 1 | Understand the task | clarify goals, constraints, and context |
| 2 | Extract requirements | functional, non-functional, assumptions |
| 3 | Define architecture | components, responsibility boundaries, data/control flow |
| 4 | Design modules and interfaces | package layout, module responsibilities, public APIs |
| 5 | Design data and persistence | entities, DTOs, validation, storage ownership |
| 6 | Define error handling | failure modes, exception/retry/logging policy |
| 7 | Define test strategy | unit, integration, edge cases, failure-path tests |
| 8 | Produce an implementation plan | ordered phases, dependency-aware task order |
| 9 | Review the design | verify completeness, consistency, and testability |

## Required Output
When relevant, produce these sections:

1. Goal
   - what the program does
   - what problem it solves

2. Scope
   - in scope
   - out of scope

3. Requirements
   - functional requirements
   - non-functional requirements
   - constraints
   - assumptions
   - dependencies

4. Architecture
   - main components
   - responsibility boundaries
   - control flow
   - data flow

5. Module Design
   - package layout
   - module responsibilities
   - dependency direction

6. Interface Design
   - public classes
   - public functions
   - input/output contracts
   - abstractions only when justified

7. Data Model
   - key entities
   - DTOs / dataclasses / TypedDict / Pydantic models if needed
   - validation rules
   - persistence model if needed

8. Error Handling
   - failure modes
   - exception policy
   - retry policy
   - logging policy

9. Configuration
   - config sources
   - config ownership
   - runtime vs startup-only settings
   - environment variable usage

10. Test Strategy
    - unit tests
    - integration tests
    - edge cases
    - failure-path tests

11. Implementation Plan
    - ordered phases
    - dependency-aware task order

12. Risks / Open Questions
    - risk descriptions with mitigations
    - unresolved design decisions

## Rules

- Keep modules small and explicit.
- Keep dependency direction clean.
- Separate current design from future ideas.
- Prefer stable, simple interfaces.
- Do not add abstraction without a clear reason.
- Include failure paths, not only success paths.
- Make runtime behavior explicit when relevant.
- Define responsibilities and boundaries for every component.
- State assumptions explicitly.
- Include test strategy and failure handling in the design.
- Provide an implementation-ready plan.
- Do not write production code unless explicitly requested.
- Do not replace design with large code blocks.
- Do not overcomplicate the architecture.
- Do not mix current design with speculative future design without labeling it.

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
4. Architecture
5. Module Design
6. Interface Design
7. Data Model
8. Error Handling
9. Configuration
10. Test Strategy
11. Implementation Plan
12. Risks / Open Questions
