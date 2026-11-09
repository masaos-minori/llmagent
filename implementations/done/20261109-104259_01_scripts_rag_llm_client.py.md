## Goal
Make `RagLLM.expand_queries` raise `RagExpansionError` for every malformed-LLM-response failure (`REQ-001`: null content, empty `choices`, non-JSON body), keep prompt construction outside the converted region (`REQ-002`: a configuration defect stays loud), and leave retry/timeout behavior and the stage-layer catch lists unchanged (`REQ-005`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the exception conversion inside `RagLLM.expand_queries` and its docstring, plus the companion tests in `tests/rag/test_llm_client_timeout.py`.
- Not in scope: `_call_llm`, `cross_encoder_rerank`, `scripts/rag/stages/mqe.py`, `scripts/rag/stage_lifecycle.py` (see Out of Scope).

## Assumptions
- Overlap judgments (`tools/check_plan_target_overlaps.py`, Step 2): `plans/20261108-164455_ragrev002_rag-context-boundary-injection.md` also edits `scripts/rag/llm_client.py` but only `refine_context`, a disjoint method: compatible, any order. `plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md` edits `expand_queries` and declares a dependency on this Plan's phase 2: a sequencing dependency, so this change lands first and ragrev007 later adds an argument to the parse call in the same method. `plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md` shares only `tests/rag/test_stage_lifecycle.py`, which belongs to the sibling procedure for that file.
- `orjson.JSONDecodeError` and `MqeParseError` are `ValueError` subclasses (`MqeParseError(ValueError)` in `scripts/rag/llm_prompts.py`; `parse_http_json` wraps decode errors as `ValueError`), so adding `ValueError` covers every shape in `REQ-001`. The existing explicit entries are kept to minimize the diff.
- `_mqe_prompt` builds the prompt with `str.format`, so a bad `mqe_prompt_template` can raise `KeyError`, `IndexError`, or a plain `ValueError`. Once `ValueError` is converted, leaving the prompt build inside the `try` would disguise that configuration defect as an LLM failure; moving it out is therefore required (`REQ-002`), and the test covers the `ValueError` case, not only `TypeError`.
- The existing tests build clients with `_make_fake_client` and configs with `_make_cfg` in the companion file; they are reused instead of adding an `httpx.MockTransport`, which the Plan allows ("reuse that pattern or add a transport").

## Design decisions
- Convert at the `RagLLM` boundary, matching `cross_encoder_rerank`, which already lists `ValueError`; the stage layer keeps knowing only `RagExpansionError`.
- The converted region is only the LLM call and the response parse.

## Alternatives considered
N/A: the rejected alternatives (broadening `MqeStage.run` to `Exception`, adding `ValueError` to the `_run_stage` catch list) are recorded in the Plan's Design section; both would contradict the pinned propagation test.

## Implementation
### Target file
`scripts/rag/llm_client.py`

### Procedure
1. Add the companion tests first and confirm the three malformed-shape tests fail against the current code (a plain `ValueError` escapes).
2. In `RagLLM.expand_queries`, build the prompt before the `try`, keep `_call_llm` and `_parse_mqe_response` inside it, add `ValueError` to the except tuple, and extend the docstring to say malformed responses raise `RagExpansionError`.
3. Run the validation plan.

### Method
- Evaluate `_mqe_prompt(query, context, cfg)` into a local value before the `try`; the `messages` list passed to `_call_llm` then uses that value.
- Keep `raise RagExpansionError(f"MQE expansion failed: {e}") from e` unchanged so `__cause__` is the original `ValueError`.

### Details
- Do not change `_call_llm`, `cross_encoder_rerank`, `MqeStage.run`, or `_run_stage`; the pinned test `test_run_llm_exception` in `tests/rag/test_rag_stages.py` must stay green unmodified.
- Comments and log text stay in English; no new import is needed because `ValueError` is a builtin.

### Companion test files
- `tests/rag/test_llm_client_timeout.py`
  - Procedure: add a parametrized async test over three response bodies built with `_make_fake_client` (content null, empty `choices`, non-JSON bytes) asserting `RagExpansionError` and that `__cause__` is a `ValueError`; add tests that a `TypeError` from a monkeypatched `rag.llm_client._mqe_prompt` and a `ValueError` from a malformed `mqe_prompt_template` (an unmatched brace passed through `_make_cfg`) both propagate unchanged and are not converted.
  - Validation: `uv run pytest tests/rag/test_llm_client_timeout.py -q`; the three malformed-shape tests fail before the change and pass after; the two prompt-error tests pass both before and after (verified in Step 3a: before the change nothing converts a `TypeError`/format `ValueError`, so they guard the converted region against swallowing config defects); the existing timeout tests pass unmodified.

## Compatibility considerations
`expand_queries` already documents `RagExpansionError` as its failure type; the change makes the code honor that. Its only caller is `MqeStage` (via `_run_mqe`), which already catches `RagExpansionError`. No caller was found that relied on a `ValueError` escaping.

## Security considerations
N/A: the LLM response is untrusted input already; the change only narrows which failures abort the pipeline, and the cause stays chained for logging.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_llm_client_timeout.py tests/rag/test_rag_stages.py -q`
- `uv run pytest tests/rag -q` (a stage-level test elsewhere may assume a `ValueError` escapes MQE)
- `uv run ruff format scripts/rag/llm_client.py tests/rag/test_llm_client_timeout.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `PYTHONPATH=scripts uv run lint-imports`

## Completion criteria
- `expand_queries` raises `RagExpansionError` (cause `ValueError`) for null content, empty `choices`, and a non-JSON body.
- A `TypeError` and a `ValueError` raised while building the prompt propagate unchanged.
- The pinned propagation test and the existing timeout tests pass unmodified; ruff, mypy, and lint-imports are clean.

## Out of Scope
- Widening `MqeStage.run` or `_run_stage` catch lists; rerank and refiner handling; prompt or temperature changes; retry or timeout behavior of `_call_llm`.
- Documentation: no doc change is needed (checked in Step 3a; the Plan's Documentation Impact is `N/A`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the companion tests first and confirm the malformed-shape tests fail on the current code | Completed | 20261109-125342 | 20261109-125926 | 3b: corrected companion Validation wording; stale check clean red state confirmed: 3 malformed-shape tests fail (plain ValueError escapes), 2 prompt-error guard tests pass before change |
| 2 | Move the prompt build out of the `try` and add `ValueError` to the conversion in `RagLLM.expand_queries` | Completed | 20261109-125926 | 20261109-130042 | tests added; now editing expand_queries green: 74 passed incl. pinned test_run_llm_exception; ruff/mypy/lint-imports clean |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20261109-132200 | full suite 11987 passed/9 skipped; diff-cover 100% >= 90; docs N/A verified |

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
- **Requirement ID**: `REQ-001` (convert malformed responses to `RagExpansionError`), `REQ-002` (prompt build stays unconverted), `REQ-005` (retry/timeout and catch lists unchanged)
- **Source issue**: issues/20261108-131003_ragrev001_mqe-malformed-response-abort.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-104259
- **Related target files**: `scripts/rag/llm_client.py`, `tests/rag/test_llm_client_timeout.py`