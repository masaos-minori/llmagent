# Issue: Missing Documentation for RAG System Overview Constraints Table

## Summary
`docs/03_rag_01_system_overview.md` lists constraints but doesn't explain how they affect operational behavior or where to find configuration overrides.

## Evidence
- File: `docs/03_rag_01_system_overview.md`, Constraints section
- Text: "| Constraint | Value | Source |" with entries like "Language Detection: CJK ratio ≥ 0.10 → ja; otherwise en; fallback to hint if < 100 chars"
- The constraint values are listed without explanation of their impact on search quality
- No guidance on whether these should be tuned for specific use cases

## Impact
- Operators cannot make informed decisions about tuning these constraints
- The rationale behind default values is undocumented
- Performance issues may arise from suboptimal constraint settings

## Recommended Action
Add a subsection explaining:
1. Why each constraint value was chosen (empirical basis, trade-offs)
2. How changing each value affects search quality/performance
3. Guidance on when to adjust each constraint
4. References to any ADRs or design decisions that established these values
