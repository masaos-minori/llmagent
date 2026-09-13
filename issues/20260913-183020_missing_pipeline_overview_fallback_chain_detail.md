# Issue: Missing Documentation for RAG Query Pipeline Overview augment() Fallback Chain

## Summary
`docs/03_rag_03_01_query_pipeline-overview.md` describes the augment() fallback chain but doesn't document what happens when each step returns empty string vs None vs actual result.

## Evidence
- File: `docs/03_rag_03_01_query_pipeline-overview.md`, augment() Fallback Chain section
- Text: "augment() determines the final result through the following sequence. Each step only falls back to the next if it returns None (Explicit in code)."
- The distinction between empty string and None is critical but not documented per-step
- Step 1 (HTTP Mode): Returns `str` (including empty string) or `None` (fallback)
- Step 3 (Refiner): Returns compressed text (final) or `None` (fallback)
- Step 4 (Raw Chunks): Formatted by chunk formatting function (final)

## Impact
- Developers debugging fallback behavior may not understand when each step triggers
- Empty string results are treated as valid, which is counterintuitive
- The fallback logic is complex and undocumented beyond the high-level description

## Recommended Action
Add a detailed table documenting:
1. Each step's possible return values
2. When fallback occurs (only on None, not empty string)
3. What the final result looks like at each step
4. How diagnostics track which path was taken
