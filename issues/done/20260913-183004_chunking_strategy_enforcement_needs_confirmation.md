# Issue: Chunking Strategy Enforcement Needs Confirmation Not Tracked

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` contains a Needs Confirmation marker about `chunking_strategy` field enforcement that is not tracked in the Known Issues inventory.

## Evidence
- File: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, line 294
- Text: "no enum enforced in code (Needs confirmation: whether a closed value set is intended)"
- This refers to the `chunking_strategy` field which accepts `"text"` or `"heading"` by convention but has no enum validation in code

## Impact
- Without tracking this item, it risks being silently accepted as fact rather than investigated
- If a closed value set is intended but not enforced, invalid `chunking_strategy` values could cause unexpected behavior downstream

## Recommended Action
Add this item to the Known Issues inventory as a Needs Confirmation entry with appropriate ID. Investigate whether `chunking_strategy` validation against a closed value set (`"text"` / `"heading"`) is intended or should remain unvalidated.
