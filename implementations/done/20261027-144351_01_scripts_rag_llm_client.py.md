# Implementation Procedure: Explicit per-request timeout at the two unguarded POST call sites in `llm_client.py`

## Goal

Make `RagLLM._call_llm` and `get_embedding` declare their per-request timeout explicitly at
the call site by forwarding the injected client's own configured timeout, so the value is
visible in the RAG code without changing any production numeric behavior (REQ-001, REQ-002,
REQ-003, REQ-004).

## Scope

- Two kwarg additions and two docstring/doc-comment updates in `scripts/rag/llm_client.py`.
- No import change (the client objects are already in scope). No config field, no
  client-construction change, no change to `refine_context` or `call_rag_service`.

## Assumptions

- `httpx.AsyncClient.timeout` exposes the construction value (`httpx.Timeout` or float) and
  `post(timeout=...)` accepts the same type, so forwarding the attribute is type-safe (Plan
  Assumptions; httpx 0.28).
- Overlap with the rag001 Plan procedures on this file (its `refine_context` sanitize edit)
  is disjoint from `_call_llm`/`get_embedding`. Verified 2026-10-27: the rag001 edits have
  already landed (`rag.utils` import + `sanitize_document` in `refine_context`), so all line
  references below are against the post-rag001 file state.
- Non-blocking caveat (UNK-01 analog in the Plan Risks): if a future caller builds a client
  with `timeout=None`, forwarding yields no timeout; no `scripts/` caller does this today
  (Plan-verified) and the new tests pin derived values.

## Design decisions

- Inherit the client's timeout at the call site (`timeout=client.timeout`) rather than pin a
  constant: production effective values are 120.0s on both client paths
  (`scripts/agent/factory.py` L95 + `config/agent.toml` `http_timeout = 120.0`;
  `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py` L110-111 hardcoded 120.0), so
  any new literal (30.0 or 10.0) would silently retune production (Plan Design).
- No new `RagConfig` timeout field: two sources that can diverge is the drift the Issue
  wants removed (Plan Design).

## Alternatives considered

- Fixing timeouts in `factory.py`/`rag_pipeline_service.py` client construction — rejected:
  spreads RAG policy into two unrelated modules; timeout semantics stay in the RAG module
  (Plan Design).
- Converging the delegate (10.0s) and in-process numbers — rejected: contrast, not copy
  (Plan Design).

## Implementation
### Target file

`scripts/rag/llm_client.py`

### Procedure

1. In `RagLLM._call_llm` (verified at L108-125 post-rag001; current signature is
   `(self, messages, temperature, max_tokens)`), add `timeout=self._client.timeout` to the
   `self._client.post(self._llm_url, json={...})` call.
2. In `get_embedding` (verified at L259-271 post-rag001), add `timeout=client.timeout` to the
   `client.post(embed_url, json={"content": text})` call.
3. Extend both functions' docstrings to state that the in-process per-request timeout is the
   injected client's configured timeout, and name the delegate path
   (`scripts/rag/pipeline_service.py::call_rag_service`, fixed `_REQUEST_TIMEOUT_SECONDS =
   10.0`) as the fixed-timeout contrast (REQ-004).

### Method

One kwarg addition per `post(...)` call plus docstring text. `_call_llm`'s json body
(`messages`, `temperature`, `max_tokens`) and `get_embedding`'s `{"content": text}` body stay
byte-identical.

### Details

- Only `expand_queries`, `cross_encoder_rerank`, and `summarize_tool_result` route through
  `_call_llm`, and `scripts/rag/stages/search.py` (L41) is the `get_embedding` caller — all
  inherit the change with no edit (REQ-001 coverage assumption verified).
- Production values verified 2026-10-27: `config/agent.toml` L28 `http_timeout = 120.0` →
  `scripts/agent/factory.py` L95; `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
  L110-111 fixed 120.0; `scripts/rag/pipeline_service.py` L21 `_REQUEST_TIMEOUT_SECONDS =
  10.0` (used at L147).
- `refine_context` (L223-250) must remain untouched (REQ-003, AC-3). Verified 2026-10-27: the
  Plan's claim that it "already passes an explicit `timeout` parameter" is stale against the
  current code — the current `_call_llm` signature is `(self, messages, temperature,
  max_tokens)` (no `client`/`timeout` kwargs) and `refine_context` passes neither; it routes
  through `_call_llm` and inherits the client timeout like the other callers. No edit needed.
- Type note for mypy: `httpx.AsyncClient.post` accepts `timeout: httpx._types.TimeoutTypes`,
  the same type `AsyncClient.timeout` returns; no cast needed.

## Compatibility considerations

- No signature changes; every existing caller's effective timeout stays the value its client
  was built with (120.0s in both production paths, REQ-003).
- `call_rag_service`'s 10.0s per-attempt timeout and retry policy untouched.
- No config file or config dataclass changes (`config_resolution.py`, `models_config.py`
  untouched).

## Security considerations

- N/A: availability/robustness change; makes the timeout dependency reviewable at the call
  site rather than implicit.

## Rollback considerations

- N/A: revert the commit (two kwargs + docstrings).

## Validation plan

- `uv run pytest tests/rag/test_llm_client_timeout.py` — kwarg-capture tests pass at 7.5 and
  120.0 (from the sibling test procedure; AC-2).
- `uv run pytest tests/rag/ tests/mcp_servers/rag_pipeline/` — all pre-existing tests pass
  unmodified (AC-4), including `tests/rag/test_rag_http_mode.py`,
  `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_stages.py`.
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
  — clean; no import changes needed.

## Completion criteria

- AC-1: both POST call sites carry a `timeout` kwarg readable without consulting the
  factory; AC-2: forwarded value equals the client's configured value (7.5 and 120.0 tests);
  AC-3: `call_rag_service`/`refine_context` untouched, no config changes; AC-5: both
  docstrings name the client-inheritance source and the delegate-path fixed timeout.

## Out of Scope

- The new test file (own procedure document), the two docs pages (own procedure documents),
  `refine_context`, `call_rag_service`, client construction in `factory.py` /
  `rag_pipeline_service.py`, ingestion-side HTTP clients, and any new config field.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261027-202638 | 20261027-202638 | Run Phase 1 characterization baseline first (`tests/rag/test_rag_http_mode.py`, `test_rag_pipeline.py`, `test_rag_stages.py`) per the Plan |
| 2 | Add or update tests per Validation plan | Completed | 20261027-202638 | 20261027-202638 | Tests live in the sibling procedure `implementations/20261027-144351_02_tests_rag_test_llm_client_timeout.py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261027-202638 | 20261027-202638 | — |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261027-202638 | 20261027-202638 | Docs covered by `implementations/20261027-144351_03_*`/`_04_*` |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20261027-071811_rag002_rag-timeout-enforcement-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-144351
- **Related target files**: scripts/rag/llm_client.py