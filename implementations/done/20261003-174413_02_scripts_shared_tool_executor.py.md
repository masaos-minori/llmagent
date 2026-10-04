# Implementation Procedure — `scripts/shared/tool_executor.py`

## Goal

Route `ToolExecutor._raw_execute()` through the shared private helper `_run_precall_gates` (added in `scripts/shared/tool_transport_invoker.py`, row 1), removing its inline gate sequencing while preserving `server_key` resolution from `tool_name` and the async lifecycle await position (`REQ-003`). Combined with row 1, this eliminates the second copy of the gate chain so the live path can no longer diverge from the tested `invoke()` path.

## Scope

- **In-Scope**: Refactor `_raw_execute()` to delegate to `_run_precall_gates`; delete the now-dead `_run_gate_chain`, `_ensure_lifecycle_ready`, and `_resolve_transport` methods whose bodies duplicate the helper; preserve exact observable behavior (`REQ-003`, `REQ-004`).
- **Out-of-Scope**: `_check_startup_mode` (already unused before this refactor — pre-existing, unrelated cleanup); any production caller outside this module; test additions (rows 3–4); gating policy, health states, lifecycle contract, semaphore/retry semantics.

## Assumptions

- `_run_gate_chain` (L89), `_ensure_lifecycle_ready` (L60), and `_resolve_transport` (L72) are each called **only** from `_raw_execute` (rg across `scripts/`: 8 hits = 3 definitions + 1 docstring mention + 3 call sites in `_raw_execute`; 0 hits under `tests/`). After delegation they reach zero callers.
- `_check_startup_mode` (L76) has zero callers today, before this refactor — it is pre-existing dead code and out of scope.
- `_raw_execute()`'s signature `(tool_name: str, args: dict[str, Any]) -> ToolCallResult` and its wrapper `execute()` (L128–134) are unchanged; production entry points are unaffected.
- `"No transport configured"` is referenced nowhere in `tests/` (rg: 0 matches), so normalizing the disabled-server wording on this path does not break an existing assertion.

## Design decisions

- **Minimal `_raw_execute` body.** Replace lines 105–126 with:
  ```python
  async def _raw_execute(self, tool_name, args) -> ToolCallResult:
      """Execute tool via the appropriate transport; applies per-server-key Semaphore when configured."""
      server_key = self._resolver.resolve(tool_name)
      return await self._run_precall_gates(server_key, tool_name, args)
  ```
  `server_key` is still resolved from `tool_name` first (L105); the async `await self._lifecycle.ensure_ready(...)` now occurs inside `_run_precall_gates` in the same relative order (after resolution, before transport/dispatch), so ordering is preserved.
- **Delete the three now-dead methods.** Remove `_run_gate_chain`, `_ensure_lifecycle_ready`, and `_resolve_transport` entirely. Each duplicates the shared helper (health-only; lifecycle wrapper; transport getter) and reaches zero callers after delegation. Leaving them would re-create the duplicate-gate divergence surface this Plan removes. Confirm zero remaining callers with `rg` immediately before deleting (idempotent check — do not re-run expecting a different result).
- **Leave `_check_startup_mode` untouched.** It is pre-existing dead code unrelated to this unification; removing it is out of scope and conflicts with `rules/coding.md` deprecation policy. Flag it separately if desired.
- **Disabled-server normalization (UNK-01).** Previously `_raw_execute()` reached a disabled server via the transport-missing fall-through (`"No transport configured..."`) because `_run_gate_chain` ran only `_check_health`. Through the helper it now returns `"MCP server {key!r} is disabled (startup_mode=none) and cannot be used"`. Outcome is unchanged (`error_type="tool"`, `is_error=True`); the server key stays in the output string, so existing disabled-key assertions still match. This is the one documented deviation from the issue's "no log-message change" constraint.

## Alternatives considered

- **Keep the three methods as dead stubs.** Rejected — they duplicate helper logic and invite future divergence.
- **Remove only the call sites, keeping the method definitions.** Rejected — same duplication; dead weight.
- **Reuse `_ensure_lifecycle_ready` as the helper's lifecycle implementation.** Rejected — the helper already inlines an identical lifecycle block (row 1); no savings.

## Implementation

### Target file

`scripts/shared/tool_executor.py`

### Procedure

1. Edit `_raw_execute()` (lines 99–126): keep the docstring and the `server_key = self._resolver.resolve(tool_name)` line; replace the inline gate block (lines 107–125) with `return await self._run_precall_gates(server_key, tool_name, args)`.
2. Confirm via `rg` that `_run_gate_chain`, `_ensure_lifecycle_ready`, and `_resolve_transport` have zero callers outside their own definitions (they currently have exactly one each, in `_raw_execute`).
3. Delete the three method definitions (`_ensure_lifecycle_ready` L60–70, `_resolve_transport` L72–74, `_run_gate_chain` L89–97).
4. Verify `_check_startup_mode` (L76–87) is left intact and untouched.

### Method

Read-only reference: confirm `self._resolver` (`ToolRouteResolver`) still resolves `tool_name` → `server_key` identically; `_run_precall_gates` (row 1) accepts `(server_key, tool_name, args)`.

### Details

- Preserve English comments/log wording; keep line length ≤ 88 (`ruff format`).
- No new imports needed (`HttpTransport` was only used by `_resolve_transport`'s annotation — after removal, check whether `HttpTransport` is still referenced elsewhere in the file; if it becomes unused, drop that import to keep `ruff` clean. Do not add anything.)
- The helper lives on the base class `ToolTransportInvoker`; inheritance provides it to `ToolExecutor` with no import on this side.

## Compatibility considerations

- `_raw_execute()` and `execute()` signatures/returns unchanged; production callers unaffected.
- Only the disabled-server branch wording changes on this path (UNK-01); every other outcome (healthy, HALF_OPEN trial, unavailable, lifecycle-failed, transport-missing, malformed-response) is byte-for-behaviorally identical.
- Existing `test_tool_executor.py` malformed-response path (`stat_transport_errors == 1`) still holds: `_raw_execute` → `_run_precall_gates` → `_invoke_and_record` → `transport.call` → `TransportError` → `_record_transport_error` is the same chain.

## Security considerations

None introduced. No new I/O or secret handling; error results remain structured (`error_type`) rather than exposing raw exception text.

## Rollback considerations

Contained to this file. Restoring `_raw_execute()`'s original body and re-adding `_run_gate_chain`, `_ensure_lifecycle_ready`, and `_resolve_transport` fully reverts. No config/schema/deploy impact.

## Validation plan

| Target File/Module | Strategy | Tool / Command | Expected |
|---|---|---|---|
| `scripts/shared/tool_executor.py` | Unit: existing `_raw_execute` suite unchanged | `uv run pytest tests/shared/test_tool_executor.py` | All pass; malformed/transport-error outcomes unchanged |
| `scripts/shared/tool_executor.py` | Static: lint/type/security | `uv run ruff check scripts/shared/tool_executor.py`, `uv run mypy scripts/shared/tool_executor.py`, `uv run bandit -r scripts/shared/ -c pyproject.toml` | Zero findings; unused `HttpTransport` import removed if orphaned |

## Completion criteria

- `_raw_execute()` delegates to `_run_precall_gates` with no residual inline gate sequencing.
- `_run_gate_chain`, `_ensure_lifecycle_ready`, and `_resolve_transport` are deleted (zero callers confirmed).
- Every pre-refactor outcome is reproduced identically except the documented disabled-server message normalization.
- `ruff`, `mypy`, and `bandit` report zero findings; no orphaned imports remain.

## Out of scope

`_check_startup_mode` (pre-existing dead code), production callers, and all test changes (rows 3–4). Gating policy and concurrency/lifecycle semantics are unchanged.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | — | — | Delegate `_raw_execute` to shared helper; delete dead gate methods |
| 2 | Add or update tests per Validation plan | Done | — | — | Row 4 covers the invoke-vs-_raw_execute equivalence test |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | — | — | pytest + ruff/mypy/bandit |
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
- **Requirement ID**: `REQ-003`, `REQ-004`
- **Source issue**: `issues/20261003-154614_invoc001_unify-duplicated-mcp-transport-gate-chain.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261003-162605_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-174413
- **Related target files**: `scripts/shared/tool_executor.py`
