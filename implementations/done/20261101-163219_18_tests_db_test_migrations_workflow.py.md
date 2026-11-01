## Goal

Cover the lease migration step in `tests/db/test_migrations_workflow.py`: registration, row-preserving migration over `running` rows, resume/idempotence, and version codes (REQ-004, REQ-009 / AC-8).

## Scope

- Extend `TestWorkflowRegistry` (`:109-133`) with `test_registry_holds_the_attempt_lease_step` (spec id, from/to codes, pre/post conditions present).
- Extend the migration-execution pattern (`TestWorkflowTaskNonceStep`, `:361-438`; closest landed template): seed an old-shape attempts table with `running` rows, apply the registry path, assert both columns exist and existing rows keep all values with the new ones null; re-applying is empty (resume); a forged stamp without the ledger row is refused (pattern at `:276`).
- Assert `WORKFLOW_VERSION_CODES`/`WORKFLOW_TARGET_VERSION` include the landing-order code together with procedure 17's edit.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Expected version codes in assertions are written at implementation time from the landing-order decision (procedure 17).

## Design decisions

- Reuse the file's existing tmp_path DB fixture helpers so the new step's tests mirror the landed step-by-step structure.

## Alternatives considered

- Parameterizing a step-matrix test — rejected: the file's per-step explicit style is the convention.

## Implementation
### Target file
`tests/db/test_migrations_workflow.py`

### Procedure
1. Add the registry case.
2. Add a `TestWorkflowAttemptLeaseStep` class following the `:361-438` template.
3. Extend version-code assertions.

### Method
Test-only additions in the existing module.

### Details
- `running`-row preservation is the AC-8 anchor: seed with the exact production `Z` `started_at` format so the migrated rows also feed procedure 02's legacy branch.

## Compatibility considerations

- Land with procedure 17 in the same commit chain.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Revert with procedure 17.

## Validation plan

- `uv run pytest tests/db/test_migrations_workflow.py -v`

## Completion criteria

- AC-8 migration half covered.

## Out of Scope

- Production `/opt/llm/db/workflow.sqlite` execution (deploy skill gate).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | lease migration test class + registry/version-code tests added |
| 2 | Add or update tests per Validation plan | Completed | — | — | validated via tests/db suite (392 passed) incl. procedures 13/18 tests |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | full suite 10889 passed; diff-cover 100%; ruff/lint-imports/bandit/db-separation/module-size OK; mypy clean on changed files |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: docs/41_db schema reference lists table names only |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 2 (Schema)
- **Requirement ID**: `REQ-004`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/db/test_migrations_workflow.py`, `scripts/db/migrations_workflow.py`, `scripts/db/schema_sql.py`, `tests/db/test_create_schema.py`