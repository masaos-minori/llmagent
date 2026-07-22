## Goal

Add two-stage tool resolution section to MCP routing documentation explaining LLM visibility vs runtime routability distinction.

## Scope

- Update `docs/04_mcp_03_01_dispatch-and-routing.md` — add two-stage tool resolution section under ツール呼び出しディスパッチフロー

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

- `docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_03_01_dispatch-and-routing.md`
2. Find the ツール呼び出しディスパッチフロー section heading
3. Identify where the existing flow description ends and the new section should begin

#### Step 2: Add two-stage tool resolution section

Insert the following markdown after the existing ツール呼び出しディスパッチフロー content:

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

#### Step 3: Verify cross-references

1. Check that any references to tool resolution in the existing document align with the new two-stage model
2. Update any outdated descriptions if they contradict the two-stage concept

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- Method names used must match actual codebase

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added subsection if method names were incorrect or the two-stage model is inaccurate

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Documentation consistency check | Manual review | Section added correctly, flows naturally |

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
- Generated at: 20260722-174448
- Related target files: docs/04_mcp_03_01_dispatch-and-routing.md
