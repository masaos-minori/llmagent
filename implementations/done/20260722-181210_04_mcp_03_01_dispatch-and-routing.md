## Goal

Verify RuntimeToolRegistry is consistently documented as sole routing authority across all MCP documents.

## Scope

- Review `docs/04_mcp_03_01_dispatch-and-routing.md` — verify RuntimeToolRegistry as sole routing source
- Review `docs/04_mcp_03_02_tool-registry.md` — verify no ToolRegistry descriptions imply routing source

## Assumptions

1. The existing documentation structure and content are correct; only verification is needed
2. RuntimeToolRegistry is already documented as the sole routing authority (confirmed via grep)

## Design decisions

- Read both documents and verify the claims made in the requirement
- If any misleading references are found, add them to the implementation steps

## Alternatives considered

- Skipping this step since it was confirmed via grep
- Creating separate procedures for each document

## Implementation

### Target files

- `docs/04_mcp_03_01_dispatch-and-routing.md`
- `docs/04_mcp_03_02_tool-registry.md`

### Procedure

#### Step 1: Verify dispatch-and-routing.md

1. Open `docs/04_mcp_03_01_dispatch-and-routing.md`
2. Search for mentions of RuntimeToolRegistry
3. Confirm it is documented as the sole routing source
4. Check for any ToolRegistry descriptions that might imply routing authority

#### Step 2: Verify tool-registry.md

1. Open `docs/04_mcp_03_02_tool-registry.md`
2. Search for mentions of ToolRegistry
3. Confirm it is described as drift-detection input only
4. Check for any descriptions implying ToolRegistry is a routing source

#### Step 3: Fix any issues found

If any misleading references are found during verification, add them to the implementation steps for Phase 1 of the parent plan.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The verification ensures consistency across documents

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert any fixes if the original meaning was intentional

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_01_dispatch-and-routing.md` | Verification | grep for routing mentions | Consistency confirmed |
| `docs/04_mcp_03_02_tool-registry.md` | Verification | grep for ToolRegistry mentions | No routing implications found |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124722_require.md
- Source plan: plans/20260722-165616_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-181210
- Related target files: docs/04_mcp_03_01_dispatch-and-routing.md, docs/04_mcp_03_02_tool-registry.md
