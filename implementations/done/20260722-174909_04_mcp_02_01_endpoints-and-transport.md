## Goal

Replace minimal /v1/tools JSON example with full example showing all fields, clearly marking required vs optional fields.

## Scope

- Update `docs/04_mcp_02_01_endpoints-and-transport.md` — update /v1/tools section with complete field example

## Assumptions

1. The current /v1/tools response shape includes all fields listed in the requirement (schema_version, status, is_write, requires_serial, resource_scope, enabled, capabilities, server_key, config_dependent, disabled_reason)
2. The distinction between required and optional fields is accurate per McpToolDiscoveryService validation behavior
3. `inputSchema` is the correct field name (to be verified in Phase 1)

## Design decisions

- Replace the existing minimal JSON example with a comprehensive example
- Use inline comments or a separate table to mark required vs optional fields
- Keep the example realistic by including typical values

## Alternatives considered

- Adding a separate reference table instead of modifying the example
- Keeping the minimal example and adding a "complete example" subsection

## Implementation

### Target file

- `docs/04_mcp_02_01_endpoints-and-transport.md`

### Procedure

#### Step 1: Verify field names (read-only)

Before editing, confirm the following in `mcp_tool_discovery.py`:
1. Whether `inputSchema` or `input_schema` is the correct field name
2. The exact set of required vs optional fields
3. Whether `capabilities` field exists

#### Step 2: Locate the /v1/tools section

1. Open `docs/04_mcp_02_01_endpoints-and-transport.md`
2. Find the /v1/tools endpoint section
3. Identify the existing minimal JSON example

#### Step 3: Replace the JSON example

Replace the existing minimal example with a complete example. Based on the requirement, the example should include:

```json
{
  "schema_version": "2024-11-05",
  "tools": [
    {
      "name": "example_tool",
      "description": "Example tool description",
      "inputSchema": { ... },
      "status": "available",
      "is_write": false,
      "requires_serial": false,
      "resource_scope": [],
      "enabled": true,
      "capabilities": {},
      "server_key": "example-server",
      "config_dependent": true,
      "disabled_reason": null
    }
  ]
}
```

#### Step 4: Add required/optional field annotations

Add a note after the example indicating which fields are required:

```markdown
**Required fields:** `name`, `description`, `inputSchema`
**Optional fields:** `status`, `is_write`, `requires_serial`, `resource_scope`, `enabled`, `capabilities`, `server_key`, `config_dependent`, `disabled_reason`
```

#### Step 5: Update any cross-references

If there are references to the old minimal example elsewhere in the document, update them to point to the new example.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new example must match actual /v1/tools response format

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the example if field names are incorrect after Phase 1 verification

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `mcp_tool_discovery.py` | Read-only verification | grep for field definitions | Field names confirmed |
| `docs/04_mcp_02_01_endpoints-and-transport.md` | Documentation consistency check | Manual review | Example added correctly |

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
- Generated at: 20260722-174909
- Related target files: docs/04_mcp_02_01_endpoints-and-transport.md
