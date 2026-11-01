## Goal

## Goal

Pass the stage timeout plus the lease margin from `scripts/agent/workflow/workflow_engine.py` at attempt start and define the margin constant (REQ-005 / AC-5).

## Scope

- Define the named module constant `_LEASE_MARGIN_SEC = 30` (Plan Assumptions UNK-03: named constant, not configuration).
- In `_run_stage` (`workflow_engine.py:242` region), where the stage timeout is computed at `:261` (`stage_def.timeout_sec if stage_def else 60`), pass `timeout + _LEASE_MARGIN_SEC` as `lease_duration_sec` to the `begin_stage_if_new` call at `:264`.
- Any direct `start_attempt` call path the engine uses (`_run_stage_with_retry`, `:188` region) passes the same value.

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06): `master` records code 2 / "1.2.0" (`migrations_workflow.py:42`); wftaskapi001 procedure 12 (`implementations/20261101-140834_12_scripts_db_migrations_workflow.py.md`, Pending) reserves the next slot. This Plan takes code 3 / "1.3.0" only if its step registers before wftaskapi001's, otherwise 4 / "1.4.0" (same rule as `implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`).
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- `timeout_sec` per stage comes from `config/workflows/default.json` (120 s for `execute`); the lease horizon is therefore 150 s for `execute` — longer than any normally running stage because `asyncio.wait_for` (`:278`) enforces the timeout (Plan Design 'Lease without heartbeat').

## Design decisions

- The engine owns the margin because it owns the timeout; ops modules receive only the finished duration (procedures 03-04), keeping the constant single-sourced.
- No renewal calls are added (Plan UNK-02: deadline lease).

## Alternatives considered

- Margin as configuration — rejected by Plan UNK-03 default; promote later only if the owner asks.
- Deriving the lease inside ops modules from a stage lookup — rejected: the engine already resolved `stage_def` and duplicating the lookup would drift from the enforced `wait_for` timeout.

## Implementation
### Target file
`scripts/agent/workflow/workflow_engine.py`

### Procedure
1. Add `_LEASE_MARGIN_SEC = 30` near the module constants.
2. Pass `lease_duration_sec=timeout + _LEASE_MARGIN_SEC` at both attempt-start call sites.

### Method
Constant plus two call-site keyword additions; no control-flow change.

### Details
- Timeout source at `:261` already falls back to 60 s for stages without a definition; the lease falls back with it (`60 + 30`), so no lease is ever unstamped on the engine path.
- The engine keeps using `begin_stage_if_new` (`:264`) — no new imports beyond the ops signatures from procedures 03-04.

## Compatibility considerations

- Blocked until procedures 03, 04, 06 and 17 land (parameter and columns must exist first) — Plan execution-order rule.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Single-commit revert; behavior returns to no-lease attempt starts.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (procedure 11).
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-5: for every engine-started attempt, `parse_iso_utc(lease_expires_at) - parse_iso_utc(started_at) == stage timeout_sec + 30`.

## Out of Scope

- Retry policy and timeout-failure propagation (`wfretry001` issue, Plan Out-of-Scope).
- `_run_stage_with_retry` structure changes beyond the two keyword arguments.

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
| 1 | Blocked until procedures 03-04 (parameters) and 06/17 (columns) land | No | — |

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
- **Related target files**: `scripts/agent/workflow/workflow_engine.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/agent/workflow/idempotency_ops.py`, `tests/agent/workflow/test_workflow_engine.py`
