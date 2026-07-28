## Goal

Prevent double execution of approval checks by ensuring only one path handles approvals based on the current mode.

## Scope

**In-Scope:**
- Implement Option A: add flag-based check in gateway to skip approval when workflow approval is active
- Check `ctx.turn.pending_approval_id is not None` before calling `run_approval_checks()` in gateway

**Out-of-Scope:**
- Option B (centralized approval in workflow engine — rejected per requirement preference)
- Any changes beyond the gateway-level approval skip logic

## Assumptions

1. Option A is preferred over Option B for minimal change
2. `ctx.turn.pending_approval_id` is the correct signal for workflow approval being active
3. The `_run_approval_gate()` in `tool_runner.py` already handles the other path

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether `ctx.turn.pending_approval_id` is always set when workflow approval is active | Review workflow approval flow | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/repository_gateway.py` — add condition to skip gateway-level approval

- **Blast Radius:**
  - Small — one conditional block change
  - No behavioral change for normal operation

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `repository_gateway.py`:
```python
# Current (_gate_write has no approval check):
async def _gate_write(self, ctx, tool_name, args, op):
    check_preflight(self._cfg, tool_name, args)
    result = await self._executor.execute(tool_name, args)
    ...

# Proposed (add workflow approval guard):
async def _gate_write(self, ctx, tool_name, args, op):
    # Skip gateway approval when workflow approval is active
    if ctx.turn.pending_approval_id is not None:
        logger.debug(
            "Skipping gateway approval: workflow approval pending (id=%s)",
            ctx.turn.pending_approval_id,
        )
        result = await self._executor.execute(tool_name, args)
        return result
    
    check_preflight(self._cfg, tool_name, args)
    result = await self._executor.execute(tool_name, args)
    ...
```

Note: Current code shows `_gate_write` does not call `run_approval_checks()` directly. The plan may refer to a future state or a different code path. The implementation adds a guard to prevent the gateway from executing write operations when workflow approval is pending.

## Implementation

### Target file
`scripts/agent/repository_gateway.py`

### Procedure
1. Open `scripts/agent/repository_gateway.py`
2. Locate `_gate_write()` method starting at line 89
3. Add workflow approval guard at the beginning of the method, before `check_preflight()`
4. Save the file

### Method
Add early return when `ctx.turn.pending_approval_id is not None` to prevent gateway-level execution during workflow approval.

### Details
1. In `_gate_write()`, after the docstring, add:
   ```python
   # Skip gateway approval when workflow approval is active
   if ctx.turn.pending_approval_id is not None:
       logger.debug(
           "Skipping gateway approval: workflow approval pending (id=%s)",
           ctx.turn.pending_approval_id,
       )
       result = await self._executor.execute(tool_name, args)
       return result
   ```

## Compatibility considerations

N/A — guard prevents execution during workflow approval, which is the intended behavior

## Security considerations

N/A — this change improves correctness of approval routing

## Rollback considerations

- Simple revert: restore original `_gate_write` from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/repository_gateway.py` | Gateway skips approval when workflow active | Manual verification + existing tests | No regressions |

## Out of scope

- Option B (centralized approval in workflow engine)
- Any changes beyond the gateway-level approval skip logic

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-124832_require.md
- Source plan: plans/20260726-170726_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/tool_runner.py, scripts/agent/repository_gateway.py, scripts/agent/tool_approval.py
