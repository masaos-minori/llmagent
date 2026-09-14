# Issue: Missing Documentation for RAG Configuration Reference Operational Values

## Summary
`docs/03_rag_05_1-configuration-reference.md` lists operational config values but doesn't document where they come from or how they differ from code defaults in a way that's actionable for operators.

## Evidence
- File: `docs/03_rag_05_1-configuration-reference.md`, section 1.4
- Text: "For fallback calls to external RAG services (`call_rag_service()`), a `timeout=10.0` is hardcoded for each attempt (`scripts/rag/pipeline_service.py`). This value is not loaded from configuration or `RagPipelineConfig`, so changing it requires source code modification."
- Multiple parameters have different default values in `RagPipelineConfig` vs operational `.toml` file
- The note at line 109 warns about differences but doesn't provide guidance on which values take precedence

## Impact
- Operators may assume all configurable values can be changed via TOML, but some require code changes
- Confusion arises when operational values don't match what's documented as "default"
- Risk of deploying incorrect configurations if precedence isn't clear

## Recommended Action
Add a dedicated subsection documenting:
1. Which configuration values are TOML-configurable vs hardcoded
2. Precedence rules (TOML overrides code defaults)
3. A table showing code default vs operational value for each parameter
4. Clear warnings about values that cannot be changed without source modification
