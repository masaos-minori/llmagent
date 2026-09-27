## Goal

Add an explicit non-`NONE` `startup_mode` to `test_disabled_discovered_tool_excluded_from_llm_payload`'s `McpServerConfig(...)` call, so `McpToolDiscoveryService.discover_all()` actually probes the mocked HTTP server instead of skipping it as disabled (REQ-001).

## Scope

In scope: this one test's `McpServerConfig(...)` call. Out of scope: `scripts/agent/services/mcp_tool_discovery.py`'s `cfg.is_disabled` skip in `discover_all()` (confirmed already correct and intentional, same pattern as `shared001`/`shared002`).

## Assumptions

- Same as `shared001`/`shared002`'s confirmed evidence: `StartupMode.PERSISTENT` is appropriate here too, since the test already supplies a `url` and mocks HTTP responses directly rather than spawning a real subprocess.

## Design decisions

- Add `startup_mode=StartupMode.PERSISTENT` as a kwarg to the test's `McpServerConfig(...)` call, matching the same fix pattern as `shared001`/`shared002`.

## Alternatives considered

- N/A: same reasoning as `shared001`/`shared002` — no alternative approach considered given the identical, confirmed root cause.

## Implementation

### Target file

`tests/agent/services/test_runtime_tool_routing_integration.py`

### Procedure

1. Re-confirm the test's exact current `McpServerConfig(...)` call via Read (inside `test_disabled_discovered_tool_excluded_from_llm_payload`) — confirm `startup_mode` is still not passed (adversarial re-verification).
2. Add `startup_mode=StartupMode.PERSISTENT` as a kwarg to `McpServerConfig(TransportType.HTTP, "http://127.0.0.1:9100", auth_token="test-token")`.
3. Confirm `StartupMode` is already imported in this file — add the import if missing.

### Method

Direct kwarg addition to 1 constructor call — no structural change.

### Details

- Before: `McpServerConfig(TransportType.HTTP, "http://127.0.0.1:9100", auth_token="test-token")`.
- After: `McpServerConfig(TransportType.HTTP, "http://127.0.0.1:9100", auth_token="test-token", startup_mode=StartupMode.PERSISTENT)`.
- Confirmed via Read: `McpToolDiscoveryService.discover_all()` (`scripts/agent/services/mcp_tool_discovery.py:305`) skips any server config where `cfg.is_disabled` is `True` — this fix makes it `False` so the mocked `visible_tool`/`hidden_tool` HTTP response is actually processed.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added `startup_mode` kwarg.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/agent/services/test_runtime_tool_routing_integration.py` | Integration | `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q` | All tests pass, with `"visible_tool"` present and `"hidden_tool"` absent from the resulting LLM tool definitions |

## Completion criteria

- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py::TestDiscoveryToLlmVisibilityEndToEnd::test_disabled_discovered_tool_excluded_from_llm_payload -q` passes.
- `uv run pytest tests/agent/services/test_runtime_tool_routing_integration.py -q` (full file) passes with no regression in other discovery/routing tests.

## Out of scope

- `scripts/agent/services/mcp_tool_discovery.py` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing test's fixture call is itself the fix |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs/00_index.md task-scope mapping for this test file |

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
- **Requirement ID**: REQ-001: add explicit `startup_mode` to the test's fixture call
- **Source issue**: issues/20260927-075256_agent005_runtime_tool_routing_integration-visible-tool-set-empty.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-085007_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093206
- **Related target files**: tests/agent/services/test_runtime_tool_routing_integration.py
