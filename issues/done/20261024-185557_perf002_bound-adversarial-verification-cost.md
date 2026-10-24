# Bound adversarial verification cost in issue-to-plan Steps 2-4 and 6

## Priority
Medium

## Summary
Add explicit scope and repetition bounds to the adversarial verification the
`issue-to-plan` workflow applies per claim (Steps 2-4) and per Implementation
Target Files row (Step 6), so verification stops at its first sufficient check.
Intended outcome: lower reasoning volume per cycle with unchanged verification
criteria.

## Background
2026-10-24 session-history-DB investigation (16 plan-producing sessions).
Measurements (Operationally observed):

- Reasoning text per plan: 113K-224K characters in single-plan cycles; ~180K
  characters/plan in batch sessions — 10-20x the written Plan (median 6.8KB,
  recent cycles 14-46KB).
- Reasoning attribution across those sessions: ~61% is interpreting shell/repo
  investigation output, 7% git-history checks, 6.5% baseline tool output
  interpretation, 1.3% writing the Plan itself. Generation time 56-140 min per
  plan vs 0.3-21 min tool execution: the cost is verification reasoning, not tools.
- `rules/ai-execution.md` "Adversarial Verification (Base)" already carries a stop
  rule (check once against a concrete source; a disconfirming finding ends the
  investigation) — Explicit in code — but `skills/issue-to-plan/workflow.md` applies
  it to every claim and then re-applies it per row in Step 6 with no bound on
  how deep the investigation order (target file → direct dependencies → related
  tests) is expanded or how many times a row touched earlier in the cycle is
  revisited.

## Problem
A row that was already verified while checking the Issue's claims in Steps 2-4 is
adversarially re-verified again in Step 6, and investigation beyond the base order
is left open-ended ("expand beyond this order when evidence remains insufficient"
has no ceiling in practice). This is the single largest generator of reasoning
tokens in the measured cycles.

## Reason for Change
Verification reasoning is ~99% of cycle time; the same decode speed as other LLMs
is being spent on repeated checks. Counter-evidence to consider: `memo-workflow.md`
and git history (re-anchor commits `646881e0d`, `c2a423617`) show downstream
re-anchoring rework happens when documents go stale — so verification cannot simply
be deleted; it must be bounded. Cutting redundant repeats is the safe first step.

## Implementation Intent
Keep the verification criteria exactly as they are (all four row criteria in
`rules/workflow-lifecycle.md`, the Base investigation order in
`rules/ai-execution.md`); change only when a check may be skipped:

- State in Steps 2-4/6 that a claim or row verified earlier in the same cycle is
  not re-verified unless repository state changed since that check or the check was
  inconclusive.
- Give the investigation order a ceiling: Steps 2-4/6 MUST NOT expand beyond the
  base order (target file → direct dependencies → related tests) unless a concrete
  disconfirming finding was produced inside that order.
- Record in the Plan which step performed each row's evidence check, so Step 8 can
  confirm every row was checked at least once without a second verification pass.

The exact wording placement (workflow steps vs a reference to the Base section) is
a design decision for the plan; the Base rule file itself should not be weakened.

## Target Files or Areas
- `skills/issue-to-plan/workflow.md` (Steps 2-4, Step 5 scope, Step 6)
- `skills/issue-to-plan/SKILL.md` (Routing/step summaries if wording changes)
- `rules/ai-execution.md` — only if a bound must live in the Base section;
  preferred choice is to leave the Base untouched and bound application in the
  workflow

## Required Changes
- Add a same-cycle dedup rule: no re-verification of an already-verified claim/row
  unless repository state changed or the prior check was inconclusive.
- Add a depth ceiling to the investigation order in Steps 2-4 and Step 6.
- Add a "verified by step" reference on Implementation Target Files rows (or an
  equivalent existing field) so Step 8 validation can rely on earlier checks.

## Constraints
- The four row-validation criteria (Exists / Requires modification / Has supporting
  evidence / Linked to a Plan requirement) and the correction procedure on a
  disconfirming finding MUST NOT change.
- MUST NOT restate `rules/ai-execution.md` inline — reference it.
- Changes must apply identically to Path A and Path B unless the plan explicitly
  justifies a path-split (see Unresolved Questions).
- Edits under `skills/`, `rules/` must pass
  `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py`.

## Acceptance Criteria
- In at least one post-change real cycle, reasoning characters per plan are lower
  than the pre-change band (113K-224K) while every Implementation Target Files row
  still shows at least one concrete evidence check.
- No increase in downstream corrections attributed to stale Plan rows in the cycles
  following the change (checked against `implementations/` correction notes and git
  re-anchor commits).
- Step 8 validation demonstrably consumes the recorded checks instead of re-running
  them.
- Both skills checkers exit 0.

## Testing Expectations
- Before/after measurement with the same session-history-DB methodology as the
  2026-10-24 investigation (reasoning chars/plan, turns/cycle) over at least one
  real cycle.
- Manual review of one post-change Plan confirming every row has a concrete
  Repository Evidence citation.
- Unit tests: Not required (instruction-only change).

## Documentation Impact
No `docs/` update required. If the dedup rule is promoted into
`rules/ai-execution.md`, the Base section's scope statement must be updated there
(intent and boundaries only).

## Out of Scope
- Lazy loading of the Step 0 mandatory-load set — removed from scope by user
  decision (2026-10-24): the fixed load is absorbed by the prompt cache (applies to
  all perf issues).
- Redundant re-read and tool-batching changes (filed as `perf001`).
- Plan template section reduction (filed as `perf003`).
- Any change to the Plan Freeze criteria in `rules/workflow-lifecycle.md`.
- Baseline-tool selection changes in Step 5 beyond limiting output interpretation.

## Dependencies
- `perf001` and `perf003` edit the same `skills/issue-to-plan/workflow.md`; each
  MUST be re-anchored against the current file state when applied after the other.
- Sibling-issue check (2026-10-24): no open issue or plan covers verification-cost
  bounding.

## Unresolved Questions
- Is the quality trade-off acceptable to bound only Path A cycles, keeping Path B
  verification at full depth? (`Needs confirmation` — ask the user.)
- What downstream rework rate (stale-row corrections found by
  plan-to-implementation-procedure) counts as an acceptable regression signal?
  (`Needs confirmation`)

## AI Implementation Instruction
Bound application of verification, never its criteria. Do not weaken or inline-copy
`rules/ai-execution.md`; do not remove any Step 8 validation requirement; re-read
the current `workflow.md` before editing since companion issues touch the same
file. Run both skills checkers before committing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-185557
- **Related target files**: skills/issue-to-plan/workflow.md; skills/issue-to-plan/SKILL.md; rules/ai-execution.md
