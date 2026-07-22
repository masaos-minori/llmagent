## Goal

Add metadata update paths section documenting that both /v1/tools and config/agent.toml must be updated independently.

## Scope

- Update `docs/04_mcp_06_14_new-tool-registration-procedure.md` — add metadata update paths section

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The new section should reference the dispatch-and-routing.md documentation about DAG scheduling

## Design decisions

- Add a new top-level section titled "Metadata update paths" after the existing registration steps
- Document the two independent update paths clearly

## Alternatives considered

- Adding this as a note within existing steps instead of creating a new section
- Creating a separate appendix for metadata updates

## Implementation

### Target file

- `docs/04_mcp_06_14_new-tool-registration-procedure.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_06_14_new-tool-registration-procedure.md`
2. Find the end of the existing registration steps
3. Identify where the metadata update paths section should be inserted

#### Step 2: Add metadata update paths section

Insert the following markdown after the existing registration steps:

```markdown
## Metadata update paths

When updating tool metadata, you must understand that there are two independent update paths:

### Path 1: /v1/tools metadata (runtime availability)

Updating `/v1/tools` response affects:
- What tools are visible to the LLM via `/v1/tools`
- Runtime routing decisions made by `RuntimeToolRegistry`
- LLM visibility (enabled/disabled state)

This path is controlled by the MCP server's `/v1/tools` endpoint implementation.

### Path 2: config/agent.toml metadata (DAG scheduling)

Updating `config/agent.toml` tool definitions affects:
- DAG scheduling metadata (`requires_serial`, `resource_scope`, `is_write`, etc.)
- How tools execute in the DAG context
- Shell-specific serial behavior

This path is controlled by the agent configuration file.

### Important: Independent updates

These two update paths are **independent**. Updating `/v1/tools` metadata alone does not change DAG scheduling behavior. If you need to change both runtime availability AND DAG scheduling metadata, you must update both `/v1/tools` and `config/agent.toml` separately.

See [dispatch-and-routing.md](./04_mcp_03_01_dispatch-and-routing.md#data-source-for-dag-scheduling) for details on the data source distinction.
```

#### Step 3: Cross-reference the DAG scheduling section

Ensure the section references the DAG scheduling data source section in dispatch-and-routing.md so readers can understand the full picture.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section complements existing registration steps without conflicting

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if the metadata update paths description is incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_14_new-tool-registration-procedure.md` | Documentation consistency check | Manual review | Section added correctly, references accurate |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124113_require.md
- Source plan: plans/20260722-144242_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180209
- Related target files: docs/04_mcp_06_14_new-tool-registration-procedure.md
