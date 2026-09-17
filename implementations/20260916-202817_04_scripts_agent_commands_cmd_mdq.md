## Goal

Add a mandatory `check_preflight()` call in `_execute_mdq()` before its direct `ToolExecutor.execute()` call, denying and reporting (not executing) when policy rejects the tool. (REQ-005; "Add a mandatory `check_preflight(ctx.cfg, tool_name, tool_args)` call in `_execute_mdq()` (`scripts/shared/runtime_tool.py`) before its direct `ToolExecutor.execute()` call, denying and reporting (not executing) when policy rejects the tool.")

## Scope

- Add `check_preflight()` call before the `tools.execute(tool_name, tool_args)` call in `_execute_mdq()`.
- On `PolicyViolationError`, report a denial message instead of executing.

## Assumptions

- `ctx.cfg` is available at this point in `_execute_mdq()` via `self._ctx` (inherited from `MixinBase`).
- `tool_name` and `tool_args` are already passed as parameters to `_execute_mdq()`, so they can be forwarded directly to `check_preflight()`.
- `PolicyViolationError`'s existing message format does not echo tool arguments, so no credential/payload exposure is introduced by surfacing it in the denial output.

## Design decisions

- **Placement**: Insert the `check_preflight()` call immediately after the `ctx.services.tools` availability guard in each caller that invokes `_execute_mdq()`, or within `_execute_mdq()` itself before the `execute()` call. Placing it within `_execute_mdq()` is preferred because it centralizes the gate and ensures all callers benefit automatically.
- **Denial handling**: Catch `PolicyViolationError` and write a denial message using the exception's own text, consistent with how `check_approval()` already surfaces denials via `emit_denied(str(preflight_exc))`.
- **Import**: Both `runtime_tool.py` and `check_preflight()` reside in the `shared` layer, so no new import-layer exception is introduced.

## Alternatives considered

- **Adding the check in `ToolExecutor.execute()` itself**: Rejected — the `shared` layer must not import from `agent` (import-layer contract); the fix must live at the `agent`-layer call site.
- **Adding a wrapper method on `ToolExecutor`**: Rejected — over-engineering; the existing `check_preflight()` function is sufficient.

## Implementation

### Target file

`scripts/shared/runtime_tool.py`

### Procedure

1. Import `PolicyViolationError` from `agent.tool_policy`.
2. In `_execute_mdq()`, after the `tools` availability check (line 64), add a `try/except` block wrapping the `execute()` call:
   ```python
   try:
       agent.tool_policy.check_preflight(self._ctx.cfg, tool_name, tool_args)
   except PolicyViolationError as e:
       self._out.write(f"[DENIED] {tool_name}: {e}")
       return
   ```
3. Move the existing `execute()` call inside the `try` block.

### Method

Modify the `_execute_mdq()` method body and add an import. No new dependencies.

### Details

**Step 1: Add the import**

After line 19 (`from typing import TYPE_CHECKING, Any`), add:
```python
from agent.tool_policy import PolicyViolationError
```

**Step 2: Wrap the execute() call**

Replace lines 64-69 with:
```python
        try:
            agent.tool_policy.check_preflight(self._ctx.cfg, tool_name, tool_args)
        except PolicyViolationError as e:
            self._out.write(f"[DENIED] {tool_name}: {e}")
            return
        result = await tools.execute(tool_name, tool_args)
        if result.is_error:
            self._out.write(f"[mdq] error: {result.output}")
            return
        self._out.write(f"[mdq] {success_label}")
        self._out.write(result.output)
```

Key changes:
- Added `check_preflight()` call before the `execute()` call.
- On `PolicyViolationError`, write a denial message and return early.

## Compatibility considerations

- **No signature change**: The method signature remains unchanged; only internal control flow is modified.
- **Denial message format**: Uses `[DENIED]` prefix, consistent with the existing `[DENIED]` prefix used in `result.output.startswith("[DENIED]")` checks across MDQ subcommand handlers.

## Security considerations

This change closes a confirmed security gap: multiple MDQ subcommands bypass the LLM visibility filter by calling `ToolExecutor.execute()` directly without checking `check_preflight()`.

## Rollback considerations

If the denial message format causes UX issues, revert to silently skipping (the current behavior) — but this would re-open the security gap. A better rollback would be to log the denial rather than display it to the user.

## Validation plan

- Unit test in `tests/agent/commands/test_cmd_mdq.py`: confirm `_cmd_mdq_search()` denies (does not execute) when the tool is absent from `cfg.tool.allowed_tools`.
- Regression: `uv run pytest tests/agent/commands/test_cmd_mdq.py -v` — confirm all pre-existing transport/error-path tests still pass.
- Static analysis: `uv run mypy scripts/shared/runtime_tool.py` — confirm no type regressions.
- Architecture check: `PYTHONPATH=scripts uv run lint-imports` — confirm no new import-layer violations.

## Completion criteria

- `_execute_mdq()` calls `check_preflight()` before executing any tool.
- When a tool is absent from `cfg.tool.allowed_tools`, `_execute_mdq()` reports a denial and returns without executing.
- All pre-existing tests in `tests/agent/commands/test_cmd_mdq.py` continue to pass.

## Out of scope

- Adding `check_preflight()` to `_cmd_diff()` (covered by a separate document).
- Tests for the `/diff` bypass (covered by a separate document).
- Changes to `apply_policy()` (covered by a separate document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `PolicyViolationError` import | Completed | 20260917-114807 | 20260917-114807 |  |
| 2 | Add `check_preflight()` call before `execute()` in `_execute_mdq()` | Completed | 20260917-114807 | 20260917-114807 |  |
| 3 | Add denial regression test | Completed | 20260917-114815 | 20260917-114815 |  |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: scripts/shared/runtime_tool.py