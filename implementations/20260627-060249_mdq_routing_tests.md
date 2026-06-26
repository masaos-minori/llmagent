## Goal

Add routing, tool definition, and safety tier consistency tests for MDQ to prevent tool name and metadata drift across MDQ_TOOLS, tool registry, /v1/tools, tool definitions, and safety tiers.

## Scope

**In-Scope**:
- Test MDQ_TOOLS contains exactly 7 expected tools
- Test tool registry maps all MDQ tools to server key mdq
- Test /v1/tools returns the same MDQ tool names
- Test tool definitions expose all MDQ tools required by LLM
- Test safety tiers classify read-only and indexing tools correctly
- Test no MDQ tool is accidentally unmapped

**Out-of-Scope**:
- Adding new tools or features
- Changes to other MCP servers' routing/tests

## Assumptions

1. MDQ_TOOLS should contain exactly: search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs
2. Safety tiers should classify read-only tools as READ_ONLY and indexing tools as WRITE_DANGEROUS
3. Tests should run at startup validation time to catch drift early

## Implementation

### Target file: config/agent.toml

**Procedure**: Add MDQ tools to tool_safety_tiers section.

**Method**: Add entries in [tool_safety_tiers] section of agent.toml.

**Details**:
1. Add read-only tools to READ_ONLY tier:
   - `search_docs = "READ_ONLY"`
   - `get_chunk = "READ_ONLY"`
   - `outline = "READ_ONLY"`
   - `stats = "READ_ONLY"`
   - `grep_docs = "READ_ONLY"`
2. Add indexing tools to WRITE_DANGEROUS tier:
   - `index_paths = "WRITE_DANGEROUS"`
   - `refresh_index = "WRITE_DANGEROUS"`

### Target file: scripts/shared/tool_constants.py

**Procedure**: Verify MDQ_TOOLS definition is correct.

**Method**: Check existing MDQ_TOOLS constant in tool_constants.py.

**Details**:
1. Verify MDQ_TOOLS contains exactly 7 tools: search_docs, get_chunk, outline, index_paths, refresh_index, stats, grep_docs
2. No changes needed if definition is already correct

### Target file: scripts/shared/tool_registry.py

**Procedure**: Test tool registry maps all MDQ tools to server key mdq.

**Method**: Add test in test_route_resolver.py to verify MDQ tool mappings.

**Details**:
1. Add test_mdq_tools() function in test_route_resolver.py
2. Verify each MDQ_TOOLS tool is mapped to server key "mdq"

### Target file: scripts/mcp/mdq/server.py

**Procedure**: Test /v1/tools endpoint returns the same MDQ tool names.

**Method**: Add test to verify /v1/tools response contains all MDQ tools.

**Details**:
1. Add test_mdq_tools_endpoint() function in test_route_resolver.py
2. Verify /v1/tools response contains exactly 7 MDQ tools with matching names

### Target file: tests/test_mdq_routing.py

**Procedure**: Create new test file for MDQ metadata consistency.

**Method**: Create new test file with integration tests for MDQ tool metadata.

**Details**:
1. Add test_mdq_tools_count() — verify MDQ_TOOLS contains exactly 7 tools
2. Add test_mdq_no_unmapped_tools() — verify no MDQ tool is accidentally unmapped across config, registry, and live sources
3. Add test_mdq_safety_tiers() — verify safety tiers classify MDQ tools correctly (read-only vs WRITE_DANGEROUS)

### Target file: scripts/mcp/mdq/server.py

**Procedure**: Add startup validation for MDQ drift.

**Method**: Add validate_all_routing() call at startup for MDQ tools.

**Details**:
1. Call validate_all_routing() at startup for MDQ tools
2. Return warnings if drift detected
3. Run as separate test suite (not blocking startup)

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| test_route_resolver.py | Verify MDQ routing tests pass | pytest tests/test_route_resolver.py::test_mdq_tools | All MDQ tools mapped correctly |
| test_mdq_routing.py | Verify metadata consistency tests pass | pytest tests/test_mdq_routing.py | No drift detected |
| agent.toml | Verify safety tiers updated | Check [tool_safety_tiers] section | MDQ tools present with correct classification |

## Risks

- **Risk**: Startup validation adds latency to agent startup | **Likelihood**: Low | **Mitigation**: Run validation asynchronously; log warnings instead of blocking | False
- **Risk**: Safety tier changes break existing tool behavior | **Likelihood**: Medium | **Mitigation**: Test thoroughly before deployment; document expected behavior changes | False
