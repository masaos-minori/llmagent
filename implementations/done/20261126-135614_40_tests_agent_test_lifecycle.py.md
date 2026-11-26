# Implementation Procedure: tests/agent/test_lifecycle.py

## Goal
- Give the mocked `/health` responses in `tests/agent/test_lifecycle.py` a body that proves readiness, so the report-based readiness rule (REQ-005) does not turn a mocked 200 into a poll timeout.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `TestStartHttpSubprocess` fixtures that stub a `/health` response with a status code and no body, plus the `_wire_http_client` helper they share.
- Out of scope: the implementation changes (seq 03, seq 04); every other test in this file.

### Companion test files
- N/A: this document is the procedure for the test file itself.

## Assumptions
- Verified in Step 3a: four tests fail — `test_starts_process_and_polls_health`, `test_health_poll_retries_before_success`, `test_timeout_boundary_fires_after_controlled_time`, `test_merges_env_vars`. Each stubs a response with only `status_code` set. `MagicMock().json()` returns a MagicMock, which `parse_health_body` rejects as not an object, so `parse_report` returns None and the poll runs to the deadline instead of ending ready.
- Corrected in Step 3b: this file is not a row of the Plan's frozen `Implementation Target Files` table and is not named as a companion test file by seq 03 or seq 20. It is a fallout amendment discovered during seq 03 execution, found by running `uv run pytest tests/agent`. The Plan is archived (`plans/done/`), so `tools/amend_plan.py` refuses a new row; it is treated as a fallout amendment recorded in the Final Report, the same way seq 39 was (user decision, 2026-11-26).
- The assertion intent of each test does not change: each still asserts the poll ends ready, retries then succeeds, runs to the deadline, or starts the process. Only the fixtures gain a readiness proof.

## Design decisions
- Use the legacy `ready` proof (`{"ready": true}` / `{"ready": false}`) rather than a capability block: the test server keys (`s`, `srv`) have no `config/tool_catalog.toml` entry, so the legacy fallback is the shape the readiness rule reads for them (D-6).
- `_wire_http_client` gains a `body` parameter defaulting to the unproven body, because most call
  sites assert a failure path; the success-path tests pass the proving body explicitly.

## Alternatives considered
- Patch `HttpLifecycle._resolve_required_capability` per test (rejected: these fixtures assert nothing about capability resolution, and the legacy fallback is the simpler, intent-preserving proof).
- Keep the status code as proof (rejected by REQ-005/AC-05: readiness is the parsed report, not the status code).

## Implementation
### Target file
`tests/agent/test_lifecycle.py`

### Procedure
1. In `_wire_http_client`, set `mock_resp.json = Mock(return_value=body)` with `body` defaulting to
   `{"ready": False}`: the helper is used by failure-path tests too, so the default must stay unproven.
2. The success-path tests that assert the poll ends ready pass `body={"ready": True}`:
   `test_starts_process_and_polls_health` and `test_merges_env_vars`.
3. `test_health_poll_retries_before_success` gives `fail_resp` `{"ready": False}` and `ok_resp`
   `{"ready": True}`; the retry-then-success shape is unchanged.
4. Corrected in Step 3b: `test_timeout_boundary_fires_after_controlled_time` does not need a body — its
   mocked response is already unproven — but REQ-002 adds one `time.monotonic()` call per request (the
   remaining-to-deadline cap), so `monotonic_values` gains one entry and `StopIteration` stops leaking
   through the patched `time.monotonic`. The values are set so one request is still issued while time
   remains, then the deadline is crossed before the next poll. The asserted boundary is unchanged.
5. Leave every status code and every assertion unchanged.

### Method
- One fixture line per test plus one helper parameter; no new test cases.

### Details
- `mock_resp` is a `MagicMock`, so `json` must be a plain `Mock` returning a dict, not an `AsyncMock`.

## Compatibility considerations
- Only this file's fixtures change, plus one guard in `scripts/agent/http_lifecycle_health_checker.py`:
  `remaining_sec <= 0` breaks the poll before the request, so no request starts once the deadline has
  passed (D-4, seq 03 Procedure step 1). Without the guard the capped timeout can be negative when the
  controlled clock crosses the deadline between the loop check and the cap, which is what made
  `test_timeout_boundary_fires_after_controlled_time` fail with `StopIteration`. Recorded here as a
  Step 3b deviation because the production file is already archived under seq 03.

## Security considerations
- N/A: no secret value in the fixtures.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_lifecycle.py`; `uv run ruff format` and `uv run ruff check` on this file; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The four tests pass; no existing case is weakened; the rest of the file is unchanged.

## Out of Scope
- The implementation changes (seq 03, seq 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the fixture changes | Completed | 20261126-174149 | 20261126-174149 | _wire_http_client gained a body parameter defaulting to the unproven body; the two success-path tests pass {"ready": True} and the retry test's ok_resp proves. Added the `remaining_sec <= 0` break in scripts/agent/http_lifecycle_health_checker.py so no request starts past the deadline (D-4); the boundary test's monotonic_values gained one entry. |
| 2 | Confirm the four tests pass and no existing case is weakened | Completed | 20261126-174149 | 20261126-174149 | tests/agent/test_lifecycle.py: 90 tests passed, including the four that were failing. Status codes and assertions unchanged. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-174149 | 20261126-174149 | ruff format/check pass; mypy on the production file clean (test files are outside the mypy scope); lint-imports 6 contracts kept; bandit pass; check_mock_patch_targets, check_module_size (13240 B), check_docstrings pass. Full suite pending at end of batch. |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

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
- **Related target files**: `tests/agent/test_lifecycle.py`