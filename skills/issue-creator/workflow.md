# Issue Creator — Detailed Workflow

## Phase 1: Classify and Frame

Identify the source of the work:
- review findings, investigation notes, an implementation plan, or a raw user request

Identify:
- scope of the work described
- whether requirements are complete or need assumptions
- whether the source already provides evidence (code review, investigation) or is request-only

If requirements are incomplete, mark assumptions and open questions instead of inventing
missing requirements.

---

## Phase 2: Task Grouping

Decide whether to split work into multiple issues or group it into one.

### Group tasks into one issue only when

- they modify the same file or tightly coupled files
- they are part of the same reviewable change
- separating them would cause duplicate work
- they share the same acceptance criteria
- they must be tested together

### Do not group tasks when

- they affect unrelated areas
- they have different owners
- one can be completed safely without the other
- they require different validation strategies
- grouping would make review harder

---

## Phase 3: Draft Reason for Change and Implementation Intent

**Reason for Change** — explain why the change is needed. Include relevant context: current
problem, maintenance risk, operational risk, correctness risk, documentation/code mismatch,
user or developer impact.

**Implementation Intent** — explain how the work should be approached at a high level.
Focus on responsibility boundaries, minimal change, expected design direction, what should be
preserved, and what should not be changed. Do not include excessive implementation details.

---

## Phase 4: Scope and Boundaries

**Target Files or Areas** — list only likely relevant files or areas. Do not list the entire
repository. Use `Unknown` if the exact file is not confirmed.

**Required Changes** — list concrete changes as small, actionable bullets.

**Out of Scope** — list what must not be changed in this issue.

---

## Phase 5: Acceptance Criteria and Testing

**Acceptance Criteria** — list verifiable completion criteria. Each item should be testable
by review, test execution, or documentation inspection.

**Testing Expectations** — include when relevant: unit tests, integration tests, regression
tests, type checks, lint checks, documentation consistency checks, manual verification. Use
`Not required` only when the task is documentation-only or clearly does not affect behavior.

---

## Phase 6: Documentation Impact

State whether documentation must be updated. If affected, specify what kind of information
should be documented: intent, boundaries, constraints, failure behavior, operational notes,
Known Issues, Needs Confirmation items.

### Documentation cleanup rules

For documentation-related issues, focus on: design intent, responsibility boundaries,
constraints, design decisions, operational notes, failure behavior, Known Issues, Needs
Confirmation items.

Avoid asking implementers to add: exhaustive file lists, complete public method catalogs,
complete DTO/TypedDict/dataclass/Pydantic field tables, complete configuration key tables,
complete CLI argument tables, long command examples, full JSON payload examples that simply
mirror schemas.

If implementation-derived details are currently present, prefer in this order: remove,
compress, replace with source reference, move to Known Issues, move to Needs Confirmation.

---

## Phase 7: Priority Assignment

### High

Tasks that affect: correctness, data integrity, security-sensitive behavior, startup or
deployment failure, workflow execution, public API behavior, production reliability,
critical documentation/code mismatch.

### Medium

Tasks that affect: maintainability, testability, type safety, unclear ownership, ambiguous
configuration behavior, non-critical documentation/code mismatch, documentation structure
that affects AI or developer usability.

### Low

Tasks such as: wording cleanup, small metadata cleanup, minor formatting improvements,
opportunistic link descriptions, non-blocking consistency improvements.

---

## Phase 8: AI Implementation Instruction

Give concise instructions for an AI coding agent. Include constraints such as: do not
rewrite unrelated files, keep changes minimal, preserve public behavior unless explicitly
required, stop and report open questions if requirements are unclear, do not implement
out-of-scope items.

---

## Phase 9: Evidence, Markdown Safety, and Final Checklist

### Evidence and assumptions

When the issue is based on code review or investigation:
- include evidence where available
- distinguish confirmed facts from assumptions
- mark unknowns explicitly
- do not present suspected behavior as confirmed

When the issue is based on a user request only:
- state assumptions clearly
- include open questions if requirements are incomplete
- do not invent missing requirements

### Markdown safety rules

- Emit each issue as a separate Markdown block when requested.
- Avoid nested triple-backtick blocks inside issue bodies.
- If code examples are unavoidable, prefer indented examples or short inline snippets.
- Do not put large code blocks inside Markdown tables.
- Use bullet lists instead of complex tables when copy-paste safety matters.
- Keep headings consistent.
- Ensure every opened list, quote, or block is closed.

### Final checklist

Before finalizing issues, verify:
- [ ] each issue is actionable
- [ ] each issue has a clear reason for change
- [ ] each issue has clear implementation intent
- [ ] acceptance criteria are verifiable
- [ ] out-of-scope items are explicit
- [ ] testing expectations are included or intentionally marked not required
- [ ] related tasks are grouped only when appropriate
- [ ] Markdown is safe to copy and paste
- [ ] no secrets or sensitive data are included
