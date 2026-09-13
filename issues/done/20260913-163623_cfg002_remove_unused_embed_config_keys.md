# Remove unused config keys embed_retry and embed_workers from RAG pipeline

## Priority
Low

## Summary
Remove `embed_retry` and `embed_workers` config fields that are defined but never used in the embedding fetch code. These fields suggest retry/concurrency capabilities that don't exist, misleading operators into thinking they control retrieval reliability.

## Background
RagConfigImpl defines `embed_retry: int` (default 3) and `embed_workers: int` (default 4). However, get_embedding() in llm_client.py makes a single HTTP POST with no retry logic, and _search_all_queries() uses asyncio.gather without any concurrency limiting. The fields have no effect on actual behavior.

## Problem
1. Misleading configuration: Operators set these values expecting them to affect reliability/performance
2. Dead code: The fields consume config space and validation effort for zero behavioral impact
3. Maintenance burden: Future developers may assume retry/concurrency logic exists when it doesn't

## Reason for Change
Remove dead config fields to eliminate confusion and reduce maintenance overhead. If retry/concurrency support is needed later, it should be implemented explicitly rather than suggested by unused config keys.

## Implementation Intent
1. Remove `embed_retry` and `embed_workers` from RagConfigImpl dataclass
2. Remove from _ALL_FIELDS and _DEFAULTS_FOR_ALL in config_resolution.py
3. Remove from RagConfigValidator if referenced
4. Update any documentation referencing these fields
5. Do NOT implement retry/concurrency — just remove the misleading fields

## Target Files or Areas
- scripts/rag/models_config.py
- scripts/rag/config_resolution.py
- scripts/shared/config_validator.py (if references exist)

## Required Changes
- RagConfigImpl: remove `embed_retry: int` and `embed_workers: int` fields
- config_resolution.py: remove from _ALL_FIELDS frozenset and _DEFAULTS_FOR_ALL dict
- Any config loader/schema files: remove references

## Constraints
- Must not break existing configs that include these fields — they will be silently ignored after removal (filtered by _ALL_FIELDS check)
- Must not implement retry/concurrency as part of this change

## Acceptance Criteria
- embed_retry and embed_workers removed from all source files
- Configs containing these fields still work (fields filtered out by _ALL_FIELDS)
- All existing tests pass
- No runtime warnings about missing fields

## Testing Expectations
- Run: pytest tests/rag/ -k config
- Verify configs with embed_retry/embed_workers still load without error
- Verify configs without these fields still work

## Documentation Impact
Update any config documentation that lists embed_retry/embed_workers as available options.

## Out of Scope
- Implementing retry logic for embedding failures
- Implementing concurrency limits for embedding fetches
- Changing the default values of existing fields

## Dependencies
N/A: none

## Unresolved Questions
Should we add a deprecation warning when these fields are present in config, before removing them entirely?

## AI Implementation Instruction
1. Read scripts/rag/models_config.py — remove lines with `embed_retry: int` and `embed_workers: int`
2. Read scripts/rag/config_resolution.py — remove from _ALL_FIELDS and _DEFAULTS_FOR_ALL
3. Search for references in shared/config_validator.py and remove if found
4. Do NOT add any new functionality — only remove dead config fields
5. Run pytest tests/rag/ -k config to verify

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-163623
- **Related target files**: scripts/rag/models_config.py, scripts/rag/config_resolution.py
