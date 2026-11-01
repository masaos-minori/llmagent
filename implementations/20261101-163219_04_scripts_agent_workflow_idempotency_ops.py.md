## Goal

## Goal

Carry the lease duration into the attempt-start transaction in `scripts/agent/workflow/idempotency_ops.py` so the idempotent stage-start path stamps the same ownership fields (REQ-005 / AC-5).

## Scope

- Extend `begin_stage_if_new` (`idempotency_ops.py:18-67`) with `lease_duration_sec: int | None = None`; the attempt INSERT at `:48-51` writes `owner_id` and `lease_expires_at` exactly as procedure 03 (import `get_owner_id` from `attempt_ops`), inside the same `BEGIN IMMEDIATE` transaction that inserts the `processed_events` row.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- Engine calls always pass a concrete `lease_duration_sec` (procedure 05); the `None` default exists only so direct unit callers stay compilable.

## Design decisions

- Reuse `attempt_ops.get_owner_id()` and a shared lease-formatting helper rather than duplicating the identity/lease math in the second insert site (Plan Design 'Owner identity': one identifier per process).

## Alternatives considered

- Stamp the lease in the engine after `begin_stage_if_new` returns — rejected: a separate statement outside the transaction can observe a half-written attempt row and adds a second `BEGIN IMMEDIATE` round under the 30000 ms busy timeout.

## Implementation
### Target file
`scripts/agent/workflow/idempotency_ops.py`

### Procedure
1. Add the parameter and extend the INSERT at `:48-51`.
2. Import the identity/lease helpers from `attempt_ops` (same package layer; `lint-imports` unaffected).

### Method
One signature extension plus one INSERT edit; transaction structure untouched.

### Details
- `begin_stage_if_new` already receives `db`, `event_id`, `task_id`, `stage_id` at `:18-24`; the new keyword goes last.
- The processed-event dedup semantics (`is_event_processed`) are untouched (Plan: different methods, compatible overlap with wftaskapi001).

## Compatibility considerations

- Blocked until procedures 06 and 17 land (columns must exist).
- Existing callers that omit the parameter keep today's behavior.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Revert the parameter; the transaction shape never changed.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (procedure 11 asserts the stamp through the engine path).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-5 holds for attempts started through the idempotent path, with identical `owner_id` as the plain path.

## Out of Scope

- Event dedup and ledger semantics (wfrecovery001 / wftaskapi001 contracts).

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
| 1 | Blocked until procedures 06 and 17 add the lease columns (Plan execution-order rule) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Ownership and lease-based recovery)
- **Requirement ID**: `REQ-005`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/workflow/test_workflow_engine.py`
