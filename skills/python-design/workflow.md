# Python Program Design Workflow

## Step 1: Understand the Task

Read the task description and extract:
- **Goal**: what should be true when done
- **Actor**: who or what uses the system
- **Input/output**: what data enters and leaves each boundary
- **Constraints**: performance, security, compatibility, deployment

If any of Goal/Actor/Input-output/Constraints cannot be determined from the task
description and available code, list specific questions for it instead of guessing.

**Completed when**: all four items are recorded, each either as a confirmed value or as
an explicit question.
**Stop and ask the user before Step 2 when**: Goal cannot be determined even provisionally
— every later step depends on it, so continuing would design against an assumed goal.
For the other three items, record the open question and continue to Step 2 with them
marked `UNKNOWN`.

---

## Step 2: Extract Requirements

List:
- **Functional requirements**: what the system must do
- **Non-functional requirements**: latency, concurrency, reliability, scalability
- **Assumptions**: things you accept as true but cannot verify now
- **Dependencies**: libraries, services, data sources the design depends on

If any requirement is ambiguous, flag it as `UNKNOWN` with the information needed to resolve.

**Completed when**: Functional requirements, Non-functional requirements, Assumptions, and
Dependencies are each recorded — either as concrete items or as `UNKNOWN` entries.
**Stop and ask the user before Step 3 when**: zero functional requirements can be
determined even provisionally — there is nothing left to design against. Any other
ambiguity is recorded as `UNKNOWN` and design continues.

---

## Step 3: Define Architecture

Read existing code to understand the current architecture. Run both command groups below,
always, in this order — layer contracts first, since module decomposition is read in light
of the contract they must respect:

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

Keep the component count at or below the number of distinct use cases identified in Step 2:
if a proposed component's responsibility can be merged into an existing one without
violating one-way dependency direction (Core Design Rules), merge it instead of adding
a new component.

Include a concurrency model when relevant: synchronous, asynchronous (`asyncio`), threaded,
multi-processed, or hybrid. State the boundary between sync and async code explicitly.

**Completed when**: Components, Boundaries, Control flow, and Data flow are all defined and
the component count is justified against Step 2's use cases.

---

## Step 4: Design Modules and Interfaces

For each module in the design:
- **Package path**: where it lives (e.g. `scripts/mcp/<name>/`)
- **Responsibility**: one sentence per module
- **Public API**: functions or classes exposed to other modules
- **Dependency direction**: which modules it imports and which import it

Design package layout and interface contracts at responsibility level (externally relevant
public contracts, caller-visible behavior, input/output type boundaries for major use cases).
Apply `skills/DESIGN.md` Avoid implementation-reference duplication — list a file, function,
or method only when the boundary itself is a design decision.

Run this validation only when the module design introduces a new `Protocol`, `abc.ABC`, or
a new base-class hierarchy — check the design against existing patterns before finalizing it.
Skip it when the design reuses an existing base class or introduces no new abstraction.
```bash
ast-grep --pattern 'class $NAME(BaseModel): $$$' --lang python scripts/   # existing patterns
ast-grep --pattern 'class $NAME(MCPServer): $$$' --lang python scripts/   # server patterns
```

Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule: do not re-run the
same `ast-grep` pattern against an unchanged target expecting a different result. Per
`rules/ai-execution.md` Repository Tool Usage #8, no matches from `ast-grep` is evidence
of "no conflicting pattern" only after confirming the pattern actually searched
`scripts/` (a typo'd pattern or path also yields no matches).

**Completed when**: every module has a package path, one-sentence responsibility, public API,
and dependency direction recorded, and (if applicable) the ast-grep check above found no
conflicting existing pattern.

---

## Step 5: Design Data and Persistence

For each entity:
- **Fields and types**: `field_name: type` list
- **Validation rules**: min/max length, required, unique, regex
- **Storage**: in-memory, config file, SQLite table, or external service
- **Serialization**: JSON, TOML, pickle (never), or Pydantic model

Use Pydantic `BaseModel` at module boundaries, plain dataclasses internally.

Keep data model design at semantic level: ownership, lifecycle, validation boundaries,
compatibility constraints, and invariants. Apply `skills/DESIGN.md` Avoid
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

Design so the implementation can satisfy `skills/DESIGN.md` Pythonic safety constraints
(context managers for resource management): specify the `with`/`async with` boundary for each
resource the design introduces, before implementation begins.

---

## Step 7: Define Test Strategy

For each module:
- **Unit tests**: pure logic, no I/O, fast
- **Integration tests**: module boundary with real I/O (DB, filesystem, network)
- **Edge cases**: empty inputs, missing data, concurrent access, timeouts
- **Failure-path tests**: what happens when a dependency fails

---

## Step 8: Produce an Implementation Plan

### Step 8a: List phases in dependency order

1. Phase N: <name>
   - Files to create or modify
   - Key change

A phase depends on another phase only when it imports, calls, or otherwise requires a
symbol the other phase introduces. Order phases so no phase precedes one it depends on.

### Step 8b: Verify independent testability

For each phase, state the verification step that confirms it in isolation (unit test,
type check, or manual check). If a phase cannot be verified without a later phase also
being in place, merge the two phases — they are not actually independent.

### Step 8c: Define rollback strategy

For each phase, state what reverting it requires (revert the commit, remove a feature
flag, restore a config value). If a phase has no clean revert path (e.g. it runs a
data migration), say so explicitly and name the phase as a rollback risk in Step 9's
Risks and Open Questions.

### Step 8d: Note migration path and documentation update points

If the design changes a public contract, data format, or configuration key, state the
migration path for existing data/callers. List which `docs/*.md` files this change would
require updating, if any.

**Completed when**: every phase has passed Step 8a–8d — dependency-ordered, independently
verifiable, with a stated rollback path (or documented risk), and migration/doc impact noted.

---

## Step 9: Review the Design

Check:
- [ ] every functional requirement has a corresponding module or interface
- [ ] every non-functional requirement is addressed (latency, security, etc.)
- [ ] external inputs are validated before reaching domain logic
- [ ] logs comply with `skills/DESIGN.md` No secrets in output
- [ ] tests are feasible without real external services
- [ ] abstractions are justified and the design is no larger than the problem requires
- [ ] no assumption is untested or contradictory
- [ ] the implementation plan covers all modules and is small enough for independent phases
- [ ] open questions and implementation-verification items are listed
- [ ] design complies with `skills/DESIGN.md` Import layer contract and Pythonic safety constraints

If a section is not relevant, omit it instead of filling it with generic text.

**Completed when**: every checked item above is true.
**On an unchecked item**: return to the step that owns it (see mapping below), fix the gap,
then re-check only the item(s) that gap affects — not the full checklist from the top —
before proceeding. Per `AGENTS.md` Loop Prevention > Attempt Limit, at most 3
fix-and-recheck round-trips per item; if it still cannot be checked after 3 attempts,
record it as an Open Question (Step 9's Risks and Open Questions) instead of leaving it
silently unchecked or retrying indefinitely.

| Unchecked item | Return to |
|---|---|
| requirement/module or interface mismatch | Step 2 or Step 4 |
| non-functional requirement unaddressed | Step 2 |
| unvalidated external input | Step 5 |
| secret in logs | Step 6 |
| infeasible test | Step 7 |
| unjustified abstraction / oversized design | Step 4 |
| untested or contradictory assumption | Step 2 |
| implementation plan gap | Step 8 |
| missing open question | Evidence and Assumptions (below) |
| Import layer contract / Pythonic safety violation | Step 3, Step 4, or Step 6 |
| ast-grep found a conflicting existing pattern | Step 4 |

---

## Evidence and Assumptions

### Existing Codebase Design Review

When reviewing or redesigning an existing Python codebase, apply `skills/DESIGN.md` Evidence
labels and Confidence levels to describe current behavior. In addition:
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

- Use pseudocode or interface sketches only when the design needs them.
- Keep modules small and explicit; avoid monolithic files or dumping unrelated behavior into `utils.py`.
- Prefer simple functions over classes when state is not required. Use classes for state, lifecycle, dependency injection, polymorphism, or a stable public concept.
- Include failure paths explicitly — timeouts, disconnected states, partial failures, malformed inputs, invalid configuration, and resource cleanup.
- Apply `skills/DESIGN.md` Avoid implementation-reference duplication to generated or mechanically discoverable details (CLI help, configuration schemas, DTO fields, file trees — see also `skills/DESIGN.md` Docs content policy — remove for the "full file tree" category specifically).
- Respect project-specific constraints: if a general rule conflicts with an existing project convention, document the exception and explain why it is acceptable.
- Separate current design from future extensions.

---

## Final Output

Produce these sections when relevant. Populate each from what Steps 1-9 already
recorded — do not re-derive or re-run a check merely to produce this output. Omit
sections that do not apply to the task; do not fill irrelevant sections just to satisfy
the template.

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
