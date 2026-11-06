## Goal

Update the `max_pages` description in `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`
(`REQ-001`, `REQ-002`; AC-4) so the §2.1.1 Configuration Parameters paragraph reflects
the two-counter semantics introduced by the companion `orchestrator.py` procedure:
`max_pages` bounds pages actually **persisted**, and the BFS schedules up to
`2 * max_pages` URLs per `crawl_site` call.

## Scope
**Release unit**: crawl-persisted-budget (Plan Phase 4)

## Assumptions
- The behavior change is implemented by the companion `orchestrator.py` procedure
  document before this doc is updated.
- This paragraph and the `config/crawler.toml` bullet in `rag_05_01` are the only two
  places describing `max_pages` semantics (Plan Step 3 scan).

## Design decisions
- Edit only the `max_depth`/`max_pages` paragraph (lines 39-44). Leave the surrounding
  prose (historical-rationale sentence, `skip_nofollow` sentence) intact to avoid an
  unrelated rewrite.

## Alternatives considered
- Rewriting the whole §2.1.1 heading block: rejected — out of scope for `REQ-001`;
  only the `max_pages` semantics change.

## Implementation
### Target file
- `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`

### Procedure
1. Rewrite the `max_depth`/`max_pages` paragraph so it states that `max_pages` bounds
   the number of pages **persisted** by the crawl, and that the BFS schedules up to
   `2 * max_pages` URLs per `crawl_site` call (fixed internal scheduling headroom for
   non-persisted fetches), plus the `BFS stop:` summary log.

### Method
- Replace lines 39-44 with prose such as:
  "`max_depth` bounds the crawl's BFS traversal depth to prevent unbounded growth in
  processing time, storage, and external-site load. `max_pages` bounds the number of
  pages **persisted** by the crawl for the site: the BFS persists until `max_pages`
  pages are written to `rag-src/` and then stops. Because 304 / empty-content /
  language-rejected / failed fetches do not persist, the BFS schedules up to
  `2 * max_pages` URLs per `crawl_site` call (a fixed internal scheduling headroom) so
  those non-persisted fetches cannot consume the operator's page budget or make the
  loop unbounded. A `BFS stop: scheduled=%d persisted=%d max_pages=%d` summary line is
  logged when the crawl stops — see [Configuration Reference, `config/crawler.toml`]
  (rag_05_01-configuration-reference.md) for the current operational values."
- Keep the trailing `skip_nofollow` sentence (line 45-46) intact.

### Details
- Verify the updated wording against the implemented behavior in the companion
  `orchestrator.py` procedure before updating — do not describe behavior not yet
  implemented.
- Do not alter the historical-rationale sentence or any other section.

## Compatibility considerations
N/A: documentation-only change describing already-implemented behavior.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Review of the updated paragraph confirms it matches the implemented two-counter
  behavior (AC-4); the old single-counter "reaching it stops BFS" wording is gone.

## Completion criteria
- The `max_pages` description in §2.1.1 describes persisted-page semantics with the
  2x scheduling headroom and the stop-summary log.

## Out of Scope
- Any other section of this doc; any other documentation file (the `rag_05_01`
  `max_pages` bullet is the companion document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Run the documentation checkers in `routing.md` Tools "When to run which tool" | Pending | — | — | REQ-001 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | N/A at plan creation | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-154603
- **Related target files**: `docs/21_rag/rag_02_02_ingestion_pipeline-crawler.md`
