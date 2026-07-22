## Goal

Clarify that web-search is NOT an active example of disabled_reason usage (unlike git-mcp).

## Scope

- Update `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` — clarify web-search as non-example

## Assumptions

1. The existing documentation structure and content are correct; only clarifications are needed
2. git-mcp is already documented as an active example of disabled_reason usage

## Design decisions

- Add a note within the disabled_reason section indicating web-search is NOT an active example
- Include reference to the web-search documentation for details on its specific behavior

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

#### Step 2: Add web-search clarification

Add the following note near the disabled_reason description, after the git-mcp note:

```markdown
**Not yet implemented:** The web-search server does NOT implement `disabled_reason` for `browser_fetch`, despite having `config_dependent=true`. See [web-search availability metadata](./04_mcp_04_01_web-search-file-read-github.md#availability-metadata) for details on its current limitations.
```

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The clarification helps prevent misunderstanding about web-search implementing disabled_reason

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added note if web-search is later determined to implement disabled_reason

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
- Source requirement: requires/ready/20260722-124007_require.md
- Source plan: plans/20260722-143806_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180025
- Related target files: docs/04_mcp_03_06_tool-runtime-availability-metadata.md
