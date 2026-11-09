## Goal

Correct the MQE variant-count statement in the search-stages document and state that the fan-out is capped and deduplicated and that embedding concurrency is bounded (`REQ-005`: document the cap, dedup, and concurrency bound).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: section 5.1 (MqeStage) and the embedding bullet of section 5.2 (SearchStage) of `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`.
- Plan step 3 (documentation); apply after the code procedures.

## Assumptions

- Re-verified at generation time: section 5.1 says "The number of variants is controlled by the `mqe_n_queries` setting", which overstates configuration control until the cap lands; section 5.2 says embeddings are generated "in parallel for all queries".
- Overlap with `implementations/20261109-121538_03_docs_21_rag_rag_03_04_query_pipeline-search-stages.md.md` (ragrev004): compatible; that procedure edits the retrieval-leg failure wording in section 5.2. Edit only the sentences named here and re-read the section before editing if it has changed.
- Docs are English (`skills/DESIGN.md` Output language) and follow the Docs content policy: state the contract, not the algorithm or the numeric constant.

## Design decisions

- Replace the 5.1 variant-count bullet with: the expanded list holds the original query first, then at most `mqe_n_queries` distinct paraphrases (trimmed, case-insensitive duplicates and whitespace-only entries removed).
- Reword the 5.2 embedding bullet to say embeddings are generated in parallel with a bounded number of concurrent requests; do not state the constant (it is a tunable implementation detail).

## Alternatives considered

N/A: two-sentence documentation edit.

## Implementation
### Target file
`docs/21_rag/rag_03_04_query_pipeline-search-stages.md`

### Procedure
1. Edit the variant-count bullet in section 5.1 as described under Design decisions.
2. Edit the first bullet of section 5.2 as described under Design decisions.
3. Keep headings, front matter, and links unchanged.

### Method
- Plain prose edits; no code block and no constant value.

### Details
- Do not edit another document; a needed change elsewhere is an additional target file discovery.

## Compatibility considerations

N/A: documentation only; no file is renamed or removed.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_03_04_query_pipeline-search-stages.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The document states the cap, the dedup, and the bounded embedding concurrency, and no longer says the variant count is controlled by `mqe_n_queries` alone.
- All five checkers report no findings.

## Out of Scope

- Code, tests, and other documents.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit sections 5.1 and 5.2 of the search-stages document | Pending | — | — | |
| 2 | Run the documentation checkers named in Validation plan | Pending | — | — | |

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
- **Requirement ID**: `REQ-005` (document cap, dedup, and bounded concurrency)
- **Source issue**: issues/20261108-131120_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165229_ragrev007_mqe-queries-uncapped-duplicated.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-133800
- **Related target files**: `docs/21_rag/rag_03_04_query_pipeline-search-stages.md`
