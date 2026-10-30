# Implementation Procedure: `tests/db/test_recovery_drill.py` (drill harness tests)

## Goal
Create coverage for the recovery drill harness across all four domains: artifact emission, measurement fields, and live-database immutability (Plan row 19; REQ-007).

## Scope
- In scope: new pytest module exercising `scripts/db/recovery_drill.py` (row 11) against sandboxed archive fixtures.
- Out of scope: drill invocation wiring in `deploy/init_db.sh` (row 13), recovery behavior changes (row 10 is zero-behavior-change).

## Assumptions
- Fixtures are tmp_path copies of each domain's canonical shape (DDL from the row-matched schema sources: `schema_sql.py` DDL builders for rag/session/workflow, `scripts/eventbus/schema.sql` for eventbus) plus archive copies produced by the row-12 `_archive_db_file` path, so drills run against real file layouts without production paths.
- The drill writes `{archive_dir}/drills/{domain}_{timestamp}.json` (row 11 contract); tests assert the artifact, not just the return value.

## Design decisions
- Byte-identity assertions on every live fixture DB after a drill (the "never mutates live DBs" contract is a test, not a comment).
- One failing-domain test uses a corrupted archive (tampered copy) to prove the artifact is still written with a failed status and the harness exits nonzero — a failed drill must be auditable, matching the row-11 contract.

## Alternatives considered
- Unit-testing only the artifact writer — rejected: REQ-007/AC-6 requires the four-domain end-to-end path (rotate point, restore to isolated copy, measure, verify).

## Implementation
### Target file
- `tests/db/test_recovery_drill.py` (new)

### Procedure
1. Fixtures: per-domain sandbox DB + verified archive under tmp_path; drill output dir under tmp_path.
2. Tests per domain (rag, session, workflow, eventbus):
   - Drill completes; artifact JSON exists and contains `domain`, `archive_path`, `archive_ts`, `drill_ts`, `rto_seconds`, `rpo_window_seconds`, `integrity`, `verification`, `policy`, `current_version`, `baseline_row` (row 11 schema; workflow/eventbus carry ledger fields, rag/session carry null baseline fields per row 11's out-of-scope ledger note).
   - Live fixture DB hash identical before/after; restore target is an isolated copy, never the live path.
   - `--domain all` runs all four and emits four artifacts.
3. Failure path: corrupted archive → artifact written with failed integrity status, nonzero exit, live DB untouched.
4. `rto_seconds` measured (monotonic clock sanity: > 0, < timeout bound); `rpo_window_seconds` derived from archive age vs DB state (row 11 definition: age of last verified recovery point).

### Method
pytest + tmp_path; invoke harness functions in-process, and one subprocess argv test for the CLI contract (`uv run python scripts/db/recovery_drill.py --domain workflow` style per `rules/coding.md`).

## Compatibility considerations
- New file only; runs under `uv run pytest tests/db/test_recovery_drill.py` named in the Plan's test matrix row for `recovery_drill`/`rotation`/`recovery`.

## Security considerations
- No production DB or archive paths (the configured `sqlite_archive_dir` is never opened). Subprocess calls use argv lists.

## Rollback considerations
- Delete the file.

## Validation plan
- Automated: `uv run pytest tests/db/test_recovery_drill.py` (fails before row 11 lands, passes after); combined run with `tests/db/test_db_maintenance.py` and `tests/db/test_db_recovery.py` per the Plan matrix stays green.
- Manual: none.

## Completion criteria
- Four-domain artifacts emitted with all schema fields; live DBs byte-identical; failed drill auditable; nonzero exit on failure.

## Out of Scope
- RPO/RTO numeric targets (Plan UNK-01 open — tests assert field presence/measurement, not thresholds).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | Wrote tests/db/test_recovery_drill.py (6 tests): healthy all-four sweep, per-domain artifact schema fields + verdicts, live-DB byte-identity, and audited missing-ledger failure incl. 2 subprocess CLI exit-code cases. |
| 2 | Add or update tests per Validation plan | Completed | — | — | This row is itself a test module 6/6 pass; tests/db green. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | ruff format+check clean; lint-imports 6 KEPT; bandit 0 med/high; ast-grep bare-except clean; check_db_separation no violations; check_docstrings no new; mypy no new regressions (12 pre-existing in other files). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | Out of scope: new file only; deploy/init_db.sh drill wiring (row 13) left unchanged. |

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
- **Requirement ID**: `REQ-007`
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `tests/db/test_recovery_drill.py`