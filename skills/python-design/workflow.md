# Python Program Design Workflow

## Step 1: Understand the Task

Read the task description and extract:
- **Goal**: what should be true when done
- **Actor**: who or what uses the system
- **Input/output**: what data enters and leaves each boundary
- **Constraints**: performance, security, compatibility, deployment
- **Mode**: `new` (design before implementation) or `existing` (design review of, or refactoring design for, current code). In `existing` mode, apply `skills/DESIGN.md` Evidence labels to every statement about current behavior from this step on (see Evidence and Assumptions).
- **Delivery**: confirm the default delivery described in `SKILL.md` (English design document in the chat); ask only if the user wants a file and gave no location.

If Goal/Actor/Input-output/Constraints cannot be determined from the task description and available code, list specific questions instead of guessing.

**Completed when**: all four items are recorded, each as a confirmed value or an explicit question, and the mode is set.
**Stop and ask the user before Step 2 when**: Goal cannot be determined even provisionally
(every later step depends on it). For the other three items, record the open question and
continue to Step 2 with them marked `UNKNOWN`.

---

## Step 2: Extract Requirements

List:
- **Scope**: what is in scope, what is out of scope, and explicit non-goals
- **Functional requirements**: what the system must do
- **Non-functional requirements**: latency, concurrency, reliability, scalability
- **Assumptions**: things you accept as true but cannot verify now
- **Dependencies**: libraries, services, data sources the design depends on

If any requirement is ambiguous, flag it as `UNKNOWN` with the information needed to resolve.

**Completed when**: Scope, Functional requirements, Non-functional requirements, Assumptions, and
Dependencies are each recorded, as concrete items or `UNKNOWN` entries.
**Stop and ask the user before Step 3 when**: zero functional requirements can be
determined even provisionally. Any other ambiguity is recorded as `UNKNOWN` and design continues.

---

## Step 3: Define Architecture

First read what is already decided, then the code:

1. Existing design documents and ADRs: use `docs/00_index.md` "Document References by Task" to
   find the documents for the area, and read the relevant ADRs under `docs/10_adr/` (index:
   `docs/10_adr/adr_01_index.md`). Record each accepted decision the design must respect.
   MUST NOT load all of `docs/` (`AGENTS.md` Global Rule 3).
2. Layer contracts and the layer diagram: `rules/env.md` Architecture is the canonical diagram
   (MUST NOT restate it); read `.importlinter` with the Read tool.
3. Run both command groups below, in this order (layer contracts first):

```bash
# Layer contracts (command per rules/toolchain.md section 3)
PYTHONPATH=scripts uv run lint-imports

# Module decomposition: list the real top-level layout, then the packages the design touches
ls scripts/
ls scripts/<package>/            # for each package named in Step 2's scope, e.g. mcp_servers, shared, eventbus
```

Define:
- **Components**: what the major pieces are
- **Boundaries**: which component owns what
- **Process separation**: for each component that runs as its own process, the reason it is separate and the reason its configuration is scoped to that process (`skills/DESIGN.md` Docs content policy — retain), and the boundaries that cannot change unilaterally
- **Control flow**: how requests or events move through the system
- **Data flow**: what data is read, written, and transformed at each step

In `new` mode, keep the component count at or below the number of distinct use cases identified
in Step 2: if a proposed component's responsibility can be merged into an existing one without
violating one-way dependency direction (Core Design Rules), merge it. In `existing` mode,
describe the components that exist (with Evidence labels) and apply this rule only to
components the design proposes to add.

Include a concurrency model when relevant: synchronous, asynchronous (`asyncio`), threaded,
multi-processed, or hybrid. State the sync/async boundary explicitly.

**Completed when**: Components, Boundaries, Process separation (where it applies), Control flow,
and Data flow are all defined, the accepted ADRs/documents consulted are recorded, and (in
`new` mode) the component count is justified against Step 2's use cases.

If a proposed component's count cannot be justified against Step 2's use cases even after
attempting to merge per the rule above: do not stop the design. Mark the component as an
Open Question (`UNKNOWN` justification) in Risks and Open Questions and continue; Step 9's
YAGNI check then decides whether it stays.

---

## Step 4: Design Modules and Interfaces

For each module in the design:
- **Package path**: where it lives (e.g. `scripts/mcp_servers/<name>/`)
- **Responsibility**: one sentence per module
- **Public API**: functions or classes exposed to other modules
- **Dependency direction**: which modules it imports and which import it

Design package layout and interface contracts at responsibility level (externally relevant
public contracts, caller-visible behavior, input/output type boundaries for major use cases).
Apply `skills/DESIGN.md` Avoid implementation-reference duplication — list a file, function,
or method only when the boundary itself is a design decision.

Run this validation only when the module design introduces a new `Protocol`, `abc.ABC`, or
base-class hierarchy: check the design against existing patterns before finalizing it.
Skip it when the design reuses an existing base class or introduces no new abstraction.
```bash
ast-grep --pattern 'class $NAME(BaseModel): $$$' --lang python scripts/   # existing patterns
ast-grep --pattern 'class $NAME(MCPServer): $$$' --lang python scripts/   # server patterns
```

Apply `rules/ai-execution.md` Tool Usage's idempotent-command rule: MUST NOT re-run the
same `ast-grep` pattern against an unchanged target expecting a different result. Per
`rules/ai-execution.md` Repository Tool Usage #8, no `ast-grep` matches is evidence of
"no conflicting pattern" only after confirming the pattern actually searched `scripts/`
(a typo'd pattern or path also yields no matches).

For every non-obvious design decision (a new abstraction, a boundary choice, a deviation from
an existing pattern), record a decision entry:
- **Decision**: what was chosen
- **Alternatives considered**: at least one realistic alternative, and why it was rejected
- **Compatibility impact**: effect on existing callers, data, and configuration keys
- **Reversibility**: how hard it is to undo (feeds Step 8c)

If a decision contradicts or extends an accepted ADR, state it as a proposed ADR change.

**Completed when**: every module has a package path, one-sentence responsibility, public API,
and dependency direction recorded, every non-obvious decision has a decision entry, and (if
applicable) the ast-grep check found no conflicting existing pattern.

---

## Step 5: Design Data, Persistence, Configuration, and Security

### Step 5a: Data and persistence

For each entity:
- **Fields and types**: `field_name: type` list
- **Validation rules**: min/max length, required, unique, regex
- **Storage**: in-memory, config file, SQLite table, or external service
- **Serialization**: JSON, TOML, pickle (never), or Pydantic model

Use Pydantic `BaseModel` at module boundaries, plain dataclasses internally.

Keep data model design at semantic level: ownership, lifecycle, validation boundaries,
compatibility constraints, and invariants. Apply `skills/DESIGN.md` Avoid
implementation-reference duplication — avoid exhaustive field listings unless needed to
explain a design decision.

### Step 5b: Configuration

For each setting the design adds or changes:
- **Owner and source**: which component owns it; env var, TOML (`config/agent.toml` is the SSOT
  per `rules/env.md`), or JSON
- **Lifetime**: startup-only or runtime-changeable; restart or hot-reload boundary
- **Sensitivity**: whether it is security-sensitive (never logged, never in docs)
- **Per-process scoping**: why it belongs to one process's configuration rather than a shared one

### Step 5c: Security and trust boundaries

- **Trust boundaries**: where external or model-generated input enters (HTTP and MCP inputs,
  file paths, subprocess arguments, tool calls) and where it is validated
- **Approval and permission paths**: for any tool-executing path, which existing approval or
  permission check applies; a new path MUST NOT bypass the checks neighboring paths use
- **Secrets**: where secrets live and that they never reach logs, errors, or docs
  (`skills/DESIGN.md` No secrets in output)
- **Serialization risks**: no `pickle` or other unsafe deserialization of untrusted data

**Completed when**: every entity identified has Fields and types, Validation rules,
Storage, and Serialization all specified (5a); every new or changed setting has Owner, Lifetime,
Sensitivity, and Per-process scoping (5b); and every trust boundary the design touches has
validation and approval stated, or 5b/5c is recorded as not applicable (5c).

---

## Step 6: Define Error Handling

For each failure mode:
- **Detection**: how the system knows the failure occurred
- **Response**: abort, retry, fallback, or degrade
- **Logging**: what context to include in the log message
- **User visibility**: is the error shown to the user, logged only, or silently handled?

Specify logging at the convention level, not as code: module-level `logging.getLogger(__name__)`,
`key=value` messages, and the repository's `fmt_kvlog` helper where neighboring modules use it
(`scripts/shared/formatters.py`; `python-implementation` Phase 7 owns the details). State only
which context each failure log must carry.

Design so the implementation can satisfy `skills/DESIGN.md` Pythonic safety constraints
(context managers for resource management): specify the `with`/`async with` boundary for each
resource the design introduces, before implementation.

**Completed when**: every failure mode identified has Detection, Response, Logging,
and User visibility specified, and every resource requiring a `with`/`async with`
boundary has it stated.

---

## Step 7: Define Test Strategy

For each module:
- **Unit tests**: pure logic, no I/O, fast
- **Integration tests**: module boundary with real I/O (DB, filesystem, network)
- **Edge cases**: empty inputs, missing data, concurrent access, timeouts
- **Failure-path tests**: what happens when a dependency fails

Repository constraints to reflect in the strategy:
- test files mirror `scripts/` (`tests/<package>/test_<module>.py`); the work itself is done
  with `python-test-and-fix`
- running tests on this host can touch production state under `/opt/llm`: state that the
  isolation guard in `tests/conftest.py` must cover any new path, DB, or port the design
  introduces
- tests that start real subprocesses or services use the `integration` marker and are a
  separate command

**Completed when**: every module has at least one specified test category (unit,
integration, edge case, or failure-path) matching its I/O/boundary characteristics from Step 4.

---

## Step 8: Produce an Implementation Plan

When this skill is called by `issue-to-plan` (which owns the work plan) or for the narrow
`plan-to-implementation-procedure` use, produce only the phase list and risks that feed that
document; the full implementation plan below is for a standalone design task. MUST NOT write a
second, competing plan document.

### Step 8a: List phases in dependency order

1. Phase N: <name>
   - Files to create or modify
   - Key change

A phase depends on another only when it imports, calls, or otherwise requires a symbol the
other introduces. Order phases so none precedes one it depends on.

### Step 8b: Verify independent testability

For each phase, state the verification step that confirms it in isolation (unit test,
type check, or manual check). If a phase cannot be verified without a later phase also
being in place, merge the two phases — they are not actually independent.

### Step 8c: Define rollback strategy

For each phase, state what reverting it requires (revert the commit, remove a feature
flag, restore a config value). If a phase has no clean revert path (e.g. a data
migration), say so explicitly and name it as a rollback risk in Step 9's Risks and Open Questions.

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
- [ ] design is consistent with the accepted ADRs and documents recorded in Step 3; any deviation is a proposed ADR change
- [ ] every new or changed setting has owner, lifetime, sensitivity, and per-process scoping (Step 5b)
- [ ] trust boundaries and approval paths are stated (Step 5c)
- [ ] every non-obvious decision lists an alternative and its compatibility impact (Step 4)
- [ ] (`existing` mode) every statement about current behavior carries an Evidence label

If a section is not relevant, omit it instead of filling it with generic text.

**Completed when**: every checked item above is true.
**On an unchecked item**: return to the step that owns it (see mapping below), fix the gap,
then re-check only the item(s) that gap affects, not the full checklist, before proceeding.
Per `AGENTS.md` Loop Prevention > Attempt Limit, at most 3 fix-and-recheck round-trips per
item; if it still cannot be checked after 3 attempts, record it as an Open Question (Step 9's
Risks and Open Questions) instead of leaving it unchecked or retrying indefinitely.

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
| ADR/document inconsistency | Step 3 or Step 4 |
| configuration gap | Step 5b |
| security gap | Step 5c |
| missing alternative or compatibility impact | Step 4 |
| missing Evidence label (`existing` mode) | Evidence and Assumptions (below) |
| Import layer contract / Pythonic safety violation | Step 3, Step 4, or Step 6 |
| ast-grep found a conflicting existing pattern | Step 4 |

---

## Evidence and Assumptions

### Existing Codebase Design Review

When reviewing or redesigning an existing Python codebase (mode `existing`, set in Step 1),
apply `skills/DESIGN.md` Evidence labels and Confidence levels to describe current behavior in
every step — components and boundaries in Step 3, interfaces in Step 4, data and configuration
in Step 5, failure behavior in Step 6 — not only in the final document. In addition:
- distinguish implemented behavior from desired design
- preserve known issues and unresolved documentation/code mismatches

### New Design Work

When designing new behavior before implementation:
- clearly distinguish proposed decisions from implemented behavior
- clearly mark assumptions, constraints, and open questions
- list implementation verification items
- MUST NOT describe proposed behavior as if it already exists

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
recorded; MUST NOT re-derive or re-run a check merely to produce this output. Omit sections
that do not apply; MUST NOT fill irrelevant sections just to satisfy the template.

1. **Goal** — what the program or change is intended to do, what problem it solves, what value it provides.
2. **Scope** — in scope, out of scope, assumptions, explicit non-goals.
3. **Requirements** — functional/non-functional requirements, edge cases, Python-version and performance constraints, external dependencies, assumptions to verify later.
4. **Architecture** — main components, responsibility/ownership boundaries, process separation and its reasons, control/data flow, dependency direction, concurrency model, operational constraints.
5. **Module Design** — package layout at responsibility level, module responsibilities, allowed/forbidden dependency direction, import boundaries, circular-import constraints.
6. **Interface Design** — externally relevant public contracts, caller-visible behavior, input/output type boundaries, protocol/ABC usage only when justified, stability expectations, compatibility considerations for existing callers.
7. **Data Model and Serialization** — key domain entities and ownership, data lifecycle, validation/persistence/serialization boundaries, immutability strategy.
8. **Error Handling and Resource Lifecycle** — failure modes, exceptions, retry/timeout policy, disconnected/malformed-input behavior, logging context, resource lifecycle (files, sockets, DB connections, HTTP/async clients).
9. **Configuration** — ownership, source boundaries (env vars, TOML, JSON), startup-only vs. runtime-changeable settings, restart/hot-reload boundaries, security-sensitive settings, per-process scoping and its reason (Step 5b).
10. **Security and Trust Boundaries** — trust boundaries and where input is validated, approval/permission paths, secret handling, serialization risks (Step 5c).
11. **Test Strategy** — unit/integration/contract test targets, mocking and fixture strategy, external dependency isolation, production-isolation requirement, `integration` marker use, type-checking expectations, regression tests for failure paths.
12. **Design Decisions and Alternatives** — each non-obvious decision with alternatives considered, compatibility impact, reversibility, the accepted ADRs/documents respected, and any proposed ADR change (Step 3 and Step 4).
13. **Implementation Plan** — ordered phases, measurable milestones, dependency-aware task order, migration path, rollback strategy, documentation update points.
14. **Risks and Open Questions** — risks and mitigations, dynamic-typing/third-party/concurrency/operational risks, unresolved design decisions, assumptions requiring confirmation, implementation verification items.

Deliver the result as the delivery rule in `SKILL.md` describes (an English design document; a
short Japanese summary and the open questions in the chat).
