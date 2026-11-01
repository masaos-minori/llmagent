## Goal

## Goal

Stamp `owner_id` and `lease_expires_at` when an attempt starts in `scripts/agent/workflow/attempt_ops.py` (REQ-004, REQ-005 / AC-5).

## Scope

- Add a per-process owner identity created once: module-level lazy `get_owner_id() -> str` built from `socket.gethostname()`, `os.getpid()`, and a `secrets.token_hex(4)` suffix (Plan Design 'Owner identity': a bare PID can be reused, so the random part is required).
- Extend `start_attempt` (`attempt_ops.py:12-31`) with `lease_duration_sec: int | None = None`; when set, the INSERT at `:19-22` also writes `owner_id=get_owner_id()` and `lease_expires_at = started_at + lease_duration_sec` in the same production format (`Z` string computed from the aware `started_at`); when `None`, both columns stay NULL (legacy-compatible unit callers).

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- `started_at` stays the existing value the function already writes; the lease is derived from the same instant so the AC-5 equality test compares parsed values, not strings.

## Design decisions

- `get_owner_id()` lives here (the attempt writer) and `idempotency_ops.py` imports it — the two attempt-insert sites must write the identical identity string (procedure 04).
- Lease math uses the aware `datetime` from the same `_now()` call that produced `started_at` (`attempt_ops.py:44-45` region), formatted back with the `Z` suffix so stored values round-trip through `parse_iso_utc`.

## Alternatives considered

- UUID stored per attempt as the owner — rejected: REQ-005 asks for host+pid+random so a dead process is identifiable in the manual recovery path (procedure 15 documents it).

## Implementation
### Target file
`scripts/agent/workflow/attempt_ops.py`

### Procedure
1. Add `get_owner_id()` with a module-level cached value.
2. Add the `lease_duration_sec` parameter to `start_attempt` and extend the INSERT columns/values.
3. Keep `finish_attempt` (`:34-48`) unchanged here — its conditional fencing is the wfrecovery001 procedure 04 (Pending).

### Method
Two small edits in one module; parameter-bound SQL unchanged pattern.

### Details
- `import secrets` and `import socket`/`os` are stdlib and bandit-clean (`token_hex` is not a password primitive; no bandit finding expected).
- `AttemptRecord` (`models.py`) is not extended: the lease fields are row-level detection data, not part of the record the engine consumes.

## Compatibility considerations

- `lease_duration_sec` defaults to `None`, so every existing caller and test compiles and behaves identically until procedure 05 starts passing it.
- Blocked until procedures 06 and 17 land: the columns must exist before the INSERT references them (Plan execution-order rule).

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Remove the parameter and identity helper; no persisted data depends on it once 02's takeover is also reverted.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_workflow_engine.py -v` (procedures 09, 11 assert the stamp).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-5: a started attempt has `owner_id` and `lease_expires_at` equal to start plus the stage `timeout_sec` plus the margin (margin value owned by procedure 05).

## Out of Scope

- Conditional `finish_attempt` fencing (wfrecovery001 procedure 04).
- Lease renewal/heartbeat (owner decision, Plan UNK-02).

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
| 1 | Blocked until procedures 06 and 17 add the `owner_id`/`lease_expires_at` columns (Plan execution-order rule) | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phase 3 (Ownership and lease-based recovery)
- **Requirement ID**: `REQ-004`, `REQ-005`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `scripts/agent/workflow/workflow_engine.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_workflow_engine.py`
