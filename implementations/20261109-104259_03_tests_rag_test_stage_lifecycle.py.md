## Goal
Add regression tests proving that a malformed MQE response degrades gracefully: `MqeStage.run()` leaves `ctx.queries == [ctx.query]` and reports the `fallback` / `mqe_exception` status without raising (`REQ-003`), and a full run through `RagPipelineStageLifecycle` continues past MQE and returns a result built from the original query (`REQ-004`).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: new tests in `tests/rag/test_stage_lifecycle.py` only.
- Depends on the production change of the sibling procedure for `scripts/rag/llm_client.py` (same Plan, `seq` 01): these tests fail until `RagLLM.expand_queries` converts malformed responses.

## Assumptions
- Overlap judgment (`tools/check_plan_target_overlaps.py`, Step 2): `plans/20261108-165604_ragrev009_dead-pipeline-stage-runner.md` also adds tests to this file (direct `_run_stage` tests). Compatible: both add independent test classes; either order works.
- Every existing test in this file patches `_run_stage`, which would hide the catch list; the lifecycle test here therefore runs the real `_run_stage` and replaces only the later stages with a recording stub, patched where the lifecycle looks the class up (`rag.stage_lifecycle`), since it imports `SearchStage` at module level.
- With `use_rerank=False` and no search results, `FusionStage`, `RerankStage`, and `AugmentStage` do not touch the database or the network, so a `MagicMock` database is enough.
- The malformed responses are produced by a small local fake client defined in this module (a `MagicMock` of `httpx.AsyncClient` with `timeout` and an `AsyncMock` `post` whose response carries the body), mirroring the pattern in `tests/rag/test_llm_client_timeout.py`; test modules do not import each other's private helpers.

## Design decisions
- Use a real `RagLLM` over the fake client so the conversion in `RagLLM.expand_queries` is exercised end to end, instead of a mocked `expand_queries` that would pass without the production fix.
- Cover the three shapes at the stage level (parametrized) and one shape at lifecycle level, which is enough because the conversion point is shared.

## Alternatives considered
N/A: the Plan fixes the test levels (stage-level over three shapes, one lifecycle-level test).

## Implementation
### Target file
`tests/rag/test_stage_lifecycle.py`

### Procedure
1. Add a module-level helper `_make_malformed_llm` (new) that returns a real `RagLLM` whose client answers HTTP 200 with a given body, built from the `mock_cfg` fixture.
2. Add a parametrized async stage-level test over the three bodies (content `null`, empty `choices`, non-JSON bytes): run `MqeStage` on a fresh `PipelineContext` and assert `ctx.queries == [ctx.query]`, no exception, and `MqeStage.get_status(ctx)` equals `("fallback", "mqe_exception")`.
3. Add one async lifecycle-level test: patch `rag.stage_lifecycle.SearchStage` with a stub whose `run` records `ctx.queries`, run `RagPipelineStageLifecycle.run(query, db=MagicMock())` with the malformed `RagLLM`, and assert a `PipelineRunResult` is returned, `result.queries == [query]`, the stub saw `[query]`, and the `MqeStage` entry of `result.stage_results` has status `fallback` and reason `mqe_exception`.
4. Confirm both tests fail before the production change and pass after it.

### Method
- Fake client: `MagicMock(spec=httpx.AsyncClient)` with `timeout` set and `post` an `AsyncMock` returning a response object whose `raise_for_status` is a no-op and whose `content` is the body bytes (`parse_http_json` reads `.content`).
- Build the lifecycle with the existing `mock_cfg`, `mock_http_client`, and `embed_url=""`, passing the real `RagLLM` as `llm`.

### Details
- Do not modify the existing tests or the pinned propagation test in `tests/rag/test_rag_stages.py`.
- Name new tests for the behavior (malformed MQE response falls back); comments in English.

## Compatibility considerations
N/A: tests only; no production contract changes in this file.

## Security considerations
N/A: tests only; the fake client performs no network access.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_stage_lifecycle.py tests/rag/test_rag_stages.py -q` (new tests green after the production change; pinned propagation test unchanged)
- `uv run ruff format tests/rag/test_stage_lifecycle.py`, `uv run ruff check tests/rag/test_stage_lifecycle.py`
- `uv run python tools/check_mock_patch_targets.py` (the stub patch targets the lifecycle module that looks up the class)

## Completion criteria
- A stage-level test per malformed shape asserts the fallback queries and the `fallback` / `mqe_exception` status without an exception.
- A lifecycle-level test asserts the run continues, the search stage receives the original query, and the result carries the MQE fallback.
- The new tests fail against the unfixed `expand_queries` and pass after the sibling change; existing tests pass unmodified.

## Out of Scope
- Production code changes, the existing `_run_stage` tests, and the ragrev009 direct `_run_stage` tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the malformed-response `RagLLM` helper and the stage-level and lifecycle-level tests | Pending | — | — | Fails until the `scripts/rag/llm_client.py` procedure (`seq` 01) lands |
| 2 | Run the validation sequence (`rules/toolchain.md`) and the targeted test modules | Pending | — | — | |

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
- **Requirement ID**: `REQ-003` (stage falls back to the original query), `REQ-004` (lifecycle run continues past a malformed MQE response)
- **Source issue**: issues/20261108-131003_ragrev001_mqe-malformed-response-abort.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-104259
- **Related target files**: `tests/rag/test_stage_lifecycle.py`
