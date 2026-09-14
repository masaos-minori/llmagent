# Issue: Missing Documentation for RAG Augment Stages Content-only Invariance Rule

## Summary
`docs/03_rag_03_05_query_pipeline-augment-stages.md` mentions a "Content-only Invariance Rule" but doesn't explain what it means or why it exists.

## Evidence
- File: `docs/03_rag_03_05_query_pipeline-augment-stages.md`, section 5.5
- Text: "**Content-only Invariance Rule:** AugmentStage only formats `content` and never uses `normalized_content`. See [ADR-009](adr/ADR-009-rag-ft5-text-separation.md) for rationale, alternatives, and tradeoffs."
- The rule is stated without explanation of its purpose or implications
- ADR-009 reference is provided but the rule itself isn't explained inline

## Impact
- Developers unfamiliar with ADR-009 won't understand why `normalized_content` is excluded
- Future changes to AugmentStage could accidentally introduce `normalized_content` usage
- The rule's scope and limitations aren't clear from the statement alone

## Recommended Action
Add an inline explanation of the Content-only Invariance Rule:
1. What it means (AugmentStage formats only raw text, not normalized forms)
2. Why it exists (FTS5 uses COALESCE(normalized_content, content) for indexing, so raw text is sufficient for output)
3. Scope (applies only to AugmentStage, not to other pipeline stages)
4. Limitations (e.g., Japanese text loses normalization benefits in output)
