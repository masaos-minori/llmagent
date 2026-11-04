# Scope companion-test candidates to the target plan's procedures

## Priority
Medium

## Summary
Stop `check_workitem_traceability.py --plan-coverage` from counting companion tests of other plans' procedures, which produces a false `companion-multi-row` finding.

## Background
Confirmed by repository evidence on 2026-11-04: in `find_plan_coverage_findings` (`tools/check_workitem_traceability.py`), the per-document loop skips documents whose `Source plan` is another plan, but the later `companion_candidates` set is built from every implementation document in `documents` (`for doc in documents if doc.kind == "implementation"`). A companion test file named in `Related Tests` of two rows of the checked plan is then reported as `companion-multi-row` even when the companion declarations come from procedures of a different plan.

This produced a real false positive while generating the startretry001 procedures (`tests/agent/test_agent_factory.py`); the plan was changed as a workaround, recorded in that plan's Assumptions.

## Problem
The rule is meant to find a companion that two rows of one plan both name, but its candidate set is repository-wide. Unrelated plans can fail each other's coverage check, and the only available workaround is editing the plan.

## Reason for Change
Correctness defect in a gating tool (pre-commit runs `check_workitem_traceability`) that forces plan edits to satisfy the checker. Not time-sensitive beyond that.

## Implementation Intent
Build the candidate set from the same documents the function already filters by `Source plan`. Keep every other finding code and the rule's meaning unchanged.

## Target Files or Areas
- `tools/check_workitem_traceability.py` (`find_plan_coverage_findings`)
- `tests/tools/test_check_workitem_traceability.py`

## Required Changes
- Restrict `companion_candidates` to implementation documents whose `Source plan` is the checked plan.
- Add a regression test: procedures of plan A declare a companion that two rows of plan B also name; checking plan B reports no `companion-multi-row`.
- Keep a positive test: both rows of the same plan name the companion and a procedure of that plan declares it; the finding is still reported.

## Constraints
- Do not change finding codes, output format, or exit codes.
- Preserve behavior for plans whose procedures were all generated for that plan.

## Acceptance Criteria
- A companion declared only by another plan's procedure never yields `companion-multi-row` for the checked plan.
- The existing same-plan multi-row detection still reports the finding.
- `uv run pytest tests/tools/test_check_workitem_traceability.py -q` passes.

## Testing Expectations
- Unit tests as above; run `uv run python tools/check_workitem_traceability.py --plan-coverage <plan>` against an existing plan before and after to confirm no new findings.

## Documentation Impact
Only if the docstring or `TOOL_DESCRIPTIONS.md` states the candidate scope; update it then.

## Out of Scope
- The `row-uncovered`, `path-covered-twice`, and `companion-not-eligible` rules.
- Revisiting the startretry001 plan workaround.

## Dependencies
N/A: none (no open issue or plan targets this tool).

## Unresolved Questions
- Whether the startretry001 plan should regain the removed `Related Tests` entry after the fix: unknown.

## AI Implementation Instruction
Make the smallest change that filters by `Source plan`, with the failing regression test written first.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261104-152002
- **Related target files**: `tools/check_workitem_traceability.py`, `tests/tools/test_check_workitem_traceability.py`
