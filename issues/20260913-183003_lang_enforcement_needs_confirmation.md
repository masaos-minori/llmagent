# Issue: Language Enforcement Needs Confirmation Not Tracked

## Summary
`docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` contains a Needs Confirmation marker about `lang` field enforcement that is not tracked in the Known Issues inventory.

## Evidence
- File: `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`, line 267
- Text: "the `en`/`ja` value set (`LanguageCode`) is convention only — not enforced at parse time (Needs confirmation: whether enforcement is intended)"
- This is a distinct Needs Confirmation item that should be added to the inventory

## Impact
- Without tracking this item, it risks being silently accepted as fact rather than investigated
- If enforcement is intended but not implemented, this could lead to incorrect language handling downstream

## Recommended Action
Add this item to the Known Issues inventory as a Needs Confirmation entry with appropriate ID. Investigate whether `lang` field validation against `LanguageCode` enum values is intended or should remain unvalidated.
