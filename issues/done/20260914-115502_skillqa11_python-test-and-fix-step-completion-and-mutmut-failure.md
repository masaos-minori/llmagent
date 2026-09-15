# Add completion criteria to Steps 3/4/7 and define mutmut command-failure handling in python-test-and-fix

## Priority
Medium

## Summary
`skills/python-test-and-fix/workflow.md` Step 3 (Flaky Detection), Step 4 (Mutation Testing), and Step 7 (Contract Validation) each describe a procedure with no stated completion condition; Step 4 additionally does not state what to do if the `mutmut run` command itself fails (as opposed to reporting surviving mutants, which the Step already handles).

## Background
This issue follows a skill/workflow design review (5 evaluation criteria, 55 files) requested and conducted in this session. Step 4 already handles one failure mode carefully (the "0 surviving mutants out of 0 total" false-positive, citing `rules/ai-execution.md` Repository Tool Usage #8) — the gap identified here is a different one: the command's own exit code, not its reported results.

## Problem
Confirmed by direct reading:
- Step 3 (lines 99-121): describes a 3-command flaky-detection sequence with "stop as soon as one produces a clear answer" — this is a stopping heuristic, not a stated completion condition (what counts as "a clear answer" is not defined).
- Step 4 (124-146): describes `mutmut run`/`results`/`show` with no statement of what to do if `mutmut run` itself exits non-zero (e.g. a syntax error in the target, or the target path not found) — the Step's existing "0 surviving mutants out of 0 total" handling addresses a different case (the command succeeds but mutates nothing), not a command failure.
- Step 7 (212-243): describes when to use `hypothesis` (all-of conditions) but states no completion condition for the Step once hypothesis tests are written.

## Reason for Change
Step 3's "clear answer" and Step 7's implicit completion are both left to inference; Step 4's gap is more concrete — an agent that doesn't distinguish "mutmut ran and found 0 survivors" from "mutmut failed to run" could misreport a tooling failure as a clean mutation-testing pass.

## Implementation Intent
Add a "Completed when" line to Step 3 and Step 7 defining what a "clear answer"/finished Step looks like; add explicit command-failure handling to Step 4 distinguishing "ran, 0 total mutants" (already handled) from "did not run at all" (not yet handled).

## Target Files or Areas
- `skills/python-test-and-fix/workflow.md`

## Required Changes
- Step 3: add "Completed when: the failure is confirmed either as seed-order-dependent (fails only on certain seeds) or as true non-determinism independent of seed (fails under `--reruns` regardless of seed), with the dependency (if any) identified via the replay commands above."
- Step 4: add, before the existing "0 surviving mutants" handling: "If `mutmut run` itself exits non-zero (distinct from completing and reporting results): treat as a tool failure per `rules/ai-execution.md` Step-Level Failure Triage — do not report mutation testing as passed."
- Step 7: add "Completed when: a property-based test has been written for each function meeting both listed conditions, or the Step is confirmed not applicable (no function in scope meets both conditions)."

## Constraints
Do not change Step 4's existing "0 total mutants" false-positive handling — this issue adds a distinct, earlier check (command exit code) alongside it, not a replacement.

## Acceptance Criteria
- Step 3 and Step 7 each have an explicit "Completed when" line.
- Step 4 explicitly distinguishes a `mutmut run` command failure from a "ran but 0 total mutants" result, with the command-failure case routed to Step-Level Failure Triage.
- `tools/check_skills_references.py` still passes.

## Testing Expectations
Not applicable — prose-only workflow file. Run `tools/check_skills_references.py` per `routing.md`'s relevant row.

## Documentation Impact
This issue's entire scope is `skills/python-test-and-fix/workflow.md`.

## Out of Scope
- Steps 1, 2, 5, 6, 8-13 — not reviewed as gaps in this pass (Steps 1, 9, 12 already have adequate completion/exit conditions per this review).
- Any other evaluation criterion from the same review — tracked in separate issues.

## Dependencies
N/A: none.

## Unresolved Questions
N/A: none.

## AI Implementation Instruction
Add only the three items described in Required Changes; do not alter Step 4's existing "0 total mutants" handling, only add the command-failure check alongside it.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-115502
- **Related target files**: skills/python-test-and-fix/workflow.md
