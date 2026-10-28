## Goal

Add three unit tests that pin the new default per-server concurrency cap: the
unconfigured-default cap (`REQ-002`), the configured-positive override (`REQ-003`),
and the `0`/negative opt-out (`REQ-003`), using a concurrency-measuring fake
transport (`REQ-001`).

## Scope

Modifies only `tests/shared/test_tool_transport_invoker.py`: adds an `asyncio`
import, a module-level concurrency-probe helper, and one test class with three
tests. No existing test is edited; the full existing suite must still pass
unmodified (`AC-4`).

## Assumptions

- The constant DEFAULT_PER_SERVER_CONCURRENCY is defined by the seq-01 row
  (`scripts/shared/tool_transport_invoker.py`); it exists by the time
  code-implementation executes the rows in order, so these tests can reference it.
- `_make_invoker()` builds an invoker whose `_transports` is populated by assigning
  a fake transport (the pattern the existing suite already uses), and that
  `invoke()` routes through `_run_precall_gates()` → `_ensure_semaphores()`, so the
  semaphore under test is the one exercised on the real call path.
- Overlap with the sibling `mcpcompat001` Plan on this file is **Compatible**, not a
  conflict: `mcpcompat001` moves the `McpServerHealthRegistry` import (lines 14-20)
  to `shared.mcp_health`; this Plan appends new tests at the end of the file.
  Different regions; whichever Plan lands later rebases.
- Measurement is deterministic via asyncio events (a probe sets an event once its
  high-water mark is reached, then the test releases a gate); no wall-clock sleeps.

## Design decisions

- **Measure peak, not latency.** A fake `call` increments an in-flight counter on
  entry, records the max, and blocks on a gate until the test releases it. The
  semaphore (or `nullcontext` for the opt-out) bounds how many `call`s are in
  flight at once, so the recorded peak is exactly the effective limit.
- **Reference the constant, not a literal.** The default-cap case passes
  the constant DEFAULT_PER_SERVER_CONCURRENCY as the expected peak and asserts against it
  (`REQ-001`), so the test tracks the constant if its value changes.

## Alternatives considered

- **Wall-clock timing** (start N tasks, sleep, count in-flight): rejected — flaky
  and non-deterministic. The event-gate pattern makes the peak exact.
- **Inspecting `_semaphores._value` directly**: rejected — it would not prove the
  cap is *enforced on the call path*, only that a semaphore was built.

## Implementation
### Target file

`tests/shared/test_tool_transport_invoker.py`

### Procedure

1. Add `import asyncio` to the top-of-file imports (after `import logging`).
2. Add the `_ConcurrencyProbe` (new) helper class immediately before the
   `TestDefaultPerServerConcurrency` (new) class (module scope, after the existing
   `_make_invoker` helper).
3. Append the `TestDefaultPerServerConcurrency` (new) class, which drives each
   case through its `_measure_peak` (new) helper, plus the three tests (see
   Details).

### Method

The driver constructs an invoker, installs the probe as `"srv"`'s transport,
launches 20 concurrent `invoke()` calls, waits for the probe to report that its
expected high-water mark was reached, releases the gate, and returns the recorded
peak. Each test supplies the expected peak: the `(new)`-row constant for the
default case, the configured value for the override, and `20` for the opt-out.

### Details

- **Import** (Step 1) — insert `import asyncio` among the stdlib imports.
- **Probe** (Step 2) — a minimal stand-in for `HttpTransport.call`:

  ```python
  class _ConcurrencyProbe:
      """Fake transport recording peak simultaneous in-flight calls.

      Holds every call open on ``gate`` until the test releases it, so the
      observed peak is deterministic (no wall-clock sleeps). Sets ``reached``
      once expected_peak calls are simultaneously in flight."""

      def __init__(self, expected_peak: int) -> None:
          self.current = 0
          self.peak = 0
          self.expected_peak = expected_peak
          self.reached = asyncio.Event()
          self.gate = asyncio.Event()

      async def call(self, tool_name: str, args: dict[str, Any]) -> ToolCallResult:
          self.current += 1
          self.peak = max(self.peak, self.current)
          if self.current == self.expected_peak:
              self.reached.set()
          await self.gate.wait()
          self.current -= 1
          return ToolCallResult(
              output="ok", is_error=False, request_id="", server_key="srv"
          )
  ```

- **Driver + tests** (Step 3):

  ```python
  class TestDefaultPerServerConcurrency:
      @staticmethod
      async def _measure_peak(
          concurrency_limits: dict[str, int] | None,
          expected_peak: int,
          n_calls: int = 20,
      ) -> int:
          invoker = _make_invoker(concurrency_limits=concurrency_limits)
          probe = _ConcurrencyProbe(expected_peak=expected_peak)
          invoker._transports["srv"] = probe  # type: ignore[assignment]
          tasks = [
              asyncio.create_task(invoker.invoke("srv", "tool", {}))
              for _ in range(n_calls)
          ]
          try:
              await asyncio.wait_for(probe.reached.wait(), timeout=10)
          finally:
              probe.gate.set()
              await asyncio.gather(*tasks)
          return probe.peak

      @pytest.mark.asyncio
      async def test_unconfigured_server_uses_default_cap(self) -> None:
          peak = await TestDefaultPerServerConcurrency._measure_peak(
              None, DEFAULT_PER_SERVER_CONCURRENCY
          )
          assert peak == DEFAULT_PER_SERVER_CONCURRENCY

      @pytest.mark.asyncio
      async def test_configured_positive_limit_overrides_default(self) -> None:
          peak = await TestDefaultPerServerConcurrency._measure_peak({"srv": 2}, 2)
          assert peak == 2

      @pytest.mark.asyncio
      async def test_zero_limit_opts_out_of_default(self) -> None:
          peak = await TestDefaultPerServerConcurrency._measure_peak({"srv": 0}, 20)
          assert peak == 20
  ```

- Why it is deterministic: the semaphore admits exactly `expected_peak` (new) calls
  before blocking the rest, and `nullcontext` (the `0`/negative opt-out) lets all
  `n_calls` (new) through; none of the `call`s decrement the counter until the gate
  is released, so `probe.peak` equals the effective limit exactly.
- DEFAULT_PER_SERVER_CONCURRENCY is referenced here only inside the test bodies
  (code), where it exists by execution order; see Assumptions.

## Compatibility considerations

- No existing test is modified; the whole `tests/shared/test_tool_transport_invoker.py`
  and `tests/shared/test_tool_executor*.py` suites must pass unmodified (`AC-4`).
- The appended class and helper do not collide with `mcpcompat001`'s import edit
  (top of file) — this change is purely additive at the end of the file.
- `test_tool_executor_order.py` assigns `_semaphores = None` directly and stays
  valid with the seq-01 restructured lazy builder.

## Security considerations

N/A: test-only additions; no runtime or access-control behavior changes.

## Rollback considerations

Revert the commit; the change is one import, one helper class, and one test class.

## Validation plan

- Unit (new behavior): `uv run pytest tests/shared/test_tool_transport_invoker.py -k "DefaultPerServerConcurrency"`.
- Regression: `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_executor*.py`.
- Static + contract: `uv run ruff check tests/`, `uv run mypy --no-namespace-packages tests/`, `PYTHONPATH=scripts uv run lint-imports`.
- Full suite: `uv run pytest tests/`.

## Completion criteria

- `test_unconfigured_server_uses_default_cap` (new) asserts the peak for an unconfigured
  server equals the seq-01 constant DEFAULT_PER_SERVER_CONCURRENCY (`REQ-002`, `REQ-001`).
- `test_configured_positive_limit_overrides_default` (new) asserts a configured positive
  limit caps at that value, not the default (`REQ-003`).
- `test_zero_limit_opts_out_of_default` (new) asserts a `0` limit reaches the full fan-out
  (`REQ-003`).
- All pre-existing semaphore, health, lifecycle, and gate-order tests pass without
  modification (`REQ-003`, `AC-4`).

## Out of Scope

- Any change to `scripts/shared/tool_transport_invoker.py` or `tool_executor.py`
  (covered by earlier rows).
- Documentation updates (covered by later rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20261028-102436 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20261028-102436 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261028-102436 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20261028-102436 |  |

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
- **Requirement ID**: `REQ-001` (default-cap test references the module-level constant), `REQ-002`
  (unconfigured server capped at the default), `REQ-003` (configured-positive override and `0`/negative opt-out preserved)
- **Source issue**: issues/20261027-001921_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-104612_mcpinv004_unbounded-per-server-concurrency-default.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-004831
- **Related target files**: tests/shared/test_tool_transport_invoker.py