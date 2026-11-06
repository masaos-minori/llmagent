## Goal

Update the `max_pages` key description in `docs/21_rag/rag_05_01-configuration-reference.md`
(`REQ-001`, `REQ-002`; AC-4) to reflect the two-counter semantics: `max_pages` counts
pages actually persisted, and scheduling is capped at `2 * max_pages`.

## Scope
**Release unit**: crawl-persisted-budget (Plan Phase 4)

## Assumptions
- The behavior change is implemented by the companion `orchestrator.py` procedure
  document before this doc is updated.
- No other doc references the old single-counter wording in a way that needs a
  parallel update (Plan Step 3 scan found only this line and `rag_02_02` §2.1.1).

## Design decisions
- Edit only the `max_pages` bullet (line 34). Leave surrounding bullets and the rest
  of the reference untouched to avoid an unrelated rewrite.

## Alternatives considered
- Rewriting the whole `config/crawler.toml` section: rejected — out of scope for
  `REQ-001`; only the `max_pages` bullet changes.

## Implementation
### Target file
- `docs/21_rag/rag_05_01-configuration-reference.md`

### Procedure
1. Rewrite the `max_pages` bullet so it states that `max_pages` bounds the number of
   pages **persisted** by the crawl, and that the BFS schedules up to `2 * max_pages`
   URLs per `crawl_site` call (the extra headroom covers 304 / empty-content /
   language-rejected / failed fetches that do not persist).

### Method
- Replace the clause "`max_pages`: reaching it stops BFS for the site" with prose such
  as: "`max_pages`: maximum number of pages **persisted** by the crawl for the site.
  The BFS persists until `max_pages` pages are written and schedules up to
  `2 * max_pages` URLs per call (a fixed internal scheduling headroom) so that
  non-persisted fetches (304, empty content, unsupported language, task failures)
  cannot consume the operator's page budget or make the loop unbounded. A
  `BFS stop: scheduled=%d persisted=%d max_pages=%d` summary line is logged when the
  crawl stops."
- Keep the trailing "`skip_nofollow` / `skip_external` exclude ..." clause intact.

### Details
- Verify the updated wording against the implemented behavior in the companion
  `orchestrator.py` procedure before updating — do not describe behavior not yet
  implemented.
- Do not alter other key descriptions or the `config/crawler.toml` header.

## Compatibility considerations
N/A: documentation-only change describing already-implemented behavior.

## Security considerations
N/A: documentation-only.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- Review of the updated bullet confirms it matches the implemented two-counter
  behavior (AC-4); the old "reaching it stops BFS" wording is gone.

## Completion criteria
- The `max_pages` bullet describes persisted-page semantics with the 2x scheduling
  headroom and the stop-summary log.

## Out of Scope
- Any other section of this doc; any other documentation file.

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
|---------|--------------|------|-------|----------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-001`, `REQ-002`
- **Source issue**: `issues/20261106-073538_raging009_crawl-max-pages-pending-tasks.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261106-104423_raging009_crawl-max-pages-pending-tasks.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261106-154603
- **Related target files**: `docs/21_rag/rag_05_01-configuration-reference.md`
