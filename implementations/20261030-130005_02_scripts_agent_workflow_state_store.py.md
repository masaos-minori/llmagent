## Goal

Make stale detection in `scripts/agent/workflow/state_store.py` timezone-safe, observable, and lease-aware (`REQ-002`, timezone-independent parsing; `REQ-003`, observable unparseable timestamps and a recovery report; `REQ-006`, lease-based staleness without the fixed 30-second rule; `REQ-007`, conditional takeover; `REQ-008`, conservative legacy rule).

## Scope

- Modify only `scripts/agent/workflow/state_store.py` (`find_stale_running_attempts`, `recover_stale_attempts`, and the module constants).
- Atomic attempt-plus-task recovery is the wfrecovery001 Plan's work in the same method; this document adds detection and takeover conditions on top.

## Assumptions

- Plan Dependencies (`plans/20261030-114516_wflease001_stale-attempt-lease.md` Scope): Phase 1 steps (parse, report, legacy rule) have no schema or wfrecovery001 dependency and run first, after row 01 (`parse_iso_utc`). Phase 3 steps (lease detection and conditional takeover) need the schema row (`Blocked` for this document set, Plan row 6, which needs `plans/20261029-214108_dbmig001_forward-only-db-migrations.md` Phase 3), `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` Phase 3 (atomic recovery in this method), and rows 03-05. Execution order follows the Plan's phases, not `seq`.
- Plan overlap judgments (Step 8b): `state_store.py` is also a target of the wfrecovery001 Plan (recovery rewrite), `plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md` (task delegation), and `plans/20261029-233524_toolexec001_idempotent-tool-call-snapshot.md` (tool-call helpers): sequencing; the later change rebases and reconciles `recover_stale_attempts`.
- `recover_stale_attempts` keeps returning the recovered count (18 test references in 2 files rely on it); the report is a separate method.
- Verified in Step 3 of the Plan: production `started_at` values end in `Z`, so the current `time.strptime("%Y-%m-%dT%H:%M:%S")` raises `ValueError` and every production row is skipped; tests seed values without `Z`.
- Names created by earlier rows of this Plan, flagged by `tools/stale_detector.py` and acceptable because they exist when `code-implementation` executes the rows in order: `parse_iso_utc` (row 01 document), `worker_id`-related and lease columns (rows 03-04 documents and the schema row).

## Design decisions

- Phase 1 detection: parse `started_at` with `parse_iso_utc`; an attempt without a lease is "legacy" and counted stale only when older than a named constant age of 3600 seconds (far above the 120 s execute timeout); the 30-second rule is removed in this step, so recovery starts working in production without ever stealing a live attempt.
- Phase 3 detection: when `lease_expires_at` is present and parses, staleness is `lease_expires_at <= now (UTC)`; an unexpired lease is never stale.
- A scan result separates `stale`, `live` (valid lease not expired), `unparseable`, and `legacy_recovered` (new); `find_stale_running_attempts` returns the stale list as before and a new method returns the full report.
- Takeover passes the observed `owner_id` and `lease_expires_at` as expected values to the conditional finish, so a racing recoverer or a late renewal loses.

## Alternatives considered

- Keep the elapsed-time rule with a larger grace: rejected, it still cannot tell a healthy long stage from a dead worker (Plan Design).
- Periodic heartbeat renewal: rejected by the owner (2026-10-30), the engine enforces `timeout_sec`.

## Implementation

### Target file

`scripts/agent/workflow/state_store.py`

### Procedure

1. Phase 1: replace the `time.strptime` and `time.mktime` parsing in `find_stale_running_attempts` (`:217`, parse at `:232`) with `parse_iso_utc`; remove `_STALE_GRACE_SEC` (`:22-23`) and add a named legacy-age constant (3600 s); remove the `time` import if nothing else uses it.
2. Phase 1: log each unparseable `started_at` at warning level with the attempt id and the value, keep it out of the stale list, and add a `scan_stale_attempts` (new) method that returns the stale, live, unparseable, and legacy lists; make `find_stale_running_attempts` return the stale list from it.
3. Phase 1: add `recover_stale_attempts_report` (new) returning a small immutable report (recovered, live, legacy_recovered, unparseable counts) and let `recover_stale_attempts` (`:246`) return its recovered count.
4. Phase 3: read `owner_id` and `lease_expires_at` in the scan and apply the lease rule; pass the observed values to the conditional takeover in `recover_stale_attempts` through the `attempt_ops` finish operation, treating a zero-row result as a lost race (skipped, not an error).

### Method

- The current-time source is `datetime.now(UTC)` through the shared helper style used elsewhere; do not use `time.time()` or local time.
- Report counts are plain integers in a frozen dataclass defined in this module (no new module).

### Details

- Line numbers are from the pre-change file; the wftaskapi001 and wfrecovery001 documents change this file earlier, so locate by symbol.
- The orchestrator call (`scripts/agent/orchestrator.py:92`) is unchanged because the signature and return type are kept.

## Compatibility considerations

- `find_stale_running_attempts` keeps its return shape (list of dicts with `attempt_id`, `started_at`, `elapsed_sec`); tests that mock it keep working, but the mock-only tests are replaced in the test rows.
- Behavior change: recovery now actually runs on production timestamps (intended; the Phase 1 age is conservative).

## Security considerations

- N/A: persisted timestamps are parsed strictly and reported, never evaluated.

## Rollback considerations

- Phase 1: revert the commit. Phase 3: revert together with the schema row; rows taken over remain legitimately `failed`.

## Validation plan

- `uv run pytest tests/agent/workflow/ -v`
- `rg "mktime|strptime" scripts/agent/workflow` (empty)
- `uv run ruff format scripts/agent/workflow/state_store.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run python tools/check_module_size.py`

## Completion criteria

- A production-format `started_at` is parsed; recovery results do not depend on the host timezone.
- An unparseable timestamp produces a warning, an `unparseable` count, and is not recovered.
- Phase 3: an attempt with an unexpired lease is never recovered; two racing recoverers yield one takeover.

## Out of Scope

- The atomic attempt-plus-task transaction (wfrecovery001 Plan), owner and lease writes (rows 03-05), schema, tests, docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Parse with `parse_iso_utc`; legacy-age rule; remove the 30-second rule; report unparseable rows | Pending | — | — | Plan Phase 1; independent |
| 2 | Add the recovery report | Pending | — | — | Plan Phase 1 |
| 3 | Lease-based detection and conditional takeover | Pending | — | — | Plan Phase 3; gated on the schema row and wfrecovery001 Phase 3 |
| 4 | Add or update tests per Validation plan | Pending | — | — | Test rows' documents |
| 5 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (timezone-independent parsing), REQ-003 (observable unparseable rows and report), REQ-006 (lease-based staleness), REQ-007 (conditional takeover), REQ-008 (legacy rule)
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-130005
- **Related target files**: scripts/agent/workflow/state_store.py
