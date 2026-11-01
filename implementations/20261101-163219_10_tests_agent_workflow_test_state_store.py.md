## Goal

## Goal

Replace the mocked detection/recovery tests in `tests/agent/workflow/test_state_store.py` with real-database report and race tests (REQ-003, REQ-009 / AC-2, AC-3).

## Scope

- Replace the mock-based tests (`find_stale_running_attempts` lambdas at `:26-167`) with real-`StateStore` tests against the fixture DB: single stale recovery, non-stale untouched, mixed stale/live, multiple stale, no-running-attempts.
- Replace the `"not-a-date"` test (`:217`): an unparseable `started_at` (and a new unparseable `lease_expires_at` case) yields a warning log (captured with `caplog`), an `unparseable` count in `last_recovery_report`, and a row still `running` (REQ-003 / AC-3).
- Keep the concurrency-flavored test (`test_recover_concurrent_calls_only_one_succeeds`, `:74`) but re-express it against the conditional update: two sequential recover calls produce one takeover (`rowcount` path), deep two-connection racing belongs to procedure 12.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- This file imports the same fixture helpers as procedure 09's file so seeds stay in one style.

## Design decisions

- Mock removal is deliberate (REQ-009: the mock-only seeds are replaced): mocking `find_stale_running_attempts` hid the production parse defect (Plan Background).

## Alternatives considered

- Keeping the mocks for speed — rejected: the fixture DB is an in-memory/temp SQLite and already used by sibling files.

## Implementation
### Target file
`tests/agent/workflow/test_state_store.py`

### Procedure
1. Delete the lambda-mock blocks and rebuild each scenario with seeded rows (production-format timestamps, explicit lease values).
2. Add the `caplog` warning assertion (`unparseable workflow attempt timestamp`).
3. Assert the four-count report after each scenario.

### Method
Test rewrite in place; same test-class skeleton names.

### Details
- Report assertions also lock `recover_stale_attempts()`'s int return (compatibility with the 18 existing references).

## Compatibility considerations

- Any remaining test in this file that mocks `_db` internals is left alone unless it touches detection.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- File-level revert.

## Validation plan

- `uv run pytest tests/agent/workflow/test_state_store.py -v`

## Completion criteria

- AC-3 fully covered in this file; AC-2 partially with procedure 09.

## Out of Scope

- Multi-connection race coverage (procedure 12).

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
- **Workflow phase**: Phase 1 (Timezone-safe parsing and conservative detection)
- **Requirement ID**: `REQ-003`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/agent/workflow/test_state_store.py`, `scripts/agent/workflow/state_store.py`, `tests/agent/workflow/test_workflow_state_store.py`
