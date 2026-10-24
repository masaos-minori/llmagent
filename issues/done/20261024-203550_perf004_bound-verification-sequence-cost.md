# Bound verification sequence cost in code-implementation cycles

## Priority
Medium

## Summary
Reduce the machine time the `code-implementation` workflow spends re-running its
validation and test sequence: make impact-based test selection (`pytest --testmon`,
already a declared dependency but never used) actually run during fix iterations,
scope post-fix re-validation to the validators the fix can affect, and keep the
per-cycle full-suite run to the once-plus-Attempt-Limit bound the workflow already
states. All verification gates stay fully enforced.

## Background
2026-10-24 investigation over the opencode session history DB, `code-implementation`
phase (25 sessions, 186 implementation cycles). Measurements (Operationally observed):

- Shell commands per cycle: 34.8 calls, 7.14 min/cycle of command execution.
  Share of categorized command time: full-suite `pytest` 30.2%, `git` 18.5%,
  targeted `pytest` 16.1%.
- `pytest` runs 3.44 times per cycle (565.2 min total, 3.0 min/cycle); each
  full-suite run averages 157 s (369.3 min total).
- Full-suite re-runs beyond the per-cycle bound are common in failure-retry loops:
  worst measured session ran the full suite 22 times across 6 cycles; another 16
  times across 23 cycles.
- `pytest --testmon`: 0 calls across all 186 cycles, although Step 4 of
  `skills/code-implementation/workflow.md` names it as the targeted-scope method
  "when available" and `pytest-testmon` 2.2.0 is a declared dev dependency in
  `pyproject.toml` (Explicit in code).
- Post-fix re-validation re-runs the whole Step 3e sequence: per-cycle call counts
  (ruff 1.51, mypy 1.44, bandit 0.77, lint-imports 0.72, coverage/diff-cover 0.56)
  all exceed what a single passing sequence pass would produce.
- Wall-time composition per cycle: 50.4 min model generation + 7.1 min shell +
  4.8 min question waits (~62 min/cycle); command execution is ~11% of cycle time
  and validation is its largest component.

## Problem
Verification re-runs — repeated full-suite `pytest` and whole-sequence re-passes
after each fix — are the largest controllable machine-time cost inside a cycle,
while the configured impact-based selection tool is never invoked.

## Reason for Change
Full-suite execution alone consumed 369 min across the measured 186 cycles, and
multi-run retry loops compound it (up to 3.7 full-suite runs per cycle observed).
At identical prefill/decode speed this is pure work volume, the same cost structure
measured for `issue-to-plan` in `perf001`-`perf003`.

## Implementation Intent
Keep every gate; change iteration discipline only:

- During Step 3e/4 fix iterations, run impact-based targeted tests (`pytest
  --testmon tests/`) and only the validators the fix can affect; re-run the
  complete sequence only when the fix actually spans families (formatting,
  typing, imports) — the workflow already enforces this for the Step 3e/4
  cross-re-run edge case; generalize the scoping consistently.
- After fixing a full-suite failure, confirm with the targeted scope first, then
  re-run the full suite once per attempt, respecting the existing Attempt Limit —
  no full-suite run that a targeted run could have caught.
- Record per-cycle which validation runs were skipped as already-passed-and-
  unaffected, so evidence requirements remain auditable.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 3e, Step 4)
- `skills/python-test-and-fix/workflow.md` (Step 10 impact-based execution, if the
  policy needs the same strengthening)

## Required Changes
- Make testmon-based selection the required iteration path (not the "when
  available" fallback) given `pytest-testmon` is a declared dependency, or record
  why it is unusable and name the replacement selection method.
- Add scoped-re-validation wording to Step 3e's on-failure path and Step 4's
  fix-then-rerun path.

## Constraints
- MUST NOT remove or weaken the single per-cycle full-suite gate, the coverage
  threshold in `rules/toolchain.md` (Completion checklist, diff-cover), the boundary
  test requirement, or the routing-checker obligations in `routing.md`.
- MUST NOT change AGENTS.md Attempt Limit or Failure Log semantics.
- MUST NOT weaken evidence requirements from `rules/ai-execution.md` Repository
  Tool Usage #8 (non-empty target confirmation, collected-test confirmation).
- `.testmondata` stays gitignored and uncommitted (already covered by
  `skills/python-test-and-fix/workflow.md` Step 10).

## Acceptance Criteria
- In a comparable cycle, iteration-phase test runs use impact-based selection (a
  `--testmon` run or a recorded equivalent is observable in the session's tool
  calls).
- Full-suite runs per cycle ≤ 1 + 1 per distinct full-suite failure attempt,
  verifiable from the session's tool calls; no session exceeds this bound.
- Comparable cycle's total `pytest` execution time is measurably below the
  3.0 min/cycle baseline.
- `rules/toolchain.md` validation sequence and the repo test suite still pass with
  no new failures.

## Testing Expectations
- Before/after measurement with the same session-history-DB methodology used in
  the 2026-10-24 investigation, over at least one real code-implementation cycle.
- `uv run python tools/check_skills_references.py` and
  `uv run python tools/check_skills_heading_cycles.py` pass.
- Unit tests: Not required (instruction-only change; no code behavior changes).

## Documentation Impact
No `docs/` update required. `routing.md` is not touched: the tool inventory already
lists `pytest --testmon`.

## Out of Scope
- Redundant re-reads, redundant `git` state checks, and tool-call sequencing
  (covered by `perf001`, extended 2026-10-24 to code-implementation).
- Question-call count and human-wait latency (filed as `perf005`).
- Lazy loading of the Step 0 mandatory-load set — excluded by the 2026-10-24
  prompt-cache user decision, same as the other perf issues.
- Changes to the toolchain itself (pytest config, CI, coverage thresholds,
  `rules/toolchain.md` gate definitions).

## Dependencies
- `perf001` now targets the same `skills/code-implementation/workflow.md`; this
  issue MUST be re-anchored against the current file state if applied after it.
- `perf005` will also edit `skills/code-implementation/workflow.md`; same
  re-anchoring rule applies.
- Sibling-issue check (2026-10-24): no open issue or plan in `issues/`,
  `issues/done/` (last 30 days), or `plans/` covers validation-sequence cost;
  `ci001` (scheduled CI result check) is unrelated to per-cycle local validation.

## Unresolved Questions
- Why `--testmon` was never used in 186 measured cycles despite being installed
  and instructed: runtime unavailability on this environment, first-run cold-cache
  behavior (a cold `.testmondata` makes the first run a full collection), or
  instruction ambiguity (`Needs confirmation` — verify at runtime during planning).
- Whether scoped re-validation conflicts with Step 3e's "Completed when: all of
  the above pass" semantics for a multi-family fix — a design decision for the
  Plan (`Needs confirmation`).

## AI Implementation Instruction
Edit only the validation-iteration discipline in the named workflow files. Keep
the full-suite gate, coverage threshold, evidence-confirmation rules, and Attempt
Limit wording intact. Re-read the current file state before editing (`perf001` and
`perf005` may already have changed the same file). Run both skills checkers before
committing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261024-203550
- **Related target files**: skills/code-implementation/workflow.md; skills/python-test-and-fix/workflow.md
