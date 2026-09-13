# Issue: Missing Documentation for RAG System Overview MCP Server Responsibility Division

## Summary
`docs/03_rag_01_system_overview.md` references another document for MCP server responsibility division but doesn't summarize the key responsibilities inline.

## Evidence
- File: `docs/03_rag_01_system_overview.md`, MCP Server Responsibility Division section
- Text: "For details on responsibilities of `rag_pipeline_server.py`, `rag_pipeline_service.py`, and `scripts/rag/pipeline.py`, please refer to `docs/03_rag_03_01_query_pipeline-overview.md`."
- The section exists but contains no content beyond the cross-reference
- Operators reading this overview won't understand the division of responsibilities

## Impact
- New developers can't understand the MCP pipeline architecture from this document alone
- Cross-referencing adds cognitive load during debugging
- The responsibility boundaries remain undocumented at the system level

## Recommended Action
Add a brief summary of each component's responsibilities:
1. `rag_pipeline_server.py`: HTTP route handling, request/response formatting
2. `rag_pipeline_service.py`: Pipeline orchestration, error handling
3. `scripts/rag/pipeline.py`: Core search logic, stage execution
4. How they interact (caller → callee flow)
