# Issue: Type Inconsistency in CrawlTarget.lang vs Other DTOs lang Field

## Summary
`CrawlTarget.lang` uses the `LanguageCode` enum while other DTOs use plain `str` for `lang`, creating a type inconsistency across the RAG pipeline.

## Evidence
- File: `docs/03_rag_04_01_dto-models_data.md`, Constraints Regarding Persistence, Search, and Compatibility section
- Text: "`CrawlTarget.lang` uses the `LanguageCode` enum, whereas other DTOs use a plain `str` for `lang` (Note the type inconsistency)"
- This inconsistency means validation logic must handle both types depending on which DTO is being processed

## Impact
- Type checking tools may flag inconsistencies between `CrawlTarget` and other DTOs
- Validation logic must branch based on which DTO is being processed
- Potential for subtle bugs if code assumes uniform typing across all DTOs

## Recommended Action
Investigate whether `LanguageCode` enum enforcement on `CrawlTarget.lang` provides meaningful value over plain string validation. If it does, consider applying the same pattern to other DTOs. If not, remove the enum usage and unify on `str` for consistency.
