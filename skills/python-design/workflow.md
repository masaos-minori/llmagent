# Python Program Design Workflow

Design first. Do not implement unless explicitly requested.

## Step 1: Understand the Task

Read the task description and extract:
- **Goal**: what should be true when done
- **Actor**: who or what uses the system
- **Input/output**: what data enters and leaves each boundary
- **Constraints**: performance, security, compatibility, deployment

If the task is vague, list specific questions. Do not guess.

---

## Step 2: Extract Requirements

List:
- **Functional requirements**: what the system must do
- **Non-functional requirements**: latency, concurrency, reliability, scalability
- **Assumptions**: things you accept as true but cannot verify now
- **Dependencies**: libraries, services, data sources the design depends on

If any requirement is ambiguous, flag it as `UNKNOWN` with the information needed to resolve.

---

## Step 3: Define Architecture

Read existing code to understand the current architecture:

```bash
# Layer contracts
lint-imports
cat .importlinter

# Module decomposition
ls scripts/
ls scripts/shared/ scripts/db/ scripts/rag/ scripts/mcp/ scripts/agent/
```

Define:
- **Components**: what the major pieces are
- **Boundaries**: which component owns what
- **Control flow**: how requests or events move through the system
- **Data flow**: what data is read, written, and transformed at each step

Keep the architecture minimal. Do not over-engineer.

Include a concurrency model when relevant: synchronous, asynchronous (`asyncio`), threaded,
multi-processed, or hybrid. State the boundary between sync and async code explicitly.

---

## Step 4: Design Modules and Interfaces

For each module in the design:
- **Package path**: where it lives (e.g. `scripts/mcp/<name>/`)
- **Responsibility**: one sentence per module
- **Public API**: functions or classes exposed to other modules
- **Dependency direction**: which modules it imports and which import it

Design package layout and interface contracts at responsibility level (externally relevant
public contracts, caller-visible behavior, input/output type boundaries for major use cases).
Apply `skills/DESIGN.md` §Avoid implementation-reference duplication — list a file, function,
or method only when the boundary itself is a design decision.

Validate with:
```bash
ast-grep --pattern 'class $NAME(BaseModel): $$$' --lang python scripts/   # existing patterns
ast-grep --pattern 'class $NAME(MCPServer): $$$' --lang python scripts/   # server patterns
```

---

## Step 5: Design Data and Persistence

For each entity:
- **Fields and types**: `field_name: type` list
- **Validation rules**: min/max length, required, unique, regex
- **Storage**: in-memory, config file, SQLite table, or external service
- **Serialization**: JSON, TOML, pickle (never), or Pydantic model

Use Pydantic `BaseModel` at module boundaries, plain dataclasses internally.

Keep data model design at semantic level: ownership, lifecycle, validation boundaries,
compatibility constraints, and invariants. Apply `skills/DESIGN.md` §Avoid
implementation-reference duplication — avoid exhaustive field listings unless required to
explain a design decision.

---

## Step 6: Define Error Handling

For each failure mode:
- **Detection**: how the system knows the failure occurred
- **Response**: abort, retry, fallback, or degrade
- **Logging**: what context to include in the log message
- **User visibility**: is the error shown to the user, logged only, or silently handled?

Copy the standard logging pattern:
```python
logger = logging.getLogger(__name__)
logger.error("descriptive_message key=value key2=%s", val)
```

Apply `skills/DESIGN.md` §Pythonic safety constraints: design explicit context managers
(`with` / `async with`) for files, sockets, database connections, HTTP clients, and async
clients.

---

## Step 7: Define Test Strategy

For each module:
- **Unit tests**: pure logic, no I/O, fast
- **Integration tests**: module boundary with real I/O (DB, filesystem, network)
- **Edge cases**: empty inputs, missing data, concurrent access, timeouts
- **Failure-path tests**: what happens when a dependency fails

---

## Step 8: Produce an Implementation Plan

List implementation phases in dependency order:

1. Phase N: <name>
   - Files to create or modify
   - Key change
   - Verification step

Each phase must be independently testable and revertable. Note migration path, rollback
strategy, and documentation update points if relevant.

---

## Step 9: Review the Design

Check:
- [ ] every functional requirement has a corresponding module or interface
- [ ] every non-functional requirement is addressed (latency, security, etc.)
- [ ] external inputs are validated before reaching domain logic
- [ ] logs are useful without exposing secrets
- [ ] tests are feasible without real external services
- [ ] abstractions are justified and the design is no larger than the problem requires
- [ ] no assumption is untested or contradictory
- [ ] the implementation plan covers all modules and is small enough for independent phases
- [ ] open questions and implementation-verification items are listed
- [ ] design complies with `skills/DESIGN.md` §Import layer contract and §Pythonic safety
      constraints (dependency direction, `Any`/untyped-dict avoidance, sync/async isolation,
      resource lifecycle, retries/error classification)

If a section is not relevant, omit it instead of filling it with generic text.

---

## Evidence and Assumptions

### Existing Codebase Design Review

When reviewing or redesigning an existing Python codebase, apply `skills/DESIGN.md` §Evidence
labels and §Confidence levels to describe current behavior. In addition:
- distinguish implemented behavior from desired design
- preserve known issues and unresolved documentation/code mismatches

### New Design Work

When designing new behavior before implementation:
- clearly distinguish proposed decisions from implemented behavior
- clearly mark assumptions, constraints, and open questions
- list implementation verification items
- do not describe proposed behavior as if it already exists

Use these concepts when helpful: Proposed Decision, Assumption, Constraint, Open Question,
Verification Item.

---

## Rules

- Do not modify source files during design; do not generate production code unless explicitly requested.
- Use pseudocode or interface sketches only when the design needs them.
- Keep modules small and explicit; avoid monolithic files or dumping unrelated behavior into `utils.py`.
- Prefer simple functions over classes when state is not required. Use classes for state, lifecycle, dependency injection, polymorphism, or a stable public concept.
- Include failure paths explicitly — timeouts, disconnected states, partial failures, malformed inputs, invalid configuration, and resource cleanup.
- Apply `skills/DESIGN.md` §Avoid implementation-reference duplication to generated or mechanically discoverable details (CLI help, configuration schemas, DTO fields, file trees).
- Respect project-specific constraints: if a general rule conflicts with an existing project convention, document the exception and explain why it is acceptable.
- Separate current design from future extensions.

---

## Final Output

Produce these sections when relevant. Omit sections that do not apply to the task; do not
fill irrelevant sections just to satisfy the template.

1. **Goal** — what the program or change is intended to do, what problem it solves, what value it provides.
2. **Scope** — in scope, out of scope, assumptions, explicit non-goals.
3. **Requirements** — functional/non-functional requirements, edge cases, Python-version and performance constraints, external dependencies, assumptions to verify later.
4. **Architecture** — main components, responsibility/ownership boundaries, control/data flow, dependency direction, concurrency model, operational constraints.
5. **Module Design** — package layout at responsibility level, module responsibilities, allowed/forbidden dependency direction, import boundaries, circular-import constraints.
6. **Interface Design** — externally relevant public contracts, caller-visible behavior, input/output type boundaries, protocol/ABC usage only when justified, stability expectations.
7. **Data Model and Serialization** — key domain entities and ownership, data lifecycle, validation/persistence/serialization boundaries, immutability strategy.
8. **Error Handling and Resource Lifecycle** — failure modes, exceptions, retry/timeout policy, disconnected/malformed-input behavior, logging context, resource lifecycle (files, sockets, DB connections, HTTP/async clients).
9. **Configuration** — ownership, source boundaries (env vars, TOML, JSON), startup-only vs. runtime-changeable settings, restart/hot-reload boundaries, security-sensitive settings.
10. **Test Strategy** — unit/integration/contract test targets, mocking and fixture strategy, external dependency isolation, type-checking expectations, regression tests for failure paths.
11. **Implementation Plan** — ordered phases, measurable milestones, dependency-aware task order, migration path, rollback strategy, documentation update points.
12. **Risks and Open Questions** — risks and mitigations, dynamic-typing/third-party/concurrency/operational risks, unresolved design decisions, assumptions requiring confirmation, implementation verification items.
