# Implementation: docs — production hardening documentation updates

## Goal

Update 5 documentation files for the comprehensive `ProductionConfigValidator` changes.

## Scope

- `docs/04_mcp_05_security_and_safety_model.md`
- `docs/04_mcp_06_configuration_and_operations.md`
- `docs/05_agent_06_tool-execution-and-approval.md`
- `docs/05_agent_08_configuration.md`
- `docs/05_agent_11_extension-points.md`

## Assumptions

1. All 5 doc files exist and have the current production-config sections.
2. The plan's "Recommended changes" section is the canonical source for behavior.

## Implementation

### Target files

1. `docs/04_mcp_05_security_and_safety_model.md`
2. `docs/04_mcp_06_configuration_and_operations.md`
3. `docs/05_agent_06_tool-execution-and-approval.md`
4. `docs/05_agent_08_configuration.md`
5. `docs/05_agent_11_extension-points.md`

### Procedure

1. **`docs/04_mcp_05_security_and_safety_model.md`:** Add rows for `tool_safety_tiers` bidirectional validation; clarify `allowed_repos_mode="fail_open"` production prohibition.
2. **`docs/04_mcp_06_configuration_and_operations.md`:** Add pre-production checklist items for `use_tool_dag`, `allowed_tools`, and `tool_safety_tiers`.
3. **`docs/05_agent_06_tool-execution-and-approval.md`:** Document `allowed_tools=[]` behavior and `use_tool_dag=false` production impact.
4. **`docs/05_agent_08_configuration.md`:** Add production-recommended-value column for strict keys and safety tiers.
5. **`docs/05_agent_11_extension-points.md`:** Document production prohibition for missing safety tier entries.

### Details

See plan design section for exact content per doc.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Manual review | `git diff docs/` | All doc edits correct |
| MCP docs consistency | `uv run check-mcp-docs` | Pass |
