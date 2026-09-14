# Issue: Missing Documentation for RAG System Overview Component Responsibilities

## Summary
`docs/03_rag_01_system_overview.md` describes component responsibilities but doesn't explain why each component owns its stated state.

## Evidence
- File: `docs/03_rag_01_system_overview.md`, System Architecture section
- Text: "- **Component Responsibilities**: Agent turn invokes `RagPipeline.augment(query)` via MCP HTTP; RagPipeline executes MQE → Search → RRF → Rerank → Augment stages; KNN + BM25 search operates over SQLite (rag.db)."
- The ownership model isn't explained — why does RagPipeline own query execution lifecycle?
- No justification for why SQLite owns vector store layer

## Impact
- Developers modifying components may not understand the ownership boundaries
- Cross-component refactoring may violate implicit contracts
- New developers may assume different ownership than intended

## Recommended Action
Add a subsection explaining:
1. Why each component owns its stated state
2. The rationale for the ownership boundaries
3. How ownership affects modification rights
4. Any known exceptions to the ownership rules
