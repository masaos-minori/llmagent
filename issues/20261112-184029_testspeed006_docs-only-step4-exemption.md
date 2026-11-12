# Define the Step 4 test requirement for documentation-only implementation cycles

## Priority
Medium

## Summary
`skills/code-implementation/workflow.md` Step 4 requires targeted tests and one full-suite run per cycle and does not say what applies when the cycle changes only documentation or workflow files. Define explicitly which verification replaces the test run for such cycles, so the executor neither runs a pointless full suite nor skips tests by judgment, and so the rule is consistent with the 0-collected-test rule.

## Background
- Step 4 says to run targeted tests, to confirm that "the run collected at least one test (a 0-collected, exit-0 run is not a pass)", and then to run "the repository-defined full test suite exactly once per cycle". The only documentation-only exemption in Step 4 is for diff-cover: "when no source file changed (docs, skills, templates only), record `N/A`". Row 3 of the Row mapping says it is Completed when Step 3e passes and "Step 4's full-suite run passes". `skills/code-implementation/SKILL.md` repeats the full-suite rule.
- For a documentation-only change, impact-based selection (`--testmon-forceselect`) selects nothing, so the 0-collected rule makes the targeted run a non-pass by the text, while the full suite takes minutes (3m47s wall time with 8 workers on 2026-11-12) for a change that cannot touch `scripts/`.
- `templates/implementation-procedure.md` "Lightweight fill" says a documentation-only row drops the "Add or update tests" step and keeps the documentation checkers named in `routing.md` as the validation step. That covers the procedure document, not the workflow's Step 4.
- In the 2026-11-12 run of 14 documentation-only procedures (`implementations/done/20261112-123928_*`), the executor ran the documentation checkers and did not run Step 4. The workflow text does not state that this is permitted, so it was a judgment call.
- The same run showed that checkers and tests can differ in coverage: the pre-commit hook `check-compat-shims` (which includes the opt-in removed-name check) failed on a wording change that the documentation checkers named in the procedure's Validation plan had passed. A heuristic search finds 17 files under `tests/` that build paths into `docs/` or `skills/`, so some tests do read those trees.

## Problem
The workflow is ambiguous for documentation-only cycles: read literally it demands a test run that cannot be satisfied (0 tests collected) or is wasteful (full suite), and an executor who skips it has no rule to cite. The stated replacement for tests is not defined, so which checkers must pass instead is left to each executor.

## Reason for Change
Documentation-only cycles are frequent in this repository (for example 14 in the 2026-11-12 batch), and each ambiguity either costs minutes of test time or weakens verification. Making the rule explicit removes both, and is the part of the speedup that costs no tooling.

## Implementation Intent
State in Step 4 a documentation-only case: define which paths count (a change set confined to documentation and workflow-artifact directories, with no `scripts/`, `tests/`, `tools/`, or `config/` file), and state what replaces targeted and full-suite runs: the documentation checkers required by `routing.md` "When to run which tool" and the pre-commit gates, with the Execution Status Notes recording `N/A: documentation-only change; replaced by ...`. Make the 0-collected rule explicitly not apply there, and make Row 3's completion condition and the Final Report consistent. Decide at planning time whether the replacement should also include running the repository-scan tests (see the related issue) because some tests read `docs/` and `skills/`.

## Target Files or Areas
- `skills/code-implementation/workflow.md` (Step 4, Row mapping row 3, Final Report Execution Status)
- `skills/code-implementation/SKILL.md` (Core Execution Rules, phase overview row 4)

## Required Changes
- Add the documentation-only case to Step 4 with the path definition and the replacement verification.
- State that the 0-collected rule and the full-suite rule do not apply to that case, and what is recorded in the Notes.
- Adjust Row 3's "Completed when" and the Final Report wording to match.
- Keep `skills/code-implementation/SKILL.md` consistent with the workflow text (single statement, no restatement; reference `workflow.md`).
- Name which checkers act as the replacement, referencing `routing.md` rather than copying its table.

## Constraints
- `AGENTS.md` Global Rule 9 stays satisfied: checkers named in `routing.md` still run for `docs/` and `tools/` changes.
- A cycle that touches any `scripts/`, `tests/`, `tools/`, or `config/` file keeps the existing Step 4 behavior unchanged.
- Do not restate the checker list in the skill; reference `routing.md` (single source of truth).
- Skill text changes follow `skills/DESIGN.md` conventions and must not create a heading-level reference cycle.

## Acceptance Criteria
- Step 4 contains an explicit documentation-only case with a stated path definition and a stated replacement verification.
- The 0-collected rule is explicitly scoped so that it does not make a documentation-only cycle impossible to complete.
- Row 3's completion condition and the Final Report are consistent with the new case.
- `skills/code-implementation/SKILL.md` and `workflow.md` do not contradict each other.
- `uv run python tools/check_skills_references.py` and `uv run python tools/check_skills_heading_cycles.py` pass.

## Testing Expectations
- `uv run python tools/check_skills_references.py`.
- `uv run python tools/check_skills_heading_cycles.py`.
- A dry application of the new text to the 14 archived procedures of 2026-11-12 (read-only) to confirm that each would be classified as documentation-only and that the stated replacement checkers cover what was run.
- Pytest is not required for the skill edit itself (no code behavior changes).

## Documentation Impact
Yes, limited to `skills/code-implementation/workflow.md` and `skills/code-implementation/SKILL.md`: state the intent and the boundary of the documentation-only case. No `docs/` change.

## Out of Scope
- Changing the full-suite or coverage rules for cycles that touch code or tests.
- Changing `routing.md` or the checkers.
- Making the full suite run less often for code cycles (a separate proposal).
- Adding or removing tests.

## Dependencies
- `issues/20261112-183738_testspeed001_mark-repo-scan-tests.md`: related; if a repository-scan marker is added there, the replacement verification here may include running the marked tests for changes under `docs/` and `skills/`. Not blocking.

## Unresolved Questions
- Whether the replacement should include running the 17 (heuristically found) test files that read `docs/` or `skills/`, or only the checkers: 不明. Their contents were not read.
- The exact path set that counts as documentation-only (for example whether `rules/`, `templates/`, `prompts/`, `config/*.toml` belong): 不明; proposal is documentation and workflow-artifact directories only.
- Whether `git-commit-and-sync` Phase 4 gate results should be accepted as the replacement evidence: 不明.

## AI Implementation Instruction
Edit only the two skill files named above and keep the change minimal: add the case, scope the rules, align the references. Do not copy checker lists into the skill. Do not change behavior for code cycles. Run the two skill checkers after editing. If the path definition is contested, list the candidates and ask instead of choosing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261112-184029
- **Related target files**: `skills/code-implementation/workflow.md`, `skills/code-implementation/SKILL.md`
