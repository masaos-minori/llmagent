## Goal

Extend the minimal workflow-table fixtures in `tests/agent/test_repl_health.py` so the startup health check exercises the new required columns (REQ-004 / AC-8).

## Scope

- Add `owner_id TEXT` and `lease_expires_at TEXT` to the hand-written `CREATE TABLE attempts` fixture (`:538`, fixture helper `:519-561`) so `check_workflow_schema` passes on the fixture once procedure 07 makes the columns required.
- Add one negative case: dropping `owner_id` from the fixture makes the startup check report the missing column (AC-8).

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- These fixtures intentionally build minimal (un-migrated-shaped) tables; the new columns join the existing minimal vocabulary, not the full canonical DDL.

## Design decisions

- The negative case locks the actionable error path the operational runbook (procedure 15) promises.

## Alternatives considered

- Reuse `create_workflow_tables` in the fixture — rejected: the point of this file is minimal hand-built tables to prove the check catches drift.

## Implementation
### Target file
`tests/agent/test_repl_health.py`

### Procedure
1. Edit the fixture DDL at `:538`.
2. Add the missing-column negative case using the fixture's existing `missing_column` mechanism (`:546-549`; example test `:598-602`) in the health-check class (`:567-640` region).

### Method
Fixture string edit plus one test case.

### Details
- Fixture edits must land with procedure 07 in the same commit chain or these tests fail at startup-check time.

## Compatibility considerations

- Other fixtures in the block (`tasks`, `processed_events`) are untouched.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Revert with procedure 07.

## Validation plan

- `uv run pytest tests/agent/test_repl_health.py -v`

## Completion criteria

- AC-8 covered for the startup path.

## Out of Scope

- Health checks outside the workflow-table section.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | fixture attempts DDL += owner_id/lease_expires_at |
| 2 | Add or update tests per Validation plan | Completed | — | — | test_missing_attempt_lease_column_fails added via missing_column mechanism |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | 43 passed; full suite 10890; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: docs covered by procedures 15/16 |

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
- **Requirement ID**: `REQ-004`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/agent/test_repl_health.py`, `scripts/agent/services/workflow_schema.py`, `scripts/db/schema_sql.py`