# Implementation Procedure: Add the DB-error row to the RagIngester error table

## Goal
Record the new explicit catch in the subsystem's error contract: add one row to the RagIngester error table documenting the `sqlite3.Error` batch behavior (REQ-004, AC-4).

## Scope
- One added table row in the `## RagIngester` section. No other table, section, or page change.

## Assumptions
- The Issue's "Documentation Impact: None" is incomplete: the RagIngester table (verified rows: embedding retry, retry-limit, invalid `lang`, invalid `fetched_at`; section heading at L82, table rows through the `fetched_at` row around L88) has no database-error row, and the reference is the contract record reviewers consult (Plan Problem).
- Overlap: `docs/21_rag/rag_05_04-error-handling-reference.md` is also targeted by the rag003 Plan procedures (implementations/20261027-154425_26_*), which rename the `rag_service_url` occurrence in the RagPipeline table; this procedure adds a row to the RagIngester table. Disjoint tables; whichever implements second rebases (Plan Dependencies).

## Design decisions
- Docs as contract: the row prevents a future "fix" from re-narrowing the catch (Plan Design). Row wording mirrors the implemented behavior exactly, in the table's existing `Error | Action` two-column style.

## Alternatives considered
- Leave the table unchanged since the docstring already promises no-stop — rejected: the per-component table is the machine-checkable contract record; docstrings alone proved insufficient (the bug existed despite the docstring).

## Implementation
### Target file
`docs/21_rag/rag_05_04-error-handling-reference.md`
### Procedure
1. In the `## RagIngester` table, append one row (new):
   `| sqlite3.Error during URL group processing (caught by `_process_url_groups()`) | Skip URL group; `ERROR` (with traceback); continue with remaining groups; `check_consistency` still runs after the batch |`
2. Keep the existing four rows byte-identical.
3. Do not touch the `## RagPipeline` table (that is the rag003 Plan's edit region on this page).
### Method
Single Markdown table row in the existing style; no reflow of neighboring rows.
### Details
- The row must match implemented behavior after procedure _01 lands; sequence the doc edit with the code change in the same implementation pass (Plan Phase 4).

## Compatibility considerations
- Page is high-churn (30d churn 8 per Plan Affected areas): rebase immediately before editing and re-verify the table region line numbers.

## Security considerations
- Documentation-only change.

## Rollback considerations
- Single commit adding the import, the widened tuple, tests, and the doc row; rollback is `git revert`. No config, schema, or deployed-state change.

## Validation plan
- `rules/toolchain.md` documentation consistency check for the 21_rag domain passes; the row is present and matches the implemented catch (AC-4).
- If the rag003 procedure (implementations/20261027-154425_26_*) has already renamed the RagPipeline row on this page, rebase before editing (overlap note).

## Completion criteria
- RagIngester table contains exactly one sqlite3.Error row with the wording above; RagPipeline table untouched by this procedure.

## Out of Scope
- Broadening the catch to bare `Exception`/`BaseException` (Issue Constraint).
- Changing transaction boundaries or rollback behavior (`SQLiteHelper.begin_immediate` stays as-is).
- Changing `ingest_url_group`'s own exception semantics for direct callers.
- The `int(cfg[...])` coercion style in `crawler.py`, `chunk_splitter.py`, `db/config.py`, `db/maintenance.py`.
- httpx/transport error handling — verified contained inside `ChunkFactory.prepare` and converted to `failed_paths` (Issue Unresolved Question, answered: no change).
- Rewording the existing RagIngester rows or the RagPipeline table.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261027-074526_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261027-111107_rag004_ingester-sqlite3-error-aborts-batch.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-165951
- **Related target files**: docs/21_rag/rag_05_04-error-handling-reference.md
