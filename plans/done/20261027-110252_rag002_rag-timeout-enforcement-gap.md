# Plan: Explicit per-request timeout on in-process RAG LLM and embedding calls

## Goal
- Make the in-process RAG query-path HTTP calls (`RagLLM._call_llm`, `get_embedding`) declare their
  per-request timeout explicitly at the call site, derived from the injected `httpx.AsyncClient`'s
  configured timeout, so the value is visible in the RAG code without changing any production
  numeric behavior.

## Priority
Low

## Scope
- **In-Scope**:
  - Passing an explicit `timeout=` kwarg to the POST calls in `RagLLM._call_llm` and
    `get_embedding`, sourced from the client's own `timeout` attribute.
  - Docstring/comment documentation in `scripts/rag/llm_client.py` of where the in-process timeout
    comes from.
  - New unit tests asserting the timeout kwarg is forwarded and tracks the client's configured
    value.
  - Documentation updates describing the two timeout mechanisms (delegate path fixed 10s,
    in-process path client-configured) in the 21_rag docs.
- **Out-of-Scope**:
  - Changing the delegate path (`call_rag_service`, `_REQUEST_TIMEOUT_SECONDS = 10.0`) or its retry
    policy (carried from the Issue).
  - Changing `refine_context`, which already takes an explicit `timeout` parameter (carried from
    the Issue).
  - Adding a new RAG config field (rejected — see Design; the Issue's Constraints forbid numeric
    behavior change, and any new field value would either duplicate or contradict the client
    value). `scripts/rag/config_resolution.py` and `scripts/rag/models_config.py` are not touched.
  - Modifying `scripts/agent/factory.py` or `scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`
    client construction (carried from the Issue).
  - Ingestion-side HTTP clients (carried from the Issue).
- **Dependencies**:
  - The Issue's dependency "factory.py continues to build the shared client with a finite
    `http_timeout`" holds (verified: `config/agent.toml` sets `http_timeout = 120.0`;
    `rag_pipeline_service.py` builds its client with a hardcoded `120.0`).
  - Overlap with the rag001 Plan (`plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md`):
    both target `scripts/rag/llm_client.py` and
    `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`. Compatible: rag001 edits
    `refine_context` and adds a sanitization invariant; this Plan edits `_call_llm`/`get_embedding`
    and adds timeout-source text. Disjoint regions; whichever Plan implements second rebases.
    Overlap with the rag003 Plan (`plans/20261027-110727_rag003_rag-url-key-ambiguity.md`):
    `docs/21_rag/rag_05_01-configuration-reference.md`. Compatible: this Plan extends the
    `http_timeout` paragraph; rag003 renames config-key occurrences and adds a key-contrast
    paragraph. Disjoint paragraphs; the second implementer rebases.

## Background
- The query path makes four HTTP call families with three timeout stories (verified individually):
  - `call_rag_service` (`scripts/rag/pipeline_service.py`): explicit `timeout=_REQUEST_TIMEOUT_SECONDS`
    (10.0) per attempt.
  - `refine_context` (`scripts/rag/llm_client.py`): explicit `timeout` parameter passed to `post`
    (resolved elsewhere, default 30.0).
  - `RagLLM._call_llm` (`scripts/rag/llm_client.py`): `self._client.post(...)` with **no**
    `timeout` argument — inherits the client default. Used by `expand_queries` (MQE),
    `cross_encoder_rerank`, and `summarize_tool_result`.
  - `get_embedding` (`scripts/rag/llm_client.py`): `client.post(...)` with **no** `timeout`
    argument — inherits the client default. Called from `scripts/rag/stages/search.py` with the
    pipeline's injected client.
- The injected clients in production (verified): the agent process builds
  `httpx.AsyncClient(timeout=ctx.cfg.llm.http_timeout)` (`scripts/agent/factory.py`) with
  `http_timeout = 120.0` from `config/agent.toml`; the rag_pipeline MCP server builds
  `httpx.AsyncClient(timeout=120.0)` directly (`scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py`).
- `docs/21_rag/rag_05_01-configuration-reference.md` already documents the delegate/in-server
  timeout split but does not state that the in-process LLM/embedding calls inherit the client value.

## Problem
- `_call_llm` and `get_embedding` depend entirely on the injected client's global default; the
  value is not visible when reading the RAG code and silently changes whenever a caller changes its
  client construction.
- Corrected Issue claims (repository evidence):
  - "The shared client ... default is 30.0s" is the dataclass default
    (`scripts/agent/config_dataclasses.py` `http_timeout: float = 30.0`), not the production value.
    Production is **120.0s** on both client-building paths, so the Issue's "Do not change the
    current effective timeout values (30.0s for in-process)" must be read as "do not change the
    inherited client values" — which this Plan satisfies by inheriting, not by pinning 30.0.
  - "If a caller ever constructs the client without a timeout, these calls can hang indefinitely":
    httpx 0.28 applies a finite default (5.0s) unless a caller explicitly passes a null timeout, so
    the hang scenario requires an explicit `timeout=None`, which no caller in `scripts/` does.
  - The Problem heading counts "two of four" call sites while naming three families (MQE, rerank,
    embedding); all three share the two unguarded POST call sites (`_call_llm`, `get_embedding`).

## Reason for Change
- As the RAG surface grows, more callers share one client with one global timeout. Declaring the
  timeout at the call site removes the silent dependency, makes the two mechanisms (fixed delegate
  timeout vs inherited client timeout) comparable in code review, and keeps per-call tuning possible
  through the existing client construction without inventing a second timeout knob.

## Implementation Intent
- Pass `timeout=self._client.timeout` in `_call_llm` and `timeout=client.timeout` in
  `get_embedding`. The client's configured value remains the single source; the call sites stop
  relying on an implicit default and state the dependency explicitly. Document in both functions'
  docstrings that the in-process timeout is the injected client's configured timeout, contrasted
  with the delegate path's fixed `_REQUEST_TIMEOUT_SECONDS`.

## Requirements
- `REQ-001`: `RagLLM._call_llm` passes an explicit `timeout` kwarg to `self._client.post(...)` whose
  value is `self._client.timeout`.
- `REQ-002`: `get_embedding` passes an explicit `timeout` kwarg to `client.post(...)` whose value is
  `client.timeout`.
- `REQ-003`: No numeric behavior change: every existing caller's effective timeout stays the value
  its client was built with (120.0s in both production paths). `call_rag_service`'s 10.0s, retry
  policy, and `refine_context`'s timeout handling are untouched; no new config field is added.
- `REQ-004`: `llm_client.py` documents at both call sites that the timeout derives from the injected
  client's configured timeout, and names the delegate path as the fixed-timeout contrast.
- `REQ-005`: `docs/21_rag/rag_05_01-configuration-reference.md` and
  `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` state both mechanisms: the delegate
  path's fixed per-attempt timeout and the in-process calls' explicit inheritance of the shared
  client timeout.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/llm_client.py | Add `timeout=self._client.timeout` to `_call_llm` and `timeout=client.timeout` to `get_embedding`; document the source in both docstrings | The two unguarded POST call sites are where the implicit inheritance hides | REQ-001, REQ-002, REQ-003, REQ-004 | `_call_llm` posts with json only, no `timeout`; `get_embedding` posts `{"content": text}` with no `timeout` | tests/rag/test_llm_client_timeout.py (new); tests/rag/test_rag_http_mode.py, tests/rag/test_rag_stages.py (regression, unmodified) | Verified |
| tests/rag/test_llm_client_timeout.py | New unit tests capturing the forwarded `timeout` kwarg and proving it tracks the client's value | Issue Testing Expectations; no existing test asserts timeout forwarding on either call site (verified: only `refiner_timeout`/`sqlite` timeout fixtures exist in `tests/rag/`) | REQ-001, REQ-002, REQ-003 | No `tests/rag/` file constructs `RagLLM` and asserts on `_call_llm` request kwargs; `test_rag_stages.py` mocks `get_embedding` entirely | the file itself | Verified |
| docs/21_rag/rag_05_01-configuration-reference.md | Extend the existing `http_timeout`/delegate-timeout paragraph to state that in-process LLM/embedding calls inherit the client timeout explicitly at the call site | The page already contrasts the two timeouts but omits the in-process mechanism the Issue requires documented | REQ-005 | "neither is loaded from configuration or `RagPipelineConfig`" paragraph on `http_timeout` | N/A: documentation file | Verified |
| docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | State the timeout source where `RagLLM` and `get_embedding` helpers are described | This is the page documenting the RAG LLM helper functions; a future call site added here must see the rule | REQ-005 | Page describes `RagLLM` methods and helper modules with no timeout statement | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/rag/pipeline_service.py | `call_rag_service` and `_REQUEST_TIMEOUT_SECONDS` — the fixed-timeout pattern the docs contrast against; must stay unchanged | REQ-003 |
| scripts/agent/factory.py, scripts/mcp_servers/rag_pipeline/rag_pipeline_service.py, config/agent.toml | The two production client constructions (both 120.0s) that define current effective timeouts and must not shift | REQ-003, Problem corrections |
| scripts/rag/stages/search.py | `get_embedding` call site and its injected `http` client; confirms the client-attribute source reaches every embedding call | REQ-002 |
| scripts/rag/llm_client.py `refine_context` | Already-explicit timeout path that must remain untouched and serves as the in-module precedent for an explicit kwarg | REQ-003 |
| tests/rag/test_rag_http_mode.py, tests/rag/test_rag_pipeline.py | Issue-named regression suites that must pass unmodified | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001, REQ-002): Both POST call sites pass a `timeout` kwarg; reading `llm_client.py`
  alone shows the value source without consulting the factory.
- `AC-2` (REQ-003): With a client built at timeout X, captured requests carry exactly X — including
  a non-production X (e.g. 7.5) in tests, proving derivation rather than a copied literal; production
  clients (120.0s) keep their effective timeout.
- `AC-3` (REQ-003): `call_rag_service` still uses `_REQUEST_TIMEOUT_SECONDS` and `refine_context`'s
  timeout parameter are untouched; no config file or config dataclass changes.
- `AC-4` (REQ-003): `tests/rag/test_rag_http_mode.py`, `tests/rag/test_rag_pipeline.py`, and the
  rest of `tests/rag/` pass unmodified.
- `AC-5` (REQ-004, REQ-005): Docstrings and both docs name the client-inheritance source and the
  delegate-path fixed timeout.

## Tests
- `REQ-001`: Unit — construct `RagLLM` with a fake client whose `timeout` attribute is 7.5 and whose
  `post` records kwargs; call `expand_queries` (which routes through `_call_llm`) and assert the
  captured `post` kwargs contain `timeout=7.5`.
- `REQ-002`: Unit — call `get_embedding` with the same fake client and assert `post` received
  `timeout=7.5`.
- `REQ-003`: Unit — the same fake with `timeout=120.0` (production value) asserts the forwarded value
  is 120.0, pinning "no numeric drift" for the production configuration.
- Regression: `uv run pytest tests/rag/` plus `tests/mcp_servers/rag_pipeline/` suites, all unmodified.

## Documentation Impact
- Required: `docs/21_rag/rag_05_01-configuration-reference.md` (timeout configuration page) and
  `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` (RAG LLM helper page), per
  `docs/00_index.md`'s "Document References by Task" mapping for the RAG query pipeline. The Issue's
  Documentation Impact ("note in the RAG pipeline docs") is satisfied by these two pages; no 22_mcp
  or 23_agent doc describes these timeouts (verified by grep) and needs no change.

## Assumptions
- Both of the Issue's Unresolved Questions are answered by the Issue's own Constraints plus
  repository evidence: keep the inherited client value (not the delegate's 10s, because pinning any
  constant would change production's effective 120.0s), and no new config field (client.timeout is
  the single documented source).
- `httpx.AsyncClient.timeout` exposes the construction value (a `httpx.Timeout` or `float`) and
  `post(timeout=...)` accepts the same type, so forwarding the attribute is type-safe; the
  rag_pipeline server's client always has a finite timeout (120.0).
- `summarize_tool_result` routes through `_call_llm` and is therefore covered by REQ-001 without a
  separate change; it is not treated as a fourth path.
- A mocked/fake client in the new tests must expose a `timeout` attribute; the existing test style
  (MagicMock or duck-typed fakes in `tests/shared/test_tool_executor.py`) shows this pattern is
  established in the repository.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| — | No blocking unknowns. The Issue's two unresolved questions are resolved in Assumptions/Design from the Issue's Constraints and verified production values. | — | — | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/rag/llm_client.py | Explicit timeout kwarg at two POST call sites + docstrings | All in-process RAG LLM/embedding calls (MQE, rerank, summarization, embedding) | 0 | High (single author, 100%) | None: no new module or config |
| tests/rag/test_llm_client_timeout.py | New test file (3 unit tests) | Test suite only | N/A (new file) | High (single author) | None |
| docs/21_rag/rag_05_01-configuration-reference.md | Timeout-mechanism paragraph extension | Docs domain 21_rag | 14 | High (single author, 100%) | None |
| docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | Timeout-source note on the helper page | Docs domain 21_rag | 16 (shared page with the rag001 Plan — rebase before editing) | High (single author, 100%) | None |

## Design
- **Inherit the client's timeout at the call site (Issue questions answered)**: `timeout=client.timeout`
  is the only design that satisfies the Constraint "do not change the current effective timeout
  values" — the production effective values are 120.0s on both client paths, so any new constant
  (30.0 or 10.0) would silently retune production. The kwarg makes the dependency explicit without
  owning a second value.
- **No new config field (Issue question answered)**: a `RagConfig` timeout field would create two
  sources that can diverge — exactly the drift the Issue wants removed — and would require touching
  `config_resolution.py`, `models_config.py`, `agent.toml`, and config docs. The client construction
  is already the single tuned surface (`http_timeout`).
- **Contrast, not copy**: the delegate path's fixed 10.0s stays as-is; the in-process path keeps its
  inherited semantics. The Plan documents the two mechanisms side by side instead of converging the
  numbers, matching the Issue's "describe the responsibility rather than copying the literal".
- **Call-site declaration over client construction**: fixing this in `factory.py`/`rag_pipeline_service.py`
  (e.g. adding RAG-specific clients) would spread RAG policy into two unrelated modules; declaring
  it inside `llm_client.py` keeps RAG timeout semantics in the RAG module.
- **Overlap handling**: the rag001 Plan edits `refine_context` (untouched here) and the same helper
  docs page's sanitization paragraph (untouched here); both Plans record the overlap as Compatible.

## Implementation steps
1. **Phase 1: Characterization baseline**
   - [ ] Run `tests/rag/test_rag_http_mode.py`, `tests/rag/test_rag_pipeline.py`,
     `tests/rag/test_rag_stages.py` unchanged to pin current call behavior (REQ-003).
2. **Phase 2: Explicit timeouts**
   - [ ] Add `timeout=self._client.timeout` to `_call_llm` and document the source in its docstring
     (REQ-001, REQ-004; `scripts/rag/llm_client.py`).
   - [ ] Add `timeout=client.timeout` to `get_embedding` and document the source (REQ-002, REQ-004;
     `scripts/rag/llm_client.py`).
3. **Phase 3: Tests**
   - [ ] Add `tests/rag/test_llm_client_timeout.py` with the three capture tests (REQ-001, REQ-002,
     REQ-003; new file).
4. **Phase 4: Docs, deployment check, and verification**
   - [ ] Extend the timeout paragraph in `docs/21_rag/rag_05_01-configuration-reference.md`
     (REQ-005).
   - [ ] Add the timeout-source note to
     `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` (REQ-005).
   - [ ] Deployment validation/scripts check: no new module, config key, or client-construction
     change, so `deploy.sh` and `config/*.toml` stay unchanged (REQ-003).
   - [ ] Run the full `rules/toolchain.md` validation sequence (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/llm_client.py | Unit (kwarg capture through fake client) | `uv run pytest tests/rag/test_llm_client_timeout.py` | Timeout forwarded and equal to the client's configured value at 7.5 and 120.0 |
| scripts/rag/llm_client.py | Regression | `uv run pytest tests/rag/ tests/mcp_servers/rag_pipeline/` | All pre-existing tests pass unmodified |
| scripts/rag/llm_client.py | Static | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; no import changes needed (client objects already in scope) |
| docs/21_rag/rag_05_01-configuration-reference.md, docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | Documentation consistency (21_rag domain) | `rules/toolchain.md` documentation consistency check | Both timeout mechanisms described and match code |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New kwarg lines covered |

## Risks
- **Risk**: a caller builds a client with a timeout that is wrong for RAG and the call site now
  makes it look intentional → **Mitigation**: this is the Issue's stated goal (explicitness); the
  docstrings name the client as the source so the mismatch is reviewable where it is set, and the
  two production clients both use 120.0 (verified).
- **Risk**: forwarding `client.timeout` when a client was built with `timeout=None` yields no
  timeout → **Mitigation**: no `scripts/` caller passes a null timeout (verified across all
  `httpx.AsyncClient(` constructions); httpx's own default is a finite 5.0s; the new tests pin the
  derived value.
- **Risk**: edit collision with the rag001 Plan on `llm_client.py` and the `rag_03_06` doc page →
  **Mitigation**: disjoint functions/paragraphs; both Plans record the overlap as Compatible and the
  second implementer rebases.
- **Risk**: docs pages are moderate churn (14 and 16 commits/30d) → **Mitigation**: single-paragraph
  edits; rebase immediately before implementing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Completed | 20261027-202638 | 20261027-202638 |  |
| 2 | Phase 2: explicit timeouts | Completed | 20261027-202638 | 20261027-202638 |  |
| 3 | Phase 3: tests | Completed | 20261027-202638 | 20261027-202638 |  |
| 4 | Phase 4: docs, deployment check, verification | Completed | 20261027-202638 | 20261027-202638 |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-144351_01_scripts_rag_llm_client.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-144351_02_tests_rag_test_llm_client_timeout.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261027-144351_03_docs_21_rag_rag_05_01-configuration-reference.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261027-144351_04_docs_21_rag_rag_03_06_query_pipeline-helpers-and-cache.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-071811_rag002_rag-timeout-enforcement-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-110252
- **Related target files**: scripts/rag/llm_client.py, tests/rag/test_llm_client_timeout.py, docs/21_rag/rag_05_01-configuration-reference.md, docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes ("pass an explicit `timeout`"); `_call_llm` verified | scripts/rag/llm_client.py | Phase 2 | AC-1, AC-2 | `_call_llm` kwarg-capture test | Confirmed by repository evidence |
| REQ-002 | Required Changes; `get_embedding` verified | scripts/rag/llm_client.py | Phase 2 | AC-1, AC-2 | `get_embedding` kwarg-capture test | Confirmed by repository evidence |
| REQ-003 | Constraints (no numeric change, no new retries/fields); production 120.0s verified | scripts/rag/llm_client.py | Phase 2 | AC-3, AC-4 | 120.0 pin test + unmodified regression suites | Confirmed by repository evidence |
| REQ-004 | Required Changes ("document where the in-process timeout comes from") | scripts/rag/llm_client.py | Phase 2 | AC-5 | Docstring review | Confirmed by repository evidence |
| REQ-005 | Documentation Impact | docs/21_rag/rag_05_01-configuration-reference.md | Phase 4 | AC-5 | 21_rag documentation consistency check | Confirmed by repository evidence |
| REQ-005 | Helper page lacking the timeout mechanism | docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | Phase 4 | AC-5 | 21_rag documentation consistency check | Confirmed by repository evidence |
| REQ-001, REQ-002, REQ-003 | Issue Testing Expectations | tests/rag/test_llm_client_timeout.py | Phase 3 | AC-1, AC-2 | Three new unit tests | Confirmed by repository evidence |