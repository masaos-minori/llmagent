## Goal

Add clear two-stage explanation (LLM visibility vs runtime routability) to MCP routing documentation, including verification of method names against current codebase.

## Scope

- Verify `RuntimeToolRegistry.llm_tool_definitions()` method name in `shared/runtime_tool_registry.py`
- Verify `LLMTurnRunner._filter_disabled_tool_definitions()` method name in agent module
- Update `docs/04_mcp_03_01_dispatch-and-routing.md` — add two-stage tool resolution section

## Assumptions

1. The existing documentation structure and content are correct; only additions/clarifications are needed
2. The two-stage concept (LLM visibility → runtime routability) accurately reflects the current architecture
3. Operators and developers need this distinction for diagnosis purposes

## Design decisions

- Add a new subsection under ツール呼び出しディスパッチフロー titled "Two-stage tool resolution" rather than modifying existing sections
- Keep the two stages clearly separated with explicit labels (Stage 1, Stage 2)

## Alternatives considered

- Embedding the two-stage explanation within existing sections instead of creating a new subsection
- Adding cross-references from multiple places instead of consolidating into one section

## Implementation

### Target file

- `shared/runtime_tool_registry.py` — read-only verification of method name
- `agent/llm_turn_runner.py` or equivalent — read-only verification of method name
- `docs/04_mcp_03_01_dispatch-and-routing.md` — write access for adding two-stage section

### Procedure

#### Step 1: Verify RuntimeToolRegistry method name

1. Open `shared/runtime_tool_registry.py`
2. Search for method definitions containing `llm_tool_definitions`
3. Confirm the exact method name matches `llm_tool_definitions()`
4. Record any discrepancies for correction in the documentation

#### Step 2: Verify LLMTurnRunner method name

1. Search for `_filter_disabled_tool_definitions` in the agent module
2. Confirm the exact method name matches `_filter_disabled_tool_definitions()`
3. Record any discrepancies for correction in the documentation

#### Step 3: Add two-stage tool resolution section to dispatch-and-routing.md

1. Locate the ツール呼び出しディスパッチフロー section in `docs/04_mcp_03_01_dispatch-and-routing.md`
2. Insert a new subsection titled "Two-stage tool resolution" after the existing flow description
3. Include the following content:

```markdown
## Two-stage tool resolution

Tools go through two distinct resolution stages before being available for execution:

**Stage 1: LLM Visibility** (`RuntimeToolRegistry.llm_tool_definitions()`)

- Tools returned here are visible to the LLM as potential tool calls
- This stage determines what tools the LLM can propose
- Disabled tools may still appear at this stage depending on configuration

**Stage 2: Runtime Routability** (`LLMTurnRunner._filter_disabled_tool_definitions()`)

- After the LLM proposes a tool call, this stage determines whether the tool can actually be routed to its handler
- Disabled tools are filtered out at this stage
- A tool can be LLM-visible but not runtime-routable (e.g., disabled due to config)

**Critical failure mode:** If `RuntimeToolRegistry` is missing entirely, the LLM sees no tools at all, resulting in "Unknown tool" errors even when tools exist in the system.
```

4. Review surrounding context to ensure the addition flows naturally

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- Method names used must match actual codebase to avoid confusion

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added subsection if method names were incorrect
- Ensure no other sections reference the two-stage concept before rollback

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `shared/runtime_tool_registry.py` | Read-only verification | grep for method definition | Method name confirmed |
| `agent/llm_turn_runner.py` | Read-only verification | grep for method definition | Method name confirmed |
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Documentation consistency check | Manual review | Section added correctly |

## Out of scope

- Adding `RuntimeTool.disabled_reason` as a first-class field
- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-123620_require.md
- Source plan: plans/20260722-135916_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-174253
- Related target files: shared/runtime_tool_registry.py, agent/llm_turn_runner.py, docs/04_mcp_03_01_dispatch-and-routing.md
