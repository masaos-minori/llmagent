## Goal

Clarify that git-mcp is an active example of disabled_reason usage, not a reserved case.

## Scope

- Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — clarify git-mcp as active example

## Assumptions

1. The existing documentation structure and content are correct; only clarifications are needed
2. git-mcp currently implements disabled_reason correctly (confirmed in code)

## Design decisions

- Add a note within the existing disabled_reason section indicating git-mcp is an active example
- Include reference to the git-mcp documentation for details

## Alternatives considered

- Adding this as a separate subsection instead of a note
- Creating a table of examples across all MCP servers

## Implementation

### Target file

- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure

#### Step 1: Locate disabled_reason section

1. Open `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
2. Find the disabled_reason field description

#### Step 2: Add git-mcp clarification

Add the following note near the disabled_reason description:

```markdown
**Active example:** The git-mcp server actively uses `disabled_reason` to indicate why tools are disabled. See [git-mcp availability metadata](./04_mcp_04_05_git.md#availability-metadata) for details on its specific precedence rules.
```

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The clarification helps prevent misunderstanding about disabled_reason being reserved

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added note if git-mcp is later determined not to be an active example

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` | Documentation consistency check | Manual review | Note added correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-123849_require.md
- Source plan: plans/20260722-142109_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-175805
- Related target files: docs/04_mcp_03_06_tool-runtime-availability-metadata.md
