## Goal

Close the silent overlay-only write gap on durable-dedup store **initialization** failure: when `_dedup_context()` returns `(None, None)`, `dispatch_tool()` currently skips the whole dedup block for every tool (including non-retryable ones) and returns a successful overlay-only write with `dedup_state=""`. Reconcile that init-failure path with the existing store-**lookup**-error asymmetry so non-retryable tools fail closed and retryable tools degrade (`REQ-001`/`REQ-002`/`REQ-003`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- The Plan's open failure mechanism is approach (a) mirror-the-lookup-asymmetry or approach (b) fail-fast-at-startup (mutually exclusive, `UNK-01`). This document implements whichever is chosen; approach (a) is recommended.
- Retryability comes from `retry_class()` in `scripts/shared/mcp_dedup.py` (`L128-132`), which defaults unknown tools to `non_retryable`; shell/delete/etc. are absent from the default config's retry map and therefore fail closed.
- `DispatchResult` shape (`output`, `is_error`, `error_type`, `dedup_state`) is a broad public runtime contract (imported by all ten server modules plus `server.py`/`formatters.py`); preserve it.

## Design decisions
- **Approach (a) — mirror the lookup-failure asymmetry.** In `dispatch_tool`, when `_dedup_context()` yields `(None, None)` (init failure or already-disabled), classify the tool with `retry_class`: non-retryable tools return `DispatchResult(is_error=True, error_type="dedup_store_error", dedup_state="store_error")` (fail closed); retryable tools set `dedup_state="store_error"` and proceed overlay-only. This makes the init-failure path byte-for-byte equivalent to the lookup-failure path at `L309-323`.
- **Classify defensively.** Call `retry_class(name)` (it reloads config when given `None`); wrap it and, on any exception (config load itself failed), treat the tool as `non_retryable` (fail closed) — matching `retry_class`'s own unknown→`non_retryable` default.

## Alternatives considered
- **Approach (b) fail-fast at startup:** surface the init failure so the process refuses to serve. Higher blast radius — non-retryable *and* retryable tools lose dedup, and startup validation must be added. Only choose if the owner wants a broken dedup store to be a hard startup error (`UNK-01`). Recommended against in favor of (a), which preserves the documented fail-open intent for retries and closes the gap with minimal change.
- **Leave the block unchanged:** rejected — non-retryable tools still succeed silently with `dedup_state=""`.

## Implementation
### Target file
`scripts/mcp_servers/dispatch.py`

### Procedure
1. Locate the caller block in `dispatch_tool()`: `store, config = _dedup_context()` at `L304`, guarded by `if store is not None and config is not None:` at `L305`.
2. Add an `else` branch to the `L305` guard handling the `(None, None)` init-failure / disabled case (`REQ-001`/`REQ-002`).
3. Under approach (a): classify with `retry_class`; non-retryable tools `return` a `dedup_store_error` `DispatchResult` (fail closed), retryable tools set `dedup_state="store_error"` and fall through to tool execution at `L414`.
4. Keep the lookup-failure asymmetry at `L309-323` untouched so the two paths stay identical (`REQ-003`).

### Method
Edit the `if store is not None and config is not None:` guard (`L305`) to add an aligned `else:` clause; do not reorder any startup check or change exit codes.

### Details
Current (approach (a) baseline), `dispatch_tool()` `L304-305`:
```python
        store, config = _dedup_context()
        if store is not None and config is not None:
```
Add an `else` after the existing `if store is not None` body (which closes at `L412`, immediately before `try:\n    result = await handler(args)` at `L414`):
```python
        else:
            # Init failure / disabled: reconcile with the lookup-failure
            # asymmetry (REQ-001/REQ-002/REQ-003). Non-retryable tools fail
            # closed; retryable tools degrade to overlay-only store_error.
            try:
                is_retryable = retry_class(name) == "retryable"
            except Exception:  # noqa: BLE001 -- config load failed too; default closed
                is_retryable = False
            if not is_retryable:
                return DispatchResult(
                    output=(
                        f"Dedup store unavailable; call to tool {name!r} refused"
                    ),
                    is_error=True,
                    error_type="dedup_store_error",
                    dedup_state="store_error",
                )
            dedup_state = "store_error"
```
Under approach (b), instead raise inside `_dedup_context()` where `_dedup_disabled` is set (`L185-193`) so the process fails to start; do not add the `else` branch above.

**Implementer decision (flag; do not silently resolve):** apply this `else` to a *fresh* init failure only, or also to subsequent calls while `_dedup_disabled` stays `True` (the observable defect is identical). Uniform application is simplest and matches `REQ-001`; narrowing is a scope/behavior change — record the choice.

### Companion test files
- `tests/mcp_servers/test_mcp_dispatch.py`
  - Procedure: extend with a parametrized assertion over a retryable and a non-retryable tool that forces a store-**initialization** failure (raise in `open_dedup_store()` or `load_dedup_config()`) and asserts the `REQ-001`/`REQ-002` behavior; mirror the existing lookup-failure test `test_store_error_retryable_proceeds_non_retryable_fails_closed` (`tests/mcp_servers/test_mcp_dispatch.py` `L513-544`).
  - Validation: the new assertion fails on current code (non-retryable tool currently returns a successful overlay-only write with `dedup_state=""`) and passes after the fix.

## Compatibility considerations
- `DispatchResult` keeps its shape; `error_type="dedup_store_error"` and `dedup_state="store_error"` reuse the lookup-path values for a consistent downstream marker.
- Non-retryable tools now return an error where they previously returned a successful overlay-only write — the intended change (`REQ-001`). Retryable tools keep the documented fail-open degradation.

## Security considerations
- Closing non-retryable write-protection tools (shell/delete/etc.) on store failure restores the durable idempotency/write-protection guarantee the overlay-only path bypassed. Under approach (a) the tool handler runs only after the guard (`L414`), so a fail-closed refusal does not execute the handler.

## Rollback considerations
- Revert the commit; the change is confined to `dispatch_tool()`'s init-failure branch.

## Validation plan
- `uv run pytest tests/mcp_servers/test_mcp_dispatch.py` — new and existing tests pass.
- `uv run pytest tests/mcp_servers` — new and existing tests pass.
- `uv run ruff check scripts/ tests/` — clean.
- Baseline (Step 5): radon rates `dispatch.py` helpers A(1); `bandit -ll` reports no high/medium findings; `lint-imports` 6 kept / 0 broken.

## Completion criteria
- `REQ-001`: a non-retryable tool with a store that fails to initialize returns `error_type="dedup_store_error"` (approach a) and never returns a successful overlay-only write with `dedup_state=""`.
- `REQ-002`: a retryable tool degrades to `dedup_state="store_error"` and proceeds overlay-only.
- `REQ-003`: the init-failure asymmetry matches the lookup-failure path (`L309-323`).
- `REQ-004`: the extended `test_mcp_dispatch.py` fails on current code and passes after the fix.

## Out of Scope
- Approach (b) startup-validation additions — only if the owner selects approach (b).
- Changing which tools are classified retryable/non-retryable (`models.py` / dedup config) — out of scope.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: `REQ-001` (init-failure fail-closed for non-retryable), `REQ-002` (retryable degrade), `REQ-003` (asymmetry parity with lookup path)
- **Source issue**: `issues/20261107-132027_mcpstartup002_dedup-init-fail-open.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261107-213831_mcpstartup002_dedup-init-fail-open.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261108-082130
- **Related target files**: `scripts/mcp_servers/dispatch.py`, `tests/mcp_servers/test_mcp_dispatch.py`
