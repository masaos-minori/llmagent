# MQE paraphrases are neither capped nor deduplicated before fan-out

## Priority
Medium

## Summary
`_parse_mqe_response` returns `[original_query] + valid` with no limit and no deduplication, and the search stage then embeds and searches every entry, so a model that repeats the query or returns many paraphrases multiplies requests and double-counts a ranking in RRF.

## Background
Review finding F-009. Evidence (Explicit in code): `scripts/rag/llm_prompts.py` `_parse_mqe_response` keeps every non-empty string of the parsed array; `mqe_n_queries` only appears in the prompt text. `scripts/rag/stages/search.py` `_search_all_queries` starts one `get_embedding` task per query with `asyncio.gather` and no concurrency limit, then runs two SQL searches per query. `RagScorer.rrf_merge` adds `1/(rrf_k+rank)` once per list, so an exact duplicate of the original query adds its list twice. The token budget (`_MQE_MAX_TOKENS`) bounds the count only indirectly.

## Problem
A chatty or looping model can trigger dozens of concurrent embedding requests against a single local embedding server, and duplicated queries bias the fused ranking toward the duplicated list.

## Reason for Change
The fan-out size should be a property of configuration, not of what the model chooses to emit.

## Implementation Intent
Normalize the expanded list (strip, case-insensitive dedup including the original query) and cap it at the configured `mqe_n_queries + 1`; bound embedding concurrency with a small semaphore.

## Target Files or Areas
- `scripts/rag/llm_prompts.py` (`_parse_mqe_response`)
- `scripts/rag/stages/search.py` (`_search_all_queries`)
- `tests/rag/` MQE and search tests

## Required Changes
- Deduplicate paraphrases against each other and against the original query.
- Cap the number of queries at the configured value.
- Limit concurrent embedding calls.
- Add tests for duplicate, oversized and whitespace-only outputs.

## Constraints
- Keep the original query as the first element.
- Do not change the prompt template contract.

## Acceptance Criteria
- A response containing the original query again and five duplicates yields at most the configured number of distinct queries.
- Embedding concurrency never exceeds the configured limit.

## Testing Expectations
- Unit tests for `_parse_mqe_response` and an async test that counts concurrent `get_embedding` calls.
- ruff and mypy on touched files.

## Documentation Impact
No documentation change expected beyond the MQE description if it states the query count.

## Out of Scope
- Prompt wording changes.
- Changing RRF.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Keep the change minimal and confined to the Target Files or Areas. Do not rewrite unrelated files, keep public behavior unchanged unless Required Changes says otherwise, and do not implement items listed under Out of Scope. Add the tests named in Testing Expectations before or with the fix. If a requirement is unclear, stop and report the open question instead of guessing.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261108-131120
- **Related target files**: `scripts/rag/llm_prompts.py`, `scripts/rag/stages/search.py`, `tests/rag/`
