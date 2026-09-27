## Goal

Remove `tests/agent/test_tool_approval_preflight.py::TestRunApprovalChecks::test_regression_existing_agent_tests_pass`, whose confirmed self-recursive `subprocess.run(["uv", "run", "pytest", "tests/agent/test_tool_approval_preflight.py", "-v"])` call re-invokes pytest on the same file it is itself collected from, causing unbounded/very-long-running execution (REQ-001).

## Scope

In scope: removing this one test from this file. Out of scope: any other test in the file (confirmed unaffected).

## Assumptions

- No CI workflow or other automation depends on this test's name as a required check (to be confirmed via Implementation step 1's search before removal).

## Design decisions

- Remove the test entirely rather than attempting to deselect it from its own subprocess's collection (e.g. via `-k 'not test_regression_existing_agent_tests_pass'`) — per the Plan's own Implementation intent, any subprocess-based self-check adds a redundant, fragile mechanism with no coverage benefit over the file's other tests running normally.

## Alternatives considered

- Fixing the subprocess call to deselect itself (`-k 'not test_regression_existing_agent_tests_pass'`) instead of removing the test: rejected per the Plan — this would still leave a fragile subprocess-based self-check with no coverage benefit over simply running the file's tests directly (which any invocation of this file, or the full suite, already does).

## Implementation

### Target file

`tests/agent/test_tool_approval_preflight.py`

### Procedure

1. Search for any external dependency on this test's name before removal: `rg -n "test_regression_existing_agent_tests_pass" --type py .` and check `.github/workflows/*.yml` for any reference to it by name (per the Plan's own stated assumption to confirm, not assume).
2. If no external dependency is found, delete `test_regression_existing_agent_tests_pass` (lines 791-806) from `tests/agent/test_tool_approval_preflight.py` in its entirety, including its docstring.
3. Confirm no other test in the class/file references this method (e.g. via a helper call or fixture dependency) before finalizing the removal.

### Method

Direct deletion of one test method (16 lines) — no other change to the file.

### Details

- Removed block: the entire `def test_regression_existing_agent_tests_pass(self) -> None:` method (lines 791-806), including its `subprocess.run(...)` call and its `assert result.returncode == 0` check.
- Confirm via `rg -n "class TestRunApprovalChecks"` that this test's removal does not leave the class empty or otherwise structurally broken (per this session's earlier investigation, this class contains other, unrelated tests that remain after this removal).

## Compatibility considerations

- No production code changes; test-suite cleanup only. Regression coverage for "existing Agent tests still pass" is already provided by the file's own other tests running normally in any full-suite or per-file invocation — no coverage gap results from this removal.

## Security considerations

N/A: test-only removal, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually restore the removed test method. Given this test never completed in two independent reproduction attempts (90s, 400s timeouts) prior to this fix, restoring it would reintroduce the confirmed resource-exhaustion risk.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/test_tool_approval_preflight.py` | Unit (strict-timeout completion check) | `timeout 60 uv run pytest tests/agent/test_tool_approval_preflight.py -q` | Completes within 60s; all remaining tests pass; no nested `uv run pytest` subprocess spawned |

## Completion criteria

- `timeout 60 uv run pytest tests/agent/test_tool_approval_preflight.py -q` completes well within that bound (confirmed via the command's own exit, not a timeout kill).
- No nested `uv run pytest` subprocess is spawned during the run (confirmed via `ps` inspection during the run, or by the run's own completion time being consistent with the file's other tests' normal per-test duration).

## Out of scope

- Any other test file tracked under a separate Plan/issue.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm no external dependency on the test's name (REQ-001) | Pending | — | — | |
| 2 | Remove the test | Pending | — | — | |
| 3 | Verify strict-timeout completion | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: internal test-suite cleanup, no documented contract changes |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001: remove the self-recursive subprocess test
- **Source issue**: issues/20260927-075301_test001_self-recursive-subprocess-test-causes-resource-exhaustion.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085830_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093537
- **Related target files**: tests/agent/test_tool_approval_preflight.py
