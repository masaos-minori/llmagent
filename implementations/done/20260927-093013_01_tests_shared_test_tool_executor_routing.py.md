## Goal

Add an explicit non-`NONE` `startup_mode` to both `TestSetSessionId` tests' `McpServerConfig(...)` calls, so `ToolTransportInvoker.__init__` builds a real `HttpTransport` entry for key `"srv"` instead of skipping it as disabled (REQ-001).

## Scope

In scope: both `McpServerConfig(...)` calls inside `TestSetSessionId`. Out of scope: `ToolTransportInvoker.__init__`'s `if cfg.is_disabled: continue` skip (confirmed already correct and intentional, same pattern as `shared001`).

## Assumptions

- Same as `shared001`'s confirmed evidence: `StartupMode.PERSISTENT` is appropriate here too, since both tests already supply `url=...` and no `cmd`.

## Design decisions

- Add `startup_mode=StartupMode.PERSISTENT` as a kwarg to both `McpServerConfig(...)` calls directly (both tests construct their own config inline, unlike `shared001`'s shared `_http_cfg` helper) — no shared-helper refactor needed since each test already builds its own config independently.

## Alternatives considered

- N/A: same reasoning as `shared001` — no alternative approach considered given the identical, confirmed root cause.

## Implementation

### Target file

`tests/shared/test_tool_executor_routing.py`

### Procedure

1. Re-confirm both `McpServerConfig(...)` calls' exact current form via Read (inside `test_session_id_injected_into_http_transport_header` and `test_set_session_id_empty_string_does_not_inject_header`) — confirm `startup_mode` is still not passed (adversarial re-verification).
2. Add `startup_mode=StartupMode.PERSISTENT` as a kwarg to both `McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:8000", auth_token="test-token")` calls.
3. Confirm `StartupMode` is already imported in this file — add the import if missing.

### Method

Direct kwarg addition to 2 constructor calls — no structural change.

### Details

- Before (both tests, identical): `McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:8000", auth_token="test-token")`.
- After: `McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:8000", auth_token="test-token", startup_mode=StartupMode.PERSISTENT)`.
- Confirmed via `shared001`'s evidence: `ToolTransportInvoker.__init__` (`scripts/shared/tool_transport_invoker.py:40-62`) builds `self._transports[key] = HttpTransport(...)` only when `not cfg.is_disabled`.

## Compatibility considerations

- No production code changes; test-only fix.

## Security considerations

N/A: test-only fix, no security-relevant behavior change.

## Rollback considerations

- `git revert` the commit, or manually remove the added `startup_mode` kwargs.

## Validation plan

| Target | Strategy | Command | Expected |
|---|---|---|---|
| `tests/shared/test_tool_executor_routing.py` | Unit | `uv run pytest tests/shared/test_tool_executor_routing.py -q` | All tests pass, including `TestSetSessionId`'s 2 previously-failing tests |

## Completion criteria

- `uv run pytest tests/shared/test_tool_executor_routing.py::TestSetSessionId -q` passes (both tests).
- `uv run pytest tests/shared/test_tool_executor_routing.py -q` (full file) passes with no regression in `TestRawExecuteWithLifecycle`/`TestResolverIntegration`/other classes.

## Out of scope

- `scripts/shared/tool_transport_invoker.py` (confirmed already correct).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: fixing the existing 2 tests' fixture calls is itself the fix |
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
- **Requirement ID**: REQ-001: add explicit `startup_mode` to both tests' fixture calls
- **Source issue**: issues/20260927-075252_shared002_tool_executor_routing-keyerror-srv-in-set_session_id.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260927-084627_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-093013
- **Related target files**: tests/shared/test_tool_executor_routing.py
