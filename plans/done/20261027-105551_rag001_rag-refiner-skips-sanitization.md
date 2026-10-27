# Plan: Uniform prompt-injection sanitization for all chunk-content LLM paths in RAG

## Goal
- Make every query-time RAG path that embeds retrieved chunk content into an LLM prompt sanitize
  that content with the existing `sanitize_document()` helper, so the refiner and Cross-Encoder
  rerank paths match the sanitization already applied by the raw-chunk formatting path, and record
  the trust-boundary invariant in the RAG docs.

## Priority
Medium

## Scope
- **In-Scope**:
  - Sanitize chunk content in `RagLLM.refine_context` (`scripts/rag/llm_client.py`) before it
    enters the refiner prompt.
  - Sanitize candidate content in `_build_rerank_prompt` (`scripts/rag/llm_prompts.py`) before the
    preview truncation. This is a **scope extension**: the Issue names two injectable paths, but
    repository verification found a third (the rerank preview) with the same hole. The extension
    was approved by the user on 2026-10-27 (refiner + rerank together).
  - Unit tests for both paths and a parity check that the raw-chunk path is unchanged.
  - Correction of two stale boundary claims (one doc sentence, one integration-test docstring).
  - Documentation of the invariant: chunk content reaching an LLM prompt is sanitized at the
    formatting site.
- **Out-of-Scope**:
  - Changing `_INJECTION_PATTERNS` or what counts as a pattern (carried from the Issue).
  - Sanitizing the refiner's **output** (carried from the Issue; separate concern).
  - The HTTP augment path and the search/fusion stages (carried from the Issue).
  - `summarize_tool_result`: it summarizes agent tool output, not corpus chunks, so it is a
    different trust boundary and is not touched (verified: it receives tool text, not `RagHit`
    content).
  - `RagExpansion` (MQE) prompt building: verified it composes query variants only, with no chunk
    content.
  - Adding a corpus-wide re-sanitization at ingestion or storage time.
- **Dependencies**:
  - The Issue's dependency "sanitize_document remains the single source of injection sanitization
    for the query path" is satisfied structurally: both changed paths import the same helper from
    `rag.utils`; no second sanitizer is introduced.
  - Overlap with sibling plans: the rag002 Plan
    (`plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md`) also targets
    `scripts/rag/llm_client.py` and `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`.
    Compatible: rag002 edits `_call_llm`/`get_embedding` and adds timeout-source text; this Plan
    edits `refine_context` and adds the sanitization invariant. Disjoint functions and paragraphs;
    whichever Plan implements second rebases. The other five target files appear in no other
    Frozen Plan.

## Background
- `scripts/rag/utils.py::sanitize_document()` replaces matches of `_INJECTION_PATTERNS` with the
  literal `[REMOVED]` and returns a plain `str`; `sanitize_document_full()` adds a `SanitizeResult`
  audit trail and is not used by the query pipeline.
- Query-time chunk content reaches an LLM through three formatting sites, verified individually:
  - `scripts/rag/stages/augment.py::_format_chunks` — sanitizes
    (`sanitize_document(c.content)` inside the `[RAG_CONTEXT_START]` block). Guarded today.
  - `scripts/rag/llm_client.py::RagLLM.refine_context` — builds
    `f"[{i}] {title}\n{c.content[:per_chunk_chars]}"` and sends it as a single user message. No
    sanitization. Unguarded.
  - `scripts/rag/llm_prompts.py::_build_rerank_prompt` — builds
    `chunk.content[:300].replace("\n", " ")` previews into the configured rerank template. No
    sanitization. Unguarded.
- `scripts/rag/pipeline_refiner.py::refine_context()` is the only caller of `RagLLM.refine_context`
  (verified: the only non-definition reference in `scripts/`); it passes the reranked hits straight
  through and converts refiner errors into `RefineResult(text=None, reason=...)` so the caller
  falls back to raw-chunk formatting.
- `RagLLM` is constructed with an injected `httpx.AsyncClient` (`self._client`) and posts the
  prompt to `self._llm_url`, so a unit test can capture the exact prompt text.

## Problem
- A control applied at one formatting site is absent at two others. Content placed in the corpus by
  an attacker reaches the refiner LLM and the rerank LLM unsanitized, while the identical content
  would be sanitized on the raw-chunk path — an inconsistent trust boundary.
- The gap is already encoded in documentation as if it were the design:
  `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` states "`AugmentStage` uses
  `sanitize_document()` exclusively", and `tests/integration/test_rag_turn_integration.py` (module
  docstring and `test_f04` docstring) states `sanitize_document()` "is only ever called from
  `rag/stages/augment.py`'s chunk-formatting step". Both become false after this Plan and both are
  currently used as the justification for why the agent layer does not sanitize.
- Corrected Issue claims: the Issue's "two distinct injectable paths" is incomplete (three, see
  Background), and its Dependency framing implies the refiner gap is the whole hole. The Issue's
  Unresolved Question 1 ("was the sanitizer intended to cover the refiner path?") is resolved by
  the user's 2026-10-27 decision: yes, the sanitizer covers every chunk-to-prompt path.

## Reason for Change
- The asymmetry is easy to widen: a future formatting site will copy whichever precedent it finds,
  and today the precedent is documented as "sanitization belongs to the augment stage only".
  Closing the two unguarded sites while recording the invariant makes the control uniform and the
  docs safe to copy from.

## Implementation Intent
- Apply the same helper at each formatting site, keeping each site's own truncation and template
  behavior: sanitize the full chunk content first, then truncate to the site's existing character
  budget. Reuse `sanitize_document` from `rag.utils` in both changed modules; do not add a new
  sanitizer, a pattern change, or a config knob. Record the invariant in the two RAG docs so a
  future path can be checked against it.

## Requirements
- `REQ-001`: `RagLLM.refine_context` must pass each chunk's content through `sanitize_document()`
  before embedding it in the refiner prompt, with sanitization applied before the
  `per_chunk_chars` truncation.
- `REQ-002`: `_build_rerank_prompt` must pass each candidate's content through `sanitize_document()`
  before the 300-character preview truncation. The configured `rerank_prompt_template`, the query
  substitution, and the 300-character budget are otherwise unchanged.
- `REQ-003`: Both changed modules import `sanitize_document` from `rag.utils`; no second sanitizer
  and no change to `_INJECTION_PATTERNS`. The import direction (`rag.llm_prompts` / `rag.llm_client`
  → `rag.utils`) is within the `rag` package and preserves the import-linter contract
  (`rag must not import from agent or mcp_servers`).
- `REQ-004`: `_format_chunks` sanitization, the refiner prompt template/temperature/`max_tokens`,
  the refiner exception-to-`RefineResult` conversion, the empty-output fallback, and all behavior
  when `use_refiner=False` are unchanged.
- `REQ-005`: `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` and
  `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` state the invariant — every query-time
  path that embeds retrieved chunk content into an LLM prompt sanitizes it with `sanitize_document`
  at the formatting site — and the stale "exclusively" claim is removed.
- `REQ-006`: The stale call-site claims in `tests/integration/test_rag_turn_integration.py` (module
  docstring and `test_f04` docstring) are corrected to name all sanitized sites; the test's actual
  assertions (agent layer does not sanitize) are unchanged.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| scripts/rag/llm_client.py | Sanitize chunk content in `RagLLM.refine_context` before truncation and prompt substitution | The refiner prompt is the unguarded path named by the Issue | REQ-001, REQ-003, REQ-004 | `refine_context` builds `text = c.content[:per_chunk_chars]` and interpolates it into `_REFINER_PROMPT_TEMPLATE` with no `sanitize_document` call | tests/rag/test_augment_refiner.py; tests/rag/test_pipeline_refiner_fallback.py (regression, unmodified) | Verified |
| scripts/rag/llm_prompts.py | Sanitize candidate content in `_build_rerank_prompt` before the 300-character preview | Second unguarded chunk-to-prompt site found during verification (scope extension, user-approved) | REQ-002, REQ-003, REQ-004 | `_build_rerank_prompt` builds `preview = chunk.content[:300].replace("\n", " ")` with no `sanitize_document` call | tests/rag/test_rag_pipeline.py (new parity test) | Verified |
| tests/rag/test_augment_refiner.py | Add the refiner-path sanitization test with a captured prompt | Issue Testing Expectations; no existing test asserts refiner input sanitization | REQ-001 | The file injects the `llm` dependency into `AugmentRefiner` via `_make_refiner(llm=...)` but never constructs a real `RagLLM`; the new test constructs `RagLLM` with a mock `httpx.AsyncClient` (constructor takes an injected client) to capture the prompt | the file itself | Verified |
| tests/rag/test_rag_pipeline.py | Add the rerank-preview sanitization test and the `_format_chunks` unchanged-parity test | This file already hosts the `sanitize_document` and `_format_chunks` tests, so the parity invariant lives with them | REQ-002, REQ-004 | Existing tests cover `sanitize_document` pattern behavior and `_format_chunks` output only | the file itself | Verified |
| tests/integration/test_rag_turn_integration.py | Correct the two stale `sanitize_document` call-site claims in docstrings; keep assertions unchanged | Both claims become false after the change and are currently cited as the reason the agent layer does not sanitize | REQ-006 | Module docstring and `test_f04` docstring: "sanitize_document() ... is only ever called from rag/stages/augment.py's chunk-formatting step" | the file itself (assertions untouched) | Verified |
| docs/21_rag/rag_03_05_query_pipeline-augment-stages.md | Replace the "uses `sanitize_document()` exclusively" claim with the cross-path invariant | That sentence is the documented form of the asymmetry this Plan removes | REQ-005 | "`AugmentStage` uses `sanitize_document()` exclusively and does not consume the audit trail." | N/A: documentation file | Verified |
| docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | State the sanitization invariant where `refine_context` and the rerank helper are described | This is the page that documents the RAG LLM helpers; the invariant must be visible where a future prompt builder is added | REQ-005 | Page describes `RagLLM` methods including `refine_context` and notes prompt templates live in `scripts/rag/llm_prompts.py`, with no sanitization statement | N/A: documentation file | Verified |

## Reference Files

| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| scripts/rag/utils.py | The sanitizer and `_INJECTION_PATTERNS` that must not change; `sanitize_document` vs `sanitize_document_full` contract | scripts/rag/llm_client.py, scripts/rag/llm_prompts.py; REQ-003 |
| scripts/rag/pipeline_refiner.py | Only caller of `RagLLM.refine_context`; confirms error handling and the empty-output fallback must stay intact | REQ-004 |
| scripts/rag/stages/augment.py | `_format_chunks` parity reference that must not be modified | REQ-004 |
| scripts/rag/augment.py | `AugmentRefiner` orchestration and the `refine_context()` call site that supplies `per_chunk_chars` from config | REQ-004 |
| scripts/rag/models_result.py | `RagHit` field contract (`content` vs `normalized_content`) — the Content-only Invariance Rule means only `content` is formatted | REQ-001, REQ-002 |
| tests/rag/test_pipeline_refiner_fallback.py | Refiner fallback regression suite that must pass unmodified | REQ-004 |
| .importlinter | Confirms intra-`rag` imports are permitted so `rag.utils` can be imported by both changed modules | REQ-003 |

## Acceptance Criteria
- `AC-1` (REQ-001): A chunk containing a `_INJECTION_PATTERNS` phrase produces a refiner prompt in
  which that phrase is replaced by `[REMOVED]`; the captured HTTP request body shows no raw
  injection phrase.
- `AC-2` (REQ-002): The same content produces a rerank prompt whose 300-character preview contains
  `[REMOVED]` instead of the injection phrase.
- `AC-3` (REQ-004): `_format_chunks` output for the same chunk is byte-identical to its current
  output, and the refiner prompt template, temperature, and `max_tokens` fields in the request body
  are unchanged.
- `AC-4` (REQ-004): `tests/rag/test_pipeline_refiner_fallback.py` and
  `tests/rag/test_pipeline_refiner_fallback_counters.py` pass unmodified; sanitizing clean text does
  not produce empty refiner input, so `refiner_returned_empty` and `refiner_exception` reasons are
  unaffected.
- `AC-5` (REQ-005, REQ-006): No document or test docstring still claims `sanitize_document` is used
  only by the augment stage.
- `AC-6` (REQ-003): `lint-imports` passes with the new intra-`rag` imports and `ruff` reports no
  unused imports.

## Tests
- `REQ-001`: Unit — construct `RagLLM` with a mock `httpx.AsyncClient` whose `post` captures the
  JSON body; call `refine_context` with a chunk containing "ignore previous instructions" and assert
  the captured prompt contains `[REMOVED]` and not the raw phrase.
- `REQ-002`: Unit — call `_build_rerank_prompt` directly with a candidate carrying an injection
  phrase and assert the returned prompt contains `[REMOVED]` and stays within the 300-character
  preview budget.
- `REQ-004`: Unit — `_format_chunks` parity test asserting unchanged sanitized output for the same
  fixture chunk (the guard against "fixing one path by changing another").
- Regression: `tests/rag/` (refiner fallback, augment integration, quality regression) and
  `tests/integration/test_rag_turn_integration.py`; `tests/mcp_servers/rag_pipeline/` suites.

## Documentation Impact
- Required, per `docs/00_index.md`'s "Document References by Task" mapping for the RAG query
  pipeline (`21_rag/rag_03_05_query_pipeline-augment-stages.md`,
  `21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`): both pages must describe the sanitized
  invariant, and the stale exclusivity claim must be removed (REQ-005). The integration-test
  docstring correction (REQ-006) is a code-comment change carried as a target row because those
  claims are actively consulted as the sanitization boundary record.

## Assumptions
- Scope extension to the rerank path was approved by the user on 2026-10-27 ("refiner + rerank both")
  after verification showed the third unguarded path.
- The Issue's Unresolved Question 1 is answered in the affirmative: the sanitizer is intended to
  cover every chunk-to-prompt path, not only the augment stage (user decision 2026-10-27).
- Sanitize-then-truncate is the correct order at both sites: `[REMOVED]` replacement only shortens
  or preserves length locally, so the configured character budgets keep their meaning, and
  truncating first would let a pattern straddling the cut survive unsanitized.
- `sanitize_document` is cheap (five compiled regex substitutions) and safe to apply twice per call
  (refiner and rerank run on the same hits in a full pipeline) — no measurable cost concern.
- Neither changed site is used by the RAG ingestion path, so stored chunk content stays raw
  (verified: `sanitize_document` call sites today are query-path only).

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | Whether sanitized refiner/rerank input measurably changes compression quality or rerank scores (Issue Unresolved Question 2) | No baseline measurements of refiner output quality or rerank score drift exist in the repository | Non-blocking: sanitization only replaces known injection phrasings, which are not legitimate answer content; observe `tests/rag/test_rag_quality_regression.py` results and production rerank diagnostics after landing, and revisit only if a regression appears | False |

## Affected areas

| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| scripts/rag/llm_client.py | Sanitize in `refine_context` | All refiner-enabled query-time RAG calls | 0 | High (single author, 100%) | None: no new module or config |
| scripts/rag/llm_prompts.py | Sanitize in `_build_rerank_prompt` | All rerank-enabled query-time RAG calls | 0 | High (single author, 100%) | None |
| tests/rag/test_augment_refiner.py | New sanitization test | Test suite only | 1 | High (single author, 100%) | None |
| tests/rag/test_rag_pipeline.py | New parity and rerank tests | Test suite only | 1 | High (single author, 100%) | None |
| tests/integration/test_rag_turn_integration.py | Docstring corrections only | Test suite only | 0 | High (single author, 100%) | None |
| docs/21_rag/rag_03_05_query_pipeline-augment-stages.md | Invariant replaces exclusivity claim | Docs domain 21_rag | 18 (high churn — rebase before editing) | High (single author, 100%) | None |
| docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | Invariant added to the helper description | Docs domain 21_rag | 16 | High (single author, 100%) | None |

## Design
- **Sanitize at the formatting site, not in a shared wrapper**: each prompt builder owns its own
  sanitization, mirroring `_format_chunks`. A single shared "sanitize all hits" preprocessing step
  would hide which sites are guarded and would still not protect a future builder that formats
  content itself.
- **Reuse the plain sanitizer**: `sanitize_document` (returns `str`) is the query-path contract;
  `sanitize_document_full`'s audit trail stays unused here, consistent with the documented
  contract in `rag_03_05`. Adding audit-trail logging to the refiner would be a new behavior and is
  out of scope.
- **Ordering**: sanitize the full content, then apply each site's truncation budget. This is the
  only ordering that guarantees no partially-matched pattern survives the cut, and it preserves the
  configured `per_chunk_chars`/300-character semantics.
- **Invariant as documentation, behavior tests as the guard**: the enforcement mechanism is a pair
  of behavior tests (one per prompt-building site) plus the written invariant, not a
  source-introspection test enumerating call sites; a source-scanning test would break on harmless
  refactors without adding safety.
- **Rerank inclusion rationale**: the rerank preview is the same corpus content crossing the same
  boundary, so excluding it would leave a live unguarded path and make the documented invariant
  false on arrival. Its scoring impact is recorded as UNK-01 rather than assumed away.
- **Pattern list untouched**: five patterns remain the definition of what counts as injection, so
  this Plan changes where the control applies, not what it detects.

## Implementation steps
1. **Phase 1: Characterization baseline**
   - [ ] Run `tests/rag/test_pipeline_refiner_fallback.py`, `tests/rag/test_augment_integration.py`,
     `tests/rag/test_rag_pipeline.py`, and `tests/integration/test_rag_turn_integration.py`
     unchanged to record the pre-change behavior and current prompt shapes (REQ-004).
2. **Phase 2: Apply the control at both sites**
   - [ ] Import `sanitize_document` and sanitize before truncation in `RagLLM.refine_context`
     (REQ-001, REQ-003; `scripts/rag/llm_client.py`).
   - [ ] Import `sanitize_document` and sanitize before the preview truncation in
     `_build_rerank_prompt` (REQ-002, REQ-003; `scripts/rag/llm_prompts.py`).
3. **Phase 3: Tests**
   - [ ] Add the refiner sanitization test with a captured prompt body
     (REQ-001; `tests/rag/test_augment_refiner.py`).
   - [ ] Add the rerank preview test and the `_format_chunks` parity test
     (REQ-002, REQ-004; `tests/rag/test_rag_pipeline.py`).
   - [ ] Correct the two stale call-site claims in the integration-test docstrings without
     touching assertions (REQ-006; `tests/integration/test_rag_turn_integration.py`).
4. **Phase 4: Docs, deployment check, and verification**
   - [ ] Update the exclusivity claim into the cross-path invariant (REQ-005;
     `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`).
   - [ ] Add the invariant to the RAG LLM helper description (REQ-005;
     `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`).
   - [ ] Deployment validation/scripts check: no new module, config key, or service change, so
     `deploy.sh` and `config/*.toml` stay unchanged (REQ-003).
   - [ ] Run the full `rules/toolchain.md` validation sequence (all REQs).

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/rag/llm_client.py | Unit (prompt capture through mocked client) | `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_pipeline_refiner_fallback.py` | New sanitization test passes; fallback suites pass unmodified |
| scripts/rag/llm_prompts.py | Unit (direct prompt-builder call) | `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_augment_integration.py` | Rerank preview sanitized; `_format_chunks` parity holds |
| Both source targets | Static + contract | `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports` | Clean; intra-`rag` import contract preserved |
| All targets | Regression | `uv run pytest tests/` | Full suite green, including `tests/integration/test_rag_turn_integration.py` |
| docs/21_rag/rag_03_05_query_pipeline-augment-stages.md, docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | Documentation consistency (21_rag domain) | `rules/toolchain.md` documentation consistency check | Invariant stated; exclusivity claim removed |
| All targets | Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | New sanitization branches covered |

## Risks
- **Risk**: sanitized input changes refiner compression text or rerank scores for corpus content that
  legitimately contains a pattern phrase → **Mitigation**: the five patterns are imperative
  injection phrasings ("ignore instructions", "system:", "[SYSTEM OVERRIDE]", "disregard
  instructions", "new instructions:"), not ordinary prose; `tests/rag/test_rag_quality_regression.py`
  is part of the regression scope, and UNK-01 records the measurement follow-up.
- **Risk**: sanitize-then-truncate shifts which characters fall inside the budget, changing prompt
  length slightly → **Mitigation**: budgets (`per_chunk_chars`, 300) are unchanged, so prompt size
  stays bounded by the same configured limits; the parity test pins the raw-chunk path against
  accidental changes.
- **Risk**: the integration-test docstring is a record other tests and docs cite for the
  sanitization boundary; a stale correction could mislead later → **Mitigation**: the corrected text
  names all sanitized sites and keeps the test's actual assertion (agent layer does not sanitize)
  intact, so the boundary conclusion stays valid.
- **Risk**: both `21_rag` docs are moderately high-churn (18 and 16 commits/30d) → **Mitigation**:
  edits are confined to the sanitization paragraphs; rebase immediately before implementing.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: characterization baseline | Pending | — | — |  |
| 2 | Phase 2: apply the control at both sites | In Progress | — | — |  |
| 3 | Phase 3: tests | In Progress | — | — |  |
| 4 | Phase 4: docs, deployment check, verification | In Progress | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261027-131124_01_scripts_rag_llm_client.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-131124_02_scripts_rag_llm_prompts.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261027-131124_03_tests_rag_test_augment_refiner.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261027-131124_04_tests_rag_test_rag_pipeline.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261027-131124_05_tests_integration_test_rag_turn_integration.py.md | 3 | Procedure | Pending | — | — |
| implementations/20261027-131124_06_docs_21_rag_rag_03_05_query_pipeline-augment-stages.md.md | 4 | Procedure | Pending | — | — |
| implementations/20261027-131124_07_docs_21_rag_rag_03_06_query_pipeline-helpers-and-cache.md.md | 4 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261027-105551
- **Related target files**: scripts/rag/llm_client.py, scripts/rag/llm_prompts.py, tests/rag/test_augment_refiner.py, tests/rag/test_rag_pipeline.py, tests/integration/test_rag_turn_integration.py, docs/21_rag/rag_03_05_query_pipeline-augment-stages.md, docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md

### Requirement Traceability

| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Background and Problem (refiner path verified unguarded) | scripts/rag/llm_client.py | Phase 2 | AC-1 | Prompt-capture unit test | Confirmed by repository evidence |
| REQ-002 | Verified third path in `_build_rerank_prompt`; user-approved scope extension | scripts/rag/llm_prompts.py | Phase 2 | AC-2 | Rerank preview unit test | Confirmed by repository evidence |
| REQ-003 | Issue Dependencies (single sanitizer); `.importlinter` rag contract | scripts/rag/llm_client.py | Phase 2 | AC-6 | `lint-imports`, `ruff check` | Confirmed by repository evidence |
| REQ-003 | Same import rule for the prompt module | scripts/rag/llm_prompts.py | Phase 2 | AC-6 | `lint-imports`, `ruff check` | Confirmed by repository evidence |
| REQ-004 | Constraints (refiner contract, `use_refiner=False`, no pattern change) | scripts/rag/llm_client.py | Phase 2 | AC-3, AC-4 | Refiner fallback suites | Confirmed by repository evidence |
| REQ-004 | `_format_chunks` must stay unchanged | tests/rag/test_rag_pipeline.py | Phase 3 | AC-3 | Parity test | Confirmed by repository evidence |
| REQ-001, REQ-002 | Issue Testing Expectations | tests/rag/test_augment_refiner.py | Phase 3 | AC-1 | Refiner sanitization test | Confirmed by repository evidence |
| REQ-006 | Verified stale docstring claims | tests/integration/test_rag_turn_integration.py | Phase 3 | AC-5 | Suite run with assertions unchanged | Confirmed by repository evidence |
| REQ-005 | Verified exclusivity claim | docs/21_rag/rag_03_05_query_pipeline-augment-stages.md | Phase 4 | AC-5 | 21_rag documentation consistency check | Confirmed by repository evidence |
| REQ-005 | Helper page lacking the invariant | docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md | Phase 4 | AC-5 | 21_rag documentation consistency check | Confirmed by repository evidence |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261027-131124 -->