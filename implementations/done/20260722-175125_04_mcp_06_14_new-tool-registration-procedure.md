## Goal

Add /v1/tools requirements section to the new tool registration procedure document, referencing the updated endpoints-and-transport.md.

## Scope

- Update `docs/04_mcp_06_14_new-tool-registration-procedure.md` — add /v1/tools requirements section

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The new section should reference the full field example from endpoints-and-transport.md

## Design decisions

- Add a new top-level section titled "/v1/tools Requirements" before the existing registration steps
- Document both required and optional fields with references to the endpoints-and-transport.md example

## Alternatives considered

- Adding this as a note within existing steps instead of creating a new section
- Creating a separate appendix for field requirements

## Implementation

### Target file

- `docs/04_mcp_06_14_new-tool-registration-procedure.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_06_14_new-tool-registration-procedure.md`
2. Find the beginning of the tool registration steps
3. Identify where the /v1/tools requirements section should be inserted

#### Step 2: Add /v1/tools requirements section

Insert the following markdown before the existing registration steps:

```markdown
## /v1/tools Requirements

Before registering a new tool, ensure your MCP server responds to `/v1/tools` requests with the correct format. See [endpoints-and-transport.md](./04_mcp_02_01_endpoints-and-transport.md) for the complete field specification.

### Required fields

- `name`: Unique tool identifier
- `description`: Human-readable description of the tool
- `inputSchema`: JSON Schema defining the tool's input parameters

### Optional fields

- `status`: Tool status (e.g., "available", "degraded")
- `is_write`: Whether the tool performs write operations
- `requires_serial`: Whether the tool requires serialized execution
- `resource_scope`: List of resource scopes the tool can access
- `enabled`: Whether the tool is enabled for LLM use
- `capabilities`: Tool capabilities object
- `server_key`: Identifier for the MCP server providing the tool
- `config_dependent`: Whether the tool depends on configuration
- `disabled_reason`: Reason why the tool is disabled (if applicable)

### Deferred fields

The following fields are deferred and may not be supported yet:

- `disabled_code`: Structured error code for disabled tools (deferred)
```

#### Step 3: Cross-reference the complete example

Ensure the section references the complete JSON example in endpoints-and-transport.md so readers can see the full format.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section complements existing registration steps without conflicting

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if field names or classifications are incorrect

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
- Source requirement: requires/ready/20260722-123735_require.md
- Source plan: plans/20260722-140624_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-175125
- Related target files: docs/04_mcp_06_14_new-tool-registration-procedure.md
