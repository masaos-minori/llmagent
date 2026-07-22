## Goal

Add cross-reference link to MCP failure diagnosis document in the dispatch-and-routing.md "Unknown tools fail immediately" paragraph.

## Scope

- Update `docs/04_mcp_03_01_dispatch-and-routing.md` — add cross-reference

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The cross-reference should be added after the ValueError description in the "Unknown tools fail immediately" paragraph
3. The relative path to mcp-failure-diagnosis.md is correct

## Design decisions

- Add a single sentence cross-reference after the ValueError description
- Use relative path for the link to ensure it works regardless of deployment location

## Alternatives considered

- Adding this as a note within existing sections instead of creating a new subsection
- Creating a separate appendix for failure modes

## Implementation

### Target file

- `docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_03_01_dispatch-and-routing.md`
2. Find the "Unknown tools fail immediately" paragraph (around line 67 area)
3. Identify where the cross-reference should be inserted (after the ValueError description)

#### Step 2: Add cross-reference

After the sentence about `ValueError`, add:

```text
For diagnosis guidance, see [MCP Failure Diagnosis](04_mcp_06_09_mcp-failure-diagnosis.md#llm-called-a-tool-but-execution-failed-with-unknown-tool).
```

#### Step 3: Verify cross-reference

Ensure the relative path resolves correctly by checking that the target file exists at the expected location.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new cross-reference provides operators with a direct path to diagnosis workflow

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added cross-reference if the relative path is incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Cross-reference verification | Manual review | Link resolves correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124218_require.md
- Source plan: plans/20260722-145326_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180410
- Related target files: docs/04_mcp_03_01_dispatch-and-routing.md
