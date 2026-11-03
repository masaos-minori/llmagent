# Two unjustified suppressions fail the suppression checker, and the fencing-gate test cites a nonexistent procedure document

## Priority
Medium

## Summary
`tools/check_suppression_justification.py` currently fails with 2 issues: an unjustified `# noqa: F401` in `tests/agent/workflow/test_stale_recovery_lease.py:321` and an unjustified `# type: ignore[arg-type]` in `tests/shared/test_json_utils.py:557`. Separately, the `TestFencingGateAC7` class docstring in the same test file points to `implementations/done/20261031-212239_wfrecovery001_recovery-dag.md`, which does not exist, and describes the fencing work as "Pending in plans/done/" without citing the actual artifacts. Restore a green suppression check and correct the test's provenance references.

## Background
Adversarial code review of `scripts/agent/workflow/` (2026-11-03). Evidence:

- Confirmed: `uv run python tools/check_suppression_justification.py` reports exactly 2 issues at the time of filing (2026-11-03): `tests/agent/workflow/test_stale_recovery_lease.py:321` (`from agent.workflow.attempt_ops import AttemptFencedError  # noqa: F401` — missing em-dash justification) and `tests/shared/test_json_utils.py:557` (`parse_iso_utc(1767225600)  # type: ignore[arg-type]` — missing em-dash justification).
- Confirmed: `AttemptFencedError` is referenced only by that test (`tests/agent/workflow/test_stale_recovery_lease.py:313,321`); it is not defined anywhere under `scripts/` — the test intentionally asserts its absence.
- Confirmed: the `TestFencingGateAC7` docstring (`tests/agent/workflow/test_stale_recovery_lease.py:310-317`) cites `implementations/done/20261031-212239_wfrecovery001_recovery-dag.md` (no such file exists in `implementations/done/`) and "Pending in plans/done/". The artifacts that actually exist are: open issue `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`, its processed plan `plans/done/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md`, and the 18-file implementation batch `implementations/done/20261101-163219_*` (including `20261101-163219_12_tests_agent_workflow_test_stale_recovery_lease.py.md`).
- Likely origin: the two suppressed lines sit inside files that the `20261101-163219` procedure batch (`_12_...test_stale_recovery_lease.py.md`, `_08_...test_json_utils.py.md`) generated or rewrote, suggesting the batch produced code without the `python-lint-typecheck` Step 4 justification format.

## Problem
A failing repository check is being tolerated: `check_suppression_justification.py` is part of the validation sequence, so its failure masks future unjustified suppressions (baseline drift). The stale docstring citation sends any future reader or agent to a nonexistent document, breaking the traceability chain that the fencing gate is supposed to enforce when `AttemptFencedError` eventually lands.

## Reason for Change
Suppression governance is a stated repository rule (justification comments required, per `skills/python-lint-typecheck` Step 4 format); a permanently red checker is a hole in CI discipline. Provenance accuracy matters here because the gate test exists specifically to force a review when the fencing work is implemented.

## Implementation Intent
- Add compliant justification text (em-dash format) to both suppressed lines, keeping the suppressions themselves (both are deliberate: an intentionally unused import inside `pytest.raises(ImportError)`, and an intentional wrong-type call under test).
- Correct the `TestFencingGateAC7` docstring to cite the existing artifacts (open wfrecovery001 issue, its done plan, and the 20261101-163219 procedure batch) and to state the gate's current meaning ("fence not yet implemented").

## Target Files or Areas
- `tests/agent/workflow/test_stale_recovery_lease.py`
- `tests/shared/test_json_utils.py`

## Required Changes
- Add a justification comment to `test_stale_recovery_lease.py:321` explaining the deliberate unused import (the import must fail; the name is intentionally never bound) in the checker's em-dash format.
- Add a justification comment to `test_json_utils.py:557` explaining the deliberate `int` argument to a `str`-typed parameter (negative-path type test).
- Rewrite the `TestFencingGateAC7` docstring references to the three exact existing paths.
- Re-run `uv run python tools/check_suppression_justification.py` until it reports 0 issues.

## Constraints
- Do not remove the suppressions by restructuring the tests (e.g. moving the failing import into a helper): the checker requires justification, not absence of suppression, and the absence-assertion pattern is the point of the gate test.
- Do not change test behavior or coverage; comments and docstring only.
- Justification format must satisfy `tools/check_suppression_justification.py` (em-dash `—` explanation on the same line).

## Acceptance Criteria
- `uv run python tools/check_suppression_justification.py` exits clean (0 issues).
- `TestFencingGateAC7` docstring paths all resolve to existing files under `issues/`, `plans/done/`, and `implementations/done/`.
- Both test files pass unchanged (`uv run pytest tests/agent/workflow/test_stale_recovery_lease.py tests/shared/test_json_utils.py`).

## Testing Expectations
- No new tests; run the two affected test files and the suppression checker.
- Confirm no other suppressions were added or removed (`git diff` review of suppression lines).

## Documentation Impact
None beyond the in-file docstring fix. No `docs/` changes.

## Out of Scope
- Implementing `AttemptFencedError` or the `finish_attempt` fence — owned by `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md`.
- Auditing other test files for suppression hygiene beyond the two reported lines.

## Dependencies
- `issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md` (open): the corrected provenance must point at this issue and its plan/procedure artifacts; when its fencing lands, this gate test is expected to fail and be flipped — that flip is that issue's work, not this one's.

## Unresolved Questions
- N/A: none.

## AI Implementation Instruction
Comment-level fix only. Use the exact em-dash justification format the checker requires, and verify with the checker tool — do not declare success from reading the file alone.

## Traceability
- **Workflow phase**: `python-code-review` (adversarial review of `scripts/agent/workflow/` and integration points), filed via `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261103-134147
- **Related target files**: `tests/agent/workflow/test_stale_recovery_lease.py`, `tests/shared/test_json_utils.py`
