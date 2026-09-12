# `_http_subprocess_cfg()` test helper builds `McpServerConfig` without required `auth_token`

## Priority
Medium

## Summary
19 tests across `TestStartupOrchestratorStartServers` (9), `TestStartupVerifyMcpHealth`
(8), `TestStartupRollback::test_rollback_on_partial_multi_server_failure` (1), and
`TestStartupMemoryFailures::test_excluded_tools_log_includes_failure_policy` (1) in
`tests/agent/test_startup.py` fail with `ValueError: McpServerConfig: auth_token must
not be empty`. Confirmed stale test: a shared test helper builds `McpServerConfig`
without an `auth_token`, which validation now rejects — the validation itself is a
correct, intentional security requirement.

## Background
Commit `1bc91e7bf` ("feat: enforce loopback-only MCP/EventBus binding and mandatory MCP
authentication") changed `McpServerConfig`'s validation
(`scripts/shared/mcp_config.py::_validate_auth_token`) to reject an empty `auth_token`
unconditionally — previously an empty string default was accepted. This was a
deliberate security hardening change (mandatory MCP authentication), not a defect.
`tests/agent/test_startup.py`'s shared `_http_subprocess_cfg()` helper, used to
construct `McpServerConfig` instances across many test classes in this file, was never
updated to supply an `auth_token`, so every test that goes through it now fails at
config-construction time before the test's actual logic runs.

## Problem
All 19 failing tests share the identical traceback rooted in
`_http_subprocess_cfg()`'s `McpServerConfig(...)` construction call raising
`ValueError: McpServerConfig: auth_token must not be empty`. Confirmed this is not a
production defect: `_validate_auth_token`'s rejection is correct per
`1bc91e7bf`'s stated intent (mandatory MCP authentication), and no other test file
constructing `McpServerConfig` with a valid `auth_token` fails this way.

## Reason for Change
19 tests across 3 test classes currently fail purely because a shared test fixture
predates a security-hardening change to a validated field — none of them exercise a
real defect, and their failure obscures whatever genuine coverage they're meant to
provide for `StartupOrchestrator.start_servers()`/MCP health verification/rollback
behavior.

## Implementation Intent
Add a non-empty `auth_token` value to `_http_subprocess_cfg()`'s `McpServerConfig(...)`
construction call (a test-only placeholder value, e.g. a fixed test token string — not a
real secret) so every test using this helper constructs a valid config and proceeds to
exercise its actual intended logic.

## Target Files or Areas
- `tests/agent/test_startup.py` (`_http_subprocess_cfg()` helper)
- `scripts/shared/mcp_config.py` (reference only — confirms `_validate_auth_token`'s
  current, intentional rejection behavior; not a modification target)

## Required Changes
- Add a non-empty `auth_token` argument to `_http_subprocess_cfg()`'s
  `McpServerConfig(...)` call.
- No change to `scripts/shared/mcp_config.py` or its validation.

## Constraints
Do not weaken or bypass `_validate_auth_token`'s rejection of an empty `auth_token` —
this is confirmed intentional security hardening from `1bc91e7bf`, not a defect to
work around.

## Acceptance Criteria
- [ ] `_http_subprocess_cfg()` constructs `McpServerConfig` with a non-empty `auth_token`
- [ ] All 19 listed failing tests no longer fail at config-construction time (each
  test's own actual assertions then determine pass/fail independently — this issue's
  scope is unblocking construction, not guaranteeing every downstream assertion already
  passes)
- [ ] No change to `scripts/shared/mcp_config.py`

## Testing Expectations
- `uv run pytest tests/agent/test_startup.py::TestStartupOrchestratorStartServers
  tests/agent/test_startup.py::TestStartupVerifyMcpHealth
  "tests/agent/test_startup.py::TestStartupRollback::test_rollback_on_partial_multi_server_failure"
  "tests/agent/test_startup.py::TestStartupMemoryFailures::test_excluded_tools_log_includes_failure_policy"
  -q` — the `auth_token` `ValueError` must no longer occur for any of these; report any
  test that fails for a *different* reason after this fix as a new, separate finding,
  not silently absorbed into this issue

## Documentation Impact
N/A: test-only fixture fix; no documented behavior change.

## Out of Scope
- Any change to `scripts/shared/mcp_config.py` or MCP authentication requirements.
- `TestStartupRollback`'s other 9 failures (`log_file must be a non-empty str`) — a
  distinct cause, tracked separately as `startup04`.
- `TestStartupWorkflowPreflight`'s 6 failures — a distinct cause, tracked separately as
  `startup05`.
- `TestStartupMemoryFailures::test_memory_injection_categorized_logging`'s 3 failures —
  a distinct cause, tracked separately as `startup06`.

## Dependencies
N/A: none. Related to (but does not duplicate) `startup02`
(`issues/20260909-105724_startup02_recover-pending-approvals-test-targets-removed-module-attribute.md`),
which covers a different 9 failures in the same file.

## Unresolved Questions
N/A: none — root cause confirmed by direct traceback inspection and `git log` on
`scripts/shared/mcp_config.py`'s validation change.

## AI Implementation Instruction
Add the `auth_token` argument only to `_http_subprocess_cfg()`; do not modify
`scripts/shared/mcp_config.py`. After the fix, some of the 19 tests may still fail for
reasons unrelated to `auth_token` (their own actual assertions) — report any such
residual failure as a new finding rather than silently expanding this issue's scope to
fix it.

## Traceability
- **Workflow phase**: N/A: manually filed
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260909-130214
- **Related target files**: see Target Files or Areas above
