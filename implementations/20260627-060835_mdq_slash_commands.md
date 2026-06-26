## Goal

Add Agent slash commands for MDQ operations by creating 7 REPL commands (/mdq status, /mdq index, /mdq refresh, /mdq search, /mdq outline, /mdq get, /mdq grep) that call MDQ through MCP tools, not by directly reading mdq.sqlite.

## Scope

**In-Scope**:
- Add /mdq status command (reports health and index statistics)
- Add /mdq index <path> [--force] command
- Add /mdq refresh <path> command
- Add /mdq search <query> command
- Add /mdq outline <path> command
- Add /mdq get <chunk_id> command
- Add /mdq grep <pattern> command
- All commands must use MCP tool calls, not direct mdq.sqlite access
- Document MDQ slash commands in CLI documentation

**Out-of-Scope**:
- Adding new tools or features to MDQ MCP server
- Changes to other MCP servers' slash commands

## Assumptions

1. Slash command architecture follows existing pattern: CommandDef + mixin class with _cmd_* methods
2. /mdq index should add --force flag to MCP tool schema
3. Commands follow same pattern as /rag search (call MCP tools via tool executor)
4. MDQ MCP server already has all 7 tools needed

## Implementation

### Target file: scripts/agent/commands/cmd_mdq.py

**Procedure**: Create new mixin class with _cmd_* methods for MDQ operations.

**Method**: Create new Python file following existing pattern (e.g., rag_search mixin).

**Details**:
1. Implement _cmd_mdq_status method:
   - Call stats MCP tool via tool executor
   - Return health and index statistics
2. Implement _cmd_mdq_index method:
   - Call index_paths MCP tool via tool executor
   - Support --force flag for full re-index
3. Implement _cmd_mdq_refresh method:
   - Call refresh_index MCP tool via tool executor
4. Implement _cmd_mdq_search method:
   - Call search_docs MCP tool via tool executor
5. Implement _cmd_mdq_outline method:
   - Call outline MCP tool via tool executor
6. Implement _cmd_mdq_get method:
   - Call get_chunk MCP tool via tool executor
7. Implement _cmd_mdq_grep method:
   - Call grep_docs MCP tool via tool executor

### Target file: scripts/mcp/mdq/tools.py

**Procedure**: Add --force flag to index_paths tool schema.

**Method**: Modify index_paths tool definition in tools.py.

**Details**:
1. Update index_paths tool definition with force parameter
2. Add force field to tool schema (boolean, optional)

### Target file: scripts/agent/commands/command_defs.py

**Procedure**: Register slash commands in command_defs.py.

**Method**: Add MDQ slash command definitions to _COMMANDS list.

**Details**:
1. Add MDQ slash command definitions to _COMMANDS list:
   - /mdq status — reports health and index statistics
   - /mdq index <path> [--force] — index a path
   - /mdq refresh <path> — refresh index for a path
   - /mdq search <query> — search indexed content
   - /mdq outline <path> — get heading structure
   - /mdq get <chunk_id> — retrieve a chunk
   - /mdq grep <pattern> — search with regex

### Target file: scripts/agent/commands/registry.py

**Procedure**: Import cmd_mdq mixin in registry.

**Method**: Add import statement for cmd_mdq module.

**Details**:
1. Add `from mcp.mdq.commands.cmd_mdq import CmdMdqMixin` (adjust path as needed)
2. Register CmdMdqMixin in agent command registry

### Target file: docs/05_agent_07_cli-and-commands.md

**Procedure**: Add MDQ slash command documentation.

**Method**: Add new section to existing documentation.

**Details**:
1. Add /mdq section documenting all 7 slash commands
2. Include usage examples for each command
3. Document --force flag behavior for /mdq index

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| cmd_mdq.py | Verify all 7 slash commands exist | Check mixin class methods | All _cmd_mdq_* methods present |
| command_defs.py | Verify MDQ commands registered | Check _COMMANDS list | MDQ commands in registry |
| agent REPL | Test /mdq status command | Run /mdq status in REPL | Health and stats returned |
| docs | Verify MDQ documentation exists | Check CLI documentation | /mdq section documented |

## Risks

- **Risk**: MCP tool calling may fail if mdq-mcp server is not running | **Likelihood**: Medium | **Mitigation**: Return clear error message when MCP server unavailable | False
- **Risk**: --force flag adds complexity to index_paths tool schema | **Likelihood**: Low | **Mitigation**: Document --force behavior clearly; test thoroughly | False
