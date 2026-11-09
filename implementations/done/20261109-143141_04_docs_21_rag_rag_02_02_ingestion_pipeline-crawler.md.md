## Goal

Correct the two places in the crawler document that describe a 304 response as "skipped" so they state that a not-modified page is re-fetched for link discovery only and is not persisted (`REQ-006`: document the not-modified behavior).

## Scope
**Release unit**: N/A: not part of a release unit

- In scope: the `Conditional GET` bullet under `2.2 Detailed Behavior` and the non-persisting-outcomes sentence in `2.1.1 Configuration Parameters` of `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`.
- Out of scope: the robots paragraphs and the trust-boundary text (other Plans edit those paragraphs), the `file://` sections, and any code.
- Plan: `plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md` (Plan step 4); apply after documents `01` to `03`.

## Assumptions

- Re-verified at generation time: `2.2` says "If a 304 response is received, saving the file is skipped", and `2.1.1` lists 304 among the outcomes that do not persist while scheduling up to `2 * max_pages` URLs; both stay true for persistence but omit the discovery fetch.
- The behavior documented is the one implemented by document `02`: for a not-modified page whose depth is below `max_depth`, the page is fetched again without validator headers, only its links are enqueued, and nothing is persisted or counted against `max_pages`; at the depth limit no second request is made; a failed fetch is logged distinctly and enqueues nothing.
- Overlap: `plans/20261108-170101_ragrev012_crawler-redirect-trust-boundary.md` and `plans/20261108-170335_ragrev014_robots-policy-gaps.md` edit other paragraphs of the same document (trust boundary, robots); compatible. Re-read the two paragraphs before editing, since the file may have changed.
- Docs are English (`skills/DESIGN.md` Output language); the Docs content policy applies, so state intent and failure behavior and name no helper, line, or log text.

## Design decisions

- Edit only the `Conditional GET` bullet and the one sentence in `2.1.1`; keep the header names and the `2 * max_pages` scheduling statement unchanged.
- Say that discovery costs one extra request per unchanged page below the depth limit, so a reader does not mistake it for a defect.

## Alternatives considered

N/A: two-place documentation edit.

## Implementation
### Target file
`docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Procedure
1. Re-read the `Conditional GET` bullet of `2.2` and the `Because 304 / empty-content / language-rejected / failed fetches do not persist` sentence of `2.1.1`.
2. Rewrite the last sentence of the `Conditional GET` bullet to: a 304 response is not extracted or persisted, but when the page is below `max_depth` it is fetched once more without validators so its links are still discovered; a failed fetch is logged separately and discovers nothing.
3. In `2.1.1`, keep the sentence's list of non-persisting outcomes and add that a not-modified page below `max_depth` still triggers one extra request for link discovery.

### Method
- Two Edit calls; do not touch front matter, headings, or the Keywords section.

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
- `uv run python tools/check_docs_structure.py docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`
- `uv run python tools/check_docs_content_policy.py`
- `uv run python tools/check_docs_consistency.py --domain rag`
- `uv run python tools/check_docs_japanese.py`

## Completion criteria

- Both places state that a not-modified page is re-fetched for link discovery only (below `max_depth`), is not persisted, and that a failed fetch discovers nothing.
- The five documentation checkers report no findings.

## Out of Scope

- Code and test changes (documents `01` to `03`), the robots and trust-boundary paragraphs, and any stored-link-list design.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit the `Conditional GET` bullet and the `2.1.1` sentence | Completed | 20261109-205309 | 20261109-205309 | Step 3a confirmed both cited places unchanged. Conditional GET bullet rewritten to the re-fetch-for-discovery behavior; 2.1.1 sentence extended with the extra discovery request consuming scheduling headroom only. Line 98's 'Skipping Mechanism | 304 Not Modified' table row left untouched (out of scope). |
| 2 | Run the documentation checkers named in the Validation plan | Completed | 20261109-205309 | 20261109-205309 | check_docs_quality, check_docs_structure (file-scoped), check_docs_content_policy, check_docs_consistency --domain rag, check_docs_japanese: all clean. No Needs-Confirmation marker added or removed. |

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
- **Requirement ID**: `REQ-006` (document the not-modified behavior)
- **Source issue**: issues/20261108-131125_ragrev011_recrawl-304-drops-subtree.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261108-165922_ragrev011_recrawl-304-drops-subtree.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261109-143141
- **Related target files**: `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`