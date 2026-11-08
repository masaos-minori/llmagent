## Goal
- Make `RagLLM.expand_queries` convert every malformed-LLM-response failure (null content, empty `choices`, non-JSON body) into `RagExpansionError`, so `MqeStage` falls back to the original query with reason `mqe_exception` instead of aborting the whole `augment()` call.

## Priority
High

## Scope
- **In-Scope**:
  - `scripts/rag/llm_client.py`: widen the failure conversion in `RagLLM.expand_queries` to include `ValueError` raised by `_call_llm` (`parse_http_json` / `extract_llm_content`), while keeping prompt construction outside the converted region.
  - Regression tests at the `RagLLM.expand_queries` boundary and at the pipeline-lifecycle level for the three malformed-response shapes.
- **Out-of-Scope**:
  - Widening `MqeStage.run` or `_run_stage` catch lists (the existing test `tests/rag/test_rag_stages.py::test_run_llm_exception` pins that a non-`RagExpansionError` exception propagates from the stage; that contract stays).
  - Rerank and refiner handling (already tolerant), prompt or temperature changes, retry or timeout behavior of `_call_llm`.
- **Dependencies**: N/A: none (the archived `exc001` issue is history only; its stage-level broadening was never applied, see Assumptions).

## Background
Review finding F-001 of the `scripts/rag` adversarial review. `RagLLM._call_llm` calls `parse_http_json` and `extract_llm_content`, which raise a plain `ValueError` for invalid JSON, a non-dict body, empty `choices`, or non-string content (`scripts/shared/json_utils.py:120-170`). `RagLLM.expand_queries` converts only `httpx.HTTPStatusError`, `httpx.RequestError`, `orjson.JSONDecodeError` and `MqeParseError` (`scripts/rag/llm_client.py:160-166`), `MqeStage.run` catches only `RagExpansionError` (`scripts/rag/stages/mqe.py:50`), and `RagPipelineStageLifecycle._run_stage` catches only `RuntimeError`, `sqlite3.OperationalError`, `httpx.HTTPStatusError`, `httpx.RequestError`, `TimeoutError` (`scripts/rag/stage_lifecycle.py:75-81`). `cross_encoder_rerank` already includes `ValueError` in its handler (`llm_client.py:194`). The MCP service calls `pipeline.augment()` with no handler (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py:177,194`).

## Problem
An LLM backend that answers HTTP 200 with null content, empty `choices`, or a non-JSON body makes every RAG query fail with an unhandled `ValueError`, although MQE is optional and the original query alone would work.

## Reason for Change
The pipeline design says each stage degrades independently. A transient LLM quirk currently becomes a complete retrieval outage and an unhandled error in the MCP service.

## Implementation Intent
Convert at the `RagLLM` boundary, using the same `RagExpansionError` the other failure causes use, so the stage layer keeps knowing only `RagExpansionError`. Scope the conversion to the LLM call and the response parse, not the prompt build, so a configuration defect (for example a bad `mqe_prompt_template`) is not disguised as an LLM quirk.

## Requirements
- `REQ-001`: `RagLLM.expand_queries` raises `RagExpansionError` (not `ValueError`) for HTTP 200 with null content, with empty `choices`, and with a non-JSON body.
- `REQ-002`: Prompt construction (`_mqe_prompt`) failures are not converted: a `TypeError`/format error from a bad config still propagates.
- `REQ-003`: With such a response, `MqeStage.run()` leaves `ctx.queries == [ctx.query]`, does not raise, and the stage result is `fallback` / `mqe_exception`.
- `REQ-004`: A full pipeline run through the stage lifecycle with a malformed MQE response continues past MQE and returns a result from the original query.
- `REQ-005`: Retry/timeout behavior of `_call_llm` and the stage-layer catch lists are unchanged (the pinned propagation test stays green).

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/llm_client.py` | Modify | Add `ValueError` to the `expand_queries` conversion and keep `_mqe_prompt` outside the try region | `REQ-001`, `REQ-002`, `REQ-005` / AC-1, AC-2, AC-5 | `expand_queries` L139-166 catches 4 types but not plain `ValueError`; `parse_http_json`/`extract_llm_content` raise `ValueError` (checked in Step 3) | `tests/rag/test_llm_client_timeout.py` | Verified |
| `tests/rag/test_llm_client_timeout.py` | Modify | Add `httpx.MockTransport` regression tests for the three malformed shapes at `expand_queries` and for prompt-error non-conversion | `REQ-001`, `REQ-002` / AC-1, AC-2 | File exists and already holds `RagLLM`/client tests (checked in Step 3) | self | Verified |
| `tests/rag/test_stage_lifecycle.py` | Modify | Add a lifecycle-level test: malformed MQE response, pipeline continues, stage result `fallback`/`mqe_exception`, original query searched | `REQ-003`, `REQ-004` / AC-3, AC-4 | File exists with `_run_stage` tests (`test_failure_status_on_exception` L256) (checked in Step 3) | self | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/stages/mqe.py` | `MqeStage.run` catch (L50) and `get_status` fallback reason; stays unchanged | `REQ-003` |
| `scripts/rag/stage_lifecycle.py` | `_run_stage` catch list; unchanged by design | `REQ-004`, `REQ-005` |
| `scripts/shared/json_utils.py` | Source of the `ValueError` raised by `parse_http_json` / `extract_llm_content` | `REQ-001` |
| `scripts/rag/llm_prompts.py` | `MqeParseError(ValueError)` (L48) and `_mqe_prompt` raise sites (TypeError/format) | `REQ-002` |
| `scripts/rag/exceptions.py` | `RagExpansionError` definition | `REQ-001` |
| `tests/rag/test_rag_stages.py` | Existing MQE stage tests incl. the pinned propagation test (L602-611) that must stay green | `REQ-005` |

## Acceptance Criteria
- AC-1 (`REQ-001`): the three malformed shapes each raise `RagExpansionError` from `expand_queries`, with `__cause__` the original `ValueError`.
- AC-2 (`REQ-002`): a config-defect `TypeError` from `_mqe_prompt` still propagates unchanged.
- AC-3 (`REQ-003`): `MqeStage.run()` with a malformed-response transport leaves `ctx.queries == [ctx.query]`, `ctx._fallback_reason == "mqe_exception"`.
- AC-4 (`REQ-004`): a lifecycle run with a malformed MQE response reaches search with the original query and returns a `PipelineRunResult`.
- AC-5 (`REQ-005`): `tests/rag/test_rag_stages.py::...::test_run_llm_exception` and the existing timeout tests pass unmodified.

## Tests
- `REQ-001`: parametrized `httpx.MockTransport` test (the file currently uses its own fake client, so reuse that pattern or add a transport; null content, empty `choices`, non-JSON body) asserting `RagExpansionError`.
- `REQ-002`: monkeypatched `_mqe_prompt` raising `TypeError` asserting propagation.
- `REQ-003`: stage-level test over the same three shapes.
- `REQ-004`: one lifecycle-level test with a real `RagLLM` over a malformed transport.
- `REQ-005`: run the existing stage and timeout test modules unmodified.

## Documentation Impact
N/A: no doc change required; if the RAG error-handling reference lists MQE failure causes, the implementation phase adds the malformed-response cause there (locate via `docs/00_index.md` "Document References by Task", RAG row, before deciding).

## Assumptions
- `orjson.JSONDecodeError` and `MqeParseError` are `ValueError` subclasses (`scripts/rag/llm_prompts.py:48`; `parse_http_json` wraps decode errors as `ValueError`), so one `ValueError` entry covers them all; the explicit entries may remain for readability.
- The archived `exc001` issue asked for a broad stage catch; current source and the pinned test show it was archived without that change (MQE stage still catches only `RagExpansionError`, the last commit touching `mqe.py` is `6ed5d10bd`, a refactor of the exception base class). This plan intentionally takes the narrower boundary-conversion route that the Issue chose.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether `exc001` was implemented then reverted or archived with no code change | Full git history review of `mqe.py` beyond the last few commits | Non-blocking: current source and the pinned propagation test are the authority; no action depends on the answer | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/llm_client.py` | Modify | Low (one method's exception conversion; only `MqeStage` calls `expand_queries`) | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_llm_client_timeout.py` | Modify | Low (tests only) | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_stage_lifecycle.py` | Modify | Low (tests only) | N/A | N/A | not applicable (rsynced) |

## Design
Path A (3 target files, no public-interface change: `expand_queries` already documents `RagExpansionError` as its failure type, the change makes the code honor that contract).

Alternatives considered: (a) widen `MqeStage.run` to `except Exception` (exc001's proposal) rejected because it swallows programming errors and contradicts the pinned propagation test; (b) add `ValueError` to `_run_stage` rejected because the Issue and design keep the stage layer ignorant of transport details. Chosen: boundary conversion in `RagLLM`, matching `cross_encoder_rerank`, with the prompt build moved outside the `try` so configuration defects stay loud (`REQ-002`).

Validation baseline (Step 5): `radon cc scripts/rag/llm_client.py -s` highest complexity is `cross_encoder_rerank` B (8); `expand_queries` A (2). `vulture scripts/ --min-confidence 80` exits 3 with pre-existing unrelated findings; `bandit -r scripts/` exits 1 with pre-existing unrelated findings. `diff-cover`: no changed lines exist at plan time, so there is no baseline number; the implementation phase must reach the `rules/toolchain.md` threshold (90 percent on changed lines).

## Implementation steps
1. **Phase 1: Regression tests first**
   - [ ] Add three-shape `expand_queries` test and prompt-error test (`REQ-001`, `REQ-002`; `tests/rag/test_llm_client_timeout.py`)
   - [ ] Add lifecycle-level fallback test (`REQ-003`, `REQ-004`; `tests/rag/test_stage_lifecycle.py`)
2. **Phase 2: Boundary conversion**
   - [ ] Add `ValueError` to the conversion in `expand_queries` and move `_mqe_prompt` outside the try (`REQ-001`, `REQ-002`, `REQ-005`; `scripts/rag/llm_client.py`)
3. **Phase 3: Deployment & Verification**
   - [ ] Run the validation sequence of `rules/toolchain.md`; the scripts change is committed and pushed first, then deploy via a hand-off to `skills/deploy/SKILL.md` at the user's decision (all requirements; `scripts/rag/llm_client.py`)

### Release units
N/A: no release unit

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/llm_client.py` | Unit (MockTransport) | `uv run pytest tests/rag/test_llm_client_timeout.py -q` | new tests fail before the fix, pass after |
| `tests/rag/test_stage_lifecycle.py` | Integration (lifecycle) | `uv run pytest tests/rag/test_stage_lifecycle.py tests/rag/test_rag_stages.py -q` | green, pinned propagation test unchanged |
| touched files | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports` | clean |

## Risks
- **Risk**: converting `ValueError` hides a genuine programming `ValueError` raised inside the call/parse region → **Mitigation**: the region is only `_call_llm` plus `_parse_mqe_response`; prompt build stays outside (`REQ-002`); the cause is chained and the stage logs it.
- **Risk**: a stage-level test elsewhere assumes a `ValueError` escapes MQE → **Mitigation**: only `test_run_llm_exception` was found and it uses a generic `Exception` at the stage, unaffected; the implementation phase runs all of `tests/rag/`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: regression tests first | Pending | — | — | |
| 2 | Phase 2: boundary conversion | Pending | — | — | |
| 3 | Phase 3: deployment and verification | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131003_ragrev001_mqe-malformed-response-abort.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-164302
- **Related target files**: `scripts/rag/llm_client.py`, `tests/rag/test_llm_client_timeout.py`, `tests/rag/test_stage_lifecycle.py`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `llm_client.py:160-166` | `scripts/rag/llm_client.py` | Phase 2 | AC-1 | three-shape test | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_llm_client_timeout.py` | Phase 1 | AC-1 | three-shape test | Explicit in issue |
| REQ-002 | Design (prompt outside try) | `scripts/rag/llm_client.py` | Phase 2 | AC-2 | prompt-error test | Derived from confirmed evidence |
| REQ-002 | Design (prompt outside try) | `tests/rag/test_llm_client_timeout.py` | Phase 1 | AC-2 | prompt-error test | Derived from confirmed evidence |
| REQ-003 | Required Changes 3; Acceptance Criteria 1-2 | `tests/rag/test_stage_lifecycle.py` | Phase 1 | AC-3 | stage/lifecycle test | Explicit in issue |
| REQ-004 | Acceptance Criteria 3; Testing Expectations | `tests/rag/test_stage_lifecycle.py` | Phase 1 | AC-4 | lifecycle test | Explicit in issue |
| REQ-005 | Constraints; `test_rag_stages.py:602-611` | `scripts/rag/llm_client.py` | Phase 2 | AC-5 | existing stage and timeout tests | Confirmed by repository evidence |
