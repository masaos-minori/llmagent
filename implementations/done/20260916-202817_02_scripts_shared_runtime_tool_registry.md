## Goal

Rewrite `RuntimeToolRegistry.apply_policy()` to recompute LLM-facing tool visibility from an immutable discovery-time baseline plus the current policy on every call (so a disabled tool becomes re-enabled the moment a later policy allows it again), and apply that recomputation as a single atomic registry replacement. (REQ-002, REQ-003; "Rewrite `apply_policy()` to recompute from the immutable base field and apply the result via one atomic dict-reference swap")

## Scope

- Rewrite `apply_policy()`'s per-tool formula: change from `enabled_for_llm = enabled and tool.enabled_for_llm` (cumulative AND with current mutable state) to `enabled_for_llm = tool.llm_visibility_base and (not allowed_tools or name in allowed_tools)` (recompute from immutable base).
- Change mutation strategy from per-entry in-place dict reassignment to building a complete new `{name: RuntimeTool}` mapping and swapping the registry's internal reference in a single assignment (atomic registry replacement).

## Assumptions

- The `llm_visibility_base` field exists on `RuntimeTool` (covered by a separate document — this row depends on its completion).
- `dataclasses.replace()` preserves any field not explicitly passed, so the immutable base field carries forward unchanged automatically.
- The `tier_map` parameter maps tool name to `AgentSafetyTier`; tools absent from `tier_map` keep their current tier.
- An empty `allowed_tools` sequence means all tools remain allowed (mirrors `agent.config_dataclasses.ToolConfig.allowed_tools`'s documented convention).

## Design decisions

- **Recompute-from-base**: The left-hand operand of the AND changes from `tool.enabled_for_llm` (current mutable state) to `tool.llm_visibility_base` (immutable discovery-time value). This ensures a tool re-included in `allowed_tools` becomes visible again regardless of prior reloads.
- **Atomic swap**: Build a complete new `dict[str, RuntimeTool]` locally, then assign `self._tools = new_tools` once after the loop completes. This makes the "old-or-new, never partial" guarantee structural rather than relying on the absence of `await` as an implicit guarantee.

## Alternatives considered

- **Per-entry reassignment into live dict** (current approach): Rejected — does not provide atomicity guarantee; concurrent readers could observe torn intermediate state if an `await` is introduced later.
- **New `RuntimeToolRegistry` instance**: Rejected — would break existing callers (`config_reload.py`) that hold references to the same registry instance; a dict-swap within the same instance is the minimal change.
- **Lock-based synchronization**: Rejected — overkill for a single-threaded asyncio process today; a dict-swap is sufficient and simpler.

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py`

### Procedure

1. Before the `for` loop in `apply_policy()`, create a local variable for the new tool mapping:
   ```python
   new_tools: dict[str, RuntimeTool] = {}
   ```
2. Replace the per-entry mutation inside the loop:
   - Remove: `self._tools[name] = dataclasses.replace(tool, agent_safety_tier=tier, enabled_for_llm=enabled and tool.enabled_for_llm)`
   - Add: Build each updated tool with `dataclasses.replace()`, storing in `new_tools`:
     ```python
     new_enabled = tool.llm_visibility_base and (not allowed_tools or name in allowed_tools)
     new_tools[name] = dataclasses.replace(
         tool,
         agent_safety_tier=tier,
         enabled_for_llm=new_enabled,
     )
     ```
3. After the loop, replace the entire `_tools` dict in one assignment:
   ```python
   self._tools = new_tools
   ```

### Method

Modify only the `apply_policy()` method body. No new imports or dependencies.

### Details

**Step 1: Create the new mapping**

At line 155 (before `for name, tool in list(self._tools.items()):`), add:
```python
        new_tools: dict[str, RuntimeTool] = {}
```

**Step 2: Replace per-entry mutation**

Replace lines 156-163 with:
```python
        for name, tool in list(self._tools.items()):
            tier = tier_map.get(name, tool.agent_safety_tier)
            new_enabled = tool.llm_visibility_base and (not allowed_tools or name in allowed_tools)
            new_tools[name] = dataclasses.replace(
                tool,
                agent_safety_tier=tier,
                enabled_for_llm=new_enabled,
            )
```

Key changes:
- `enabled_for_llm` now uses `tool.llm_visibility_base` instead of `tool.enabled_for_llm` as the left-hand operand.
- The computed `new_enabled` is stored in a local variable for clarity.

**Step 3: Atomic swap**

After the loop (after the previous block), add:
```python
        self._tools = new_tools
```

This replaces the entire `_tools` dict in one assignment, making the "old-or-new, never partial" invariant structural.

## Compatibility considerations

- **Call-site compatibility**: `apply_policy()`'s signature (`tier_map`, `allowed_tools`) is unchanged — no caller modification needed.
- **`dataclasses.replace()` behavior**: Since `llm_visibility_base` is not explicitly passed in the `replace()` call, it will carry forward unchanged — this is the desired behavior (immutable base).
- **Dict identity**: External code holding references to `self._tools` before calling `apply_policy()` will see the old dict after the call — this is expected and correct (the old dict is replaced atomically).

## Security considerations

No security impact. This change strengthens the fail-closed property of the policy system by ensuring disabled tools can be re-enabled, preventing permanent lockout due to cumulative mutation.

## Rollback considerations

If the atomic swap causes issues (e.g., external code holds stale references to `self._tools`), revert to per-entry reassignment. However, the atomic swap is the safer design and should not cause regressions since no existing code relies on observing the intermediate state during `apply_policy()`.

## Validation plan

- Unit test in `tests/shared/test_runtime_tool_registry.py`: disable-then-re-enable sequence — assert `enabled_for_llm` returns to `True` after a second `apply_policy()` call with the tool back in `allowed_tools`.
- Unit test in `tests/shared/test_runtime_tool_registry.py`: atomic single-swap assertion — verify the `_tools` mapping reference changes identity exactly once per call.
- Regression: `uv run pytest tests/agent/services/test_config_reload.py -v` — confirm the existing E2E test still passes (single `apply_policy()` call, unaffected by reversibility fix).
- Static analysis: `uv run mypy scripts/shared/runtime_tool_registry.py` — confirm no type regressions.

## Completion criteria

- `apply_policy()` computes `enabled_for_llm` from `tool.llm_visibility_base` and the complete current policy on every call.
- A tool disabled by one `apply_policy()` call becomes re-enabled by a subsequent call when included in `allowed_tools`.
- The registry's internal tool mapping is replaced as a single atomic object (one dict identity change per call).
- All pre-existing `apply_policy` tests continue to pass.

## Out of scope

- Adding the `llm_visibility_base` field to `RuntimeTool` (covered by a separate document).
- Tests for the immutable base field default/override/preservation (covered by a separate document).
- Changes to `check_preflight()` call sites (covered by separate documents).

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite `apply_policy()` formula to use immutable base field | Completed | 20260917-112328 | 20260917-112328 |  |
| 2 | Change mutation strategy to atomic dict swap | Completed | 20260917-112334 | 20260917-112334 |  |
| 3 | Add disable-then-re-enable regression test | Completed | 20260917-112540 | 20260917-112540 |  |
| 4 | Add atomic-swap regression test | Completed | 20260917-112540 | 20260917-112540 |  |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260914-103138_mcpagent04_runtime-policy-reload-reversibility.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-122227_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260916-202817
- **Related target files**: scripts/shared/runtime_tool_registry.py