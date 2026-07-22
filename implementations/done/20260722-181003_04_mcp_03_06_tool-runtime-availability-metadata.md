## Goal

Clarify deferred status for include_disabled, disabled_code, and top-level capabilities in the availability metadata document.

## Scope

- Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — clarify deferred design options

## Assumptions

1. The existing documentation structure and content are correct; only clarifications are needed
2. `include_disabled` and `disabled_code` are already marked as "unimplemented" — keep as-is
3. Top-level `capabilities` needs clarification based on UNK-01 resolution

## Design decisions

- Add explicit clarification that top-level `capabilities` is also deferred (if not already implemented)
- Keep existing `include_disabled` and `disabled_code` markings as-is since they're already accurate

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new section
- Creating a separate appendix for deferred options

## Implementation

### Target file

- `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure

#### Step 1: Locate the deferred section

1. Open `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`
2. Find the "Future / deferred design options" section

#### Step 2: Clarify top-level capabilities

Add the following note near the existing deferred items:

```markdown
**Note:** Top-level `capabilities` (on the response body, not per-tool) is also deferred unless verified otherwise. If any MCP server returns top-level `capabilities` in its `/v1/tools` response, this should be updated to reflect current implementation status.
```

#### Step 3: Cross-reference the endpoints document

If there are any cross-references to the endpoints-and-transport.md document, ensure they point to the updated content.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new clarification helps prevent misunderstanding about top-level capabilities

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added note if top-level capabilities is later determined to be implemented

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
- Source requirement: requires/ready/20260722-124439_require.md
- Source plan: plans/20260722-164601_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-181003
- Related target files: docs/04_mcp_03_06_tool-runtime-availability-metadata.md
