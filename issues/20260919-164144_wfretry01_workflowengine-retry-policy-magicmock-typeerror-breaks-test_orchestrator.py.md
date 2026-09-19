# WorkflowEngine retry-policy fields are unmocked in test_orchestrator.py, causing 39 TypeError failures

## Priority
High

## Summary
`scripts/agent/workflow/workflow_engine.py`'s `_run_stage`/`_run_stage_with_retry` read
`policy.max_attempts` and a stage `timeout` value and compare them against real numbers
(`attempt >= policy.max_attempts`, `timeout <= 0`). `tests/agent/test_orchestrator.py`'s
mocked context/policy objects do not set these attributes to real numeric values, so they
resolve to auto-generated `MagicMock` instances, and the comparisons raise
`TypeError: '>=' not supported between instances of 'int' and 'MagicMock'` (and the `<=`
equivalent). 39 tests in this file fail as a result — confirmed to fail deterministically
in isolation (`pytest tests/agent/test_orchestrator.py`, no other test files involved), so
this is not test-order-dependent pollution.

## Background
Confirmed via a `git worktree` checkout of `origin/master` at commit `df4a58671` (before
this session's unrelated Agent/EventBus reference-table work was rebased on top) that the
same 39 failures reproduce identically on that commit alone — this predates and is
unrelated to that work.

## Problem
`_run_stage_with_retry`'s retry-policy check and `_run_stage`'s timeout check assume the
caller always supplies real numeric values for `policy.max_attempts` and the stage
timeout. `test_orchestrator.py`'s existing mocks for the workflow context/policy were
written before (or were not updated alongside) this retry/timeout logic, so a large
fraction of the orchestrator's `_handle_workflow_engine` test coverage currently cannot
run at all — masking whatever it was meant to verify (workflow status preservation,
callback invocation ordering, transport-error handling) behind an unrelated `TypeError`.

## Reason for Change
With 39 of the file's tests failing on setup/execution rather than on their actual
assertions, this test file provides no real regression coverage for
`Orchestrator._handle_workflow_engine` and its interaction with `WorkflowEngine`/
`WorkflowEngineAdapter`. Any future change to that code path could silently break
behavior these tests were meant to catch. "workflow execution" correctness is explicitly
a High-priority category for this project.

## Implementation Intent
Determine why the retry-policy/timeout fields are read as real numbers now (recent change
to `workflow_engine.py`, or a fixture that regressed) and bring `test_orchestrator.py`'s
mocks in line — either by giving the shared context/policy fixture real, explicit integer
defaults for `max_attempts` and timeout wherever `_run_stage`/`_run_stage_with_retry` is
exercised, or by adjusting the fixture construction so these fields are never left as bare
`MagicMock` attributes. Do not change `workflow_engine.py`'s production comparison logic
to work around a `MagicMock` (e.g. do not weaken the type check) — the fix belongs in the
test fixtures unless investigation shows the production code itself has a real gap (e.g.
should validate/default these fields defensively before comparing).

## Target Files or Areas
- `tests/agent/test_orchestrator.py` (39 failing tests, likely a shared fixture/mock setup)
- `scripts/agent/workflow/workflow_engine.py` (`_run_stage`, `_run_stage_with_retry`) — read-only investigation target; only change if the investigation finds a genuine production gap
- `scripts/agent/workflow_engine_adapter.py` (`execute_turn`) — call path between `Orchestrator._handle_workflow_engine` and `WorkflowEngine.run`

## Required Changes
- Identify every fixture/mock in `test_orchestrator.py` that stands in for the workflow
  context or retry policy consumed by `_run_stage`/`_run_stage_with_retry`.
- Set explicit real values (e.g. `max_attempts=1`, a real numeric timeout) on those
  mocks/fixtures instead of leaving them as default `MagicMock` attributes.
- Re-run `tests/agent/test_orchestrator.py` and confirm all 39 tests pass without
  weakening any existing assertion.

## Constraints
Do not alter `workflow_engine.py`'s retry/timeout comparison semantics as a workaround —
any production-code change must be justified by evidence of a real defect, not merely to
make the mocks pass.

## Acceptance Criteria
- `uv run pytest tests/agent/test_orchestrator.py -q` reports 0 failures.
- No existing passing test in this file is weakened, skipped, or deleted to reach that
  result.
- The fix does not change `workflow_engine.py`'s production behavior unless a genuine
  defect is found and documented as part of this issue's resolution.

## Testing Expectations
Run `uv run pytest tests/agent/test_orchestrator.py -q` before and after the fix; also run
the full `uv run pytest tests/ -q` to confirm no new failures are introduced elsewhere.

## Documentation Impact
N/A: test-fixture fix, no behavior or public API change expected.

## Out of Scope
Any other failing test file identified in the same investigation
(`tests/agent/services/test_config_reload.py`, `tests/eventbus/test_eventbus_auth.py`,
`tests/agent/services/test_mcp_tool_discovery.py`,
`tests/mcp_servers/git/test_git_security_compliance.py`) — each is tracked as its own
issue.

## Dependencies
N/A: none.

## Unresolved Questions
- Was the `policy.max_attempts`/timeout comparison in `workflow_engine.py` added or
  changed recently (making this a fixture drift), or has it existed for a while with
  these tests silently broken since some earlier unrelated change? Not investigated —
  left for the implementer.

## AI Implementation Instruction
Investigate `git log -p` for `scripts/agent/workflow/workflow_engine.py` to find when the
`policy.max_attempts`/timeout comparisons were introduced, then fix only
`tests/agent/test_orchestrator.py`'s fixtures/mocks to supply real numeric values. Do not
touch unrelated tests in this file. Do not modify `workflow_engine.py` unless the
investigation finds a genuine production defect — if so, stop and report it separately
before changing production code. Keep the diff minimal.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260919-164144
- **Related target files**: tests/agent/test_orchestrator.py, scripts/agent/workflow/workflow_engine.py, scripts/agent/workflow_engine_adapter.py
