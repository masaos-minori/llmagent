# Procedure: Replace the "exclusively" claim with the cross-path sanitization invariant

## Goal
- Rewrite the exclusivity sentence on the augment-stages page so it states the Plan's invariant
  instead of confining sanitization to the augment stage (REQ-005: cross-path invariant documented; AC-5).

## Scope
- The `sanitize_document()` Contract subsection of the page: the sentence naming `AugmentStage`
  as the exclusive user of `sanitize_document()`.

## Assumptions
- High-churn doc (18 commits/30d per the Plan's Affected areas): rebase immediately before
  editing and re-locate the sentence if it has moved.

## Design decisions
- Replace the exclusivity sentence with the invariant plus the site list: every query-time path
  that embeds retrieved chunk content into an LLM prompt sanitizes it with `sanitize_document` at
  the formatting site — `scripts/rag/stages/augment.py::_format_chunks`,
  `scripts/rag/llm_client.py::RagLLM.refine_context`, and `scripts/rag/llm_prompts.py::_build_rerank_prompt`.
- Keep the `sanitize_document` vs `sanitize_document_full` distinction sentence untouched; only
  the "exclusively" clause changes.

## Alternatives considered
- N/A: wording is dictated by REQ-005; no technical alternative applies to a docs row.

## Implementation
### Target file
`docs/21_rag/rag_03_05_query_pipeline-augment-stages.md`

### Procedure
1. Locate the paragraph ending "`AugmentStage` uses `sanitize_document()` exclusively and does not
   consume the audit trail."
2. Rewrite that sentence to the invariant wording (Design decisions), keeping the audit-trail note
   for the augment stage ("does not consume the audit trail") intact.

### Method
- N/A: covered by Procedure.

### Details
- Add a cross-link to `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md` where the refiner
  and rerank helper methods are described, so the two pages present one invariant.

## Compatibility considerations
- The preceding contract paragraph (five pattern categories, `[REMOVED]` substitution, plain `str`
  return) stays byte-identical.

## Security considerations
- N/A: docs only; the corrected text is the durable record of the security invariant (REQ-005).

## Rollback considerations
- N/A: revert the commit.

## Validation plan
- `rules/toolchain.md` documentation consistency check for the `21_rag` domain
  (Plan Validation plan row 5).
- Grep the page for "exclusively": no remaining exclusivity claim about `sanitize_document`.

## Completion criteria
- AC-5: the page no longer claims `sanitize_document()` is exclusive to `AugmentStage`.
- The invariant sentence and the three-site list are present on the page.

## Out of Scope
- Other sections of the page; `docs/21_rag/rag_03_06_query_pipeline-helpers-and-cache.md`
  (procedure 07); any config or code text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Apply the paragraph rewrite per Implementation > Procedure/Details | Pending | — | — | |
| 2 | Run the `rules/toolchain.md` documentation checkers for the `21_rag` domain | Pending | — | — | |

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
- **Requirement ID**: REQ-005 (invariant documented; exclusivity claim removed)
- **Source issue**: issues/20261027-071525_rag001_rag-refiner-skips-sanitization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-105551_rag001_rag-refiner-skips-sanitization.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-131124
- **Related target files**: docs/21_rag/rag_03_05_query_pipeline-augment-stages.md
