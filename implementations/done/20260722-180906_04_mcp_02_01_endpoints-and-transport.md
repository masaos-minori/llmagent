## Goal

Replace the brief /v1/tools section with expanded content showing current vs deferred fields, noting server-specific fields.

## Scope

- Update `docs/04_mcp_02_01_endpoints-and-transport.md` — replace brief /v1/tools section with expanded content

## Assumptions

1. The existing documentation structure and content are correct; only replacements are needed
2. All fields listed as "current" are indeed currently implemented and returned by `/v1/tools`
3. `include_disabled` and `disabled_code` are confirmed deferred (not yet implemented)
4. Top-level `capabilities` needs verification — may already be implemented via McpToolDiscoveryService validation

## Design decisions

- Replace the brief /v1/tools section with two clear subsections: "Current fields" and "Deferred fields"
- Note server-specific fields as such
- Use bullet points for readability

## Alternatives considered

- Adding inline notes within existing sections instead of creating new subsections
- Creating a separate appendix for field status

## Implementation

### Target file

- `docs/04_mcp_02_01_endpoints-and-transport.md`

### Procedure

#### Step 1: Locate the brief /v1/tools section

1. Open `docs/04_mcp_02_01_endpoints-and-transport.md`
2. Find the brief /v1/tools section (around lines 92-100)
3. Identify where the replacement should occur

#### Step 2: Replace the section

Replace the existing brief section with:

```markdown
## HTTP ツール一覧: `/v1/tools`

### Current fields

These fields are currently supported by the discovery service:

#### Top-level response fields

- `schema_version` — top-level discovery-time metadata (returned by all servers)

#### Per-tool fields

- `name` — per-tool identifier
- `description` — per-tool description
- `inputSchema` — per-tool schema (or `input_schema`)
- `status` — per-tool status
- `server_key` — server key injected by `build_tools_response()`
- `enabled` — maps to RuntimeTool.enabled_for_llm (server-specific; not all servers return this)
- `disabled_reason` — reason when disabled (server-specific; not all servers return this)
- `is_write` — whether the tool performs writes
- `requires_serial` — whether the tool requires serial execution
- `resource_scope` — resource scope constraints
- `capabilities` — optional capability flags (per-tool)
- `config_dependent` — whether the tool depends on configuration state

### Deferred fields

These fields are planned but NOT yet implemented:

- `include_disabled` — query parameter to include disabled tools
- `disabled_code` — structured code for disabled reasons
- Top-level `capabilities` — if not already implemented (verify during implementation)
```

#### Step 3: Verify cross-references

If there are any cross-references to the old section elsewhere in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section helps prevent misunderstanding about field availability

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the replacement if the field classifications are incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_02_01_endpoints-and-transport.md` | Documentation consistency check | Manual review | Section replaced correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124439_require.md
- Source plan: plans/20260722-164601_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180906
- Related target files: docs/04_mcp_02_01_endpoints-and-transport.md
