## Goal
- Make the `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]` block a boundary that crawled text cannot forge: neutralize the marker strings in every untrusted field (content, title, url) and collapse title and url to a single line before they enter the formatted block or the refiner prompt.

## Priority
High

## Scope
- **In-Scope**:
  - A shared marker-neutralization and single-line field helper in `scripts/rag/utils.py`; `sanitize_document` also neutralizes the markers so every content site (augment, refiner, rerank preview) is covered by one mechanism.
  - `_format_chunks` header (title, url) and `RagLLM.refine_context` title handling.
  - Tests for forged markers in content, title and url, for the refiner prompt and for the rerank prompt.
  - Documentation of what the sanitizer does and does not guarantee.
- **Out-of-Scope**:
  - Model- or classifier-based injection defense, extending the phrase blocklist as the primary defense, renaming the markers, changing what the Agent does with the block.
  - Wrapping the refiner's LLM output in boundary markers (the refined text path never had them; see Unknowns).
- **Dependencies**: N/A: none. Sibling plan note: `scripts/rag/llm_client.py` is also edited by the ragrev001 plan (different methods, compatible, any order).

## Background
Review finding F-002. `_format_chunks` (`scripts/rag/stages/augment.py:14-23`) runs `sanitize_document` on `c.content` only; `c.title` and `c.url` are interpolated verbatim into `[Source: ... | ...]`. `sanitize_document` (`scripts/rag/utils.py:55-60`) substitutes five English instruction-like phrases with `[REMOVED]` and never touches the markers. `refine_context` (`scripts/rag/llm_client.py:236-250`) sanitizes content but interpolates `title` unsanitized. `_build_rerank_prompt` (`scripts/rag/llm_prompts.py:159-170`) sanitizes only a 300-char content preview; chunk titles are not in the rerank prompt at all, so the Issue's "title in the rerank prompt" claim does not apply. The corpus comes from a web crawler, so all three fields are untrusted. `sanitize_document` has exactly three production call sites (augment, `refine_context`, `_build_rerank_prompt`), all in `rag/`. No consumer outside `scripts/rag/stages/augment.py` and docs/tests references the marker strings (checked in Step 3).

## Problem
Anything that treats the markers as a trust boundary can be spoofed: content containing `[RAG_CONTEXT_END]` closes the block early and the text after it sits outside, and an instruction-like title is not neutralized at all. The phrase blocklist is best-effort, so the structural boundary is the real control and it is forgeable.

## Reason for Change
Retrieval-augmented prompts are a trust boundary. The boundary has to hold regardless of what a crawled page says.

## Implementation Intent
Define the marker strings once in `rag/utils.py` (lowest layer) and import them from `stages/augment.py`; neutralize them case-insensitively and whitespace-tolerantly in `sanitize_document` and `sanitize_document_full` (content); add a single-line field sanitizer for title and url that applies the same phrase sanitization, neutralizes markers, and collapses control characters and newlines, so a title cannot start a new line that mimics a header or marker. Keep the marker format for consumers unchanged.

## Requirements
- `REQ-001`: Content containing the boundary markers (any case, optional inner whitespace) cannot terminate or reopen the block: the `_format_chunks` output contains exactly one start and one end marker.
- `REQ-002`: Title and url are sanitized through a single-line variant: markers neutralized, injection phrases removed, newlines and control characters collapsed to spaces.
- `REQ-003`: `refine_context` applies the same title/content handling (the title path is currently unsanitized).
- `REQ-004`: `_build_rerank_prompt` content previews neutralize the markers through `sanitize_document`; titles are not part of that prompt (not affected, recorded).
- `REQ-005`: The marker strings and format `[RAG_CONTEXT_START]` / `[RAG_CONTEXT_END]` are unchanged for consumers; `_RAG_BLOCK_START` / `_RAG_BLOCK_END` stay importable from `rag.stages.augment`.
- `REQ-006`: RAG documentation states that the blocklist is best-effort and the structural boundary is the control, without code detail.

## Implementation Target Files
**Freeze status**: Frozen

| File Path | Change Responsibility | Reason for Modification | Related Requirement / Acceptance Criterion | Repository Evidence | Related Tests | Validation Status |
|---|---|---|---|---|---|---|
| `scripts/rag/utils.py` | Modify | Define marker constants, neutralize markers in `sanitize_document`/`sanitize_document_full`, add the single-line field sanitizer | `REQ-001`, `REQ-002`, `REQ-004`, `REQ-005` / AC-1, AC-2, AC-4, AC-5 | `sanitize_document` L55-60, `_INJECTION_PATTERNS` L34-42, no marker handling (checked in Step 3) | `tests/rag/test_rag_pipeline.py` | Verified |
| `scripts/rag/stages/augment.py` | Modify | Import markers from utils; sanitize title and url in the `[Source: ...]` header | `REQ-001`, `REQ-002`, `REQ-005` / AC-1, AC-2, AC-5 | `_format_chunks` L14-23 interpolates `c.title`/`c.url` verbatim (checked in Step 3) | `tests/rag/test_rag_pipeline.py`, `tests/rag/test_rag_stages.py` | Verified |
| `scripts/rag/llm_client.py` | Modify | Sanitize the title in `refine_context` through the field sanitizer | `REQ-003` / AC-3 | `refine_context` L244-249 uses raw `title` (checked in Step 3) | `tests/rag/test_augment_refiner.py` | Verified |
| `tests/rag/test_rag_pipeline.py` | Modify | Forged markers in content/title/url for `_format_chunks`; marker case in rerank preview; marker import path | `REQ-001`, `REQ-002`, `REQ-004`, `REQ-005` / AC-1, AC-2, AC-4, AC-5 | File already imports `_format_chunks`, `_build_rerank_prompt`, `sanitize_document`, the marker constants (L10-24) (checked in Step 3) | self | Verified |
| `tests/rag/test_augment_refiner.py` | Modify | Refiner prompt title/marker tests next to the existing refiner sanitization tests | `REQ-003` / AC-3 | Existing refiner prompt sanitization tests at L571-641 (checked in Step 3) | self | Verified |
| `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Modify | State the sanitizer guarantee boundary and header field handling (5.5 AugmentStage, `sanitize_document()` Contract) | `REQ-006` / AC-6 | L43-53 describe the verbatim header format and the five-pattern contract (checked in Step 3) | `tools/check_docs_*` gates | Verified |
| `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` | Modify | Update the `sanitize_document()` bullets (marker neutralization, field sanitizer) | `REQ-006` / AC-6 | L43-44 describe only the injection-pattern replacement (checked in Step 3) | `tools/check_docs_*` gates | Verified |

## Reference Files
| File Path | Why It Must Be Read | Related Target File or Requirement |
|---|---|---|
| `scripts/rag/llm_prompts.py` | `_build_rerank_prompt` (L159-170) already calls `sanitize_document`; stays unchanged | `REQ-004` |
| `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` | Lists sanitization at each formatting site (7.3); verify it stays accurate, edit only if the implementation phase finds it wrong | `REQ-006` |
| `scripts/rag/pipeline.py` | `augment()` raw-chunk fallback calls `_format_chunks`; the refined-text path has no markers | `REQ-005`, UNK-01 |
| `tests/integration/test_rag_turn_integration.py` | Documents the sanitization boundary (test_f04) that must stay green | `REQ-001` |

## Acceptance Criteria
- AC-1 (`REQ-001`): `_format_chunks` with content containing `[RAG_CONTEXT_END]` (also lower-case and `[ RAG_CONTEXT_END ]`) yields `output.count(START) == 1` and `output.count(END) == 1`.
- AC-2 (`REQ-002`): a title or url with markers, a newline plus fake header, or `ignore previous instructions` yields a single-line, neutralized header.
- AC-3 (`REQ-003`): the refiner prompt contains a neutralized single-line title and neutralized markers in the chunk text.
- AC-4 (`REQ-004`): `_build_rerank_prompt` output contains no raw marker string for forged content.
- AC-5 (`REQ-005`): existing marker assertions (`test_rag_pipeline.py`, `test_rag_stages.py`) pass unmodified; `from rag.stages.augment import _RAG_BLOCK_START, _RAG_BLOCK_END` still works.
- AC-6 (`REQ-006`): the two docs name the best-effort blocklist versus structural boundary; docs checkers pass.

## Tests
- `REQ-001`/`REQ-002`: parametrized `_format_chunks` tests (content, title, url forged; case and spacing variants; empty title falling back to url).
- `REQ-003`: refiner prompt capture test with forged title and content.
- `REQ-004`: rerank prompt test with marker in content.
- `REQ-001`: a `sanitize_document_full` test that a marker-only text is reported as sanitized with the marker pattern in its audit trail (the function has no production caller and no existing test, found in Step 3a of `plan-to-implementation-procedure`, so this is the only coverage of its marker handling).
- `REQ-005`: existing tests unmodified.
- Static: `uv run ruff check`, `uv run mypy`, `uv run bandit -r scripts/rag -c pyproject.toml -ll`.

## Documentation Impact
Yes (`REQ-006`): the RAG query-pipeline augment-stages doc and the shared-utilities doc (located via `docs/00_index.md` RAG rows). State intent and boundary only. Run `check_docs_quality`, `check_docs_structure`, `check_docs_content_policy`, `check_docs_consistency --domain rag`, `check_docs_japanese` per `routing.md` Tools.

## Assumptions
- No code outside `scripts/rag/stages/augment.py` parses the marker strings (grep over `scripts/`, `config/`, `docs/` found only augment, a pipeline docstring, and docs); the Issue's "Needs confirmation" about `scripts/agent/` consumers is resolved for source. The system prompt/prompts under `config/` were part of that grep.
- Overlap judgment (Step 8b, `tools/check_plan_target_overlaps.py`): `scripts/rag/llm_client.py` is also a target of `plans/20261108-164302_ragrev001_mqe-malformed-response-abort.md`; compatible, because that plan edits `expand_queries` and this one edits `refine_context` (disjoint methods, no ordering requirement).
- Neutralizing by rewriting the marker text inside untrusted fields is acceptable to downstream readers because the replacement is only visible in forged content.

## Unknowns
| ID | Unknown Description | Evidence Missing | Resolution Path | Blocking? (True/False) |
|---|---|---|---|---|
| UNK-01 | The refined-text path (refiner output) returns LLM text with no boundary markers at all; whether that is intended is unknown | Product intent for the refiner result | Report to owner at implementation; not changed here (Out-of-Scope) | False |
| UNK-02 | Exact replacement spelling for neutralized markers | Consumer preference | Resolved in the implementation procedure for `scripts/rag/utils.py`: the existing `[REMOVED]` placeholder is reused, so no new vocabulary reaches consumers; AC-1 only requires the raw marker be absent and counts to hold | False |

## Affected areas
| File | Change | Blast Radius | Churn (30d) | Bus Factor | deploy.sh Impact |
|---|---|---|---|---|---|
| `scripts/rag/utils.py` | Modify | Medium (shared by augment, refiner, rerank preview) | 1 | N/A | not applicable (rsynced) |
| `scripts/rag/stages/augment.py` | Modify | Medium (every RAG answer's context block) | 0 | N/A | not applicable (rsynced) |
| `scripts/rag/llm_client.py` | Modify | Low (title line in refiner prompt) | 2 | N/A | not applicable (rsynced) |
| `tests/rag/test_rag_pipeline.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `tests/rag/test_augment_refiner.py` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |
| `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` | Modify | Low | N/A | N/A | not applicable (rsynced) |

## Design
Path B (more than 3 target files). Architecture: `rag.utils` is the lowest layer of the `rag` package, so the marker constants and sanitizers live there; `stages/augment.py` and `llm_client.py` import from it (no inversion). `lint-imports`: 6 contracts kept, 0 broken at plan time. Callers: `sanitize_document` has three production call sites, all in `scripts/rag/` (augment, `refine_context`, `_build_rerank_prompt`), so folding marker neutralization into it covers every content site with one change.

Alternatives: (a) escape only in `_format_chunks` rejected because the refiner and rerank prompts would stay forgeable; (b) extend the phrase blocklist rejected by the Issue constraint. Chosen: one marker rule in `sanitize_document` plus a separate single-line field sanitizer, because title and url need newline collapsing that content must not get (content keeps its line structure).

Not affected (consumer scan by grep of the marker strings): `scripts/agent/` has no parser of the markers; `tests/mcp_servers/rag_pipeline/test_rag_pipeline_mcp_service.py` uses a `[Source: T | U]` literal from a mocked `augment` and is unaffected.

Validation baseline: `radon cc` is recorded for `scripts/rag/llm_client.py` in the sibling plan (unchanged file); `vulture`/`bandit` over `scripts/` carry pre-existing unrelated findings (same run as the sibling plan, source unchanged). `diff-cover`: no changed lines at plan time; threshold 90 percent per `rules/toolchain.md` applies at implementation.

## Implementation steps
1. **Phase 1: Tests first**
   - [ ] Forged-marker tests for `_format_chunks` and rerank prompt (`REQ-001`, `REQ-002`, `REQ-004`, `REQ-005`; `tests/rag/test_rag_pipeline.py`)
   - [ ] Refiner title/marker test (`REQ-003`; `tests/rag/test_augment_refiner.py`)
2. **Phase 2: Helpers and call sites**
   - [ ] Marker constants, marker neutralization in `sanitize_document`/`sanitize_document_full`, single-line field sanitizer (`REQ-001`, `REQ-002`, `REQ-004`, `REQ-005`; `scripts/rag/utils.py`)
   - [ ] Import markers, sanitize header fields (`REQ-001`, `REQ-002`, `REQ-005`; `scripts/rag/stages/augment.py`)
   - [ ] Sanitize the refiner title (`REQ-003`; `scripts/rag/llm_client.py`)
3. **Phase 3: Documentation**
   - [ ] Update the two RAG docs (`REQ-006`; `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`, `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`)
4. **Phase 4: Deployment & Verification**
   - [ ] Full validation per `rules/toolchain.md`; the change is committed and pushed first, then a hand-off to `skills/deploy/SKILL.md` at the user's decision (all requirements; `scripts/rag/utils.py`)

### Release units
**Unit**: ragrev002-core | **Phases**: 1, 2 | **Reason**: the new tests fail until the helpers and call sites land, and the call-site edits do not compile without the helpers.

## Validation plan
| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/rag/utils.py`, `scripts/rag/stages/augment.py` | Unit | `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_rag_stages.py -q` | new tests pass, marker assertions unchanged |
| `scripts/rag/llm_client.py` | Unit | `uv run pytest tests/rag/test_augment_refiner.py -q` | refiner tests pass |
| sanitization boundary | Integration | `uv run pytest tests/integration/test_rag_turn_integration.py -q` | green |
| touched code | Static | `uv run ruff check`, `uv run mypy`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/rag -c pyproject.toml -ll` | clean |
| docs | Docs gates | `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` | no findings |

## Risks
- **Risk**: neutralizing alters legitimate chunks that discuss the marker names (for example this repo's own docs ingested into the corpus) → **Mitigation**: only the exact bracketed marker forms are rewritten, content is otherwise untouched; acceptable loss, documented.
- **Risk**: title collapse changes the header for titles containing newlines or brackets, breaking an exact-string test → **Mitigation**: existing header tests use plain titles (`test_rag_stages.py` L1102, L1132); run them unmodified (AC-5).
- **Risk**: `sanitize_document` is documented as removing five patterns; adding marker handling changes its contract → **Mitigation**: docs updated in Phase 3 (`REQ-006`) and the contract change pinned by tests.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Phase 1: tests first | In Progress | — | — |  |
| 2 | Phase 2: helpers and call sites | In Progress | — | — |  |
| 3 | Phase 3: documentation | In Progress | — | — |  |
| 4 | Phase 4: deployment and verification | Pending | — | — |  |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| implementations/20261109-104558_01_scripts_rag_utils.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-104558_02_scripts_rag_stages_augment.py.md | 2 | Procedure | Pending | — | — |
| implementations/20261109-104558_03_scripts_rag_llm_client.py.md | 1, 2 | Procedure | Pending | — | — |
| implementations/20261109-104558_04_tests_rag_test_rag_pipeline.py.md | 1 | Procedure | Pending | — | — |
| implementations/20261109-104558_06_docs_21_rag_rag_03_05_query_pipeline-augment-stages.md.md | 3 | Procedure | Pending | — | — |
| implementations/20261109-104558_07_docs_21_rag_rag_02_09_ingestion_pipeline-shared-utilities.md.md | 3 | Procedure | Pending | — | — |

## Traceability
- **Workflow phase**: issue-to-plan
- **Source issue**: issues/20261108-131004_ragrev002_rag-context-boundary-injection.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: this document is the generated plan
- **Source implementation procedure**: N/A: not applicable in this phase
- **Generated at**: 20261108-164455
- **Related target files**: `scripts/rag/utils.py`, `scripts/rag/stages/augment.py`, `scripts/rag/llm_client.py`, `tests/rag/test_rag_pipeline.py`, `tests/rag/test_augment_refiner.py`, `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`, `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md`

### Requirement Traceability
| Requirement ID | Source Issue section or evidence | Target file | Implementation step | Acceptance criterion | Test or validation item | Status |
|---|---|---|---|---|---|---|
| REQ-001 | Required Changes 1; `augment.py:14-23` | `scripts/rag/utils.py` | Phase 2 | AC-1 | `_format_chunks` forged-marker tests | Confirmed by repository evidence |
| REQ-001 | Acceptance Criteria 1 | `scripts/rag/stages/augment.py` | Phase 2 | AC-1 | `_format_chunks` forged-marker tests | Confirmed by repository evidence |
| REQ-001 | Testing Expectations | `tests/rag/test_rag_pipeline.py` | Phase 1 | AC-1 | forged-marker tests | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/utils.py` | Phase 2 | AC-2 | title/url tests | Explicit in issue |
| REQ-002 | Required Changes 2 | `scripts/rag/stages/augment.py` | Phase 2 | AC-2 | title/url tests | Explicit in issue |
| REQ-002 | Testing Expectations | `tests/rag/test_rag_pipeline.py` | Phase 1 | AC-2 | title/url tests | Explicit in issue |
| REQ-003 | Required Changes 3; `llm_client.py:244-249` | `scripts/rag/llm_client.py` | Phase 2 | AC-3 | refiner prompt test | Confirmed by repository evidence |
| REQ-003 | Testing Expectations | `tests/rag/test_augment_refiner.py` | Phase 1 | AC-3 | refiner prompt test | Explicit in issue |
| REQ-004 | Required Changes 3 (corrected: rerank has no title) | `scripts/rag/utils.py` | Phase 2 | AC-4 | rerank prompt test | Derived from confirmed evidence |
| REQ-004 | Testing Expectations | `tests/rag/test_rag_pipeline.py` | Phase 1 | AC-4 | rerank prompt test | Derived from confirmed evidence |
| REQ-005 | Constraints | `scripts/rag/utils.py` | Phase 2 | AC-5 | existing marker tests | Explicit in issue |
| REQ-005 | Constraints | `scripts/rag/stages/augment.py` | Phase 2 | AC-5 | existing marker tests | Explicit in issue |
| REQ-005 | Constraints | `tests/rag/test_rag_pipeline.py` | Phase 1 | AC-5 | existing marker tests | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md` | Phase 3 | AC-6 | docs gates | Explicit in issue |
| REQ-006 | Documentation Impact | `docs/21_rag/rag_02_09_ingestion_pipeline-shared-utilities.md` | Phase 3 | AC-6 | docs gates | Explicit in issue |

<!-- tools/generate_workitem.py implementation-procedure-pass timestamp: 20261109-104558 -->