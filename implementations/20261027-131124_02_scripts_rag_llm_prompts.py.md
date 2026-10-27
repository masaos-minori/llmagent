# Procedure: Sanitize candidate content in `_build_rerank_prompt`

## Goal
- Apply `sanitize_document()` to each candidate's content before the 300-character preview
  truncation (REQ-002: rerank preview sanitization, scope extension approved 2026-10-27;
  REQ-003: reuse the single `rag.utils` sanitizer; REQ-004: template and budget unchanged).

## Scope
- One function body (`_build_rerank_prompt` in `scripts/rag/llm_prompts.py`) plus one new import.
- `build`-side behavior (`_mqe_prompt`, `_apply_rerank_scores`, constants) untouched.

## Assumptions
- Double sanitization is harmless: in a full pipeline the same hits are already sanitized by
  `RagLLM.refine_context` (procedure 01) and then sanitized again here; `sanitize_document`
  replaces markers with `[REMOVED]`, so a second pass on already-clean text is a no-op
  (Plan Assumptions).
- Sanitize-then-truncate ordering (Plan Assumptions): the 300-character cut must come after
  sanitization or a pattern straddling the cut survives.
- The `.replace("\n", " ")` on the preview stays: it flattens newlines for the one-line item
  rendering and is orthogonal to sanitization.

## Design decisions
- Sanitize at the prompt-builder site itself (defense-in-depth), mirroring `_format_chunks` in
  `scripts/rag/stages/augment.py`: a caller that forgets to sanitize is still guarded here.
- Use the plain `sanitize_document` (returns `str`): query-path contract (REQ-003).

## Alternatives considered
- Relying on upstream sanitization only (rerank candidates can arrive from fusion without the
  refiner having run on them): rejected — leaves the site unguarded for exactly the corpus
  content this Plan targets.
- Sanitize after the `[:300]` slice: rejected — partial-pattern survival.
- Raising `MqeParseError`-style rejection instead of substitution: rejected — changes the
  rerank contract (REQ-004).

## Implementation
### Target file
`scripts/rag/llm_prompts.py`

### Procedure
1. Add the sanitizer import.
2. In `_build_rerank_prompt`, sanitize the full candidate content before the preview truncation;
   keep the numbering, template lookup, type check, and `template.format(query=..., items_text=...)`
   unchanged.

### Method
- Add after the `shared.types` import block:
  `from rag.utils import sanitize_document` (new)
- Replace the single line
  `preview = chunk.content[:300].replace("\n", " ")`
  with
  `preview = sanitize_document(chunk.content)[:300].replace("\n", " ")`.

### Details
- `candidates` is `list[RagHit]`-like; only the `content` field is sanitized (Content-only
  Invariance Rule, `rag/models_result.py`).
- The `rerank_prompt_template` config value, the query substitution, and the 300-character
  budget are otherwise unchanged (REQ-002).
- `_build_rerank_prompt` is called by `RagLLM.cross_encoder_rerank` in `scripts/rag/llm_client.py`
  via `_call_llm`; that call site is not modified by this procedure.

## Compatibility considerations
- Function signature and return type unchanged; existing prompt-builder tests pass unmodified.
- Clean text sanitizes to itself, so prompts for clean corpora are byte-identical to today's
  (guarded by the parity test in procedure 04, AC-3).

## Security considerations
- Closes the second unguarded chunk-to-prompt site (rerank preview) with the unchanged
  five-pattern list.
- The sanitize-before-cut order is the security-relevant part; preserve it in future edits.

## Rollback considerations
- Revert the single commit; the added import reverts with it (ruff would flag an unused import).

## Validation plan
- `uv run pytest tests/rag/test_rag_pipeline.py tests/rag/test_augment_integration.py`
  (new rerank preview test passes; `_format_chunks` parity holds).
- `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/`,
  `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
  (AC-6).
- Diff coverage per the Plan's Validation plan row.

## Completion criteria
- AC-2: a candidate carrying an injection phrase produces a prompt containing `[REMOVED]` and no
  raw phrase, with each preview still within 300 characters (verified by the test in procedure 04).
- AC-3: template/query substitution and the 300-character budget unchanged.
- AC-6: `lint-imports` and `ruff` clean with the new intra-`rag` import.

## Out of Scope
- `_INJECTION_PATTERNS` content, `rerank_prompt_template` config semantics, MQE prompt building,
  and any scoring-behavior change (Plan Out-of-Scope).

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
- **Requirement ID**: REQ-002 (rerank preview sanitization), REQ-003 (single-sanitizer import), REQ-004 (unchanged prompt semantics)
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-131124
- **Related target files**: scripts/rag/llm_prompts.py
