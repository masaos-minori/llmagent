# Issue: Missing Documentation for RAG System Overview Content

## Summary
The RAG system overview document (`docs/03_rag_01_system_overview.md`) lacks content describing the query pipeline architecture, semantic cache behavior, and MCP server responsibility division sections that are referenced but not fully explained.

## Evidence
- File: `docs/03_rag_01_system_overview.md`
- Section "Query Pipeline": References detailed stage docs but doesn't explain the overall flow
- Section "Semantic Cache": Describes behavior but doesn't document the TTL/invalidation strategy
- Section "MCP Server Responsibility Division": References another doc but doesn't summarize responsibilities
- The document structure suggests these sections should contain more detail than currently provided

## Impact
- New developers reading this overview will miss critical architectural details
- The semantic cache's invalidation strategy is undocumented, making it hard to reason about consistency
- The MCP server's role relative to the pipeline is unclear without cross-referencing

## Recommended Action
Add content to each section:
1. Query Pipeline: Add a high-level flow diagram or description of how stages connect
2. Semantic Cache: Document TTL, invalidation triggers, and consistency guarantees
3. MCP Server Responsibility Division: Summarize key responsibilities instead of just referencing another doc
