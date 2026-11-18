## Goal
Make `rebuild_vec` and `reconcile_url` run on the canonical schema and commit, and set `integrity_ok` from the integrity outcome (REQ-001 to REQ-004).

## Scope
**Release unit**: rag-repair-persistence
- `rebuild_vec`, `reconcile_url`, and `recover` of `RagMaintenanceService`; `rebuild_fts` is unchanged.
- Release unit: the failing-first tests stay red until the fix of procedure 05 lands, so the full suite and diff-cover run once at the end of the unit.

## Assumptions
- Gate: the owner confirms UNK-01 (orphan removal), UNK-02 (rows left as the return value), and UNK-05 (insert-if-absent FTS repair) of the Source plan before the first edit; stop and ask when they are not confirmed.
- Procedures 02 to 04 are done, so the new tests are red for the reasons recorded in procedure 02.
- The presence test for an FTS entry is the shadow table `chunks_fts_docsize`, the pattern `scripts/db/rag_consistency_queries.py` uses; vector rows are deleted by `chunk_id`, as `DocumentManager` and the vector store do.

## Design decisions
- One commit as the last write of a successful repair, like `rebuild_fts`; a failure raises and the context closes the connection, which discards the transaction.
- No FTS5 delete for an entry that is not indexed: on an external-content table it corrupts the index.

## Alternatives considered
`begin_immediate()` with an explicit rollback was rejected: the Issue and `rebuild_fts` use `commit()`. Re-embedding chunks in `rebuild_vec` was rejected: the service has no embedder (UNK-01).

## Implementation
### Target file
`scripts/agent/services/rag_maintenance_service.py`
### Procedure
1. Confirm the gate in Assumptions.
2. `rebuild_vec`: select the `chunk_id` of every `chunks_vec` row that is not in `chunks`, delete those rows with one `executemany` of `DELETE FROM chunks_vec WHERE chunk_id = ?`, count the rows left with `SELECT COUNT(*) FROM chunks_vec`, call `db.commit()`, and return the count; rewrite its docstring to "Remove chunks_vec rows that have no chunks row; return the number of rows left."
3. `reconcile_url`: open with `write_mode=True, row_factory=True`; keep the document lookup and the `{"found": False}` return (no commit, nothing written); insert the FTS entries that are missing with one `INSERT INTO chunks_fts(rowid, content) SELECT chunk_id, COALESCE(normalized_content, content) FROM chunks WHERE doc_id = ? AND chunk_id NOT IN (SELECT id FROM chunks_fts_docsize)`; count the URL's chunks; call `db.commit()`; return `{"found": True, "chunks": n}`; delete the vector statements and the FTS delete; rewrite its docstring to say it inserts the missing FTS entries of one URL.
4. `recover`: set `integrity_ok` to `result.success or result.action == "vacuum_failed"` with a one-line comment that the VACUUM runs only after a passing integrity check; leave `recovered` and `logical_ok` as they are.
5. Run the new tests and fix only what they show.
### Method
Keep the module imports; the code that reads rows by column name is removed from `rebuild_vec`, and `reconcile_url` reads only `doc["doc_id"]` through the Row factory. Follow the repository conventions of `rebuild_fts` (`db.execute`, `db.commit()`). Do not add a rollback call, a shim, or a history comment.
### Details
- `/session rag-rebuild-vec` (`cmd_session.py`) prints the return value as a row count, so the rows-left return keeps its message true; its docstring is stale and out of this plan's scope.
- `reconcile_url` and `recover` have no production caller (UNK-04); fix them as planned.
- `radon cc` of `reconcile_url` should fall below the current grade C.

## Compatibility considerations
The public method names and return shapes are unchanged; `rebuild_vec` now returns the rows left and no longer raises on the canonical schema; `reconcile_url` no longer touches vector rows.

## Security considerations
N/A: fixed SQL strings with bound parameters; no interpolation, no new input path.

## Rollback considerations
Revert only this procedure's own changes with `git checkout -- <path>` on each changed path (single-path revert; no bulk form). Apply the procedure's Rollback considerations after a failed full-suite run.

## Validation plan
- `uv run pytest tests/agent/services/test_rag_maintenance_persistence.py tests/agent/services/test_rag_index_integrity.py tests/agent/commands/test_agent_cmd_session.py`
- `uv run ruff format <changed files>`, `uv run ruff check <changed files>`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus tools`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `PYTHONPATH=scripts uv run lint-imports`
- `uv run radon cc scripts/agent/services/rag_maintenance_service.py -s`
- End of the release unit: `uv run pytest tests/ -n logical --cov=scripts --cov-report= -m "not integration and not production_paths_allowed and not repo_scan"`, `uv run coverage xml`, `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90`

## Completion criteria
- After `rebuild_vec()` a new connection sees no orphan vector row and every valid row; a failing commit leaves the database unchanged (AC-1).
- After `reconcile_url(url)` the missing FTS entry is visible to a new connection, nothing is raised, and vector rows are unchanged (AC-2).
- A VACUUM failure on a healthy database gives `integrity_ok=True` (AC-3).
- The persistence tests pass and diff-cover is at least 90% on the changed lines.

## Out of Scope
- Changing `rebuild_fts`, the consistency check messages, or repair action names.
- Editing `cmd_session.py`, `DbMaintenanceService`, or any ADR or docs file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm the owner decisions UNK-01, UNK-02, and UNK-05 | Completed | 20261118-123153 | 20261118-123153 | Owner decisions UNK-01 (orphan removal), UNK-02 (rows left), UNK-05 (insert the missing FTS entries) confirmed in session 2026-11-18 via AskUserQuestion |
| 2 | Implement the changes in Implementation > Procedure | Completed | 20261118-123153 | 20261118-123617 | rebuild_vec removes the orphan chunks_vec rows and commits (returns the rows left); reconcile_url opens with row_factory, inserts only the chunks absent from chunks_fts_docsize, and commits; recover maps integrity_ok = success or action vacuum_failed; changed: scripts/agent/services/rag_maintenance_service.py |
| 3 | Run the new persistence tests and the related tests | Completed | 20261118-123617 | 20261118-123617 | Targeted: persistence tests, test_rag_index_integrity, test_agent_cmd_session: 90 passed (the fake gained executemany, recorded in procedure 03) |
| 4 | Run the validation sequence (`rules/toolchain.md`) and the end-of-unit full suite | Completed | 20261118-123617 | 20261118-123617 | End-of-unit run passed: full suite 12734 passed, 7 skipped; diff-cover 100%; radon cc: reconcile_url C(12) to A(2); project mypy, bandit -ll, lint-imports, validation gates: pass. Docs: N/A, no docs/00_index.md statement conflicts and the Plan scopes docs out |

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
- **Requirement ID**: `REQ-001`, `REQ-002`, `REQ-003`, `REQ-004`: persistence, repair contracts, `integrity_ok`
- **Source issue**: issues/20261117-123007_adrchk007_rag-repair-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-112342_adrchk007_rag-repair-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-121341
- **Related target files**: `scripts/agent/services/rag_maintenance_service.py`
