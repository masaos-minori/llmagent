# Implementation Procedure: New timeout-forwarding regression tests in `tests/rag/test_llm_client_timeout.py`

## Goal

Add the three kwarg-capture unit tests that prove `_call_llm` and `get_embedding` forward the
injected client's configured timeout verbatim — including a non-production value (7.5) that
proves derivation rather than a copied literal, and the production value (120.0) that pins
"no numeric drift" (REQ-001, REQ-002, REQ-003; AC-2).

## Scope

- New file `tests/rag/test_llm_client_timeout.py` with one fake-client helper and three tests.
- No existing test file changes.

## Assumptions

- The file does not exist yet (verified), and no `tests/rag/` file currently constructs
  `RagLLM` and asserts on `_call_llm` request kwargs (Plan row evidence).
- The fake client must expose a `timeout` attribute; the MagicMock-with-spec pattern is
  established in `tests/rag/test_rag_http_mode.py` (`MagicMock(spec=httpx.AsyncClient)`,
  verified at L28).
- `expand_queries` requires a `RagConfig` carrying `mqe_prompt_template` (str) and
  `mqe_n_queries` (int) (verified in `scripts/rag/llm_prompts.py::_mqe_prompt`); reuse the
  `RagConfigImpl` fixture style of `tests/rag/test_augment_refiner.py::_make_cfg` (verified
  at L26-41).

## Design decisions

- Capture at the HTTP boundary: the fake client's async `post` records its kwargs, so the
  tests pin the actual outbound request, not an internal intermediate (Plan Tests).
- Drive `_call_llm` through `expand_queries` (its public entry) rather than calling the
  private method directly — same pattern as the Plan Tests section.

## Alternatives considered

- Patching `httpx.AsyncClient.post` globally — rejected: a directly constructed fake keeps
  the asserted `timeout` attribute under test control (Plan Assumptions).

## Implementation
### Target file

`tests/rag/test_llm_client_timeout.py` (new)

### Procedure

1. Module imports: `httpx`, `orjson`, `MagicMock`/`AsyncMock`, `pytest`, `RagLLM` and
   `get_embedding` from `rag.llm_client`, `RagConfig` type plus the `RagConfigImpl` fixture
   copy modeled on `tests/rag/test_augment_refiner.py::_make_cfg`.
2. Add helper `_make_fake_client(timeout: float)`: a `MagicMock` whose `.timeout` attribute
   is the given float and whose `post` is an `AsyncMock` recording the call kwargs and
   returning a stub whose `raise_for_status()` is a no-op and whose `content` is
   `orjson.dumps({"choices": [{"message": {"content": "[\"alt query 1\", \"alt query 2\", \"alt query 3\"]"}]})`
   — a valid chat-completion body whose content parses through `_parse_mqe_response` (JSON
   array of strings, verified at `scripts/rag/llm_prompts.py` L133-149) and through
   `parse_http_json` (reads `.content`).
3. Add `test_call_llm_forwards_client_timeout` (new) (REQ-001): build `RagLLM(client=fake(7.5),
   llm_url="http://localhost:8000/v1/chat/completions", cfg=_make_cfg())`; `await
   rag_llm.expand_queries("query")`; assert the recorded `post` kwargs contain
   `timeout=7.5`.
4. Add `test_get_embedding_forwards_client_timeout` (new) (REQ-002): `await get_embedding("text",
   fake(7.5), "http://localhost:8000/embeddings")`; assert recorded `post` kwargs contain
   `timeout=7.5`. The embedding stub's `content` for this test must be
   `orjson.dumps({"embedding": [0.1, 0.2]})` instead (get_embedding validates a non-empty
   list `embedding` field, verified at `scripts/rag/llm_client.py` L263-267).
5. Add `test_forwarded_timeout_matches_production_client_value` (new) (REQ-003): same two calls
   with `timeout=120.0`; assert the forwarded value is exactly 120.0.

### Method

`@pytest.mark.asyncio` tests with `AsyncMock` post recording (mirror
`tests/rag/test_rag_http_mode.py` mocking style). One shared fake-client helper; the two
response bodies differ per endpoint, so pass the body bytes into the helper or use two
small builders.

### Details

- The 7.5 value must never appear as a literal in `scripts/` — the test proves derivation
  from the attribute (AC-2).
- `get_embedding` is module-level with signature `(text, client, embed_url)` (verified at
  L258); no `RagLLM` instance is needed for tests 4/5-embedding-side.

## Compatibility considerations

- Test-only change; new file adds no import-graph edges into production code.

## Security considerations

- N/A: test file; pins the timeout-forwarding contract added by the `llm_client.py` procedure.

## Rollback considerations

- N/A: delete the file / revert the commit (test-only).

## Validation plan

- `uv run pytest tests/rag/test_llm_client_timeout.py` — three tests pass (run after the
  `scripts/rag/llm_client.py` change lands; written against the post-change contract).
- `uv run pytest tests/rag/ tests/mcp_servers/rag_pipeline/` — full regression unmodified
  (AC-4).

## Completion criteria

- AC-2: captured `post` kwargs carry exactly 7.5 (non-production) and exactly 120.0
  (production) at both call sites.

## Out of Scope

- `refine_context` timeout behavior (already explicit, untouched), delegate-path timeout
  tests (`call_rag_service`), and any numeric change to production timeouts.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | This document is the test file itself |
| 2 | Add or update tests per Validation plan | Pending | — | — | This document is the tests themselves |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no doc change from this row |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003 (kwarg-capture tests, Plan Tests section)
- **Source issue**: issues/20261027-071811_rag002_rag-timeout-enforcement-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-144351
- **Related target files**: tests/rag/test_llm_client_timeout.py
