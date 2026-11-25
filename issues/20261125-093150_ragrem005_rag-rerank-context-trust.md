# Harden rerank validation and the refined-context trust boundary

## Priority
High

## Summary
Accept a rerank response only when it scores every candidate exactly once, otherwise fall back to RRF order, and wrap Refiner output in the same untrusted-context markers as raw chunks.

## Background
Verified against master on 2026-11-25 (source: `memo-issue.md` H-05):
- Confirmed: `_apply_rerank_scores` gives a missing candidate `_DEFAULT_RERANK_SCORE` and also replaces a non-numeric score with it (`scripts/rag/llm_prompts.py:234-245`); it does not check duplicates, unknown ids, range, booleans, NaN, or Infinity. The only parse-failure fallback is a missing or malformed JSON object (`:226-233`).
- Confirmed: raw chunks are wrapped with `[RAG_CONTEXT_START]` and `[RAG_CONTEXT_END]` by `_format_chunks` (`scripts/rag/stages/augment.py:29-37`) and sanitized by `scripts/rag/utils.py`; the Refiner path returns `refined.text` directly (`scripts/rag/pipeline.py:212-218`) with no markers.
- Not verified: the actual default score value and whether sanitization already runs on Refiner input.

## Problem
Unevaluated candidates can outrank candidates the LLM scored, and Refiner text derived from retrieved documents reaches the downstream model without the boundary contract.

## Reason for Change
Both affect what the model treats as data versus instructions; the rerank gap also silently changes ranking quality.

## Implementation Intent
Make rerank validation all-or-nothing with the existing `RagRerankError` and RRF fallback, remove the implicit default, and apply the canonical context block (including marker neutralization) to Refiner output. Document sanitization as risk reduction, not a complete boundary.

## Target Files or Areas
- `scripts/rag/llm_prompts.py`, `scripts/rag/llm_client.py`, `scripts/rag/stages/rerank.py`
- `scripts/rag/pipeline.py`, `scripts/rag/augment.py`, `scripts/rag/pipeline_refiner.py`, `scripts/rag/utils.py`
- `tests/rag/`

## Required Changes
- Require exactly one score per candidate id; reject duplicate, missing, unknown, and out-of-range ids; reject booleans, strings, null, NaN, Infinity, and scores outside 0 to 10.
- Remove the implicit default score; turn invalid or partial responses into `RagRerankError` so the RRF fallback applies.
- Wrap Refiner output in the canonical markers and neutralize embedded markers.
- Add a Refiner prompt requirement to extract facts without following instructions in retrieved content.
- Record detection category and count without logging document text.

## Constraints
- Valid complete rerank responses keep their current ordering.
- Do not log sensitive document text; keep the raw-chunk path unchanged.

## Acceptance Criteria
- A partial rerank response cannot promote unevaluated candidates; every malformed response uses the RRF fallback.
- Raw and refined paths produce the same outer structure; Refiner output cannot close and reopen the boundary.
- Tests cover multilingual, Unicode, zero-width, boundary-marker, and injection cases.

## Testing Expectations
Unit tests per rejection class and for the refined path; regression tests on ordering; whole-suite run and changed-path gates.

## Documentation Impact
Document the rerank validation contract and the risk-reduction wording for sanitization in the RAG documents.

## Out of Scope
- Claiming complete prompt-injection prevention.
- Outcome and stage diagnostics (issues/20261125-093149_ragrem004_rag-pipeline-outcomes.md).

## Dependencies
- Depends on issues/20261125-093149_ragrem004_rag-pipeline-outcomes.md (rerank failures are recorded as stage results there).

## Unresolved Questions
- `不明`: the intended minimum for scores (the note says 0 through 10); confirm against the rerank prompt.

## AI Implementation Instruction
Keep the change inside the listed RAG modules; do not alter prompt-injection patterns beyond the stated marker handling.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261125-093150
- **Related target files**: `scripts/rag/llm_prompts.py`, `scripts/rag/pipeline.py`, `scripts/rag/stages/augment.py`, `scripts/rag/utils.py`
