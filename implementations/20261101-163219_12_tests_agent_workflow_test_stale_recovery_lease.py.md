## Goal

## Goal

Create the multi-connection lease-recovery test module `tests/agent/workflow/test_stale_recovery_lease.py` covering live-lease protection, owner death, takeover races, fencing, and legacy rows (REQ-007, REQ-008, REQ-009 / AC-4..AC-7).

## Scope

- New file with two independent SQLite connections on one temp `workflow.sqlite` (two `SQLiteHelper` instances standing in for two agent processes — no process lock exists, Plan Background).
- Cases: live attempt with unexpired lease is not recovered by the second process (AC-4); owner death with expired lease is recovered exactly once (AC-6); two concurrent recoverers produce exactly one takeover (AC-6, one `rowcount==1`, one `rowcount==0`); repeated recovery changes nothing (AC-6); legacy lease-less row older than 3600 s recovered once, younger or unparseable not recovered (AC-7); late `finish_attempt` by the fenced owner raises the typed error (AC-7 — gated on the wfrecovery001 conditional-finish procedure, see blockers).
- Timestamp literals in production `Z` format; the race case uses `lease_expires_at` values computed via `parse_iso_utc` so wall-clock arithmetic is explicit.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Two connections use the same `begin_immediate()` path as production so SQLite busy handling is exercised the same way (`scripts/db/helper.py`, Plan Reference Files).

## Design decisions

- Race ordering is deterministic: process B calls `recover_stale_attempts` while process A's row is still mid-stage (lease unexpired) for AC-4, and after lease expiry for AC-6; no sleeps on timing thresholds, only on lease-boundary literals.

## Alternatives considered

- True multiprocessing via `subprocess` — rejected: the fencing semantics are all in SQL compare-and-swap; two connections on one process reproduce the interleaving deterministically.

## Implementation
### Target file
`tests/agent/workflow/test_stale_recovery_lease.py` (new)

### Procedure
1. Create the module with a fixture that opens the temp DB and two helpers.
2. Implement the six cases above; mark the AC-7 fencing case with `pytest.mark.xfail(strict=True)` referencing wfrecovery001 procedure 04 until its typed error exists, and remove the mark in the same PR chain once it lands (Plan UNK-06).

### Method
New pytest module, class-per-scenario layout like sibling files.

### Details
- File name is frozen in the Plan table (`test_stale_recovery_lease.py`); directory `tests/agent/workflow/` exists.
- AC-4 note: the execute stage runs 120 s in production; the test uses short synthetic timeouts (1-2 s) with the same margin constant.

## Compatibility considerations

- Pure addition; no existing test depends on it.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Delete the file.

## Validation plan

- `uv run pytest tests/agent/workflow/test_stale_recovery_lease.py -v`; the new tests must fail against pre-change `master` (Plan Validation plan).

## Completion criteria

- AC-4..AC-7 demonstrated end-to-end.

## Out of Scope

- `wfretry001` retry semantics; task-level resume paths.

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
| 1 | The AC-7 fenced-late-finish case depends on the Pending wfrecovery001 conditional-finish procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Ownership and lease-based recovery)
- **Requirement ID**: `REQ-007`, `REQ-008`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/agent/workflow/test_stale_recovery_lease.py`, `scripts/agent/workflow/state_store.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/db/helper.py`
