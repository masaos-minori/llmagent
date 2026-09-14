# Add end-to-end verification that reload updates only policy fields, not discovery

## Priority
Medium

## Summary
`ADR-003`/`ADR-013` state that a runtime tool registry reload updates only policy-derived fields (tier, allowed-tools) and never re-runs tool discovery, but this invariant is currently verified only by unit tests that call `RuntimeToolRegistry.apply_policy()` directly (or via a mocked registry) — no test exercises the actual reload trigger path end-to-end to confirm discovery is genuinely skipped in the real flow, not just in the isolated function under test.

## Background
`docs/00_governance_03_issue-and-uncertainty-management.md` `CI-003` ("ADR-003 Decision Details #14 — reload-updates-only-policy-fields claim not verified", Status: open, Severity: Medium) already tracks this exact gap: "The implementation appears correct based on code inspection of `apply_policy()`, but this has NOT been validated against the actual reload flow." This issue is the implementation-tracking counterpart to that Known Issue entry, re-confirmed against current tests.

## Problem
Re-verified by direct inspection of `tests/agent/services/test_config_reload.py`: `TestApplyPolicy`'s tests (e.g. `test_apply_policy_called_with_current_tier_map_and_allowed_tools`) construct `ConfigReloadService` with a `MagicMock()` context and call `svc._sync_services(...)` directly, asserting the mock's `apply_policy` was called with expected arguments. `test_reload_does_not_fetch_tools_over_http`'s own comment states it "Uses direct `_sync_services` call to avoid MCP discovery complexity" — meaning it deliberately does not exercise the actual reload trigger (e.g. a `/reload` command or config-file-change path) against a real `RuntimeToolRegistry` and real (or realistically faked) MCP server state. `tests/shared/test_runtime_tool_registry.py`'s `apply_policy()` tests similarly test the registry method in isolation, not the end-to-end reload flow that invokes it.

## Reason for Change
Per `CI-003`'s own stated Impact: if reload also rediscovered tools, it would violate the stated invariant that policy changes don't alter tool availability — this is a safety-relevant invariant (tool availability should not silently drift on a config reload), and it currently has no test that would catch a regression introduced anywhere between the actual reload trigger and `apply_policy()`'s invocation.

## Implementation Intent
Add one end-to-end test that triggers the actual reload path (the same trigger a real `/reload` invocation uses) against a real `RuntimeToolRegistry` instance (not a mock) with a populated tool set, and confirms: (1) `apply_policy()`'s effect is observable on the real registry (tier/allowed-tools changed as expected), and (2) no tool-discovery call (e.g. an MCP `/v1/tools` request) occurs as part of that reload — the existing `test_reload_does_not_fetch_tools_over_http`'s intent, but exercised through the real trigger path rather than a direct `_sync_services` call.

## Target Files or Areas
- `tests/agent/services/test_config_reload.py`
- `tests/shared/test_runtime_tool_registry.py`
- `scripts/agent/services/config_reload.py`
- `scripts/shared/runtime_tool_registry.py`
- `docs/00_governance_03_issue-and-uncertainty-management.md`

## Required Changes
- Identify the actual reload trigger path used by a real `/reload` invocation (the entry point `ConfigReloadService._sync_services` is called from).
- Add an end-to-end test that exercises that entry point with a real `RuntimeToolRegistry` (not a mock), confirming `apply_policy()`'s effect on tool tier/visibility is observable afterward.
- In the same test (or a companion test), confirm no MCP discovery/HTTP call occurs during that reload — extending `test_reload_does_not_fetch_tools_over_http`'s existing intent to the real trigger path.
- Update `CI-003` in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect that this invariant is now verified end-to-end, once the test is added and passing.

## Constraints
This issue adds test coverage; it must not change `apply_policy()`'s or the reload trigger's actual behavior unless the new E2E test reveals a genuine discrepancy from the documented invariant (in which case, report the discrepancy rather than silently fixing it, since a behavior change would need its own review).

## Acceptance Criteria
- An end-to-end test exists that triggers reload through the same path a real `/reload` invocation uses, against a real (non-mocked) `RuntimeToolRegistry`.
- That test confirms `apply_policy()`'s effect (tier/allowed-tools changes) is observable on the real registry after reload.
- That test (or a companion one) confirms no tool-discovery call occurs during reload.
- `CI-003` is removed from the active Known Issues inventory once this test is added and passing.

## Testing Expectations
This issue's entire deliverable is new test coverage (see Required Changes) — no production code change is expected unless the new E2E test surfaces a genuine behavior discrepancy, in which case stop and report rather than silently patching it.

## Documentation Impact
Update `CI-003`'s entry in `docs/00_governance_03_issue-and-uncertainty-management.md` once the E2E test is added and passing — do not update ahead of the test.

## Out of Scope
- Changing `apply_policy()`'s or the reload trigger's actual behavior, unless the new E2E test reveals a genuine discrepancy (report it, don't silently fix it as part of this issue).
- Unrelated additional reload test coverage beyond the specific policy-fields-only invariant this issue targets.

## Dependencies
Related to `mcpagent04` (runtime policy reload reversibility), which changes reload's recomputation behavior — if both are implemented in the same session, sequence `mcpagent04` first and write this issue's E2E test against its corrected behavior, not the pre-`mcpagent04` behavior.

## Unresolved Questions
The exact entry point a real `/reload` invocation uses to reach `ConfigReloadService._sync_services` needs to be traced during implementation (see Required Changes' first item) — not assumed from this issue's own investigation, which only confirmed the existing tests bypass it.

## AI Implementation Instruction
Trace the actual reload trigger path first (see Unresolved Questions) before writing the new test — do not assume it matches the existing mocked tests' call pattern. If `mcpagent04` has already changed reload's recomputation behavior, write this test against that corrected behavior. If the new E2E test finds a genuine discrepancy from the documented invariant, stop and report it rather than silently changing production code to match the test.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260914-105949
- **Related target files**: tests/agent/services/test_config_reload.py, tests/shared/test_runtime_tool_registry.py, scripts/agent/services/config_reload.py, scripts/shared/runtime_tool_registry.py, docs/00_governance_03_issue-and-uncertainty-management.md
