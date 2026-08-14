## Goal

Extract the byte-for-byte identical tail try/except + `_record_success` /
`_record_transport_error` block — currently duplicated independently in
`ToolTransportInvoker.invoke()` (`scripts/shared/tool_transport_invoker.py:202-207`)
and `ToolExecutor._raw_execute` (`scripts/shared/tool_executor.py:140-145`) —
into one shared method `_invoke_and_record` on `ToolTransportInvoker`, kept
override-safe (no `@final`, no name-mangled double-underscore) so
`ToolExecutor` can call the inherited version instead of reimplementing it.

## Scope

In scope:
- Add `_invoke_and_record(self, server_key: str, transport: HttpTransport,
  tool_name: str, args: dict[str, Any], sem: asyncio.Semaphore | None) ->
  ToolCallResult` as a new instance method on `ToolTransportInvoker`,
  containing exactly the current try/except body at
  `tool_transport_invoker.py:202-207`.
- Update `invoke()` (`tool_transport_invoker.py:175-207`) to call
  `_invoke_and_record` after its own existing lifecycle block, instead of
  running the try/except inline.

Out of scope:
- `invoke()`'s own lifecycle-handling block
  (`tool_transport_invoker.py:185-191`, catches only `ServerCooldownError`)
  — this stays exactly as-is; it is a different code path from
  `ToolExecutor._ensure_lifecycle_ready` (catches `OSError`/`RuntimeError`,
  calls `self._health_registry.record_failure`) and the two are not being
  unified.
- The semaphore ensure/get step
  (`self._ensure_semaphores()` then `(self._semaphores or
  {}).get(server_key)`, `tool_transport_invoker.py:199-200`) — stays inline
  at each call site (both in `invoke()` and in `_raw_execute`), matching the
  suggested `_invoke_and_record(..., sem)` signature which takes `sem` as an
  already-resolved parameter.
- `ToolExecutor._run_gate_chain` extraction — separate target file,
  separate procedure (`scripts/shared/tool_executor.py`).
- Any public method signature change on `ToolTransportInvoker.invoke()`.

## Assumptions

- `ToolExecutor` is the sole subclass of `ToolTransportInvoker` in
  `scripts/` (confirmed by the plan's `rg` evidence), so this is a
  same-file-pair merge with no fan-out to other subclasses.
- The pre-existing `tests/shared/test_tool_transport_invoker.py` (9 test
  methods, unmodified by this change) already exercises `invoke()`'s
  observable side effects (stat counters, health-registry calls); a new,
  narrower characterization test file
  (`tests/shared/test_tool_transport_invoker_merge.py`, separate
  implementation procedure) pins `_record_success`/`_record_transport_error`
  call arguments directly and must be written and passing against the
  pre-merge code before this extraction lands.

## Design decisions

- Keep `_invoke_and_record` as a plain single-underscore instance method
  (not `@final`, not name-mangled `__invoke_and_record`) so `ToolExecutor`
  can call the inherited implementation without any override friction, per
  the plan's explicit "override-safe" requirement.
- Preserve parameter order and types exactly as named in the plan
  (`server_key, transport, tool_name, args, sem`) so both call sites
  (`invoke()` and `ToolExecutor._raw_execute`) can pass their
  already-resolved values with no additional glue code.

## Alternatives considered

N/A — the plan specifies the exact helper name, signature, and code range
to extract.

## Implementation

### Target file
`scripts/shared/tool_transport_invoker.py`

### Procedure
1. Add `_invoke_and_record` as a new method, placed after
   `_execute_with_semaphore` (currently ending at line 173) and before
   `invoke` (currently starting at line 175).
2. Replace `invoke()`'s tail try/except (`tool_transport_invoker.py:202-207`)
   with a single `return await self._invoke_and_record(server_key,
   transport, tool_name, args, sem)`.
3. Run `uv run pytest tests/shared/test_tool_transport_invoker.py
   tests/shared/test_tool_transport_invoker_merge.py -v` and confirm both
   pass unchanged.
4. Confirm `ToolExecutor._raw_execute`'s companion change (separate
   procedure, `scripts/shared/tool_executor.py`) calls this inherited
   method after its own gate chain and transport resolution, rather than
   re-implementing the block.

### Method
Direct, minimal-diff extraction: move the existing try/except statements
verbatim into the new method body; no logic changes, no new imports (
`TransportError`, `ToolCallResult`, `self._execute_with_semaphore`,
`self._record_success`, `self._record_transport_error` are all already
defined/imported in this file).

### Details
Current `invoke()` (`tool_transport_invoker.py:175-207`):
```python
async def invoke(
    self,
    server_key: str,
    tool_name: str,
    args: dict[str, Any],
) -> ToolCallResult:
    """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
    if err := self._check_health(server_key):
        return err

    if self._lifecycle is not None:
        try:
            await self._lifecycle.ensure_ready(server_key)
        except ServerCooldownError as e:
            msg = str(e)
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="transport")

    transport = self._transports.get(server_key)
    if transport is None:
        msg = self._transport_missing_msg(server_key)
        logger.error(msg)
        return self._error_result(server_key, msg, error_type="tool")

    self._ensure_semaphores()
    sem = (self._semaphores or {}).get(server_key)

    try:
        result = await self._execute_with_semaphore(transport, tool_name, args, sem)
        self._record_success(server_key, result)
        return result
    except TransportError as e:
        return self._record_transport_error(server_key, e)
```

Target shape after extraction:
```python
async def _invoke_and_record(
    self,
    server_key: str,
    transport: HttpTransport,
    tool_name: str,
    args: dict[str, Any],
    sem: asyncio.Semaphore | None,
) -> ToolCallResult:
    """Execute the transport call under the semaphore and record success/transport-error; shared by invoke() and ToolExecutor._raw_execute."""
    try:
        result = await self._execute_with_semaphore(transport, tool_name, args, sem)
        self._record_success(server_key, result)
        return result
    except TransportError as e:
        return self._record_transport_error(server_key, e)

async def invoke(
    self,
    server_key: str,
    tool_name: str,
    args: dict[str, Any],
) -> ToolCallResult:
    """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
    if err := self._check_health(server_key):
        return err

    if self._lifecycle is not None:
        try:
            await self._lifecycle.ensure_ready(server_key)
        except ServerCooldownError as e:
            msg = str(e)
            logger.warning(msg)
            return self._error_result(server_key, msg, error_type="transport")

    transport = self._transports.get(server_key)
    if transport is None:
        msg = self._transport_missing_msg(server_key)
        logger.error(msg)
        return self._error_result(server_key, msg, error_type="tool")

    self._ensure_semaphores()
    sem = (self._semaphores or {}).get(server_key)
    return await self._invoke_and_record(server_key, transport, tool_name, args, sem)
```

## Compatibility considerations

No public method signature change on `invoke()`. `_invoke_and_record` is a
new protected method; no existing caller outside this file, `tool_executor.py`,
and their tests references the old inline try/except directly, so nothing
else needs updating. `ToolExecutor` (the only subclass) gains access to the
inherited method automatically via normal Python attribute resolution — no
`super()` call or import change needed in `tool_executor.py` beyond calling
`self._invoke_and_record(...)`.

## Security considerations

N/A — no change to authentication, authorization, error content, or
recorded health-state semantics; `_record_transport_error`'s existing
`self._health_registry.record_failure(server_key)` call and `_record_success`'s
existing `self._health_registry.record_success(server_key)` call are moved
verbatim, not altered.

## Rollback considerations

Revert is a single-file, single-method-boundary change; `git revert` (or
manual re-inline of `_invoke_and_record`'s body into `invoke()`) fully
restores prior behavior. This extraction must land only after
`ToolExecutor._raw_execute`'s companion change is ready to call the
inherited method — landing them as two separate, independently revertable
commits (per the plan's Phase 2 step ordering) keeps either side
revertable without touching the other.

## Validation plan

`uv run pytest tests/shared/test_tool_transport_invoker.py
tests/shared/test_tool_transport_invoker_merge.py -v` — all 9 pre-existing
tests plus the new characterization tests pass unchanged, both before this
extraction (pinning current behavior) and after (confirming the merge
preserved it). Follow up with
`uv run pytest tests/shared/test_tool_executor_order.py tests/shared/ -v`
for the cross-file and broader shared-layer regression, per the plan's
Phase 3.

## Out of scope

- `ToolExecutor._run_gate_chain` extraction — separate target file,
  separate procedure.
- `tests/shared/test_tool_transport_invoker_merge.py` (new file) — separate
  target file, separate procedure; must be written and passing against the
  pre-merge code before this extraction lands (plan Phase 1).
- `tests/shared/test_tool_transport_invoker.py` — pre-existing, explicitly
  unmodified by this change; read-only regression coverage only.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-192422_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-004517
- Related target files: tool_transport_invoker.py
