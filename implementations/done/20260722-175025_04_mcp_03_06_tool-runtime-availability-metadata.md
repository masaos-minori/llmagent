## Goal

Clarify that /v1/tools is the source for RuntimeToolRegistry construction, not just an informational endpoint.

## Scope

- Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — clarify /v1/tools as RuntimeToolRegistry source

## Assumptions

1. The existing documentation structure and content are correct; only clarifications are needed
2. /v1/tools is indeed used to build RuntimeToolRegistry (needs confirmation from Phase 1 of parent plan)

## Design decisions

- Add a dedicated subsection titled "/v1/tools as RuntimeToolRegistry Source" rather than modifying existing sections
- Include explicit statement about how RuntimeToolRegistry consumes /v1/tools data

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for source relationships

## Implementation

### Target file

- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
2. Find the section describing /v1/tools response fields
3. Identify where the source clarification should be inserted

#### Step 2: Add source clarification section

Insert the following markdown after the existing /v1/tools response field descriptions:

```markdown
## /v1/tools as RuntimeToolRegistry Source

The `/v1/tools` endpoint is **not just an informational endpoint** — it is the primary source used to construct `RuntimeToolRegistry`.

When a client calls `/v1/tools`, the MCP server returns the current state of all tools including their availability metadata. This response is consumed by the agent's runtime to populate `RuntimeToolRegistry`, which determines:
- Which tools are available for routing
- Current tool status (enabled/disabled)
- Tool configuration dependencies

Any changes to tool availability (e.g., due to health degradation, config reload) will be reflected in subsequent `/v1/tools` responses and will cause `RuntimeToolRegistry` to be updated accordingly.
```

#### Step 3: Update any conflicting statements

If there are any existing statements suggesting /v1/tools is purely informational, update them to reflect its role as the RuntimeToolRegistry source.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The clarification helps prevent misunderstanding about /v1/tools purpose

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if /v1/tools is not actually used as the RuntimeToolRegistry source

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` | Documentation consistency check | Manual review | Section added correctly, clarification accurate |

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
- Generated at: 20260722-175025
- Related target files: docs/04_mcp_03_06_tool-runtime-availability-metadata.md
