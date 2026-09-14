# Issue: Missing Documentation for RAG System Overview Constraints Explanation

## Summary
`docs/03_rag_01_system_overview.md` lists constraints but doesn't explain why each constraint exists or its impact on design decisions.

## Evidence
- File: `docs/03_rag_01_system_overview.md`, Constraints section
- Text: "| Constraint | Reason |" with entries like "Embedding server must be available before starting MCP server | Embedding service is required for vector search"
- The constraint is stated without explanation of what happens if it's violated
- No documentation on whether the constraint is enforced or just assumed

## Impact
- Operators don't understand the consequences of violating constraints
- New developers may not realize they need to ensure prerequisites are met
- The constraint becomes harder to enforce without clear rationale

## Recommended Action
For each constraint, document:
1. Why the constraint exists (beyond the brief reason given)
2. What happens if the constraint is violated
3. Whether the constraint is enforced programmatically or assumed
4. Any known workarounds for common violation scenarios
