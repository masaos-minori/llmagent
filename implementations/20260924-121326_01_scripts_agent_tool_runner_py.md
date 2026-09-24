# Implementation Procedure: Resolve Gateway-Bypass Gap in tool_runner.py

## Goal

Resolve the gateway-bypass gap in `scripts/agent/tool_runner.py` where `tools.execute()` is called directly without going through the preflight gate when `ctx.services_required.gateway is None`, per REQ-03.

## Scope

- Modify `scripts/agent/tool_runner.py`
- Add a preflight check in the `else` branch (line 118-119) before calling `tools.execute()`
- Document why this path is safe OR fix it — Option A (fix) must be attempted first since it is a security concern

## Assumptions

- The 4-call-site count stated in the plan is accurate — confirmed by repository evidence below
- The `repository_gateway.py` line 114 preflight gate is the primary write enforcement boundary
- The `tool_runner.py` gateway-bypass gap (when `gateway is None`) represents a real security concern requiring resolution
- dry_run operations are intentionally preflight-exempt because they are read-only previews
- READ operations are intentionally preflight-exempt per design (direct passthrough for read-only tools)
- Three distinct gateway-bypass patterns exist: Pattern 1 (cmd_mdq.py, cmd_context.py) has preflight but bypasses gateway; Pattern 2 (tool_runner.py) lacks both preflight and gateway protection

## Design decisions

- **Priority 1**: Attempt Option A (fix) first — add a preflight check in the `else` branch before calling `tools.execute()`. This is a security concern and must be addressed.
- **Priority 2**: Standardize Patterns 1 and 2 to route all write/delete/API-write operations through the gateway for consistent enforcement.
- The fix must use `classify_operation_type()` from `tool_policy.py` to determine whether the operation requires preflight gating.
- READ operations should remain exempt (per REQ-09).

## Alternatives considered

- **Option B (document as safe)**: Document why this path is safe (e.g., gateway is always configured in production, or no tools are available when gateway is None). Not appropriate as first option — this is a confirmed security concern.
- **Require gateway configuration**: Force `gateway` to always be set during AgentContext initialization. Would require changes to the AgentContext lifecycle.

## Implementation

### Target file

`scripts/agent/tool_runner.py`

### Procedure

1. Read the current `tool_runner.py` content around lines 116-119
2. Identify the exact location of the `else` branch (line 118-119)
3. Add a preflight check before `tools.execute()` in the `else` branch
4. Ensure READ operations remain exempt (per REQ-09)
5. Verify the fix with existing tests

### Method

**Step 1: Locate the gateway-bypass gap**

Current code at lines 116-119:
```python
if ctx.services_required.gateway is not None:
    result = await ctx.services_required.gateway.execute(ctx, name, args)
else:
    result = await ctx.services_required.tools.execute(name, args)
```

**Step 2: Add preflight check in the else branch**

Replace the above block with:
```python
if ctx.services_required.gateway is not None:
    result = await ctx.services_required.gateway.execute(ctx, name, args)
else:
    # Priority 1: Add preflight check before direct tool execution
    # When gateway is None, we still need to enforce the preflight gate
    # for write/delete/API-write operations
    from agent.tool_policy import check_preflight, classify_operation_type
    from agent.tool_enums import OperationType
    
    op = classify_operation_type(name, ctx.services_required.runtime_tools)
    if op != OperationType.READ:
        try:
            check_preflight(ctx.cfg, name, args)
        except PolicyViolationError as exc:
            logger.warning("tool_runner.policy_denied tool=%r reason=%s", name, exc)
            raise  # Re-raise to prevent unauthorized execution
    
    result = await ctx.services_required.tools.execute(name, args)
```

**Step 3: Ensure imports are present**

Verify that the following imports are present at the top of the file:
- `from agent.tool_policy import check_preflight, classify_operation_type, PolicyViolationError`
- `from agent.tool_enums import OperationType`
- `import logging` (for `logger.warning`)

If any are missing, add them alongside existing imports from `agent.tool_policy`.

### Details

- **REQ-03**: Gateway-bypass gaps must be resolved across all execution patterns (either fixed or documented as safe), including `tool_runner.py`, `cmd_mdq.py`, and `cmd_context.py`
- **AC-03**: Gateway-bypass gaps are resolved across all execution patterns (either fixed or documented as safe)
- **T-04**: Gateway-bypass paths are either fixed or documented as safe across all execution patterns

## Compatibility considerations

- The change adds a preflight check that was previously absent — this may cause previously-uncaught violations to now fail
- READ operations remain exempt (no change to their behavior)
- The fix is backward-compatible: if the gateway is configured, behavior is unchanged

## Security considerations

- **Critical**: This is a security fix — the gateway-bypass gap allows unauthorized tool access when the gateway is not configured
- The preflight check uses the same logic as `repository_gateway.py:114`
- If the check fails, the operation is denied with a warning logged

## Rollback considerations

- To revert, restore the original `else` branch from git history
- Reverting would reintroduce the security gap — not recommended without a compensating control

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|--------|-----------------|----------------|-----------------|
| `scripts/agent/tool_runner.py` | Unit: verify gateway-bypass gap resolved | `uv run pytest tests/agent/test_repository_gateway.py -v` | No new failures |
| Preflight gate test | Unit: new test passes | `uv run pytest tests/agent/ -k preflight -v` | All new tests pass |
| Full test suite | Regression: existing tests pass | `uv run pytest` | All existing tests pass |

## Completion criteria

- [ ] `tool_runner.py` contains a preflight check in the `else` branch (line 118-119 area)
- [ ] The preflight check uses `check_preflight()` and `classify_operation_type()` from `tool_policy.py`
- [ ] READ operations remain exempt (no preflight check for `OperationType.READ`)
- [ ] Existing tests pass after the change
- [ ] New test confirms the gateway-bypass gap is resolved (T-04)

## Out of scope

- Modifying `check_preflight()` function logic itself (out of scope per plan)
- Adding new gate conditions beyond what already exists
- Changes to MCP server preflight behavior
- Changes to Event Bus preflight behavior
- Standardizing Patterns 1 and 2 to route through gateway (Phase 2 Step 2.3 — separate document)

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
- **Requirement ID**: REQ-03
- **Source issue**: issues/20260924-054349_req003_preflight-gate-additions-not-validated-all-execution-paths.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260924-070936_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260924-121326
- **Related target files**: scripts/agent/tool_runner.py
