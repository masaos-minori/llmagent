## Goal

Add diagnosis section for "LLM called a tool, but execution failed with Unknown tool" failure mode to the MCP failure diagnosis document.

## Scope

- Update `docs/04_mcp_06_09_mcp-failure-diagnosis.md` — add diagnosis section

## Assumptions

1. The existing documentation structure and content are correct; only additions are needed
2. The diagnosis section content specified in the requirement is accurate and complete
3. The section should be inserted after the existing circuit breaker section (before "Related Documents")

## Design decisions

- Add a dedicated subsection titled "LLM called a tool, but execution failed with Unknown tool"
- Include both possible causes and diagnosis steps
- Explain the root cause: RuntimeToolRegistry may be incomplete due to discovery failures

## Alternatives considered

- Adding inline notes within existing sections instead of creating a new subsection
- Creating a separate appendix for failure modes

## Implementation

### Target file

- `docs/04_mcp_06_09_mcp-failure-diagnosis.md`

### Procedure

#### Step 1: Locate insertion point

1. Open `docs/04_mcp_06_09_mcp-failure-diagnosis.md`
2. Find the "Related Documents" section
3. Identify where the new section should be inserted (just before "Related Documents")

#### Step 2: Add diagnosis section

Insert the following markdown before the "Related Documents" section:

```markdown
### LLM called a tool, but execution failed with Unknown tool

**Possible causes:**
- RuntimeToolRegistry is missing or incomplete
- Discovery was FATAL, WARNING, or SKIPPED
- Duplicate tool name detection excluded the tool
- ToolExecutor.set_runtime_registry() was not called

**Diagnosis steps:**
1. Check startup output for `mcp_tool_discovery` outcomes
2. Check whether discovery was FATAL, WARNING, or SKIPPED
3. Check whether the owning server's /v1/tools response includes the tool
4. Check whether duplicate tool name detection excluded the tool
5. Check whether ctx.services_required.runtime_tools was populated
6. Check whether ToolExecutor.set_runtime_registry() was called
7. Check whether the tool exists in RuntimeToolRegistry
8. Do not rely only on config/agent.toml tool_definitions

**Root cause explanation:**
The "Unknown tool" error originates from `ToolRouteResolver.resolve()` which raises `ValueError` when a tool name is not found in `RuntimeToolRegistry`. This can happen even when the LLM sees the tool via `/v1/tools` because `RuntimeToolRegistry` may be incomplete due to discovery failures.
```

#### Step 3: Verify cross-references

If there are any cross-references to other sections in the document, ensure they still work correctly.

## Compatibility considerations

- No API changes — documentation-only update
- Existing cross-references should continue to work
- The new section complements existing failure diagnosis without conflicting

## Security considerations

- N/A — documentation-only change

## Rollback considerations

- Revert the added section if the diagnosis steps or root cause explanation are incorrect

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/04_mcp_06_09_mcp-failure-diagnosis.md` | Documentation consistency check | Manual review | Section added correctly, heading level correct |

## Out of scope

- Implementing `include_disabled` query parameter for `/v1/tools`
- Implementing `disabled_code` structured field
- Any source code changes

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/ready/20260722-124218_require.md
- Source plan: plans/20260722-145326_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-180323
- Related target files: docs/04_mcp_06_09_mcp-failure-diagnosis.md
