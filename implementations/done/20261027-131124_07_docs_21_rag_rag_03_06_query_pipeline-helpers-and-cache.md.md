# Procedure: State the sanitization invariant on the RAG LLM helper page

## Goal
- Document the invariant where the RAG LLM helper methods are described, so a future prompt
  builder added to `scripts/rag/llm_prompts.py` is checked against it (REQ-005: invariant visible
  on the helper page; AC-5).

## Scope
- The `RagLLM` helper paragraph of the page (the one listing `expand_queries`,
  `cross_encoder_rerank`, `summarize_tool_result`, `refine_context`, and the
  `scripts/rag/llm_prompts.py` note).

## Assumptions
- Overlap with the rag002 Plan (`plans/20261027-110252_rag002_rag-timeout-enforcement-gap.md`):
  rag002 adds timeout-source text to this same page; per the rag001 Plan's Scope note the edits
  are disjoint paragraphs and whichever Plan implements second rebases. Re-read the paragraph
  immediately before editing.
- High-churn doc (16 commits/30d per the Plan's Affected areas): rebase immediately before editing.

## Design decisions
- Add one invariant paragraph after the `RagLLM` helper paragraph: every query-time path that
  embeds retrieved chunk content into an LLM prompt sanitizes it with `sanitize_document` at the
  formatting site; the sanitized sites are `refine_context` (refiner prompt) and
  `_build_rerank_prompt` (rerank previews), in addition to the augment stage's `_format_chunks`
  (cross-link to `docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`).
- Note explicitly that `summarize_tool_result` is a different trust boundary (agent tool output,
  not corpus chunks) and is not covered by the invariant — mirroring the Plan's Out-of-Scope
  rationale so the boundary is not overgeneralized.

## Alternatives considered
- N/A: wording is dictated by REQ-005; no technical alternative applies to a docs row.

## Implementation
### Target file
`docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`

### Procedure
1. Locate the paragraph beginning "`RagLLM` provides MQE query expansion (`expand_queries`)"
   (page line 62). Verification note: the `RagExpansionError`/`RagRerankError` clause is the second
   semicolon-joined clause *of the same paragraph*, so the procedure's original "insert before the
   RagExpansionError/RagRerankError sentence" is not achievable without splitting that sentence;
   the invariant paragraph is inserted after the whole RagLLM paragraph instead (both original
   clauses stay byte-identical, satisfying the Compatibility section).
2. Insert the invariant paragraph (Design decisions) as a new paragraph directly after it.

### Method
- N/A: covered by Procedure.

### Details
- Reference the symbols by name as they exist in source: `RagLLM.refine_context` and
  `_build_rerank_prompt`; state that both import `sanitize_document` from `rag.utils`.

## Compatibility considerations
- Existing sentences about prompt templates living in `scripts/rag/llm_prompts.py` and the
  error-handling cross-link stay byte-identical.

## Security considerations
- N/A: docs only; this page becomes the copy-source for the invariant (Plan Reason for Change).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `rules/toolchain.md` documentation consistency check for the `21_rag` domain
  (Plan Validation plan row 5).
- Grep the page for "sanitize": the invariant paragraph is present.

## Completion criteria
- AC-5: the page states the cross-path invariant with the sanitized-site list and the
  `summarize_tool_result` boundary note.

## Out of Scope
- Timeout/`_call_llm` text (owned by the rag002 Plan), cache sections of the page, and any code text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Insert the invariant paragraph per Implementation > Procedure/Details | Completed | 20261027-201844 | 20261027-201844 | — |
| 2 | Run the `rules/toolchain.md` documentation checkers for the `21_rag` domain | Completed | 20261027-201844 | 20261027-201844 | — |

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
- **Requirement ID**: REQ-005 (invariant documented on the helper page)
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-131124
- **Related target files**: docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md