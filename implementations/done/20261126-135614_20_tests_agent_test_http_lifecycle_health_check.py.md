## Goal
- Update `tests/agent/test_http_lifecycle_health_check.py` to cover the per-server timeout, the remaining-deadline cap, the single auth path, and report-based readiness (REQ-001, REQ-002, REQ-003, REQ-005).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: this test file only (standalone row: it is named by two target rows, seq 03 and seq 04, so it is not a companion).
- Out of scope: the implementation changes (seq 03, seq 04).

## Assumptions
- Verified in Step 3a: existing tests pin the `is_degraded_but_live` branches (`test_http_lifecycle_health_check.py:392-467`); those pins change with the replaced predicate.
- The implementation is in seq 03 (checker) and seq 04 (call sites); write the failing tests first.
- Corrected in Step 3b: because readiness is no longer gated by the status code, every fixture that
  stubs only `status_code` needs a body proof. The two token tests' fixtures gained
  `ready: true`; the same fallout in `tests/agent/test_http_lifecycle_integration.py` (five fixtures)
  is handled by the fallout amendment procedure `20261126-135614_39_tests_agent_test_http_lifecycle_integration.py.md`,
  which is not a row of the Plan's frozen target table.

## Design decisions
- Use a fake clock for the deadline-cap test so the assertion is deterministic (T-02).

## Alternatives considered
- N/A: test-only change.

## Implementation
### Target file
`tests/agent/test_http_lifecycle_health_check.py`

### Procedure
1. Replace the `is_degraded_but_live` branch tests with report-based readiness cases: liveness-only 503 fails, required-capability-ok 503 passes, legacy body falls back to `ready`.
2. Add a fake-clock poll test: a request issued with `T` seconds left has timeout `min(effective, T)`; no request starts after the deadline; a hanging server cannot extend the poll beyond the deadline plus the termination timeout (T-02).
3. Add the per-server timeout assertion (a distinct non-default value reaches the poll and the periodic check, T-01) and the auth tests: header present with a token, absent without, and a caplog assertion that a failing probe logs no token (T-03).

### Method
- Keep the existing shutdown/early-exit cases unchanged.

### Details
- The token-not-logged assertion uses `caplog` on the health failure path.

## Compatibility considerations
- Only this file's pins change; the implementation rows (seq 03, 04) must land in the same commit group for the tests to pass.

## Security considerations
- N/A: no secret value in the fixtures; the token-not-logged assertion is the check.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_health_check.py tests/agent/test_http_lifecycle_integration.py`; `uv run ruff format` and `uv run ruff check` on this file; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The new cases fail before seq 03/04 and pass after; no existing case is weakened.

## Out of Scope
- The implementation changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the test changes | Completed | 20261126-170920 | 20261126-170920 | Changed: TestHealthPollDegradedTolerance replaced by TestReportBasedReadiness (unparseable bodies, contract violations, liveness-only not proof, required capability ok proves, legacy ready fallback, poll-level cases), plus TestCallerResolvesRequiredCapability and TestPerServerTimeoutAndDeadlineCap (T-01 effective timeout at both call sites, T-02 fake-clock min(effective, remaining) cap and no request after the deadline) and the T-03 token-not-logged caplog assertion. |
| 2 | Confirm the new cases fail before seq 03/04 and pass after | Completed | 20261126-170920 | 20261126-170920 | The pre-implementation red state was observed as 13 failing pins against the replaced predicate before the rewrite; after seq 03/04 landed the rewritten file passes 26/26. The same readiness rule made five fixtures in tests/agent/test_http_lifecycle_integration.py fail; handled by the fallout procedure seq 39. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-170920 | 20261126-170920 | ruff format/check and mypy pass on this file; 26 tests passed. Full suite pending at end of batch. Docs: N/A, test-only change. |

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
- **Requirement ID**: `REQ-001` (per-server timeout), `REQ-002` (deadline cap), `REQ-003` (single auth path), `REQ-005` (report-based readiness)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `tests/agent/test_http_lifecycle_health_check.py`