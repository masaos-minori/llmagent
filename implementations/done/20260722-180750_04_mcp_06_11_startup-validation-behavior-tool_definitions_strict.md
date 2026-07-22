## Goal

Document production vs local behavior differences for MCP discovery, including how duplicate tools and unreachable servers are handled differently.

## Scope

- Update `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` — add production vs local behavior clarification

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. Production mode treats duplicate tools as FATAL, while local mode treats them as WARNING
3. Local mode treats unreachable servers as SKIPPED but still means all tool calls fail

## Design decisions

- Add a dedicated subsection titled "Production vs local behavior differences"
- Use bullet points to clearly show the differences between modes
- Include specific examples for each scenario

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for behavior differences

## Implementation

### Target file

- `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md`
2. Find an appropriate location for the production vs local behavior section (likely after the severity descriptions)
3. Identify where the new section should be inserted

#### Step 2: Add production vs local behavior section

Insert the following markdown:

```markdown
### Production vs local behavior differences

MCP discovery behaves differently between production and local modes:

**Duplicate tools:**
- Production: FATAL outcome, startup blocked
- Local: WARNING outcome, startup continues

**Unreachable servers:**
- Production: FATAL outcome, startup blocked
- Local: SKIPPED outcome, startup continues but all tool calls will fail for that session

This difference exists because local mode is designed to be more forgiving during development, while production mode enforces strict validation to prevent partial functionality.
```

#### Step 3: Cross-reference the severity descriptions

If there are any cross-references to the severity descriptions section, ensure they point to the updated content.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section helps prevent misunderstanding about mode-specific behavior

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if the behavior descriptions are incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md` | Documentation consistency check | Manual review | Section added correctly |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124328_require.md
- Source plan: plans/20260722-164224_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180750
- Related target files: docs/04_mcp_06_11_startup-validation-behavior-tool_definitions_strict.md
