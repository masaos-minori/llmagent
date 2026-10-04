# Implementation Procedure — `tests/shared/test_tool_transport_invoker.py`

## Goal

Add a characterization pin that locks `ToolTransportInvoker.invoke()`'s end-to-end success and error results after the gate-chain unification (row 1 / `REQ-001`, `REQ-002`), so the refactor into `_run_precall_gates` cannot silently change `invoke()`'s observable output (`REQ-005`).

## Scope

- **In-Scope**: Append new characterization test(s) to `tests/shared/test_tool_transport_invoker.py` capturing `invoke()`'s concrete `ToolCallResult` (fields + side effects) for a representative healthy call and a representative failed call. Existing tests are left unchanged.
- **Out-of-Scope**: Any production code change (rows 1–2); the `invoke()`-vs-`_raw_execute()` equivalence test belongs to `tests/shared/test_tool_executor.py` (row 4).

## Assumptions

- The module's existing helpers `_http_cfg()` (L23) and `_make_invoker()` (L35) are reusable; `_make_invoker()` defaults to a single PERSISTENT `"srv"` config and a `MagicMock(spec=httpx.AsyncClient)` HTTP client.
- `ToolCallResult` carries `output`, `is_error`, `request_id`, `server_key`, `source`, `error_type` (imported at L20); assertions compare these fields.
- The existing `merge` file (`test_tool_transport_invoker_merge.py`) pins `_invoke_and_record`'s return identity but MOCKS `_record_success`/`_record_transport_error`, so it does not exercise the real gate chain. This pin instead drives the full real chain through `invoke()`.

## Design decisions

- **New class, additive only.** Add `class TestInvokeCharacterizationPin:` at the end of the file with two `@pytest.mark.asyncio` methods. Do not modify or remove any existing method — the goal is a lock, not a rewrite.
- **Drive the real gate chain.** Configure a real (non-mocked-record) transport so `_check_health`, lifecycle, transport-resolution, semaphore, and `_invoke_and_record` all execute. This distinguishes the pin from the merge file, which stubs the record helpers.
- **Assert concrete fields, not just truthiness.** Compare `output`, `is_error`, `error_type`, and `server_key` against expected values so a silent field-level regression is caught.
- **Healthy path also asserts side effects** (lifecycle `ensure_ready` awaited once; `_record_success` invoked) to lock ordering, not just the returned value.

## Alternatives considered

- **Rely solely on the existing suite + merge file.** Rejected — neither asserts `invoke()`'s full real-chain result contract in one consolidated place; a dedicated pin makes the post-refactor lock explicit and self-documenting.
- **Parametrize over every gate outcome.** Rejected — scope is a representative healthy + failed pair (per `REQ-005`); the existing suite already covers unavailable/HALF_OPEN/disabled/lifecycle outcomes individually.

## Implementation

### Target file

`tests/shared/test_tool_transport_invoker.py`

### Procedure

Append the following class after `TestDisabledServerExclusion` (file ends at L221):

1. `test_invoke_healthy_returns_expected_result`:
   - Build `invoker = _make_invoker()`.
   - Install a health registry (`McpServerHealthRegistry`) reporting HEALTHY (or omit; default healthy is fine since no failures recorded).
   - Set a lifecycle `AsyncMock` and install a mock transport whose `call` returns `ToolCallResult(output="ok", is_error=False, request_id="r1", server_key="srv", source="mcp")`.
   - `result = await invoker.invoke("srv", "some_tool", {})`.
   - Assert `result.output == "ok"`, `result.is_error is False`, `result.error_type` is the default, `result.server_key == "srv"`; assert the lifecycle mock was awaited once with `"srv"`.
2. `test_invoke_transport_error_returns_error_result`:
   - Build `invoker = _make_invoker()`.
   - Install a mock transport whose `call` raises `TransportError("network down")`.
   - `result = await invoker.invoke("srv", "some_tool", {})`.
   - Assert `result.is_error is True`, `result.error_type == "transport"`, `result.server_key == "srv"`; assert `invoker.stat_transport_errors.get("srv", 0) == 1`.

### Method

Reuse the module's `_make_invoker()`/`_http_cfg()` and imports already present (`TransportError` at L12, `ToolCallResult` at L20, `McpServerHealthRegistry` at L15, `AsyncMock`/`MagicMock` at L8). No new imports unless verifying none are missing.

### Details

- Keep each assertion specific to a field; avoid bare `assert result` truthiness.
- Preserve English docstrings/comments; keep line length ≤ 88 (`ruff format`).
- Do not alter fixtures, existing classes, or existing test bodies.

## Compatibility considerations

Purely additive. Existing `TestToolTransportInvoker`, `TestDisabledServerExclusion`, and the `merge` file are untouched; this pin coexists with them.

## Security considerations

N/A: test-only addition; no secrets or I/O beyond mocked transports.

## Rollback considerations

Delete the appended class to fully revert.

## Validation plan

| Target File/Module | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `tests/shared/test_tool_transport_invoker.py` | New characterization pins pass | `uv run pytest tests/shared/test_tool_transport_invoker.py -v` | Both new methods pass |
| `tests/shared/test_tool_transport_invoker.py` | Full-suite regression | `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_transport_invoker_merge.py` | No regressions |
| `tests/shared/test_tool_transport_invoker.py` | Static: lint/format/import-order | `uv run ruff check tests/shared/test_tool_transport_invoker.py` | Zero findings |

## Completion criteria

- The two characterization methods exist and pass in isolation and in the full suite.
- They assert concrete `ToolCallResult` fields (not just truthiness) for a healthy and a failed call through the real gate chain.
- All pre-existing tests in the module still pass unmodified.
- `ruff` reports zero findings.

## Out of scope

Production code (rows 1–2), the `invoke()`-vs-`_raw_execute()` equivalence test (row 4), and any change to existing tests or fixtures.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Append invoke() characterization pin |
| 2 | Add or update tests per Validation plan | Done | — | — | Same additions; verify full suite |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | pytest + ruff |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | N/A: no docs describe the gate order |

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
- **Related target files**: `tests/shared/test_tool_transport_invoker.py`
