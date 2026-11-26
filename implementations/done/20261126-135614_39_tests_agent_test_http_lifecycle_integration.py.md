# Implementation Procedure: tests/agent/test_http_lifecycle_integration.py

## Goal
- Give the mocked `/health` responses in `tests/agent/test_http_lifecycle_integration.py` a body that proves readiness, so the report-based readiness rule (REQ-005) does not turn a mocked 200 into a poll timeout.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the five health-poll fixtures in this test file that stub a response with a status code and no body.
- Out of scope: the implementation changes (seq 03, seq 04); every other test in this file.

### Companion test files
- N/A: this document is the procedure for the test file itself.

## Assumptions
- Verified in Step 3a: the five failing tests (`test_failed_start_doesnt_block_subsequent_attempts`, `test_restart_handles_missing_process`, `test_restart_handles_already_stopped_process`, `test_health_check_succeeds_returns_cleanly`, `test_shutdown_event_never_set_is_noop`) build `mock_resp = MagicMock()` with only `status_code` set. `MagicMock().json()` returns a MagicMock, which `parse_health_body` rejects as not an object, so `parse_report` returns None and the poll runs to the deadline instead of ending ready.
- Corrected in Step 3b: this file is not a row of the Plan's frozen `Implementation Target Files` table and is not named as a companion test file by seq 03 or seq 20. It is a fallout amendment discovered during seq 03/20 execution. The Plan is archived (`plans/done/`), so `tools/amend_plan.py` refuses a new row; the user approved treating it as a fallout amendment recorded in the Final Report rather than as a Plan row (2026-11-26).
- The assertion intent of each test does not change: each still asserts that the poll ends ready (or that the shutdown path is unaffected). Only the fixture gains a readiness proof.

## Design decisions
- Use the legacy `ready` proof (`{"ready": true}`) rather than a capability block: these fixtures have no catalog `required_capability`, so the legacy fallback is the shape the readiness rule reads for them (D-6).

## Alternatives considered
- Patch `mgr._resolve_required_capability` in each test (rejected: the fixtures assert nothing about capability resolution, and the legacy fallback is the simpler, intent-preserving proof).
- Keep the status code as proof (rejected by REQ-005/AC-05: readiness is the parsed report, not the status code).

## Implementation
### Target file
`tests/agent/test_http_lifecycle_integration.py`

### Procedure
1. In each of the five fixtures, set `mock_resp.json = Mock(return_value={"ready": True})` alongside the existing `status_code`.
2. Leave the status codes and every assertion unchanged.
3. Replace the four bare `patch.object(httpx, "AsyncClient")` sites that reach `parse_report`
   (`test_startup_failure_contains_reason_on_timeout`, `test_health_check_poll_continues_on_error`,
   `test_confirmed_termination_on_shutdown_clears_tracking`,
   `test_unconfirmed_termination_on_shutdown_keeps_tracking`) with
   `patch.object(httpx, "AsyncClient", new=_unproven_client())`, a helper that returns a real
   `httpx.Response`. A `MagicMock` response makes `resp.json()` a coroutine that is never
   awaited, so each poll iteration emitted a `RuntimeWarning` once readiness became report-based.
   The body is `{"ready": false}`, which keeps the intended outcome: the poll runs to the deadline.

### Method
- One fixture line per test; no new test cases. The five tests are the ones that currently fail because the readiness rule no longer accepts a status code alone.

### Details
- `mock_resp` is a `MagicMock`, so `json` must be a plain `Mock` returning a dict, not an `AsyncMock`.

## Compatibility considerations
- Only this file's fixtures change; no production code is touched by this procedure.

## Security considerations
- N/A: no secret value in the fixtures.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_http_lifecycle_integration.py`; `uv run ruff format` and `uv run ruff check` on this file; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The five tests pass; no existing case is weakened; the rest of the file is unchanged.

## Out of Scope
- The implementation changes (seq 03, seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the fixture changes | Completed | 20261126-170920 | 20261126-170920 | Changed: five fixtures gained mock_resp.json = Mock(return_value={"ready": True}); the four bare patch.object(httpx, "AsyncClient") sites that reach parse_report now use _unproven_client(), a real httpx.Response, because a MagicMock response makes resp.json() an un-awaited coroutine and emitted a RuntimeWarning once readiness became report-based. |
| 2 | Confirm the five tests pass and no existing case is weakened | Completed | 20261126-170920 | 20261126-170920 | 66 tests passed, no warnings; no assertion changed. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-170920 | 20261126-170920 | ruff format/check pass on this file. Full suite pending at end of batch. Docs: N/A, test-only change. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 3 | File outside procedure scope — `tests/agent/test_http_lifecycle_integration.py`; not a Plan target row and the archived Plan cannot be amended | Yes: user approved the fallout amendment and this procedure document | 2026-11-26 |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: code-implementation (fallout amendment)
- **Requirement ID**: `REQ-005` (report-based readiness)
- **Source issue**: issues/20261119-145306_cliplc008_mcp-health-capability.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261126-111451_cliplc008_mcp-health-capability.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-135614
- **Related target files**: `tests/agent/test_http_lifecycle_integration.py`