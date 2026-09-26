# Self recursive subprocess test causes resource exhaustion

## Priority
High

## Summary
`tests/agent/test_tool_approval_preflight.py::TestRunApprovalChecks::test_regression_existing_agent_tests_pass` invokes `subprocess.run(["uv", "run", "pytest", "tests/agent/test_tool_approval_preflight.py", "-v"])` — i.e. it re-runs the entire file it is itself part of, as a subprocess. Since this same test exists in that re-run too, it recursively spawns another nested subprocess of the same file, and so on. Two attempts to run this single test (90s and 400s timeouts) both failed to complete; no orphaned processes were left behind after `timeout` killed the outer command, but this pattern is a strong candidate for having caused an unrelated background full-suite run to be killed earlier in the same investigation session due to host memory pressure.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`). While investigating the 97 full-suite failures by running failing files individually, this specific test could not be made to complete within 400 seconds, and source inspection (`tests/agent/test_tool_approval_preflight.py:791-806`) confirmed the self-recursive subprocess call.

## Problem
```
def test_regression_existing_agent_tests_pass(self) -> None:
    """Regression test: existing Agent tests still pass after adding new coverage."""
    result = subprocess.run(
        ["uv", "run", "pytest", "tests/agent/test_tool_approval_preflight.py", "-v"],
        capture_output=True, text=True,
    )
    assert result.returncode == 0, ...
```
This test, when collected as part of running `tests/agent/test_tool_approval_preflight.py` (whether alone or as part of the full suite), spawns a subprocess that re-runs the same file — which again collects this same test, spawning another subprocess, recursively. Runtime grows at least exponentially with recursion depth and is effectively unbounded within a normal test-run timeout.

## Reason for Change
This is a test-design defect with real operational impact: it can exhaust host memory/CPU when the full suite (or this file) is run, as observed indirectly in this session (a separate background full-suite re-run was killed by the harness for host memory pressure shortly after this recursive test would have executed). It must be fixed before it causes further environment instability, and it currently prevents this file's own regression-check intent from ever completing.

## Implementation Intent
Replace the self-recursive subprocess pattern. The test's evident intent — "confirm this file's other tests still pass as a regression check" — is structurally circular when implemented via subprocess re-invocation of the same file, since the regression test is itself one of the tests being re-checked. Prefer either: (a) removing this test entirely (regression coverage is already provided by the file's own other tests running normally in CI), or (b) if a subprocess-based self-check is genuinely wanted, excluding this specific test from the subprocess's own collection (e.g. via `-k 'not test_regression_existing_agent_tests_pass'` or a marker-based deselect) so it does not recurse.

## Target Files or Areas
- `tests/agent/test_tool_approval_preflight.py` (lines ~791-806)

## Required Changes
- Remove the self-recursive subprocess test, or fix it to deselect itself from the subprocess's collection so it cannot recurse.
- Confirm the fixed/removed test does not silently drop needed regression coverage — the file's other tests already provide direct coverage of the same behaviors.

## Constraints
Any replacement/fix must not reintroduce unbounded recursion or excessive runtime (the fixed version, if kept, should complete quickly, e.g. under the file's own normal per-test runtime).

## Acceptance Criteria
- Running `tests/agent/test_tool_approval_preflight.py` (and the full suite) completes without any nested nested `uv run pytest` subprocess spawning.
- The file's total run time returns to a normal per-file duration (comparable to other test files of similar size).

## Testing Expectations
Run `tests/agent/test_tool_approval_preflight.py` standalone with a strict timeout (e.g. `timeout 60`) after the fix to confirm it completes well within that bound.

## Documentation Impact
N/A: internal test-suite fix, no user-facing documentation impact.

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none — the recursive pattern is directly confirmed by source inspection.

## AI Implementation Instruction
Do not attempt to "fix" this by simply increasing a timeout or adding `--timeout` flags — the recursion itself must be eliminated (by removing the test or deselecting it from its own subprocess invocation). Verify the fix by running the file standalone under a strict wall-clock timeout before considering this done.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/agent/test_tool_approval_preflight.py
