## Goal

Correct the "other sources" freshness bullet of the DocumentManager document so it states the absence rule: a skip needs at least one validator present and the stored and new values equal, and validator-less pages are re-ingested on every run (`REQ-005`: document the absence rule).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `For other sources` bullet under `Existing-document handling` in `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`.
- Out of scope: the `file://` bullet (already states that a missing hash counts as changed), the crawler and local-file re-ingestion documents, and any code.
- Plan: `plans/20261108-165741_ragrev010_pages-without-validators-skipped.md` (Plan step 3); apply after document `01`.

## Assumptions

- Re-verified at generation time: the bullet currently says a skip happens only when both the stored ETag and Last-Modified equal the new values, and is silent on absence; `rg "both the stored ETag"` finds no other document with the same claim.
- The rule documented is the one implemented by document `01`: skip only when a validator is present on both sides and the values are equal; absence of both validators on either side means unknown and re-ingests.
- Docs are English (`skills/DESIGN.md` Output language); the Docs content policy applies, so the text states intent and failure behavior and does not name the helper or line numbers.

## Design decisions

- Edit only the one bullet: add the absence sentence and keep the existing freshness-write and `ETagManager` guard clauses as written.
- State the cost consequence in one clause (validator-less pages are re-ingested each run) so a reader does not mistake it for a defect.

## Alternatives considered

N/A: one-bullet documentation edit.

## Implementation
### Target file
`docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`

### Procedure
1. Re-read the `For other sources` bullet (the file may have changed).
2. Rewrite its first clause to: a skip happens only when the stored and new validators are both present in at least one of ETag and Last-Modified and equal; a page whose stored or new validators are both absent has no change signal, so it is re-ingested on every run.
3. Keep the rest of the bullet (freshness fields written inside the re-insert transaction, `ETagManager` guard, failed re-ingestion leaves chunks and freshness unchanged) unchanged.

### Method
- Single Edit of the bullet; do not touch front matter, headings, or the Keywords section.

### Details
- Run the checkers named in the Validation plan; no Needs-Confirmation marker is added or removed.

## Compatibility considerations

N/A: documentation only; no links, headings, or file names change.

## Security considerations

N/A: documentation only.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_docs_quality.py`
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- The bullet states the absence rule and that validator-less pages are re-ingested each run, and the remainder of the bullet is unchanged.
- The five documentation checkers report no findings.

## Out of Scope

- Code and test changes (documents `01` and `04`), other documents, and any content-hash fallback.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the `For other sources` bullet to state the absence rule | Completed | 20261109-180917 | 20261109-180917 |  |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261109-180917 | 20261109-180917 |  |

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
- **Requirement ID**: `REQ-005` (document the absence rule)
- **Source issue**: issues/20261108-131124_ragrev010_pages-without-validators-skipped.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165741_ragrev010_pages-without-validators-skipped.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-142759
- **Related target files**: `docs/21_rag/rag_02_05_ingestion_pipeline-document-manager.md`