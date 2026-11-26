# Implementation Procedure: tests/agent/test_startup_mcp_lifecycle.py

## Goal
- Give the mocked `/health` responses in `tests/agent/test_startup_mcp_lifecycle.py` a body that proves readiness, so the report-based readiness rule (REQ-005) does not turn a mocked 200 into a post-startup failure.

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `_make_http_mock` helper and the two `TestStartupVerifyMcpHealth` cases that stub a passing health check.
- Out of scope: the implementation changes (seq 05); every other test in this file.

### Companion test files
- N/A: this document is the procedure for the test file itself.

## Assumptions
- Verified in Step 3a: `test_health_check_passes_for_all_servers` and `test_health_check_passes_after_retry` fail. `_make_http_mock()` sets only `status_code`, so `resp.json()` returns a MagicMock, `parse_health_body` rejects it as not an object, and `_readiness_failure()` reports "no parseable /health body".
- Corrected in Step 3b: this file is not a row of the Plan's frozen `Implementation Target Files` table and is not named as a companion test file by seq 05. It is a fallout amendment discovered during seq 05 execution, found by running `uv run pytest tests/agent`. The Plan is archived (`plans/done/`), so `tools/amend_plan.py` refuses a new row; it is treated as a fallout amendment recorded in the Final Report, the same way seq 39 and seq 40 were (user decision, 2026-11-26).
- The assertion intent of each test does not change: each still asserts the post-startup check passes, or passes after one retry. Only the fixtures gain a readiness proof.

## Design decisions
- Use the legacy `ready` proof (`{"ready": true}` / `{"ready": false}`): the test server key `web` has no `config/tool_catalog.toml` entry, so the legacy fallback is the shape the readiness rule reads for it (D-6).
- `_make_http_mock` gains a `body` parameter defaulting to the unproven body: six call sites use the
  helper and four of them assert a failing health check, so the default stays unproven and the two
  passing cases state the proving body explicitly. This matches the convention seq 40 applied to
  `tests/agent/test_lifecycle.py`.

## Alternatives considered
- Keep the status code as proof (rejected by REQ-005/AC-05: readiness is the parsed report, not the status code).
- Leave the failing cases with no body (rejected: "no parseable body" is an accident of the mock, not the behavior the test is asserting).

## Implementation
### Target file
`tests/agent/test_startup_mcp_lifecycle.py`

### Procedure
1. In `_make_http_mock`, set `resp.json.return_value = body` with `body` defaulting to
   `{"ready": False}`, so the four failure-path call sites keep raising under the report-based rule.
2. `test_health_check_passes_for_all_servers` passes `body={"ready": True}`.
3. `test_health_check_passes_after_retry` keeps the first response unproven (default) and gives the
   second `body={"ready": True}`; the retry-then-success shape is unchanged.
4. Leave every status code and every assertion unchanged.

### Method
- One helper parameter plus three call sites; no new test cases.

### Details
- `resp` is a `MagicMock`, so `json` must return a dict, not an `AsyncMock`.

## Compatibility considerations
- Only this file's fixtures change; no production code is touched by this procedure.

## Security considerations
- N/A: no secret value in the fixtures.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/agent/test_startup_mcp_lifecycle.py`; `uv run ruff format` and `uv run ruff check` on this file; then the sequence in `rules/toolchain.md`.

## Completion criteria
- The two tests pass; no existing case is weakened; the rest of the file is unchanged.

## Out of Scope
- The implementation changes (seq 05).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the fixture changes | Completed | 20261126-174315 | 20261126-174315 | _make_http_mock gained a body parameter defaulting to the unproven body (four of its six call sites assert a failing check); the two passing cases pass {"ready": True} explicitly. Status codes and assertions unchanged. |
| 2 | Confirm the two tests pass and no existing case is weakened | Completed | 20261126-174315 | 20261126-174315 | tests/agent/test_startup_mcp_lifecycle.py: 21 tests passed, including test_health_check_passes_for_all_servers and test_health_check_passes_after_retry. No existing case weakened. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261126-174315 | 20261126-174315 | ruff format/check pass; lint-imports 6 contracts kept; check_mock_patch_targets, check_module_size, check_docstrings pass. Full suite pending at end of batch. |

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
- **Related target files**: `tests/agent/test_startup_mcp_lifecycle.py`