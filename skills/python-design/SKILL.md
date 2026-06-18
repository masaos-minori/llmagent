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

## Required Output
When relevant, produce these sections:

1. Goal
   - what the program does
   - what problem it solves
   - scope / non-scope

2. Requirements
   - functional requirements
   - non-functional requirements
   - constraints
   - assumptions
   - dependencies

3. Architecture
   - main components
   - responsibility boundaries
   - control flow
   - data flow

4. Module Design
   - package layout
   - module responsibilities
   - dependency direction

5. Interface Design
   - public classes
   - public functions
   - input/output contracts
   - abstractions only when justified

6. Data Model
   - key entities
   - DTOs / dataclasses / TypedDict / Pydantic models if needed
   - validation rules
   - persistence model if needed

7. Error Handling
   - failure modes
   - exception policy
   - retry policy
   - logging policy

8. Configuration
   - config sources
   - config ownership
   - runtime vs startup-only settings
   - environment variable usage

9. Test Strategy
   - unit tests
   - integration tests
   - edge cases
   - failure-path tests

10. Implementation Plan
   - ordered phases
   - dependency-aware task order
   - risks and follow-up items

## Design Rules
- Keep modules small and explicit.
- Keep dependency direction clean.
- Separate current design from future ideas.
- Prefer stable, simple interfaces.
- Do not add abstraction without a clear reason.
- Include failure paths, not only success paths.
- Make runtime behavior explicit when relevant.

## Python Guidance
Prefer:
- dataclasses
- pathlib
- typing
- context managers
- explicit configuration objects
- dependency injection through constructor/function arguments

If concurrency is needed:
- explain why
- define boundaries
- define timeout / cancellation behavior

If persistence is needed:
- define storage ownership
- define transaction boundaries
- define schema evolution if relevant

If multiple entry points exist:
- keep CLI / API / worker thin
- keep business logic outside transport layers

## Output Style
Use:
- headings
- bullets
- numbered lists
- short, direct statements

Avoid:
- unnecessary prose
- unnecessary abstraction
- vague phrases when a concrete decision is possible

## Constraints
You must:
- define responsibilities
- define boundaries
- state assumptions
- include test strategy
- include failure handling
- provide an implementation-ready plan

You must not:
- write production code unless explicitly requested
- replace design with large code blocks
- overcomplicate the architecture
- mix current design with speculative future design without labeling it

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
