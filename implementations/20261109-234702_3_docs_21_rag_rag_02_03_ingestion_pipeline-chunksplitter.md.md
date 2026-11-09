## Goal

- State in the ChunkSplitter documentation that the `-0000` sentinel is published last and therefore marks a complete chunk set (`REQ-006`: sentinel semantics documented).

## Scope
**Release unit**: N/A: not part of a release unit

- The idempotency sentence (L33) of `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`; sentinel semantics only.

## Assumptions

- Overlap check (Step 2 tool): no other Frozen Plan targets this docs file; the sentence update depends on the seq-1 document's behavior (sentinel published last), so this document lands after it in seq order (per `templates/plan.md` row order).
- L33 currently states "if a `{stem}-0000.json` sentinel exists, processing is skipped" without saying the sentinel implies completeness (verified in Step 3 of the plan cycle).

## Design decisions

- Extend the existing L33 sentence in place instead of adding a new section; keep the surrounding idempotency paragraph as the single description of rerun behavior.

## Alternatives considered
N/A: documentation-only row.

## Implementation
### Target file
- `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`

### Procedure
- Amend the idempotency sentence at L33 to state that chunks are published so the `-0000` sentinel appears last, so its presence marks a complete set and a skipped rerun is safe.

### Method
- Rewrite the sentence to: a rerun with `force=False` is skipped when a `{stem}-0000.json` sentinel exists; chunk files are published in descending index order so the sentinel is written last and only ever exists alongside a complete chunk set.

### Details
- Keep the sentence's existing position and the `force=False` wording; no other section changes.
- Do not describe the temporary-name mechanism beyond what the completeness claim needs (implementation detail stays in `scripts/rag/ingestion/chunk_splitter.py`).

## Compatibility considerations

- No other sentence in the file mentions the sentinel (verified in Step 3); no cross-file docs reference updates are required.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan

- Docs gates per `routing.md`: `uv run python tools/check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain rag`, `check_docs_japanese.py` — no findings.

## Completion criteria

- L33 states the sentinel is published last and marks a complete set (AC-6), and all docs checkers pass.

## Out of Scope

- Any `docs/` file other than the target; the write-protocol behavior itself (covered by the seq-1 document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the idempotency sentence per Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation checkers (Validation plan) | Pending | — | — | |

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
- **Requirement ID**: `REQ-006` (document sentinel-last publish marking a complete set)
- **Source issue**: issues/20261108-131236_ragrev017_partial-chunk-write-gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-170859_ragrev017_partial-chunk-write-gap.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-234702
- **Related target files**: `docs/21_rag/rag_02_03_ingestion_pipeline-chunksplitter.md`
