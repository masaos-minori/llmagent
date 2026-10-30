## Goal
Create `scripts/db/recovery_drill.py` (new): a drill harness for all four domains that rotates a recovery point, restores it into an isolated copy, measures restore time and data-loss window, and writes audit artifacts (REQ-007 drill tooling).

## Scope
- In scope: the drill harness module and its CLI entry for `rag`, `session`, `workflow`, `eventbus`.
- Out of scope: recovery helpers (row 10 exposes them), rotation verification (row 12), migration registry (rows 02/06), runbook documentation (row 23).

## Current shape (facts)
- No drill tooling exists: absence verified across `scripts/`, `tools/`, `docs/`, `deploy/` for "recovery drill" / "restore drill" / RPO / RTO (Plan absence search). Recovery building blocks exist in `scripts/db/recovery.py` (`_run_integrity_check:90`, `_verify_domain_identity:142`, `_backup_is_usable:165`) and `scripts/db/rotation.py` (`_archive_db_file:24-48`, WAL-consistent SQLite backup API copy).

## Assumptions
- Recovery points are production-shaped: the drill takes the archive through `rotation._archive_db_file` (same code path as `rotate_*_db`), so the drill exercises the real archive mechanism, not a bespoke copy (issue instruction: reuse existing mechanisms).
- The live databases are never mutated; the live file is only read through the SQLite backup API. The restore always targets an isolated copy under a drill directory.
- Measurement definitions (fixed here, documented in row 23): `rto_seconds` = wall-clock seconds from copy-out to the isolated path until all post-restore checks pass; `rpo_window_seconds` = seconds between recovery-point creation (archive timestamp) and drill start — the upper bound of writable data lost if the live DB had been lost at drill start.
- Domain verification: `rag`/`session` run integrity + domain identity (`recovery.py:136-139` required tables `documents`/`sessions`); `workflow` adds the `tasks`-table check and ledger state read (row 01 primitives); `eventbus` adds `shared.eventbus_schema_fingerprint.assert_matches` and ledger state read. `rag`/`session` artifacts record the recreate-only policy (no ledger fields).

## Design decisions
- Artifact contract: one JSON per domain at `{archive_dir}/drills/{domain}_{timestamp}.json` with fields `domain`, `archive_path`, `archive_ts`, `drill_ts`, `rto_seconds`, `rpo_window_seconds`, `integrity`, `verification` (per-domain checks and pass/fail), `policy` (`migrate` for workflow/eventbus, `recreate` for rag/session), and ledger fields (`current_version`, `baseline_row`) when policy is `migrate`. Retention location documented in row 23.
- Any failed check fails the drill for that domain (nonzero exit) but the harness still writes the artifact describing the failure before exiting — a drill that hides failures is worthless.
- CLI: `--domain {rag|session|workflow|eventbus|all}`, optional `--archive-dir` (default via `rotation._resolve_archive_dir`) and `--drill-dir` override.

## Alternatives considered
- Reusing `recovery._restore_from_backup` against the live path behind a `--dry-run` flag — rejected: its semantics restore the real database; the drill's requirement is an isolated copy, so the harness composes checks directly from row 10's exposed helpers instead.

## Implementation
### Target file
- `scripts/db/recovery_drill.py` (new)

### Procedure
1. Resolve live paths via `db.config.build_db_config()`; per domain: create recovery point via `rotation._archive_db_file`.
2. Copy the archive into the drill directory (isolated copy), start the timer, run row-10 public helpers (`run_integrity_check`, `verify_domain_identity`) plus the per-domain verifications from Assumptions.
3. Compute measurements, write the JSON artifact, report per-domain pass/fail to stdout and the process exit code.
4. `if __name__ == "__main__"` CLI per Design.

### Method
New module; imports stay inside the `db` layer plus `shared` (fingerprint, ledger primitives from rows 01/10). Land after rows 01/10 in `seq` order; row 12's verified archives strengthen later drills but are not a hard dependency.

### Details
- The workflow/eventbus ledger read uses row 01's ledger primitives (`current_version`-equivalent); a missing ledger table in a migrated-policy database is itself a drill finding recorded in the artifact.

## Compatibility considerations
- New module; no existing importers. `deploy/init_db.sh` gains a documented drill invocation hook via row 13.

## Security considerations
- Reads only; artifact JSON contains paths and measurements, no secrets. Drill directory lives under the configured archive dir, not ad-hoc temp locations in production.

## Rollback considerations
- Revert the commit; drill artifacts already written are inert files.

## Validation plan
- `uv run pytest tests/db/test_recovery_drill.py` (row 19 writes these tests first: four domains, artifact fields, failure artifact, measurement fields present and positive).
- `uv run mypy --no-namespace-packages scripts/`; `lint-imports`.

## Completion criteria
- A drill run against four tmp fixtures writes four artifacts with all Design fields; an injected corrupt archive produces a failed artifact plus nonzero exit; live database files are byte-identical before/after (mtime + hash assertions in row 19).

## Out of Scope
- Scheduling/cron of drills (Plan leaves frequency as placeholder in row 23), staging dry-run procedure (Plan Phase 4 execution is an operational task, not code in this row).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261030-110000 | 20261030-110000 | New module scripts/db/recovery_drill.py. Drills all four domains via rotation._archive_db_file (read-only backup-API copy), restores into an isolated copy, measures rto/rpo, verifies per domain through db.recovery helpers + eventbus assert_matches, writes one JSON artifact per domain. CLI main() exits 0 on all-pass, 1 on any fail. Read-only: live DBs never mutated. |
| 2 | Add or update tests per Validation plan | Pending | — | — | Formal coverage is row 19 (tests/db/test_recovery_drill.py), not yet generated. Hand smoke test validated: rag/session (recreate) PASS, workflow (migrate, ledger present) PASS with baseline captured, eventbus fingerprint-mismatch FAIL with artifact still written, missing-source FAIL with error field. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-110000 | 20261030-110000 | ruff format+check clean; mypy clean; lint-imports 6/6 KEPT; check_db_separation no violations; check_docstrings OK (268 grandfathered). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261030-110000 | 20261030-110000 | N/A: runbook text is row 23's scope, outside this row. Module implementation and validation are complete here. |

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
- **Requirement ID**: `REQ-007` (drill harness)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/db/recovery_drill.py`
