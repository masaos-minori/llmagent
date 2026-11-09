## Goal
- Bound the MQE fan-out by configuration rather than by what the model emits: normalize and deduplicate the expanded query list (including against the original query), cap it at `mqe_n_queries + 1` with the original first, and limit concurrent embedding calls with a small semaphore.

## Priority
Medium

## Scope
- **In-Scope**:
  - `_parse_mqe_response` strips, case-insensitively deduplicates (against each other and the original query), drops whitespace-only entries, and caps paraphrases at the configured count; `RagLLM.expand_queries` passes the configured count.
  - `_search_all_queries` bounds concurrent `get_embedding` calls with a module-level constant semaphore size.
  - Unit tests (duplicate, oversized, whitespace-only) and an async concurrency-count test; the MQE description in the search-stage doc.
- **Out-of-Scope**:
  - Prompt wording or template contract, RRF, a new configuration key for the concurrency limit (see Unknowns), per-query retry.
- **Dependencies**: Sequencing against sibling Plans that edit the same code (order only, not a data dependency):
  - **Depends on**: plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md | phase 2 | both edit `RagLLM.expand_queries` in `scripts/rag/llm_client.py`; land the malformed-response conversion first so this plan only adds an argument to the parse call.
  - **Depends on**: plans/20261108-164823_ragrev004_search-bm25-coupling.md | phase 2 | both edit `_search_all_queries` in `scripts/rag/stages/search.py`; land the leg split first, then wrap the embedding gather.

## Background
Review finding F-009. `_parse_mqe_response` (`scripts/rag/llm_prompts.py:135-157`) returns `[original_query] + valid` where `valid` keeps every non-empty string, with no normalization, dedup, or cap; the signature has no access to config. `mqe_n_queries` (default 3, `scripts/rag/config_resolution.py:83`, `config/rag_pipeline_mcp_server.toml:69`) is used only in the prompt text (`llm_prompts.py:123-129`). `_search_all_queries` (`scripts/rag/stages/search.py:41-44`) starts one `get_embedding` per query in one `asyncio.gather` with no concurrency bound, then runs two SQL searches per query. `RagScorer.rrf_merge` adds `1/(rrf_k+rank)` once per list, so a duplicated query double-counts its ranking. `_parse_mqe_response` has no direct test callers (checked in Step 3: only `llm_client.py` and `llm_prompts.py` reference it), and `docs/21_rag/rag_03_04_query_pipeline-search-stages.md:34` says the variant count is controlled by `mqe_n_queries`, which is untrue today.

## Problem
A chatty or looping model can trigger dozens of concurrent embedding requests against one local embedding server, and duplicated queries bias the fused ranking toward the duplicated list.

## Reason for Change
The fan-out size should be a property of configuration, not of the model's output.

## Implementation Intent
Add an optional `max_paraphrases` argument to `_parse_mqe_response` (default unbounded to keep the helper signature compatible) and have `expand_queries` pass `cfg.mqe_n_queries`; normalize with strip plus case-folded dedup that keeps the first spelling and the original query first. Wrap each `get_embedding` task in a shared `asyncio.Semaphore` created per call of `_search_all_queries`, sized by a module constant, keeping the single `gather` and sequential SQL.

## Requirements
- `REQ-001`: Paraphrases are stripped and deduplicated case-insensitively against each other and the original query; whitespace-only entries are dropped; the original query stays first.
- `REQ-002`: The result has at most `mqe_n_queries` paraphrases (so at most `mqe_n_queries + 1` queries); `RagLLM.expand_queries` passes the configured value.
- `REQ-003`: Concurrent `get_embedding` calls from one `_search_all_queries` run never exceed the semaphore size; results and diagnostics are unchanged for inputs within the bound.
- `REQ-004`: The parse helper stays backward compatible: without the new argument its output keeps the old shape (dedup still applies).
- `REQ-005`: The search-stage doc states that the fan-out is capped and deduplicated and that embedding concurrency is bounded.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/llm_prompts.py` | Modify | Normalize, dedup, and cap in `_parse_mqe_response` (new optional `max_paraphrases`) | `REQ-001`, `REQ-002`, `REQ-004` / AC-1, AC-2, AC-4 | L135-157 keeps every non-empty string, no cap or dedup (checked in Step 3) | `tests/rag/test_rag_stages.py` | Verified |
| `scripts/rag/llm_client.py` | Modify | Pass `cfg.mqe_n_queries` into the parse call in `expand_queries` | `REQ-002` / AC-2 | Parse call at L157, `self._cfg` available (checked in Step 3) | `tests/rag/test_rag_stages.py`, `tests/rag/test_llm_client_timeout.py` | Verified |
| `scripts/rag/stages/search.py` | Modify | Semaphore-bounded embedding fetch inside the existing `gather` | `REQ-003` / AC-3 | Unbounded `asyncio.gather` over `get_embedding` in `_search_all_queries` (checked in Step 3; re-verified in Step 3a, symbol-based because ragrev004 also edits this function) | `tests/rag/test_rag_stages.py` | Verified |
| `tests/rag/test_rag_stages.py` | Modify | Parse tests (duplicate, oversized, whitespace-only, original-first) and an async concurrency-count test | `REQ-001`..`REQ-004` / AC-1..AC-4 | Holds the MQE and `SearchStage` tests (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Modify | Correct the MQE variant-count statement (L34); state the cap, dedup, and bounded embedding concurrency | `REQ-005` / AC-5 | L34 says the count is controlled by `mqe_n_queries` (checked in Step 3) | docs gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/config_resolution.py` | `mqe_n_queries` default and validation (L50, L83) | `REQ-002` |
| `scripts/shared/types.py` | `RagConfig.mqe_n_queries: int` (L113) | `REQ-002` |
| `scripts/rag/stages/mqe.py` | Stage consuming `expand_queries`; unchanged | `REQ-002` |
| `scripts/rag/repository.py` | `rrf_merge` list-count behavior that dedup protects | `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`): a response with the original query repeated plus five duplicates (mixed case and padding) yields `[original]` plus the distinct paraphrases only.
- AC-2 (`REQ-002`): a response with ten distinct paraphrases and `mqe_n_queries=3` yields four queries.
- AC-3 (`REQ-003`): with N queries greater than the limit, a recording fake `get_embedding` observes a maximum in-flight count not above the limit; all queries are still embedded.
- AC-4 (`REQ-004`): calling `_parse_mqe_response(raw, query)` without the argument returns deduplicated output of the same shape.
- AC-5 (`REQ-005`): the doc states cap, dedup, and bounded concurrency and no longer overstates configuration control; docs checkers pass.

## Tests
- `REQ-001`: parametrized parse tests (duplicates, case, whitespace-only, original duplicate, order).
- `REQ-002`: oversized response with configured count.
- `REQ-003`: async test counting concurrent fake `get_embedding` calls.
- `REQ-004`: legacy-signature call.
- Static: `uv run ruff check`, `uv run mypy`.

## Documentation Impact
Yes (`REQ-005`): `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` (located via `docs/00_index.md` RAG rows); this file is also edited by `plans/20261108-164823_ragrev004_search-bm25-coupling.md` in a different paragraph. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese`.

## Assumptions
- `mqe_n_queries` means the number of paraphrases (the prompt asks for that many), so the total cap is `mqe_n_queries + 1`; the Issue states the same cap.
- The embedding concurrency limit is a module constant rather than a new configuration key, to avoid widening the config surface (`config/*.toml`, reference table); the Issue's "configured limit" is read as "a configured constant" (UNK-01).
- Overlap judgment (Step 8b): `scripts/rag/llm_client.py` (with `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` and `plans/20261108-164455_ragrev002_rag-context-boundary-injection.md`), `scripts/rag/stages/search.py`, `tests/rag/test_rag_stages.py`, and `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` (with `plans/20261108-164823_ragrev004_search-bm25-coupling.md`) are shared; judged sequencing dependencies, recorded under Scope Dependencies: ragrev001 and ragrev004 land first, ragrev002 touches a different method.
- Step 3a correction (plan-to-implementation-procedure): `tests/rag/test_llm_client_timeout.py` is not an `Implementation Target Files` row, so the `expand_queries` wiring test for `REQ-002` lives in `tests/rag/test_rag_stages.py` (a `RagLLM` built with a `SimpleNamespace` config, `_call_llm` patched); `mqe_n_queries <= 0` is clamped to zero paraphrases so the cap never becomes a negative slice (edge case of `REQ-002`, no new requirement).
- Step 3a correction: sibling Plans ragrev001 and ragrev004 are already converted to procedures (`implementations/20261109-104259_01_scripts_rag_llm_client.py.md`, `implementations/20261109-121538_02_scripts_rag_stages_search.py.md`) but not yet executed, so the code still has the pre-change shape; procedures locate code by symbol, not by line number.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether the embedding concurrency limit must be a config key | Owner preference | Default constant; a config key would be a separate Plan (config, reference table, docs) | False |
| UNK-02 | Appropriate default concurrency value for the local embedding server | No load data | Start at a small constant (the procedure phase picks and records the value); tune after measurement | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/llm_prompts.py` | Modify | Low (one private helper; one production caller) | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/llm_client.py` | Modify | Low (one call site) | 2 | N/A | not applicable (rsynced) |
| `scripts/rag/stages/search.py` | Modify | Medium (retrieval stage of every query) | 1 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_stages.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files). Architecture: `llm_prompts` is imported by `llm_client`; no new import edges; `lint-imports` 6 contracts kept at plan time. Dependency graph: `_parse_mqe_response` has a single production caller (`llm_client.py:157`) and no direct test callers; `_search_all_queries` is called only by `SearchStage.run`. Complexity: `_parse_mqe_response` B (7) and `_search_all_queries` B (9) are already near the B ceiling, so the normalization goes into a small helper and the semaphore wrapper into a small nested coroutine to avoid pushing either into C.

Alternatives: (a) cap in `MqeStage` instead of the parser rejected (the parser owns validation of the model output and the stage would need config-aware dedup); (b) a config key for concurrency rejected for now (UNK-01). Chosen: parser-level normalization with an optional argument, constant-sized semaphore.

Persisted schema check: not applicable.

Validation baseline: `vulture`/`bandit` pre-existing findings recorded in `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md` (source unchanged); `diff-cover`: none at plan time, 90 percent at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Parse tests and the concurrency-count test (`REQ-001`..`REQ-004`; `tests/rag/test_rag_stages.py`)
2. **Phase 2: Normalize, cap, bound**
   - [ ] Normalize/dedup/cap with the optional argument (`REQ-001`, `REQ-002`, `REQ-004`; `scripts/rag/llm_prompts.py`)
   - [ ] Pass the configured count (`REQ-002`; `scripts/rag/llm_client.py`)
   - [ ] Semaphore around the embedding fetch (`REQ-003`; `scripts/rag/stages/search.py`)
3. **Phase 3: Documentation**
   - [ ] Correct and extend the MQE description (`REQ-005`; `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] `uv run pytest tests/rag -q`, lint/type gates, docs gates; deploy hand-off to `skills/deploy/SKILL.md` after commit and push, at the user's decision (all requirements; `scripts/rag/stages/search.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/llm_prompts.py`, `scripts/rag/llm_client.py` | Unit | `uv run pytest tests/rag/test_rag_stages.py tests/rag/test_llm_client_timeout.py -q` | new tests fail on HEAD, pass after |
| `scripts/rag/stages/search.py` | Async unit | `uv run pytest tests/rag/test_rag_stages.py -q -k "embed or search"` | max in-flight within the limit |
| whole RAG | Regression | `uv run pytest tests/rag -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: capping drops useful paraphrases when the model returns more than asked → **Mitigation**: the cap equals what the prompt requests; first-N order is kept, so the model's most relevant entries stay.
- **Risk**: the semaphore slows retrieval for many queries → **Mitigation**: the limit is small but above typical `mqe_n_queries + 1` (4), so normal runs are not delayed; UNK-02 tunes it.
- **Risk**: case-insensitive dedup merges queries differing only by case, harmless for embeddings and FTS → **Mitigation**: documented; the original spelling is kept.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — |  |
| 2 | Phase 2: normalize, cap, bound | In Progress | — | — |  |
| 3 | Phase 3: documentation | In Progress | — | — |  |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-133800_01_scripts_rag_llm_prompts.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-133800_02_scripts_rag_llm_client.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-133800_03_scripts_rag_stages_search.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-133800_04_tests_rag_test_rag_stages.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-133800_05_docs_21_rag_rag_03_04_query_pipeline-search-stages.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131120_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-165229
- **Related target files**: `scripts/rag/llm_prompts.py`, `scripts/rag/llm_client.py`, `scripts/rag/stages/search.py`, `tests/rag/test_rag_stages.py`, `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `llm_prompts.py:135-157` | `scripts/rag/llm_prompts.py` | Phase 2 | AC-1 | parse dedup tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_rag_stages.py` | Phase 1 | AC-1 | parse dedup tests | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/llm_prompts.py` | Phase 2 | AC-2 | oversized test | Explicit in issue |
| REQ-002 | Required Changes 2; `llm_client.py:157` | `scripts/rag/llm_client.py` | Phase 2 | AC-2 | oversized test | Confirmed by repository evidence |
| REQ-002 | Testing Expectations | `tests/rag/test_rag_stages.py` | Phase 1 | AC-2 | oversized test | Explicit in issue |
| REQ-003 | Required Changes 3; `search.py:41-44` | `scripts/rag/stages/search.py` | Phase 2 | AC-3 | concurrency-count test | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | `tests/rag/test_rag_stages.py` | Phase 1 | AC-3 | concurrency-count test | Explicit in issue |
| REQ-004 | Constraints (helper compatibility) | `scripts/rag/llm_prompts.py` | Phase 2 | AC-4 | legacy-signature test | Derived from confirmed evidence |
| REQ-004 | Constraints | `tests/rag/test_rag_stages.py` | Phase 1 | AC-4 | legacy-signature test | Derived from confirmed evidence |
| REQ-005 | Documentation Impact; doc L34 | `docs/21_rag/rag_03_04_query_pipeline-search-stages.md` | Phase 3 | AC-5 | docs gates | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-133800 -->