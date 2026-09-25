# Rewrite rag_04_04_dto-models_config.md to match current RagConfigImpl runtime contract

## Priority
Medium

## Summary
Rewrite `docs/21_rag/rag_04_04_dto-models_config.md`'s main body to document `RagConfigImpl` and the `RagConfig` Protocol instead of the removed per-stage config dataclasses (MqeConfig, FusionConfig, RerankConfig, SearchConfig, ChunkSplitterConfig, IngesterConfig, PipelineConfig).

## Background
The 7 dataclasses documented in `docs/rag_04_04_dto-models_config.md` no longer exist in `scripts/rag/models_config.py`, which now defines only `RagConfigImpl`. This was tracked as Known Issue CI-017 in `governance_03_issue-and-uncertainty-management.md`: "The doc's main body still describes the 7 legacy per-stage config dataclasses as the runtime config contract." The actual runtime contract is `RagConfigImpl` (a flat dataclass), actively used by `scripts/rag/pipeline.py` and 5 test files, implementing the `RagConfig` Protocol (`scripts/shared/types.py`).

## Problem
A reader of `rag_04_04_dto-models_config.md` would look for config classes that no longer exist and miss the actual runtime contract (`RagConfigImpl`/`RagConfig` Protocol). The document is misleading because it presents obsolete DTOs as the current specification.

## Reason for Change
CI-017 has been open since 2026-09-20 without resolution. The document needs updating to reflect the current state before it causes confusion for developers relying on it as a reference.

## Implementation Intent
1. Read `scripts/rag/models_config.py` to understand the current `RagConfigImpl` structure
2. Read `scripts/shared/types.py` to understand the `RagConfig` Protocol definition
3. Read `scripts/rag/pipeline.py` to understand how `RagConfigImpl` is consumed at runtime
4. Rewrite the document's main body to document `RagConfigImpl` fields, types, and defaults
5. Update the "See also" references to point to the correct locations
6. Remove references to the 7 removed DTOs (MqeConfig, FusionConfig, RerankConfig, SearchConfig, ChunkSplitterConfig, IngesterConfig, PipelineConfig)

## Target Files or Areas
- `docs/21_rag/rag_04_04_dto-models_config.md`
- `scripts/rag/models_config.py`
- `scripts/shared/types.py`
- `scripts/rag/pipeline.py`

## Required Changes
- Replace all 7 DTO descriptions with documentation of `RagConfigImpl`
- Document `RagConfigImpl`'s fields, types, and defaults
- Update cross-references to point to the correct Protocol and implementation
- Keep the "Implementation Notes" section referencing CI-017 (or remove if CI-017 is resolved)
- Preserve the front matter metadata (title, area, tags, related, source)

## Constraints
- Do not change the document's front matter (title, area, tags, related, source)
- Do not modify source code — this is a documentation-only change
- Preserve the existing document structure (headings, sections) where possible
- Use American English spelling per project convention

## Acceptance Criteria
- All references to the 7 removed DTOs are replaced with `RagConfigImpl` documentation
- `RagConfigImpl`'s fields, types, and defaults are accurately documented
- Cross-references to `RagConfig` Protocol are present and accurate
- No broken links remain in the document
- The document accurately reflects the current runtime contract

## Testing Expectations
- Manual verification: confirm `uv run python tools/check_docs_structure.py docs/21_rag/rag_04_04_dto-models_config.md` passes
- Manual verification: confirm the documented fields match `scripts/rag/models_config.py::RagConfigImpl`

## Documentation Impact
This issue itself documents the remediation process. After completion, CI-017 should be updated or closed.

## Out of Scope
- Modifying `scripts/rag/models_config.py`
- Modifying `scripts/shared/types.py`
- Modifying `scripts/rag/pipeline.py`
- Changing the `RagConfig` Protocol definition
- Updating other documents that may also reference the removed DTOs

## Dependencies
- CI-017 Known Issue (source of this work item)
- `scripts/rag/models_config.py` (current implementation)
- `scripts/shared/types.py` (RagConfig Protocol)

## Unresolved Questions
- Should CI-017 be closed after this rewrite, or kept until all downstream references are updated?
- Are there other documents that also need updating due to the DTO removal?

## AI Implementation Instruction
Read `scripts/rag/models_config.py`, `scripts/shared/types.py`, and `scripts/rag/pipeline.py`. Rewrite `docs/21_rag/rag_04_04_dto-models_config.md` to document `RagConfigImpl` and the `RagConfig` Protocol. Remove all references to the 7 removed DTOs. Do not modify source code.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260925-232919
- **Related target files**: docs/21_rag/rag_04_04_dto-models_config.md, scripts/rag/models_config.py, scripts/shared/types.py
