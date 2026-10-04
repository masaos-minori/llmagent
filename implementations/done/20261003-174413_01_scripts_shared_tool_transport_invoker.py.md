# Implementation Procedure — `scripts/shared/tool_transport_invoker.py`

## Goal

Add one private async gate helper `_run_precall_gates` to `ToolTransportInvoker` and route the existing `invoke()` through it, removing `invoke()`'s inline gate block while preserving its public signature and return contract (`REQ-001`, `REQ-002`). This makes the gate chain a single source of truth that `ToolExecutor._raw_execute()` (row 2) will inherit and delegate to.

## Scope

- **In-Scope**: Add `_run_precall_gates` (`REQ-001`); refactor `invoke()` to delegate to it and delete its inline health/disabled/lifecycle/transport/semaphore block (`REQ-002`); preserve exact observable behavior for every gate outcome (`REQ-004`).
- **Out-of-Scope**: `ToolExecutor._raw_execute()` unification belongs to `scripts/shared/tool_executor.py` (row 2); characterization tests belong to rows 3–4; no change to the gating policy itself (which conditions are fatal/warning, health states, lifecycle contract, retry/timeout/semaphore semantics).

## Assumptions

- `invoke()` has no production callers: a repo-wide search finds all 17 `.invoke(` references under `tests/` (in `tests/shared/test_tool_transport_invoker.py`, `test_tool_transport_invoker_merge.py`, `test_tool_executor.py`, `test_tool_executor_routing.py`) and none under `scripts/`. Refactoring its internals does not touch any production entry point.
- Every symbol the helper needs already exists on `ToolTransportInvoker` or at module scope: attributes `_health_registry`, `_server_configs`, `_lifecycle`, `_transports`, `_semaphores`, `_concurrency_limits`; helpers `_check_health` (L128), `_handle_lifecycle_error` (L166), `_invoke_and_record` (L185), `_transport_missing_msg` (L108), `_error_result` (L112); static `_maybe_semaphore`/`_ensure_semaphores`; and module imports `StartupMode` (L19), `_PERMITTED_LIFECYCLE_EXCEPTIONS`, and `ToolCallResult`. No new import is required.
- `"No transport configured"` is defined exactly once (`_transport_missing_msg`, L110) and referenced nowhere else in `scripts/` — the only place the old wording can appear after unification is the live-path branch being normalized (supports UNK-01 resolution).

## Design decisions

- **Helper placement on the base class.** `_run_precall_gates` is a method on `ToolTransportInvoker` (the base), not on `ToolExecutor`. `invoke()` lives on the base and is the tested entry point; `ToolExecutor._raw_execute()` (row 2) subclasses it and must reach the same helper via inheritance. This is what makes the helper a true single source of truth rather than a copy moved to one caller.
- **Helper signature.** `_run_precall_gates(self, server_key: str, tool_name: str, args: dict[str, Any]) -> ToolCallResult`, `async def`. It takes the already-resolved `server_key` (row 2 resolves it from `tool_name` before calling), plus `tool_name`/`args` for the final dispatch.
- **Return contract reconciliation ("or `None` when all gates pass", `REQ-001`).** `REQ-001` lists transport-resolution and semaphore-setup *inside* the helper, yet their outputs (`HttpTransport`, `Semaphore`) are only consumable by the dispatch call. If the helper returned `None` on success and left dispatch to the caller, the caller would have to re-resolve transport + semaphore and re-invoke — re-introducing the very duplication this unifies. Therefore the helper runs `_invoke_and_record` internally and returns its `ToolCallResult`; it never actually returns `None`. Observable behavior is identical to the pre-refactor `invoke()` for every path (`REQ-004`), which is the binding constraint.
- **Disabled-server guard uses `invoke()`'s exact condition.** The helper rejects a disabled server with `if cfg is not None and cfg.startup_mode == StartupMode.NONE:` returning the `"disabled (startup_mode=none)"` message — NOT `_check_startup_mode`'s stricter `cfg is None` rejection (that method is not used by either current caller). With `cfg is None` the guard is skipped and execution falls through to transport-resolution, reproducing the pre-refactor `"No transport configured"` result identically on both paths.
- **Gate order preserved.** health → disabled-server → lifecycle(await) → transport-resolution → semaphore-setup → `_invoke_and_record`. The async `await self._lifecycle.ensure_ready(...)` stays in the same relative position (after disabled, before transport) as in `invoke()`.
- **Message normalization scoped to the disabled branch only.** On the previously-live `_raw_execute()` path the disabled-server text changes from `"No transport configured..."` to `"MCP server {key!r} is disabled (startup_mode=none) and cannot be used"`. Outcome is unchanged (`error_type="tool"`, `is_error=True`). This is the one intentional deviation recorded as UNK-01 in the Plan; it touches only the disabled-server branch.

## Alternatives considered

- **Return `(ToolCallResult | None, HttpTransport | None, Semaphore | None)` and dispatch in the caller.** Rejected: 3-tuple return leaks transport/semaphore internals and the caller still needs `tool_name`/`args`; no duplication saved.
- **Helper returns error-or-`None`; caller re-resolves transport + semaphore and calls `_invoke_and_record`.** Rejected: duplicates the transport-resolution + semaphore-setup + dispatch sequencing in *both* callers, recreating the split-brain divergence surface the Plan exists to remove.
- **Place the helper on `ToolExecutor` instead of the base.** Rejected: `invoke()` is on the base and is the exercised entry point; the helper must live where `invoke()` lives so both callers converge on one copy.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. Add `async def _run_precall_gates(self, server_key, tool_name, args) -> ToolCallResult` immediately after `invoke()` (or adjacent to the other private gate helpers). Body mirrors the current `invoke()` lines 208–235 in order:
   - `if err := self._check_health(server_key): return err`
   - `cfg = self._server_configs.get(server_key)` then `if cfg is not None and cfg.startup_mode == StartupMode.NONE:` → build the `"disabled (startup_mode=none)"` message, `logger.warning(msg)`, `return self._error_result(server_key, msg, error_type="tool")`
   - `if self._lifecycle is not None:` try `await self._lifecycle.ensure_ready(server_key)`; on exception, `if isinstance(e, _PERMITTED_LIFECYCLE_EXCEPTIONS): return self._handle_lifecycle_error(server_key, e)` else `raise`
   - `transport = self._transports.get(server_key)`; `if transport is None:` → `msg = self._transport_missing_msg(server_key)`, `logger.error(msg)`, `return self._error_result(server_key, msg, error_type="tool")`
   - `self._ensure_semaphores()`; `sem = (self._semaphores or {}).get(server_key)`
   - `return await self._invoke_and_record(server_key, transport, tool_name, args, sem)`
2. Replace `invoke()`'s body (lines 208–235) with a two-line delegation that keeps the docstring/signature/return type:
   ```python
   async def invoke(self, server_key, tool_name, args) -> ToolCallResult:
       """Invoke tool via transport; applies health check, lifecycle, semaphore, and recording."""
       return await self._run_precall_gates(server_key, tool_name, args)
   ```
   Delete the now-dead inline block (lines 208–235) wholesale — do not leave a commented copy.
3. Confirm no other method in the file referenced the deleted inline logic; the helper is now the sole owner of the gate chain.

### Method

Read-only reference while editing: confirm `_PERMITTED_LIFECYCLE_EXCEPTIONS` and `StartupMode` remain imported (they are, at module scope) and that `_invoke_and_record`'s parameter order matches the call site above.

### Details

- Preserve the `# REQ-004: reject disabled servers at the shared invocation boundary` intent as a concise comment on the helper's disabled branch.
- Do not introduce new parameters, defaults, or type annotations beyond those shown; keep line length ≤ 88 (`ruff format`).
- The helper is private (`_` prefix); it is not part of any public contract and needs no export.

## Compatibility considerations

- `invoke()`'s public signature, docstring, and `-> ToolCallResult` return type are unchanged; test callers (all under `tests/shared/`) are unaffected by an internal refactor.
- The disabled-server message normalizes on the live path (UNK-01). Existing `tests/shared/test_tool_executor.py:549` drives `ex.invoke("disabled_server", ...)` directly; `invoke()` already returned the `"disabled"` message there, so that assertion is unchanged. Only `_raw_execute()`'s former fall-through wording changes (covered by row 2).
- No `docs/*.md` describes the gate order (Plan Documentation Impact = N/A); verify none appears post-change and update only if it drifts.

## Security considerations

None introduced. No new I/O, secrets, or external input handling; log wording changes only in the documented disabled-server branch. Error results continue to carry structured `error_type` rather than raw exception text to callers.

## Rollback considerations

Contained to this file. Reverting the addition of `_run_precall_gates` and restoring the original `invoke()` body (lines 207–236) fully restores pre-refactor behavior. No data, config, or schema impact; no deploy.sh change.

## Validation plan

| Target / Module | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `scripts/shared/tool_transport_invoker.py` | Unit: existing `invoke()` suites unchanged | `uv run pytest tests/shared/test_tool_transport_invoker.py tests/shared/test_tool_transport_invoker_merge.py` | All pass; no outcome changed |
| `scripts/shared/tool_transport_invoker.py` | Static: lint/type/security | `uv run ruff check scripts/shared/tool_transport_invoker.py`, `uv run mypy scripts/shared/tool_transport_invoker.py`, `uv run bandit -r scripts/shared/ -c pyproject.toml` | Zero findings (bandit baseline clean: 455 lines, 0 issues) |

## Completion criteria

- `_run_precall_gates` exists as the sole gate-chain implementation and `invoke()` delegates to it with no residual inline gate block remaining in `invoke()`.
- `invoke()`'s signature and return type are byte-for-behaviorally identical to pre-refactor.
- Every pre-refactor gate outcome (healthy, HALF_OPEN trial, unavailable, disabled, lifecycle-failed, transport-missing) returns the same `ToolCallResult`/raises the same exceptions as before, including `error_type` and ordering.
- `ruff`, `mypy`, and `bandit` report zero findings on the file.

## Out of scope

`ToolExecutor._raw_execute()` unification (`scripts/shared/tool_executor.py`) is row 2. Characterization/equivalence tests (rows 3–4) are out of scope here. The gating policy, health states, lifecycle contract, and semaphore/retry semantics are unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `_run_precall_gates` helper to `ToolTransportInvoker` (`REQ-001`) | Done | — | — | Gate chain single source of truth |
| 2 | Refactor `invoke()` to delegate to the helper, delete inline block (`REQ-002`) | Done | — | — | Preserve signature/return type |
| 3 | Run validation sequence (`rules/toolchain.md`) (`REQ-004`) | Done | — | — | pytest + ruff/mypy/bandit |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | — | — | N/A: no docs describe gate order |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-004`
- **Source issue**: `issues/20261003-154614_invoc001_unify-duplicated-mcp-transport-gate-chain.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261003-162605_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-174413
- **Related target files**: `scripts/shared/tool_transport_invoker.py`
