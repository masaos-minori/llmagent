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

---

## Step 4: Design Modules and Interfaces

For each module in the design:
- **Package path**: where it lives (e.g. `scripts/mcp/<name>/`)
- **Responsibility**: one sentence per module
- **Public API**: functions or classes exposed to other modules
- **Dependency direction**: which modules it imports and which import it

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

Each phase must be independently testable and revertable.

---

## Step 9: Review the Design

Check:
- [ ] every functional requirement has a corresponding module or interface
- [ ] every non-functional requirement is addressed (latency, security, etc.)
- [ ] dependency direction matches the import-linter contracts
- [ ] no assumption is untested or contradictory
- [ ] the implementation plan covers all modules in the design
- [ ] the plan is small enough to implement in independent phases

---

## Rules

- Do not modify source files during design.
- Do not generate production code unless explicitly requested.
- Use pseudocode or interface sketches only when the design needs them.
- Separate current design from future extensions.
- Include failure paths — not just success paths.
- Keep the design minimal, explicit, and implementation-ready.

---

## Final Output

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
