# Replace production-path asserts in the workflow adapter

## Priority
Low

## Summary
The engine adapter carries two `assert` statements on production code paths (flagged by bandit as `assert_used`), each followed by a suppression comment for a linter rule that is not even enabled. Replace them with explicit control flow.

## Background
Code review evidence (Verified):
- Bandit reports two low-severity `B101: assert_used` findings, both in `scripts/agent/workflow_engine_adapter.py`.
- Each assert is annotated `# noqa: B101`, but the project's ruff selection does not include the `B` rule family — the suppression comments are inert noise.
- Precedent: `issues/done/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md` (resolved) audited asserts across the agent code and established the project posture on production asserts; these two survived that pass.

## Problem
Asserts vanish under `python -O` and raise `AssertionError` — a type the surrounding error handling does not plan for — on paths that are ordinary control flow, not programmer-invariant checks. The inert noqa comments additionally mislead readers into thinking the suppression is meaningful.

## Reason for Change
Small, safe cleanup that clears the project's only remaining bandit findings in the reviewed domain and removes suppression noise that hides nothing. Opportunistic, low blast radius.

## Implementation Intent
Inspect both asserts at current source: if the asserted condition can fail through ordinary operation (config/state), replace with the appropriate explicit error or control flow already used nearby; if it is a genuine internal invariant, keep it as a deliberate raise or a documented guard consistent with the assert-audit precedent. Delete the noqa comments either way.

## Target Files or Areas
- scripts/agent/workflow_engine_adapter.py

## Required Changes
- Convert both assert sites to explicit handling.
- Remove the two inert noqa suppressions.
- Re-run bandit on the file to confirm the findings are gone.

## Constraints
- No behavior change for inputs where the assert currently holds.
- If either assert encodes a contract worth enforcing, replace with a raise whose error type the callers already handle.
- Keep the diff local to the two sites.

## Acceptance Criteria
- Bandit on the file reports zero `assert_used`.
- No noqa suppression remains in the file.
- Workflow tests green; no new exception type escapes the adapter's public contract.

## Testing Expectations
- Targeted adapter tests around both sites (trigger the previously-asserted condition if reachable).
- Bandit + ruff + mypy on the touched file.

## Documentation Impact
None. Suppression-audit bookkeeping: if the repository tracks suppressions (the archived unjustified-suppressions review), confirm the removal is reflected.

## Out of Scope
- Asserts in other modules.
- Changing bandit/ruff configuration.

## Dependencies
- Context: `issues/done/20261003-180336_assertaudit001_audit-assert-risks-post-execution-crash.md` and `issues/done/20261103-134148_wfreview005_unjustified-suppressions-and-stale-test-provenance.md` (both resolved; follow their posture).

## Unresolved Questions
- Are both asserted conditions genuinely reachable in production, or true invariants? Confirm per site at implementation time (the audit precedent has the method).

## AI Implementation Instruction
Handle the two sites separately and state for each whether the condition is reachable. Prefer the error type the surrounding code already handles over inventing a new one. No unrelated formatting changes.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-203226
- **Related target files**: scripts/agent/workflow_engine_adapter.py

## Adversarial Validation

Validated against current source on 2026-11-08 (issue-to-plan Step 2 cycle), including live bandit and ruff runs.

- Two production asserts confirmed: `assert self._workflow_engine is not None` (`scripts/agent/workflow_engine_adapter.py:172`, in `execute_turn`'s engine-start path) and `assert boundary is not None` (L407, in the persist-as-assistant path). Bandit reports exactly two `B101: assert_used` findings for the file. — Evidence: `Verified by test` (live bandit) — Confidence: High
- "Each followed by a suppression comment" claim corrected: only the L407 assert carries `# noqa: B101`; the L172 assert has no suppression. — Evidence: `Verified by test` — Confidence: High
- Inert-suppression confirmed live: ruff `select = ["E", "W", "F", "I", "UP", "BLE001"]` (`pyproject.toml:106`) — no `B` family; `uv run ruff check --select RUF100 scripts/agent/workflow_engine_adapter.py` reports the L407 `# noqa: B101` as an unused directive (1 error, auto-fixable), confirming it suppresses nothing. — Evidence: `Verified by test` (live ruff) — Confidence: High
- Replacement shape note: the L172 guard protects a `WorkflowEngine | None` constructor parameter used immediately after (`engine = self._workflow_engine`, L175) — a plain `if ... is None: raise` typed-error replacement must pick an exception the `execute_turn` except branches (`WorkflowHaltError`, `WorkflowTimeoutError`, generic) already plan for, per the issue's point about `AssertionError`. The L407 guard protects `ctx.turn.persistence_boundary` before `boundary.save(...)` (L408). — Evidence: `Verified by test` — Confidence: High
