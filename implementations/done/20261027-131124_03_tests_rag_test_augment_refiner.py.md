# Procedure: Refiner-path sanitization test with a captured prompt

## Goal
- Add unit coverage proving `RagLLM.refine_context` sanitizes chunk content before it enters the
  refiner prompt, by constructing a real `RagLLM` with a mock `httpx.AsyncClient` and asserting on
  the captured request body (REQ-001: refiner prompt sanitization; AC-1).

## Scope
- New test class plus one helper in `tests/rag/test_augment_refiner.py`; existing tests unchanged.
- The tests call `RagLLM.refine_context` directly (the Plan's chosen site for the capture), not
  through `AugmentRefiner`.

## Assumptions
- Sequencing with the rag003 Plan (`plans/20261027-110727_rag003_rag-url-key-ambiguity.md`):
  rag003 renames the `rag_service_url` config key used by this file's `_make_cfg` fixture. The new
  tests here never set that key, so they are unaffected by either landing order; if rag003 lands
  first, keep using `_make_cfg` as renamed.
- `RagLLM.__init__(client, llm_url, cfg=None)` accepts an injected client, so no network is needed;
  `refine_context` posts via `self._client.post` and parses with `extract_llm_content(parse_http_json(resp))`.
- Mock response contract: `parse_http_json` reads `orjson.loads(resp.content)` (not `resp.json()`),
  so the mock object's `raise_for_status()` must return `None` and its `content` attribute must be
  `orjson.dumps({"choices": [{"message": {"content": "refined summary"}}]})` (bytes).

## Design decisions
- Capture the exact JSON body passed to `client.post` (the Plan Background notes the client is
  injected for exactly this): behavior test on the prompt text, not source introspection.
- Reuse the file's existing `_make_cfg()` for `llm_url` and the chunk fixture type `RagHit` so the
  new tests match the file's fixture style.

## Alternatives considered
- Testing through `AugmentRefiner.run_refiner`: rejected — `run_refiner` delegates to
  `rag.pipeline_refiner.refine_context`, which wraps errors into `RefineResult`; direct
  `RagLLM.refine_context` capture isolates the sanitization claim (Plan row evidence).
- Asserting only the returned refined text: rejected — the vulnerability is in the outbound
  prompt, so the captured request body is the assertion target (AC-1).

## Implementation
### Target file
`tests/rag/test_augment_refiner.py`

### Procedure
1. Add the imports needed by the new tests.
2. Add a helper that builds a `RagLLM` over a capturing mock client.
3. Add a test class with the two sanitization tests described in Method.

### Method
- Add to the imports:
  `from rag.llm_client import RagLLM` (new)
  `from shared.types import RagHit` (new)
- Add `_make_capture_llm()` (new): creates `httpx.AsyncClient`-shaped `MagicMock` whose `post` is an
  `AsyncMock` recording `(url, kwargs)` and returning the mock response described in Assumptions;
  returns `(RagLLM(mock, _make_cfg().llm_url), captured)`. Import `_REFINER_TEMPERATURE` from
  `rag.llm_prompts` for the AC-3 pin assertion.
- Add `TestRefinerPromptSanitization` (new) with:
  - `test_refiner_prompt_sanitizes_injection_phrase` (new): one `RagHit` whose `content` contains
    "ignore previous instructions"; call `refine_context(chunks, "query", max_tokens=256,
    per_chunk_chars=500, timeout=10.0)`; from the captured `json=` body assert
    `messages[0]["content"]` contains `[REMOVED]` and not the raw phrase (AC-1).
  - `test_refiner_prompt_pattern_straddling_truncation` (new): content where an injection phrase
    starts just before `per_chunk_chars` and ends past it; assert the captured prompt contains
    `[REMOVED]` and no raw phrase fragment — pins the sanitize-then-truncate order.

### Details
- The captured body must also show the unchanged request fields: `temperature` equals the
  `_REFINER_TEMPERATURE` constant and `max_tokens` equals the passed `max_tokens` (AC-3 pin).
- Existing `_make_cfg` defaults (`refiner_max_tokens=256`, `refiner_max_chars_per_chunk=500`,
  `refiner_timeout=10.0`) are the argument values the tests pass, mirroring what
  `AugmentRefiner.run_refiner` supplies from config.
- `asyncio_mode = "auto"` is set in `pyproject.toml`, but this file's tests carry explicit
  `@pytest.mark.asyncio`; follow the file's existing style for the new async tests.

## Compatibility considerations
- Test-only change: no production behavior affected; existing suites in this file must keep
  passing unmodified.

## Security considerations
- N/A: test code only; it encodes the security assertions for procedure 01.

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_pipeline_refiner_fallback.py`
  (Plan Validation plan row 1): new tests fail before procedure 01 lands, pass after.
- Full regression per Plan Tests section: `uv run pytest tests/rag/ tests/integration/test_rag_turn_integration.py`.

## Completion criteria
- AC-1: captured refiner request body contains `[REMOVED]` and no raw injection phrase.
- AC-3: captured body shows unchanged `temperature` and `max_tokens` fields.
- The truncation-straddle test passes, pinning the sanitize-before-cut order.
- All pre-existing tests in the file pass unmodified.

## Out of Scope
- Refiner output sanitization, HTTP augment path, rerank-side tests (procedure 04), and any change
  to `_make_refiner`'s existing behavior.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the new tests and helper per Implementation > Procedure/Method/Details | Completed | 20261027-201844 | 20261027-201844 | — |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261027-201844 | 20261027-201844 | — |

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
- **Requirement ID**: REQ-001 (refiner prompt sanitization test, AC-1)
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-131124
- **Related target files**: tests/rag/test_augment_refiner.py