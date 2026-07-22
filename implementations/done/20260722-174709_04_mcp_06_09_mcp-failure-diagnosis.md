## Goal

Document the critical failure mode where RuntimeToolRegistry is missing, causing tools to be invisible to the LLM even when they exist in the system.

## Scope

- Update `docs/04_mcp_06_09_mcp-failure-diagnosis.md` — document LLM-visible but execution-fails failure mode

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The RuntimeToolRegistry missing scenario is a real failure mode that operators encounter
3. Operators need clear diagnosis guidance for this specific failure mode

## Design decisions

- Add a new subsection titled "Failure mode: LLM sees tool but execution fails" under appropriate category in the failure diagnosis document
- Include both symptoms and diagnostic steps

## Alternatives considered

- Adding this as a note within existing failure modes instead of creating a new subsection
- Creating a separate document for this failure mode

## Implementation

### Target file

- `docs/04_mcp_06_09_mcp-failure-diagnosis.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_06_09_mcp-failure-diagnosis.md`
2. Find the section listing existing failure modes
3. Identify where the new failure mode should be inserted (likely near other routing-related failures)

#### Step 2: Add failure mode section

Insert the following markdown as a new subsection:

```markdown
## Failure mode: LLM sees tool but execution fails

**Symptoms:**
- LLM proposes a valid tool call using a known tool name
- Execution fails with "Unknown tool" error despite the tool name being valid

**Root cause:**
- `RuntimeToolRegistry` is missing entirely during runtime
- Tools may exist in MCP server catalogs but are not registered in the runtime registry
- This creates a mismatch: LLM knows about the tool (from discovery), but the router cannot find it

**Diagnostic steps:**
1. Check if `RuntimeToolRegistry` was initialized successfully at startup
2. Verify no errors during tool registration phase
3. Confirm all expected MCP servers have completed their tool discovery
4. Review startup logs for any tool registration failures

**Resolution:**
- Restart the agent process to re-initialize `RuntimeToolRegistry`
- If persistent, investigate MCP server connection issues that may prevent tool registration
```

#### Step 3: Cross-reference two-stage model

If the two-stage tool resolution section exists elsewhere in the documentation, add a cross-reference:

```markdown
See also: Two-stage tool resolution (LLM visibility vs runtime routability)
```

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new failure mode complements existing ones without conflicting

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added subsection if the failure mode description is inaccurate

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Documentation consistency check | Manual review | Section added correctly, diagnosis accurate |

## Out of scope

- Adding `RuntimeTool.disabled_reason` as a first-class field
- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-123620_require.md
- Source plan: plans/20260722-135916_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-174709
- Related target files: docs/04_mcp_06_09_mcp-failure-diagnosis.md
