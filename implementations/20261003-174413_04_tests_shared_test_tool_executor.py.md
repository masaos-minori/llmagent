# Implementation Procedure — `tests/shared/test_tool_executor.py`

## Goal

Add a characterization test asserting `ToolTransportInvoker.invoke()` and `ToolExecutor._raw_execute()` yield identical results for a representative healthy call and a representative failed call (`REQ-005`). After both paths delegate to the shared `_run_precall_gates` (rows 1–2), this pins that they cannot diverge; it also documents that the previously-divergent disabled-server path now converges.

## Scope

- **In-Scope**: Append a new `TestInvokeRawExecuteEquivalence` class to `tests/shared/test_tool_executor.py` comparing `invoke()` vs `_raw_execute()` output/`is_error`/`server_key`/`error_type` for a healthy and a failed call. Existing tests left unchanged.
- **Out-of-Scope**: Production code (rows 1–2); the `invoke()`-only characterization pin belongs to `tests/shared/test_tool_transport_invoker.py` (row 3).

## Assumptions

- `_make_executor(configs=...)` builds a `ToolExecutor`; passing `configs=` overrides the server map (used at L548). A bare `_make_executor()` uses a default config.
- `_raw_execute(tool_name, args)` resolves `server_key` via `self._resolver.resolve(tool_name)`; mocking `ex._resolver.resolve` to return `"test_server"` makes it converge on the same key `invoke("test_server", ...)` uses directly (this mirrors `_make_executor_with_mock_lifecycle()` at L524).
- `ToolCallResult` exposes `output`, `is_error`, `server_key`, `error_type` (imported at L25); `TransportError` is imported at L13; `McpServerHealthRegistry`, `StartupMode`, `McpServerConfig`, `TransportType` at L16–20.
- Driving both calls on the SAME instance mutates counters/health state, so the comparison uses two identically-configured instances to keep each call independent.

## Design decisions

- **Two identical fixtures per case.** Build one executor for `invoke()` and one for `_raw_execute()` with the same transport outcome, resolver mapping, and (optional) health registry, then compare field-by-field. This avoids cross-call `stat_*`/health-state mutation skewing the comparison.
- **Healthy case:** mock transport `call` returns a fixed `ToolCallResult(output="ok", is_error=False, request_id="", server_key="test_server", source="mcp")`; assert both results match on all four fields.
- **Failed case:** mock transport `call` raises `TransportError("network down")`; assert both results have `is_error is True`, `error_type == "transport"`, equal `server_key`, and equal `output` (the normalized `str(e)`).
- **Resolve to the same key.** Set `ex._resolver.resolve = MagicMock(return_value="test_server")` on the `_raw_execute` side; call `invoke("test_server", "some_tool", {})` on the other. Same key + same shared helper ⇒ identical result by construction — the assertion locks that construction.
- **Do not assert on `stat_*` counters** in the equivalence comparison (they are intentionally separate instances); the existing `test_malformed_response_is_transport_error` (L477) / `test_timeout_is_transport_error` (L446) already lock per-path counter behavior.

## Alternatives considered

- **Compare on one shared instance.** Rejected — the first call mutates `stat_transport_errors`/health state, so the second call's gate outcomes could differ; separate instances give a clean apples-to-apples comparison.
- **Include a disabled-server case.** Rejected for THIS equivalence pin — a disabled server is the exact case that DIVERGED pre-refactor (invoke → "disabled" message; `_raw_execute` → "No transport configured"). Asserting equality there would fail before the refactor and pass after, making it a migration check rather than a post-refactor characterization. Keep the healthy + transport-error pair as the stable equivalence lock.

## Implementation

### Target file

`tests/shared/test_tool_executor.py`

### Procedure

Append `class TestInvokeRawExecuteEquivalence:` after `TestDisabledServerInvocation` (file ends near L575):

1. Add a private helper `_equivalent_executor(self, call_side_effect=None, return_value=None)`:
   - `ex = _make_executor(configs={"test_server": McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:9", startup_mode=StartupMode.PERSISTENT, auth_token="test-token")}`.
   - `ex.set_health_registry(McpServerHealthRegistry())` (fresh ⇒ HEALTHY, not unavailable).
   - `mock_transport = AsyncMock(); ex._transports["test_server"] = mock_transport`.
   - If `return_value is not None`: `mock_transport.call = AsyncMock(return_value=return_value)`. Elif `call_side_effect is not None`: `mock_transport.call = AsyncMock(side_effect=call_side_effect)`.
   - `ex._resolver.resolve = MagicMock(return_value="test_server")`.
   - `return ex`.
2. `test_healthy_calls_equivalent`:
   - `expected = ToolCallResult(output="ok", is_error=False, request_id="", server_key="test_server", source="mcp")`.
   - `r_invoke = await self._equivalent_executor(return_value=expected).invoke("test_server", "some_tool", {})`.
   - `r_exec = await self._equivalent_executor(return_value=expected)._raw_execute("some_tool", {})`.
   - Assert `r_invoke.output == r_exec.output == "ok"`, `r_invoke.is_error is False`, `r_invoke.server_key == r_exec.server_key == "test_server"`, `r_invoke.error_type == r_exec.error_type`.
3. `test_transport_error_calls_equivalent`:
   - `r_invoke = await self._equivalent_executor(call_side_effect=TransportError("network down")).invoke("test_server", "some_tool", {})`.
   - `r_exec = await self._equivalent_executor(call_side_effect=TransportError("network down"))._raw_execute("some_tool", {})`.
   - Assert both `is_error is True`, both `error_type == "transport"`, both `server_key == "test_server"`, and `r_invoke.output == r_exec.output`.

### Method

Reuse imports already present in the module (`AsyncMock`, `MagicMock` at L8; `TransportError` at L13; `McpServerHealthRegistry`, `StartupMode`, `McpServerConfig`, `TransportType` at L16–20; `ToolCallResult` at L25; `_make_executor` defined in-module). No new imports unless verifying none are missing.

### Details

- Keep assertions field-level (not bare truthiness) so a silent field regression is caught.
- Preserve English docstrings/comments; keep line length ≤ 88 (`ruff format`).
- Do not modify any existing test, fixture, or class body.

## Compatibility considerations

Purely additive. Existing `_raw_execute` suites (L446, L477) and `TestDisabledServerInvocation` (L537+) are untouched. The equivalence pin coexists; it does not depend on the UNK-01 message normalization (it avoids the disabled case by design).

## Security considerations

N/A: test-only addition; no secrets or I/O beyond mocked transports.

## Rollback considerations

Delete the appended class to fully revert.

## Validation plan

| Target File/Module | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `tests/shared/test_tool_executor.py` | New equivalence pins pass | `uv run pytest tests/shared/test_tool_executor.py::TestInvokeRawExecuteEquivalence -v` | Both methods pass |
| `tests/shared/test_tool_executor.py` | Full-suite regression | `uv run pytest tests/shared/test_tool_executor.py` | No regressions (existing `_raw_execute` outcomes unchanged) |
| `tests/shared/test_tool_executor.py` | Static: lint/format/import-order | `uv run ruff check tests/shared/test_tool_executor.py` | Zero findings |

## Completion criteria

- `TestInvokeRawExecuteEquivalence` exists with healthy and failed cases and passes in isolation and in the full suite.
- It compares `invoke()` and `_raw_execute()` on `output`, `is_error`, `server_key`, and `error_type` for both cases.
- All pre-existing tests in the module still pass unmodified.
- `ruff` reports zero findings.

## Out of scope

Production code (rows 1–2), the `invoke()`-only characterization pin (row 3), and any change to existing tests or fixtures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | Append invoke-vs-_raw_execute equivalence test |
| 2 | Add or update tests per Validation plan | Pending | — | — | Same additions; verify full suite |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | pytest + ruff |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no docs describe the gate order |

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
- **Requirement ID**: `REQ-005`
- **Source issue**: `issues/20261003-154614_invoc001_unify-duplicated-mcp-transport-gate-chain.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261003-162605_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-174413
- **Related target files**: `tests/shared/test_tool_executor.py`
