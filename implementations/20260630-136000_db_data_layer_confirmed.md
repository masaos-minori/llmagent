## Goal
- Confirm Agent Data Layer documentation update to scoped DB commands is already complete

## Findings
- `grep -n "/db urls\|/db clean\b\|/db rebuild-fts\b" docs/05_agent_09_data-layer.md` → no matches (flat aliases removed)
- L93: `/db rag urls`, `/db rag clean` ✓
- L94: `/db rag stats` ✓
- L99: `/db rag stats`, `/db rag rebuild-fts` ✓
- L116: `/db rag urls`+`/db rag clean` → rag-pipeline-mcp ✓

## Conclusion
No changes needed — already completed.
