## Goal

Fix misleading section heading in shared document that incorrectly implies ToolRegistry is a routing authority.

## Scope

- Update `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` — fix misleading heading

## Assumptions

1. The existing documentation structure and content are correct; only the heading needs correction
2. The content below the heading correctly distinguishes the roles, but the heading itself is misleading

## Design decisions

- Change the heading from "ルーティングの正本" (source of truth for routing) to "ツール所有権とルーティング" (tool ownership and routing)
- This clarifies that ToolRegistry is about tool ownership, not routing authority

## Alternatives considered

- Removing the heading entirely
- Adding a note within the section instead of changing the heading

## Implementation

### Target file

- `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure

#### Step 1: Locate the misleading heading

1. Open `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
2. Find line 75 (the section heading)

#### Step 2: Replace the heading

Change from:

```markdown
## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (ルーティングの正本)
```

To:

```markdown
## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation` (ツール所有権とルーティング)
```

#### Step 3: Verify cross-references

If there are any cross-references to this section elsewhere in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The corrected heading helps prevent misunderstanding about ToolRegistry's role

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the heading change if the original meaning was intentional

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | Documentation consistency check | Manual review | Heading corrected correctly |

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
- Generated at: 20260722-181123
- Related target files: docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md
