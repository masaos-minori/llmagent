# Add a lightweight Plan form for Path A issues

## Priority
Medium

## Summary
Reduce the mandatory section set of `templates/plan.md` for Path A (small-task)
Plans — or add a Path A variant — so a small Plan carries only the sections its
downstream consumer actually reads. Intended outcome: smaller Plans, less Step 6
row-validation work, and smaller downstream procedure documents.

## Background
2026-10-24 investigation over generated documents and session history:

- `templates/plan.md` mandates 24 `##` sections (Explicit in code; 7.5KB skeleton).
- Generated Plans (statistics over the archived corpus): median 118 lines / 6.8KB,
  mean 146 lines / 10.8KB; recent Path A cycles produce 14-46KB Plans; the corpus
  max is 173KB with 199 Implementation Target Files rows. Median rows per Plan is
  3 (mean ~5-6).
- Writing the Plan itself is only ~1.3% of cycle reasoning, but Plan size drives
  two downstream costs: Step 6 verifies every row, and the
  plan-to-implementation-procedure pass sizes its output from the Plan's rows —
  its generated documents (median 103-123 lines) far exceed the template's own
  ~40-line lightweight target (recorded in `memo-workflow.md`, candidate 6: cap
  Plan size upstream in issue-to-plan).

## Problem
A 3-row Path A Plan is required to fill the same 24-section skeleton as a large
Path B Plan. Sections no consumer reads for Path A still cost generation tokens in
Step 7, validation attention in Step 8, and downstream size inflation in
plan-to-implementation-procedure.

## Reason for Change
The pipeline is now measured: Plan-side work is a multiplier on both this cycle's
reasoning and the next phase's document volume. Cutting unused Path A sections is
the cheapest way to shrink the deliverable itself (the perf001/perf002 issues cut
overhead; this one cuts the output).

## Implementation Intent

- First audit which `templates/plan.md` sections
  `skills/plan-to-implementation-procedure/workflow.md` and
  `rules/workflow-lifecycle.md` actually consume; the retained Path A set is
  derived from that audit, not from taste.
- Then either (a) mark Path-B-only sections as conditionally required in the
  single template, or (b) add a reduced Path A variant template. Which mechanism
  is chosen is a design decision for the plan — see Unresolved Questions.
- Add Path A sizing discipline: guidance that a Path A Plan whose target-row count
  or scope clearly exceeds the Path A boundary is reclassified to Path B or split
  into separate Issues (`Needs confirmation` — this bullet came from the
  investigation's candidate 6, thresholds undefined).

`N/A`-style placeholder rules (e.g. `N/A: {short reason}`) may be a cheaper
alternative for some sections; evaluate within the audit.

## Target Files or Areas
- `templates/plan.md`
- `skills/issue-to-plan/workflow.md` (Step 7 generation, Step 8 validation)
- `skills/plan-to-implementation-procedure/workflow.md` (consumer-side section
  extraction — audit input)
- `tools/check_workitem_structure.py` (required-section expectations if sections
  become conditional or a variant is added)
- `rules/workflow-lifecycle.md` (only if Plan Freeze criteria reference a section
  being made optional)

## Required Changes
- Audit and document which Plan sections each downstream consumer reads.
- Make Path-B-only sections optional (or variant-excluded) for Path A Plans.
- Update `check_workitem_structure.py` expectations to match the chosen mechanism.
- Add Path A size-discipline guidance to the workflow (threshold pending
  confirmation).

## Constraints
- The Plan Freeze row-validation contract (all four criteria over
  Implementation Target Files rows) MUST NOT change.
- Downstream extraction in plan-to-implementation-procedure Step 1 (and its
  structure checker) must keep working on both existing Plans in `plans/done/` and
  new lightweight Plans.
- Path B Plans keep the full current section set.
- MUST NOT restate `rules/workflow-lifecycle.md` inline in skills.

## Acceptance Criteria
- A post-change Path A Plan is measurably smaller than the pre-change band (median
  6.8KB / recent 14-46KB) while passing structure validation.
- One full pipeline cycle (issue → plan → implementation procedure) completes with
  the lightweight Plan, and the generated procedure documents pass their own
  structure validation.
- `check_workitem_structure.py` passes on both a lightweight Path A Plan and a
  full Path B Plan.
- `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` exit 0.

## Testing Expectations
- Structure-checker runs against both Plan forms (extend existing tool tests if
  the tool branches on Path).
- One end-to-end pipeline cycle executed on a real Path A issue, with results
  compared against the 2026-10-24 baseline corpus statistics (median Plan lines /
  bytes, procedure doc lines).
- No new unit tests for skill/prompt text itself.

## Documentation Impact
No `docs/` update required. The template's own header comments and
`routing.md`'s Document workflow directories notes are updated only if the
Plan-form mechanism changes their described contract.

## Out of Scope
- Lazy loading of the Step 0 mandatory-load set — removed from scope by user
  decision (2026-10-24): the fixed load is absorbed by the prompt cache (applies to
  all perf issues).
- Redundant re-read and tool-batching changes (`perf001`).
- Verification-scope bounding (`perf002`).
- Changes to `templates/issue.md`, `templates/unknowns-issue.md`,
  `templates/risks-issue.md`.
- Retro-editing archived Plans in `plans/done/`.

## Dependencies
- Depends on a consumer-side section audit (part of this issue, Step 1 of the
  implementation) before any section is removed.
- `perf001` and `perf002` touch `skills/issue-to-plan/workflow.md`; re-anchor
  against current file state if applied later.
- Sibling-issue check (2026-10-24): no open issue or plan covers Plan template
  reduction.

## Unresolved Questions
- Conditional-optional sections in one template vs a separate Path A variant file
  — which keeps `check_workitem_structure.py` and Step 2 extraction simpler
  (`Needs confirmation` — design decision for the plan).
- Numeric threshold at which a Plan should stop being Path A (`Needs confirmation`
  — ask the user).

## AI Implementation Instruction
Audit consumers before touching the template; never delete a section a downstream
consumer reads; keep Path B behavior identical; keep validation criteria intact;
re-read the current `workflow.md` and `templates/plan.md` before editing since
companion issues touch the same files. Run the structure checker and both skills
checkers before committing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-185701
- **Related target files**: templates/plan.md; skills/issue-to-plan/workflow.md; skills/plan-to-implementation-procedure/workflow.md; tools/check_workitem_structure.py; rules/workflow-lifecycle.md
