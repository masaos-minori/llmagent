# Implementation and Test Procedure: RAG Pipeline MCP Server

## Goal
Implement a dedicated MCP server that consolidates the RAG pipeline into a single integrated service, replacing the current centralized RAG processing in `agent_rag.py`.

## Scope
This implementation will:
- Create a new MCP server called `rag-pipeline-mcp` with integrated RAG pipeline functionality
- Provide tools for running MQE, Search, RRF, Rerank, Dedup, and Augment as a single pipeline
- Support both standard and debug modes for the RAG pipeline
- Integrate with existing MCP operating model (HTTP, OpenRC, `/mcp`, `/v1/tools`, watchdog)
- Update Agent configuration to include the new MCP server and tools

## Assumptions
- Current RAG pipeline is implemented in `agent_rag.py` with six steps: MQE, Search, RRF, Rerank, Dedup, and Augment
- Current Agent assumes HTTP MCP servers using `/v1/call_tool` and `/v1/tools` endpoints
- Current Agent performs `/v1/tools` diff checks and watchdog-based health checks
- The system has Python 3.13 installed with required dependencies
- The database directory `/opt/llm/db/` exists
- The config directory `/opt/llm/config/` exists
- The scripts directory `/opt/llm/scripts/` exists

## Implementation
The implementation will create the following files:
1. `scripts/rag_pipeline_mcp_server.py` - Main MCP server implementation
2. `config/rag_pipeline_mcp_server.json` - Configuration file for the server
3. `init.d/rag-pipeline-mcp` - OpenRC service script
4. Update `agent/config.py` to include the new MCP server
5. Update `agent/factory.py` to register the new MCP server
6. Update `agent/repl.py` to handle the new tools
7. Update `agent/commands/cmd_mcp.py` to include the new tools

## Validation plan
1. Unit tests for each RAG pipeline step
2. Integration tests for the complete workflow
3. Verify that the server responds to `/v1/tools` endpoint
4. Test that the server can be started and stopped properly
5. Validate that all required tools are available
6. Check that the MCP server integrates with the agent system
7. Confirm that the database is created and used correctly
8. Verify that tool definitions are properly registered