## Goal

Extend `tests/shared/test_tool_transport_invoker.py` to cover
`ToolTransportInvoker.__init__`'s `call_timeout_sec` resolution — a zero value ("no timeout"), a
positive value, and the default-unset case — pinning the pre-fix buggy behavior first
(characterization) and then flipping the assertion to the correct post-fix behavior once
`scripts/shared/tool_transport_invoker.py:54-58` is corrected (see the companion procedure
`implementations/20260814-004820_tool_transport_invoker.py.md`).

## Scope

In scope:
- `tests/shared/test_tool_transport_invoker.py` — extend the `_http_cfg` helper
  (currently at lines 22-23) to accept an optional `call_timeout_sec: float = 60.0` parameter and
  thread it into the `McpServerConfig(...)` call.
- Add test coverage for three `call_timeout_sec` cases: `0` (no timeout), a positive value
  (`30.0`), and the default-unset case (`_http_cfg()` with no argument).

Out of scope:
- `scripts/shared/tool_transport_invoker.py` — covered by the companion procedure
  (`implementations/20260814-004820_tool_transport_invoker.py.md`); this test file only asserts
  against its behavior, does not modify it.
- The other 9 pre-existing test methods in this file (health, lifecycle, semaphore, recording) —
  unmodified by this change.
- `tests/shared/test_mcp_config_validation.py`, `tests/shared/test_mcp_config.py` — run for
  regression only, not modified.

## Assumptions

- The characterization-test-first discipline (`AGENTS.md` → `skills/python-refactoring/workflow.md`
  §Phase 2) applies: the `call_timeout_sec=0` test must first be written to assert the current
  (buggy) `_timeout == 60.0` value, run and confirmed PASSING against pre-fix code, and only then
  flipped to assert `_timeout == 0` once the source fix lands.
- `HttpTransport` exposes the resolved timeout as `self._timeout` (confirmed at
  `scripts/shared/http_transport.py:42`, `self._timeout = timeout_sec`), so tests can assert via
  `invoker._transports["srv"]._timeout`.

## Design decisions

- Extend `_http_cfg` with a keyword-only-by-convention optional parameter rather than adding a
  second helper, to keep all existing call sites (`_http_cfg()`, `_http_cfg(url=...)`) unchanged
  and minimize diff.
- Assert on `invoker._transports["srv"]._timeout` directly (an existing pattern already used
  elsewhere in this file, e.g. `invoker._transports["srv"] = mock_transport` at line 66), rather
  than introducing a new public accessor, since this is white-box test code exercising a private
  collection that already has precedent for direct access in this file.

## Alternatives considered

N/A — the plan specifies the exact helper change and the three test cases (0 / positive /
default-unset).

## Implementation

### Target file

`tests/shared/test_tool_transport_invoker.py`

### Procedure

1. Extend `_http_cfg` (lines 22-23) to accept `call_timeout_sec: float = 60.0` and pass it through
   to `McpServerConfig(...)`.
2. Add a characterization test asserting the pre-fix value (`_timeout == 60.0`) when
   `call_timeout_sec=0` is passed. Run
   `uv run pytest tests/shared/test_tool_transport_invoker.py -k call_timeout -v` against pre-fix
   `tool_transport_invoker.py` and confirm it PASSES.
3. Once the source fix lands (companion procedure), flip that test's assertion to `_timeout == 0`
   and add the two remaining cases: `call_timeout_sec=30.0` → `_timeout == 30.0`, and
   default-unset (`_http_cfg()`) → `_timeout == 60.0`.
4. Run `uv run pytest tests/shared/test_tool_transport_invoker.py -v` and confirm all tests
   (the 9 pre-existing plus the new `call_timeout_sec` cases) pass.

### Method

Additive change to test-only code: widen an existing helper's signature with a backward-compatible
default, then add new test methods that construct an invoker via `_make_invoker`/`_http_cfg` and
assert on the resolved `HttpTransport._timeout`. No production code is touched by this procedure.

### Details

Current helper (`tests/shared/test_tool_transport_invoker.py:22-23`):
```python
def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url)
```

Target shape after extension:
```python
def _http_cfg(
    url: str = "http://127.0.0.1:8000", call_timeout_sec: float = 60.0
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP, url=url, call_timeout_sec=call_timeout_sec
    )
```

New test cases (added to `TestToolTransportInvoker`, following the existing pattern of
`_make_invoker(configs={"srv": _http_cfg(...)})` used elsewhere in this file):
```python
def test_call_timeout_sec_zero_means_no_timeout(self) -> None:
    invoker = _make_invoker(configs={"srv": _http_cfg(call_timeout_sec=0)})
    assert invoker._transports["srv"]._timeout == 0

def test_call_timeout_sec_positive_value_passed_through(self) -> None:
    invoker = _make_invoker(configs={"srv": _http_cfg(call_timeout_sec=30.0)})
    assert invoker._transports["srv"]._timeout == 30.0

def test_call_timeout_sec_default_unset_falls_back_to_60(self) -> None:
    invoker = _make_invoker(configs={"srv": _http_cfg()})
    assert invoker._transports["srv"]._timeout == 60.0
```

Note: per the characterization-test-first discipline, the first of these three
(`test_call_timeout_sec_zero_means_no_timeout`) must initially assert `== 60.0` (the current buggy
value) and be run/confirmed passing against pre-fix source before the source fix lands; the
assertion above (`== 0`) is the final, post-fix state.

## Compatibility considerations

`_http_cfg`'s new parameter has a default matching the previous hardcoded behavior
(`call_timeout_sec: float = 60.0`), so every existing call site (`_http_cfg()`, `_http_cfg(url=...)`
used throughout this file) continues to construct an equivalent `McpServerConfig` unchanged. No
existing test's behavior changes as a result of this signature extension.

## Security considerations

N/A — test-only file; no production code, credentials, or network surface affected.

## Rollback considerations

Test-only, additive change. Revert by removing the three new test methods and reverting
`_http_cfg`'s signature to its two-argument-free form; no other file depends on the extended
signature.

## Validation plan

`uv run pytest tests/shared/test_tool_transport_invoker.py -v` — all tests pass, with the
`call_timeout_sec=0` case asserting `_timeout == 0` once the companion source fix has landed (see
`implementations/20260814-004820_tool_transport_invoker.py.md`). Before that fix lands, the same
test must be confirmed to PASS with a `_timeout == 60.0` assertion against pre-fix code, per the
characterization-test-first discipline.

## Out of scope

- `scripts/shared/tool_transport_invoker.py` — separate implementation procedure
  (`implementations/20260814-004820_tool_transport_invoker.py.md`).
- `tests/shared/test_mcp_config_validation.py`, `tests/shared/test_mcp_config.py`,
  `tests/shared/` (broader suite) — run for regression only, not modified.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-192935_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-004851
- Related target files: test_tool_transport_invoker.py
