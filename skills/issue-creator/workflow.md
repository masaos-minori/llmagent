# Issue Creator — Detailed Workflow

## Multi-file processing

When Phase 2 decides to split the work into multiple issues, apply `rules/ai-execution.md`
Sequential Target Processing (Base): draft, verify (Phase 9), and generate the filename
(Phase 10) for one issue completely before starting Phase 3 for the next — do not batch-draft
several issues' Phase 3-8 content before running Phase 9/10 on any of them. This also
prevents two issues drafted in the same batch from colliding on the same generated filename,
since Phase 10's uniqueness check (below) sees each prior issue's file already written before
checking the next.

## Phase 1: Classify and Frame

Identify the source of the work:
- review findings, investigation notes, an implementation plan, or a raw user request

Identify:
- scope of the work described
- whether requirements are complete or need assumptions
- whether the source already provides evidence (code review, investigation) or is request-only

If requirements are incomplete, mark assumptions and open questions instead of inventing
missing requirements — record them in the issue's `Unresolved Questions` section
(per `templates/issue.md`), not only in this phase's internal reasoning.

**Completed when**: source, scope, and completeness (complete vs. needs assumptions) are all
recorded, and any incomplete requirement has a corresponding assumption or open question.
**Stop and ask the user before Phase 2 when**: the scope of the work cannot be determined
even provisionally — there is nothing to group or draft against. Any other incompleteness is
recorded as an assumption/open question and framing continues.

---

## Phase 2: Task Grouping

Decide whether to split work into multiple issues or group it into one.

### Group tasks into one issue only when

- they modify the same file or tightly coupled files
- they are part of the same reviewable change
- separating them would cause duplicate work
- they share the same acceptance criteria
- they must be tested together

### Split into separate issues when

- they affect unrelated areas
- they have different owners
- one can be completed safely without the other
- they require different validation strategies
- grouping would make review harder

**Completed when**: every task from Phase 1's scope has been assigned to exactly one issue
group, using the criteria above (grouping and splitting are mutually exclusive per pair of
tasks — a pair matching a "Group" criterion is not also split, and vice versa).

---

## Phase 3: Draft Background, Problem, Reason for Change, and Implementation Intent

**Background** — why this requirement exists: prior context, history, related decisions.
Use `N/A: covered by Summary` when `Summary` already says everything relevant.

**Problem** — the concrete problem being solved, stated separately from the general
`Summary`. Use `N/A: {short reason}` for proposals that are not problem-driven.

**Reason for Change** — explain why the change is needed. Include relevant context: current
problem, maintenance risk, operational risk, correctness risk, documentation/code mismatch,
user or developer impact.

**Implementation Intent** — explain how the work should be approached at a high level.
Focus on responsibility boundaries, minimal change, expected design direction, what should be
preserved, and what should not be changed. Name a specific file, function, or line number
only when the boundary itself is the design decision (see `skills/DESIGN.md` Avoid
implementation-reference duplication) — otherwise describe the responsibility, not the
location.

---

## Phase 4: Scope and Boundaries

**Target Files or Areas** — list only likely relevant files or areas. Do not list the entire
repository. Use `Unknown` if the exact file is not confirmed.

**Required Changes** — list concrete changes as small, actionable bullets.

**Constraints** — technical or domain constraints and limitations that bound the
solution space (compatibility, performance, security, operational). Use
`N/A: {short reason}` if none apply.

**Out of Scope** — list what must not be changed in this issue.

**Dependencies** — other issues, plans, or external work this issue depends on, or
that depend on it. Use `N/A: none` if there are none.

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

Apply `skills/DESIGN.md` Avoid implementation-reference duplication and Docs content policy —
remove to what implementers are asked to add.

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

This phase has three sub-steps, applied in order: verify evidence (9a), verify markdown
safety (9b), then run the final checklist (9c).

### Step 9a: Evidence and assumptions

When the issue is based on code review or investigation, apply `skills/DESIGN.md` Evidence
labels and Confidence levels — do not invent a parallel confirmed/assumption/unknown scheme.

When the issue is based on a user request only:
- state assumptions clearly
- include open questions if requirements are incomplete
- do not invent missing requirements

**Completed when**: every claim in the issue is either backed by cited evidence (code
review/investigation) or explicitly marked as an assumption/open question.

### Step 9b: Markdown safety rules

- Emit each issue as a separate Markdown block when requested.
- Avoid nested triple-backtick blocks inside issue bodies.
- If code examples are unavoidable, prefer indented examples or short inline snippets.
- Do not put large code blocks inside Markdown tables.
- Use bullet lists instead of complex tables when copy-paste safety matters.
- Keep headings consistent.
- Ensure every opened list, quote, or block is closed.

**Completed when**: every rule above has been checked against the drafted issue body.

### Step 9c: Final checklist

Before finalizing issues, verify:
- [ ] each issue is actionable
- [ ] Background, Problem, Reason for Change, and Implementation Intent meet Phase 3
  (or are explicitly `N/A` with a reason)
- [ ] Acceptance Criteria and Testing Expectations meet Phase 5
- [ ] Constraints, Out of Scope, and Dependencies are explicit (or `N/A`), per Phase 4
- [ ] Unresolved Questions reflects every open assumption from Phase 1 (or is `N/A: none`)
- [ ] grouping follows Phase 2 criteria
- [ ] Markdown safety follows Step 9b
- [ ] no secrets or sensitive data are included (see `SKILL.md` Core Principles)
- [ ] the issue follows `templates/issue.md`'s field order and names exactly

**Completed when**: every checked item above is true.
**On an unchecked item**: return to the phase that owns it (Phase 1–8, or Step 9a/9b above)
and fix only the gap the item identifies — do not redo the whole phase's output. Then
re-check only that item, not the full checklist, before proceeding to Phase 10.
Per `AGENTS.md` Loop Prevention > Attempt Limit, this fix-and-recheck loop tolerates at most
3 attempts per distinct unchecked item; if it still fails to clear after 3 attempts, stop and
report `Blocked: {item} still unresolved after 3 attempts` rather than continuing to patch.

---

## Phase 10: Generate Issue Filename

After the issue body is finalized, generate the filename using the convention defined in
`SKILL.md` Issue Filename Generation.

1. Extract or assign an `{id}` from the issue content (e.g., `NC-019` → `nc019`).
   If no meaningful ID exists, use a generic prefix + sequence number (e.g., `todo_001`).
2. Generate `{timestamp}` as `YYYYMMDD-HHmmss` at creation time.
3. Derive `{slug}` from the issue title: lowercase, replace spaces with dashes, remove
   non-alphanumeric characters except dashes.
4. Assemble: `{timestamp}_{id}_{slug}.md`
5. Verify uniqueness against existing files in `issues/` before writing — check via `ls
   issues/{timestamp}_*` or equivalent; an empty result means no collision only if the
   command actually targeted the `issues/` directory (confirm it exists first), not proof
   by itself.
6. If a collision is found, regenerate with the next available disambiguator (e.g. a
   numeric suffix on `{id}` or `{slug}`) and re-check uniqueness. Per `AGENTS.md` Loop
   Prevention > Attempt Limit, retry up to 3 times; after 3 collisions, stop and report
   `Blocked: repeated filename collision — {path}` rather than continuing to increment.

Do NOT create issues without following this naming convention.

**This task is complete when, and only when**: the issue file has been written to
`issues/` at its verified-unique filename, or the cycle ended in a `Blocked` state per
Phase 9c or this Phase's own stop condition — in either case, for a Multi-file batch (see
Multi-file processing above), proceed to Phase 3 for the next issue only after this one's
outcome (written or `Blocked`) is settled.
