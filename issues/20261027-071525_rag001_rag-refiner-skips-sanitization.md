# RAG refiner skips input sanitization

## Priority
Medium

## Summary
Apply the existing prompt-injection sanitization (`sanitize_document`) to the chunk
content that the context refiner sends to the LLM, so both injectable RAG paths
(raw-chunk formatting and refiner compression) sanitize identically. Currently the
refiner path sends raw chunk content to the LLM without any sanitization.

## Background
`scripts/rag/utils.py` defines `sanitize_document(text)`, which replaces a fixed set
of known prompt-injection patterns with `[REMOVED]`. The patterns cover commands such
as `ignore instructions`, `system:`, `[SYSTEM OVERRIDE]`, `disregard instructions`, and
`new instructions:` (see `_INJECTION_PATTERNS`, `scripts/rag/utils.py`).

In the query-time pipeline, chunk content reaches the LLM through two distinct paths:

- Raw-chunk formatting in `scripts/rag/stages/augment.py::_format_chunks` applies
  `sanitize_document(c.content)` before wrapping the chunk in the
  `[RAG_CONTEXT_START]...[RAG_CONTEXT_END]` block.
- Context refinement in `scripts/rag/llm_client.py::RagLLM.refine_context` builds the
  refiner prompt by slicing `c.content[:per_chunk_chars]` and embedding it directly in
  the prompt with no sanitization call.

`pipeline.py`'s `augment()` fallback chain (HTTP augment -> search -> rerank -> refiner
-> raw chunks) returns the refiner output verbatim when `use_refiner` is enabled and it
produces non-empty text (`scripts/rag/pipeline.py`, `augment()`).

## Problem
A prompt-injection sanitization control exists on exactly one of the two injectable RAG
paths. When `use_refiner=True`, chunk content that may contain injection markers is sent
to the refiner LLM unsanitized, while the same content would be sanitized on the
raw-chunk path. The control is therefore inconsistent at a trust boundary: an attacker
who can place an injection payload in the RAG corpus (a document that becomes a chunk)
can reach the refiner LLM through the unsanitized path even though the raw-chunk path is
guarded.

## Reason for Change
The asymmetry is latent and easy to widen: any future caller that formats chunks for an
LLM may assume sanitization is universal when it is only applied in `_format_chunks`.
There is no operational trigger making this time-sensitive, but the gap is a
defense-in-depth hole that only closes consistently if the refiner path is brought in
line. Severity belongs in Priority, not here.

## Implementation Intent
Bring the refiner path under the same sanitization responsibility already applied on the
raw-chunk path. Sanitize each chunk's content before it enters the refiner prompt, using
the same `sanitize_document` helper, without weakening the raw-chunk path or changing
the refiner's compression contract. Preserve the refiner's existing error handling and
fallback-to-raw-chunks behavior. Name the responsibility (sanitize LLM inputs at the
trust boundary) rather than copying the raw-chunk formatting.

## Target Files or Areas
- `scripts/rag/llm_client.py` (`RagLLM.refine_context`)
- `scripts/rag/utils.py` (`sanitize_document`)
- `scripts/rag/stages/augment.py` (`_format_chunks`) for parity reference
- `tests/rag/test_augment_refiner.py`

## Required Changes
- Sanitize each chunk's content in `refine_context` before building the refiner prompt,
  reusing `sanitize_document` from `rag.utils`.
- Do not alter the raw-chunk sanitization in `_format_chunks`; keep both paths applying
  the same helper so the control is uniform.
- Keep the refiner prompt structure, temperature, and max_tokens unchanged.
- Add a regression test asserting that chunk content containing a known injection pattern
  is sanitized before it reaches the LLM in the refiner path.

## Constraints
- The refiner is gated by `use_refiner`; the fix must not change behavior when
  `use_refiner=False`.
- Sanitization must not raise on clean text or turn valid content into an empty string
  in a way that would flip the refiner's empty-output fallback.
- Do not expand the injection pattern list or change what counts as a pattern as part of
  this issue.

## Acceptance Criteria
- `refine_context` calls `sanitize_document` on every chunk's content before prompt
  construction.
- A chunk whose content contains a pattern from `_INJECTION_PATTERNS` yields a sanitized
  refiner prompt (pattern replaced with `[REMOVED]`).
- Existing refiner tests and augment/refiner integration tests pass unchanged.

## Testing Expectations
- Unit test for `refine_context` (or its prompt builder) proving injection-pattern
  content is sanitized before the LLM call.
- Regression run of `tests/rag/test_augment_refiner.py` and `tests/rag/test_augment_integration.py`.

## Documentation Impact
Document in the RAG pipeline docs that both injectable paths (refiner and raw-chunk)
apply the same prompt-injection sanitization, and note the trust-boundary rationale so a
future path cannot silently drop it.

## Out of Scope
- Changing the injection pattern list in `utils.py`.
- Sanitizing the refiner's *output* (a separate concern).
- Altering the HTTP augment path or the search/rerank stages.

## Dependencies
- Depends on `sanitize_document` remaining the single source of injection sanitization
  for the query path.

## Unresolved Questions
- Whether the refiner LLM is expected to receive raw or sanitized content by design;
  confirm the sanitizer was intended to cover the refiner path (不明: no comment or doc
  states the intent).
- Whether sanitizing refiner input changes the refiner's compression quality enough to
  matter for downstream answers (不明: not measured).

## AI Implementation Instruction
Sanitize chunk content in `RagLLM.refine_context` via `sanitize_document` before building
the prompt. Do not touch `_format_chunks`, the HTTP augment path, or the injection
pattern list. Preserve refiner error handling and the fallback-to-raw-chunks behavior.
Add a regression test for sanitized refiner input. Keep the diff scoped to the refiner
input path.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261027-071525
- **Related target files**: scripts/rag/llm_client.py, scripts/rag/utils.py, scripts/rag/stages/augment.py, tests/rag/test_augment_refiner.py
