## Goal

Add a new characterization test file,
`tests/shared/test_tool_transport_invoker_merge.py`, that pins
`ToolTransportInvoker.invoke()`'s current success-path and
`TransportError`-path recording behavior — specifically, that
`_record_success`/`_record_transport_error` are each called exactly once
with the correct arguments, and that `_record_transport_error`'s return
value is what `invoke()` returns. This test must be written and passing
against the **pre-merge** code first (before `_invoke_and_record` is
extracted in `scripts/shared/tool_transport_invoker.py`), then re-verified
unchanged after the merge, per the plan's Phase 1 behavior-lock step.

## Scope

In scope:
- New test file `tests/shared/test_tool_transport_invoker_merge.py` with
  at minimum two async test cases against a real `ToolTransportInvoker`
  instance with `_record_success`/`_record_transport_error` mocked:
  1. Success path: `invoke()` returns the transport's result; `_record_success`
     is called once with `(server_key, result)`.
  2. `TransportError` path: the transport call raises `TransportError`;
     `_record_transport_error` is called once with `(server_key, exc)`; and
     `invoke()`'s return value is exactly what the mocked
     `_record_transport_error` returned.

Out of scope:
- Any change to `tests/shared/test_tool_transport_invoker.py` (pre-existing,
  9 test methods) — this new file complements it, does not replace or
  modify it.
- Re-testing observable side effects already covered by the pre-existing
  file (stat counters, health-registry state transitions via a real
  `McpServerHealthRegistry`) — this file mocks
  `_record_success`/`_record_transport_error` directly instead, per the
  plan's narrower-scope resolution (UNK-02).
- Any test targeting `ToolExecutor._raw_execute` or
  `_run_gate_chain` — those are covered by
  `tests/shared/test_tool_executor_order.py` and other
  `tests/shared/test_tool_executor*.py` files, unmodified by this plan
  except for a possible early-exit gap-fill noted as conditional in the
  plan.

## Assumptions

- This file is written and run **before** the `_invoke_and_record`
  extraction lands in `scripts/shared/tool_transport_invoker.py` (plan
  Phase 1), so its initial assertions exercise `invoke()`'s current inline
  try/except block at `tool_transport_invoker.py:202-207`.
- After the extraction (plan Phase 2), this same file is re-run unchanged
  to confirm `invoke()`'s externally observable recording behavior is
  identical whether the try/except is inline or delegated to
  `_invoke_and_record`.
- Follows the existing `tests/shared/test_tool_transport_invoker.py`
  conventions: `_http_cfg()`/`_make_invoker()`-style helper functions,
  `pytest.mark.asyncio`, `unittest.mock.AsyncMock`/`MagicMock`, imports
  from `shared.http_transport`, `shared.mcp_config`,
  `shared.tool_transport_invoker`, `shared.transport_dto`.

## Design decisions

- Mock `_record_success`/`_record_transport_error` on the invoker instance
  directly (e.g. via `monkeypatch.setattr` or `unittest.mock.patch.object`)
  rather than constructing a full `McpServerHealthRegistry`, since the
  goal is to pin the *call contract* between `invoke()` and these two
  methods, not their internal health-tracking side effects (already
  covered elsewhere).
- Give the mocked transport's `.call()` a controllable `AsyncMock` (return
  value for the success case, `side_effect=TransportError(...)` for the
  error case) reusing the pattern already present in
  `tests/shared/test_tool_transport_invoker.py::test_lifecycle_ensure_ready_called`.
- Assert on the mock's `call_args` (call count and exact positional
  arguments) rather than re-deriving expected state independently, so the
  test fails loudly if either the call count or argument shape drifts
  after the merge.

## Alternatives considered

N/A — the plan's Phase 1 step names the exact assertions this file must
contain.

## Implementation

### Target file
`tests/shared/test_tool_transport_invoker_merge.py` (new)

### Procedure
1. Create the file with a module docstring identifying its purpose
   (characterization pin for the `invoke()` / `ToolExecutor._raw_execute`
   merge) and the standard imports used by the sibling
   `tests/shared/test_tool_transport_invoker.py`.
2. Reuse (or locally redefine, to keep this file independently readable)
   `_http_cfg()` and a `_make_invoker()` helper matching the existing
   file's signatures.
3. Write `test_invoke_success_records_once_with_result`: build an invoker,
   patch `_record_success` with a `MagicMock`, give the resolved transport
   an `AsyncMock` `.call()` returning a known `ToolCallResult`, call
   `await invoker.invoke(server_key, tool_name, args)`, then assert
   `_record_success.call_count == 1`, `_record_success.call_args ==
   call(server_key, expected_result)`, and the returned value is
   `expected_result`.
4. Write `test_invoke_transport_error_records_once_and_returns_its_result`:
   same setup but the transport's `.call()` raises `TransportError("boom")`;
   patch `_record_transport_error` with a `MagicMock` returning a sentinel
   `ToolCallResult`; assert `_record_transport_error.call_count == 1`,
   `_record_transport_error.call_args == call(server_key, the_exception)`,
   and `invoke()`'s return value is the sentinel (i.e. `invoke()` returns
   exactly what `_record_transport_error` returned, not something derived
   independently).
5. Run against pre-merge code; confirm both pass. After the merge lands in
   `scripts/shared/tool_transport_invoker.py`, re-run unchanged; confirm
   both still pass with identical assertions.

### Method
New file following existing sibling-file conventions (`_http_cfg`,
`_make_invoker`, `pytest.mark.asyncio`, `AsyncMock`/`MagicMock`); no
production code touched by this file itself.

### Details
Skeleton (illustrative; concrete mock wiring may vary slightly to match
`ToolTransportInvoker`'s actual transport-resolution path, i.e. populating
`invoker._transports[server_key]` with a mock `HttpTransport` before
calling `invoke()`, as the existing sibling file's
`test_lifecycle_ensure_ready_called` does at line ~60):
```python
"""tests/shared/test_tool_transport_invoker_merge.py
Characterization pin for ToolTransportInvoker.invoke()'s success/
TransportError recording behavior, ahead of the _invoke_and_record merge
with ToolExecutor._raw_execute. Complements test_tool_transport_invoker.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest
from shared.http_transport import TransportError
from shared.mcp_config import McpServerConfig, TransportType
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url)


def _make_invoker(server_key: str = "srv") -> ToolTransportInvoker:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolTransportInvoker(
        http=http, server_configs={server_key: _http_cfg()}
    )


class TestInvokeAndRecordMerge:
    @pytest.mark.asyncio
    async def test_invoke_success_records_once_with_result(self) -> None:
        invoker = _make_invoker()
        expected = ToolCallResult(
            output="ok", is_error=False, request_id="r1",
            server_key="srv", source="mcp",
        )
        invoker._transports["srv"].call = AsyncMock(return_value=expected)  # type: ignore[attr-defined]
        invoker._record_success = MagicMock()  # type: ignore[method-assign]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result is expected
        invoker._record_success.assert_called_once_with("srv", expected)

    @pytest.mark.asyncio
    async def test_invoke_transport_error_records_once_and_returns_its_result(
        self,
    ) -> None:
        invoker = _make_invoker()
        exc = TransportError("boom")
        invoker._transports["srv"].call = AsyncMock(side_effect=exc)  # type: ignore[attr-defined]
        sentinel = ToolCallResult(
            output="boom", is_error=True, request_id="", server_key="srv",
            source="mcp", error_type="transport",
        )
        invoker._record_transport_error = MagicMock(return_value=sentinel)  # type: ignore[method-assign]

        result = await invoker.invoke("srv", "some_tool", {})

        assert result is sentinel
        invoker._record_transport_error.assert_called_once_with("srv", exc)
```
The implementer should verify the exact mocking mechanics (e.g. whether
`invoker._transports["srv"]` is itself an `HttpTransport` with a real
`.call` attribute to monkeypatch, vs. needing a `MagicMock(spec=HttpTransport)`
substituted wholesale) against the actual `ToolTransportInvoker.__init__`
transport-construction logic (`tool_transport_invoker.py:52-61`) before
finalizing this file.

## Compatibility considerations

N/A — new test file only; no production code or public contract affected.

## Security considerations

N/A — test-only file, no security-relevant logic.

## Rollback considerations

Trivially revertable: delete the new file. Since it is independently
revertable from the two production-code extractions (per the plan's Phase
1 note "This step is independently revertable (new file only)"), it can be
removed without affecting either `scripts/shared/tool_executor.py` or
`scripts/shared/tool_transport_invoker.py`.

## Validation plan

`uv run pytest tests/shared/test_tool_transport_invoker_merge.py -v` — both
new tests pass against the pre-merge code; re-run the same command after
the `_invoke_and_record` extraction lands and confirm both still pass with
identical assertions. Also run alongside the pre-existing sibling file:
`uv run pytest tests/shared/test_tool_transport_invoker.py
tests/shared/test_tool_transport_invoker_merge.py -v`.

## Out of scope

- `ToolTransportInvoker._invoke_and_record` extraction itself — separate
  target file, separate procedure (`scripts/shared/tool_transport_invoker.py`).
- `ToolExecutor._run_gate_chain` extraction — separate target file,
  separate procedure (`scripts/shared/tool_executor.py`).
- Modifying `tests/shared/test_tool_transport_invoker.py` — pre-existing,
  explicitly unmodified by this plan.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-192422_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-004553
- Related target files: test_tool_transport_invoker_merge.py
