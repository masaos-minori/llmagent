## Goal

Pass the configured paraphrase count from `RagLLM.expand_queries` into the MQE parse call so the fan-out is bounded by `mqe_n_queries`, not by what the model emits (`REQ-002`: cap equals the configured count).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the single `_parse_mqe_response(raw, query)` call in `expand_queries` in `scripts/rag/llm_client.py`.
- Out of scope: `_call_llm`, `cross_encoder_rerank`, error conversion (ragrev001), context-boundary handling (ragrev002).

## Assumptions

- Re-verified at generation time: `expand_queries` calls `_parse_mqe_response(raw, query)` and has `self._cfg` available; `_mqe_prompt` already requires `cfg.mqe_n_queries` to be an `int`, so the same attribute is valid when `expand_queries` reaches the parse call.
- Ordering: Plan ragrev001's procedure `implementations/20261109-104259_01_scripts_rag_llm_client.py.md` rewrites the `try` structure of `expand_queries`; this change must be applied after it so only an argument is added to the parse call. Locate the call by symbol, not line number. Ragrev002's procedure (`implementations/20261109-104558_03_scripts_rag_llm_client.py.md`) edits a different method.
- Depends on `..._01_scripts_rag_llm_prompts.py.md` first: the new argument must exist before it is passed.

## Design decisions

- Read the count with `cast(RagConfig, self._cfg).mqe_n_queries`, mirroring the existing `_mqe_prompt(query, context, cast(RagConfig, self._cfg))` cast; no new validation, because `_mqe_prompt` already rejects a non-int value earlier in the same call path.
- Pass it by keyword (`max_paraphrases=`) for readability.

## Alternatives considered

N/A: one-argument change at a single call site.

## Implementation
### Target file
`scripts/rag/llm_client.py`

### Procedure
1. In `RagLLM.expand_queries`, change the parse call to `_parse_mqe_response(raw, query, max_paraphrases=cast(RagConfig, self._cfg).mqe_n_queries)`.
2. Extend the `expand_queries` docstring with one clause: the result holds the original query first and at most `mqe_n_queries` distinct paraphrases.

### Method
- Reuse the `cast` and `RagConfig` names already imported in the module; add no import.

### Details
- Do not move the prompt construction, change the except tuple, or touch other methods.
- Line length stays within 88; wrap the call with ruff format if needed.

## Compatibility considerations

- `expand_queries` keeps its signature and return type; the list is at most `mqe_n_queries + 1` long and deduplicated.
- `MqeStage` consumes the list unchanged (Reference File `scripts/rag/stages/mqe.py`).

## Security considerations

N/A: passes an already validated integer configuration value.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run pytest tests/rag/test_rag_stages.py tests/rag/test_llm_client_timeout.py -q` (the wiring test in the tests procedure fails on HEAD, passes after).
- `uv run ruff check scripts/rag/llm_client.py`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`.

## Completion criteria

- `expand_queries` passes `cfg.mqe_n_queries` to the parse helper and returns at most `mqe_n_queries + 1` queries for an oversized model response.
- Existing `tests/rag/test_llm_client_timeout.py` tests pass unmodified.

## Out of Scope

- Parse normalization (`scripts/rag/llm_prompts.py`), embedding concurrency, tests, and docs (separate procedures).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Pass the configured count in `expand_queries` | Completed | 20261109-151852 | 20261109-155642 | changed: scripts/rag/llm_client.py |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261109-151852 | 20261109-155642 | ruff/mypy/bandit/lint-imports/radon/check_module_size pass; targeted pytest 85 passed |

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
- **Requirement ID**: `REQ-002` (cap equals the configured paraphrase count)
- **Source issue**: issues/20261108-131120_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133800
- **Related target files**: `scripts/rag/llm_client.py`