# Procedure: Sanitize chunk content in `RagLLM.refine_context`

## Goal
- Apply `sanitize_document()` to each chunk's content before it is truncated and interpolated
  into the refiner prompt, closing the unguarded chunk-to-prompt path (REQ-001: refiner prompt
  sanitization; REQ-003: reuse the single `rag.utils` sanitizer; REQ-004: refiner contract unchanged).

## Scope
- One function body (`RagLLM.refine_context` in `scripts/rag/llm_client.py`) plus one new import.
- No signature, template, constant, or return-contract change.

## Assumptions
- Overlap with the rag002 Plan (`plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md`):
  both touch `scripts/rag/llm_client.py`, but rag002 edits `_call_llm`/`get_embedding` and this
  procedure edits `refine_context` — disjoint functions per the Plan's Scope note; whichever
  Plan implements second rebases onto the other.
- The module-level `refine_context` in `scripts/rag/pipeline_refiner.py` is a different function
  (the only caller of this method) and is not modified here.
- Sanitize-then-truncate ordering (Plan Assumptions): truncating first would let a pattern
  straddling the cut survive.

## Design decisions
- Sanitize at the formatting site, not in a shared preprocessing wrapper (Plan Design): keeps
  each guarded site visible.
- Use the plain `sanitize_document` (returns `str`), not `sanitize_document_full`: the query-path
  contract stays audit-trail-free (REQ-003).

## Alternatives considered
- Shared "sanitize all hits" step in `pipeline_refiner.py`: rejected — hides which sites are
  guarded and would not protect a future prompt builder (Plan Design).
- Sanitize after the `per_chunk_chars` slice: rejected — partial patterns crossing the cut remain.
- `sanitize_document_full()`: rejected — audit trail is out of scope (REQ-004).

## Implementation
### Target file
`scripts/rag/llm_client.py`

### Procedure
1. Add the sanitizer import to the existing `rag` import block.
2. In `RagLLM.refine_context`, sanitize the full chunk content before the per-chunk truncation;
   leave the item formatting, prompt template, request body, timeout, and response parsing as-is.

### Method
- Add, in the `rag` import block (after `from rag.exceptions import ...`):
  `from rag.utils import sanitize_document` (new)
- Replace the single line
  `text = c.content[:per_chunk_chars]`
  with
  `text = sanitize_document(c.content)[:per_chunk_chars]`.

### Details
- `refine_context` builds `items` entries as `f"[{i}] {title}\n{text}"` and posts one user message
  built from `_REFINER_PROMPT_TEMPLATE`; only the `text` assignment changes.
- The method posts directly via `self._client.post` (it does not go through `_call_llm`), so the
  rag002 Plan's `_call_llm` edits do not intersect this function body.
- Chunk objects here are `RagHit`-like: only the `content` field is sanitized; `title`/`url` come
  from the corpus metadata and are not touched (Content-only Invariance Rule, `rag/models_result.py`).
- Error behavior (`raise_for_status`, `extract_llm_content(parse_http_json(resp))`) and the
  `pipeline_refiner.py` `RefineResult` fallback conversion are unchanged (REQ-004).

## Compatibility considerations
- Return type and exceptions unchanged; `tests/rag/test_pipeline_refiner_fallback.py` and
  `tests/rag/test_pipeline_refiner_fallback_counters.py` must pass unmodified (AC-4).
- Sanitized clean text equals the original text, so `refiner_returned_empty` semantics are
  unaffected for clean corpora (AC-4).
- Visible behavior change: a refiner-enabled query now sends `[REMOVED]`-substituted text to the
  LLM instead of raw injection phrases; the refined output is what downstream stages see (intended).

## Security considerations
- This change is the security fix itself: corpus content crossing into the refiner LLM prompt is
  sanitized at the formatting site with the same five-pattern list (unchanged).
- Order (sanitize full content, then truncate) is the security-relevant part; any future edit
  must keep it.

## Rollback considerations
- Revert the single commit; the added import reverts with it (ruff would otherwise flag an unused
  import).

## Validation plan
- `uv run pytest tests/rag/test_augment_refiner.py tests/rag/test_pipeline_refiner_fallback.py`
  (new sanitization test passes; fallback suites pass unmodified).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
  (intra-`rag` import contract preserved, AC-6).
- Diff coverage per the Plan's Validation plan row.

## Completion criteria
- AC-1: the captured refiner request body shows `[REMOVED]` and no raw injection phrase
  (verified by the test added in procedure 03).
- AC-3: refiner prompt template, temperature, and `max_tokens` fields unchanged.
- AC-4: refiner fallback suites pass unmodified.
- AC-6: `lint-imports` and `ruff` clean with the new intra-`rag` import.

## Out of Scope
- `_INJECTION_PATTERNS` content, sanitizing the refiner **output**, the HTTP augment path,
  `summarize_tool_result`, and MQE prompt building (Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (refiner prompt sanitization), REQ-003 (single-sanitizer import), REQ-004 (unchanged refiner contract)
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-131124
- **Related target files**: scripts/rag/llm_client.py
