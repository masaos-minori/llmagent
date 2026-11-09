## Goal

Add tests that pin MQE normalization, the paraphrase cap, the `expand_queries` wiring, backward compatibility of the parse helper, and the embedding concurrency bound (`REQ-001`..`REQ-004`: normalize and dedup, cap, bounded concurrency, compatible signature).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new tests in `tests/rag/test_rag_stages.py` (parse tests, an `expand_queries` wiring test, and an async concurrency-count test next to the existing `TestSearchStage` / `TestSearchDiagnostics` tests).
- Plan step 1 (tests first): write these before the code procedures run.

## Assumptions

- Re-verified at generation time: `tests/rag/test_rag_stages.py` has `TestSearchStage`, `TestSearchDiagnostics`, `TestMqeStage`, `TestRunMqe`; it patches `rag.llm_client.get_embedding` with `AsyncMock` and uses `SimpleNamespace(top_k_search=10)` configs; it contains no `RagLLM` test and no direct `_parse_mqe_response` test.
- `tests/rag/test_llm_client_timeout.py` is not a target row, so the `expand_queries` wiring test goes here with a `SimpleNamespace` config (`mqe_prompt_template` string with `{n_queries}` and `{query}`, `mqe_n_queries` int) and `RagLLM._call_llm` patched (Plan Assumptions, Step 3a correction).
- Overlap with `implementations/20261109-121538_01_tests_rag_test_rag_stages.py.md` (ragrev004): compatible; that procedure adds failure-isolation tests for the search legs. Locate insertion points by class name. The new concurrency test must tolerate the leg-split code that ragrev004 introduces (it patches `get_embedding` and the repository, as the existing tests do).

## Design decisions

- Parse tests are parametrized over raw model outputs and call `_parse_mqe_response` directly (import from `rag.llm_prompts`).
- The concurrency test patches `rag.llm_client.get_embedding` with an async function that increments an in-flight counter, awaits `asyncio.sleep(0)` a few times, records the maximum, and decrements; the query count is the limit plus five, with the limit imported as `_EMBED_CONCURRENCY` (new) from `rag.stages.search`.

## Alternatives considered

N/A: tests follow the existing class layout and the Plan's Tests section.

## Implementation
### Target file
`tests/rag/test_rag_stages.py`

### Procedure
1. Add a `TestParseMqeResponse` (new) class: a parametrized test where the original query repeats and five duplicates with mixed case and padding appear, asserting `[original]` plus only the distinct paraphrases in first-seen order (AC-1); whitespace-only and non-string entries are dropped; the original stays first.
2. In the same class: a test with ten distinct paraphrases and `max_paraphrases=3` (new keyword) yielding four queries (AC-2); a test that `max_paraphrases=0` yields only the original.
3. In the same class: a legacy-signature test calling `_parse_mqe_response(raw, query)` without the keyword and asserting the deduplicated output of the same shape (AC-4).
4. Add an async `expand_queries` wiring test: `RagLLM` with a `SimpleNamespace` config (`mqe_n_queries=3`), `_call_llm` patched to return a JSON array of ten distinct paraphrases, asserting four queries (AC-2, `REQ-002`).
5. In `TestSearchStage` or `TestSearchDiagnostics`: add an async test with `_EMBED_CONCURRENCY` (new) plus five queries asserting the recorded maximum in-flight count is at most the limit and that `get_embedding` was awaited once per query (AC-3).

### Method
- Build raw outputs with `orjson.dumps(list)` decoded to `str`, or literal JSON strings; no network.
- The concurrency fake and counters live inside the test function; no new fixture is required.

### Details
- Confirm each new test fails on HEAD for the intended reason (no dedup, no cap, no bound), not through an import error caused by a not-yet-created name; the new-name tests may fail on import until the code procedures run, which is acceptable for the tests-first step and should be noted in the Execution Status Notes.
- Do not weaken or edit existing assertions.

## Compatibility considerations

N/A: test-only change; existing tests are not modified.

## Security considerations

N/A: test-only change.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_stages.py -q` and `uv run pytest tests/rag/test_rag_stages.py -q -k "embed or search"`.
- `uv run pytest tests/rag -q`.
- `uv run ruff check tests/rag/test_rag_stages.py` and `uv run ruff format --check tests/rag/test_rag_stages.py`.

## Completion criteria

- AC-1 to AC-4 each have at least one test; the concurrency test pins AC-3.
- The new tests fail before the code procedures and pass after; no existing test was weakened; ruff is clean.

## Out of Scope

- Production code and documentation changes (separate procedures).
- Search-leg failure-isolation tests (ragrev004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add parse tests and the `expand_queries` wiring test | Completed | 20261109-151852 | 20261109-155642 | TestParseMqeResponseNormalization (5 tests) + expand_queries wiring test added |
| 2 | Add the embedding concurrency-count test | Completed | 20261109-151852 | 20261109-155642 | test_search_embedding_concurrency_is_bounded added |
| 3 | Confirm the new tests fail on HEAD, then run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-151852 | 20261109-155642 | 6 new tests confirmed failing on HEAD for intended reasons (concurrency test via ImportError on _EMBED_CONCURRENCY); gates + full suite 12029 passed; diff-cover 100% |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`..`REQ-004` (tests for normalize and dedup, cap, bounded concurrency, compatible signature)
- **Source issue**: issues/20261108-131120_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133800
- **Related target files**: `tests/rag/test_rag_stages.py`