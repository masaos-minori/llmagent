## Goal

Add a test asserting the chosen `0`/negative concurrency-limit semantics in
`tests/shared/test_tool_transport_invoker.py`: a `0` limit creates no semaphore (unlimited)
and emits a warning, while a positive limit produces a semaphore whose bound equals the
configured value; positive-limit semantics are unchanged.

## Scope

- **In-Scope**: Add a test class to `tests/shared/test_tool_transport_invoker.py` covering
  a `0` limit (unlimited + warning) and a positive limit (bounded semaphore). (REQ-003)
- **Out-of-Scope**: Any change to `scripts/shared/`, positive-limit semantics, or existing
  tests.

## Assumptions

- Option (a) is the resolved semantics (`0`/negative = unlimited); the test pins it.
- `_ensure_semaphores()` can be called directly on an invoker built with a given
  `concurrency_limits` mapping (no transport injection needed).
- The module logger is `shared.tool_transport_invoker`; warnings are captured deterministically
  via pytest's `caplog`.

## Design decisions

- **Direct `_ensure_semaphores()` calls** (rather than driving `invoke()`) keep the test
  focused on semaphore-creation semantics without needing a mocked transport.
- **`caplog` for the warning** makes the assertion independent of root logging config (per
  the Plan's Risk mitigation).
- **Bound inspection via the semaphore's internal value** is the pragmatic way to assert the
  positive-limit bound; the implementer should confirm the exact accessor for Python 3.13.

## Alternatives considered
N/A: coercing `0` → `1` is rejected by the Plan; this test pins the resolved option (a).

## Implementation
### Target file
`tests/shared/test_tool_transport_invoker.py`

### Procedure
1. Confirm the file imports `logging` (add `import logging` near the other stdlib imports if
   absent). Existing imports already include `AsyncMock`, `MagicMock`, `httpx`,
   `HttpTransport`, `ToolCallResult`, and the helpers `_make_invoker`, `_http_cfg`.
2. Append a new test class `TestConcurrencyLimitZeroSemantics` at the end of the file,
   mirroring the existing `@pytest.mark.asyncio` style.
3. Add `test_zero_limit_is_unlimited_and_warns(self, caplog)`:
   - Build `invoker = _make_invoker(concurrency_limits={"srv": 0})`.
   - Enter `with caplog.at_level(logging.WARNING, logger="shared.tool_transport_invoker"):`
   - Call `invoker._ensure_semaphores()`.
   - Assert no semaphore was created for `srv`: `assert invoker._semaphores.get("srv") is None`
     (equivalently `invoker._semaphores == {}`).
   - Assert a warning was logged: `assert any("unlimited" in r.getMessage() for r in caplog.records)`.
4. Add `test_positive_limit_bounds_semaphore(self)`:
   - Build `invoker = _make_invoker(concurrency_limits={"srv": 3})`.
   - Call `invoker._ensure_semaphores()`.
   - Assert a semaphore exists and its bound equals the configured value:
     `sem = invoker._semaphores.get("srv"); assert sem is not None; assert sem._value == 3`.
     (Confirm the bound accessor for Python 3.13 — `asyncio.Semaphore._value` is the usual
     internal counter — before finalizing.)
5. Do not modify any existing test or any file under `scripts/shared/`.

### Method
One new test class with two async methods using `_make_invoker(concurrency_limits=...)`,
direct `_ensure_semaphores()` calls, `caplog`, and semaphore-bound inspection. No new
production code.

### Details
`_make_invoker(configs=None, concurrency_limits=None)` (existing helper) forwards
`concurrency_limits` to `ToolTransportInvoker(...)`, so
`_make_invoker(concurrency_limits={"srv": 0})` yields an invoker whose
`_concurrency_limits == {"srv": 0}` and whose `"srv"` key is known (default config). Calling
`_ensure_semaphores()` then runs the guard (`self._semaphores is None and self._concurrency_limits`
is truthy), warns for the known `0` key, and builds `self._semaphores == {}` (the `if n > 0`
filter drops the `0`). For `{"srv": 3}`, the same call builds `{"srv": Semaphore(3)}`.

The module logger is `logging.getLogger(__name__)` = `shared.tool_transport_invoker`
(`scripts/shared/tool_transport_invoker.py` line 24); `caplog.at_level(...,
logger="shared.tool_transport_invoker")` captures the warning deterministically. The existing
unknown-key warning (lines 46-53) does not fire here because `"srv"` is a known key, so the
new warning is the only record at WARNING level.

Reference conventions already present in this file: `_make_invoker` (line 36),
`MagicMock(spec=httpx.AsyncClient)` (line 40), direct transport injection
`invoker._transports["srv"] = mock_transport` (line 76), and `result.is_error is True`
(line 60).

## Compatibility considerations
N/A: additive test only; no production code touched. Positive-limit semantics are asserted
unchanged, not altered.

## Security considerations
N/A: no secret handling. Uses a non-write server key (`"srv"`) and a read-style tool path;
the concurrency-limit warning carries no secrets.

## Rollback considerations
Remove the added test class.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_tool_transport_invoker.py` | New `0`/positive limit test | `uv run pytest tests/shared/test_tool_transport_invoker.py -k "TestConcurrencyLimitZeroSemantics"` | new test green |
| `tests/shared/` | Full shared-module suite | `uv run pytest tests/shared/` | all pass |

## Completion criteria
`TestConcurrencyLimitZeroSemantics` exists and passes, asserting a `0` limit creates no
semaphore + a warning and a positive limit yields a semaphore bounded to the configured
value, and `ruff`, `mypy`, and the shared-module suite pass.

## Out of scope
`scripts/shared/tool_transport_invoker.py` (REQ-001/REQ-002) and the config reference doc
(`docs/23_agent/agent_08_03_configuration-tools-memory.md`, REQ-001) are separate rows.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 3 | Add `0`-limit (unlimited + warning) and positive-limit (bounded) test; run ruff/mypy/shared-suite | Completed | — | 20261013-154442 | REQ-003, REQ-004 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | N/A: structural non-issue | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (assert `0`-limit behavior: unlimited + warning; positive limit bounded)
- **Source issue**: `issues/20261012-185224_mcp003_concurrency-limit-of-zero-silently-disables-the-per-server-semaphore-in-tooltransportinvoker.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261012-232916_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261013-092101
- **Related target files**: `tests/shared/test_tool_transport_invoker.py`