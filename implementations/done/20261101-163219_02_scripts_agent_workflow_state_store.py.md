## Goal

Rewrite stale-attempt detection and takeover in `scripts/agent/workflow/state_store.py`: parse only with `parse_iso_utc`, report unparseable rows, decide staleness from the lease (legacy age for lease-less rows), remove `_STALE_GRACE_SEC`, and make takeover a one-row conditional update (REQ-002, REQ-003, REQ-006, REQ-007, REQ-008 / AC-2..AC-7).

## Scope

- Phase 1 increment (independent): `find_stale_running_attempts` (`state_store.py:193-218`) parses `started_at` with `json_utils.parse_iso_utc`; `time.mktime(time.strptime(...))` at `:208` and the silent `continue` are deleted; `_STALE_GRACE_SEC` (`:30`) is removed and replaced for lease-less rows by the named constant `_LEGACY_STALE_AGE_SEC = 3600` (REQ-008, interim safety).
- Phase 3 increment (after procedures 03-06 and 17 land): staleness = `lease_expires_at` parsed and expired; an unexpired lease is never recovered, including by another process (REQ-006 / AC-4).
- `recover_stale_attempts` (`:222-259`) takeover becomes one conditional `UPDATE attempts SET status='failed', ended_at=?, error_msg=? WHERE attempt_id=? AND status='running' AND owner_id IS ? AND lease_expires_at IS ?` requiring `cursor.rowcount == 1`; zero rows means another recoverer took it and the row is skipped (REQ-007 / AC-6).
- Recovery report: frozen dataclass `RecoveryReport(recovered, still_live, legacy_recovered, unparseable)` stored as `last_recovery_report`; `recover_stale_attempts()` keeps returning the recovered count (18 test references in 2 files rely on it, Plan Design 'Report API').
- Unparseable `started_at` or `lease_expires_at`: `logger.warning` with attempt id and the raw value, counted in `unparseable`, row neither recovered nor silently skipped (REQ-003 / AC-3).

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- The conditional update is compare-and-swap on the exact `owner_id`/`lease_expires_at` values listed by the preceding `find` — a live owner that re-started an attempt in the meantime changes those values and fences the takeover.
- `IS` comparisons (not `=`) are used for the expected values so a legacy `NULL` owner/lease matches correctly in the legacy branch.

## Design decisions

- One detection function returns classified rows (stale-lease / legacy-stale / live / unparseable) so `find_stale_running_attempts` and `recover_stale_attempts` share the same decision; `find_stale_running_attempts` keeps its `list[dict]` return shape (external callers unchanged), extended with `owner_id`/`lease_expires_at` keys.
- Detection compares aware datetimes (`parse_iso_utc(lease) < now_utc`); no host-local time anywhere (AC-2: `rg "mktime|strptime" scripts/agent/workflow` is empty after this procedure).
- Phase 1 lands first with only the legacy-age branch (no lease columns exist yet); Phase 3 adds the lease branch behind `lease_expires_at IS NOT NULL` so the same code works before and after procedure 17 migrates an existing database.

## Alternatives considered

- Heartbeat renewal instead of deadline lease — rejected by the owner (Plan UNK-02): `asyncio.wait_for` already bounds a normal stage, and a heartbeat adds event-loop `BEGIN IMMEDIATE` writes that can wait up to the 30000 ms busy timeout.
- Deleting `find_stale_running_attempts` and inlining into recovery — rejected: the method is a public seam used by the orchestrator-adjacent tests and keeps the detection testable without mutation.

## Implementation
### Target file
`scripts/agent/workflow/state_store.py`

### Procedure
1. Import `parse_iso_utc` from `shared.json_utils` in `state_store.py`.
2. Replace the parse block at `:206-212` with `parse_iso_utc` + classification; remove `_STALE_GRACE_SEC` (`:30`) and add `_LEGACY_STALE_AGE_SEC = 3600`.
3. Add the `RecoveryReport` frozen dataclass (module level) and `last_recovery_report` attribute set by `recover_stale_attempts`.
4. Rewrite `recover_stale_attempts` (`:222-259`): classify rows, then per stale row run the conditional takeover update via the existing helper cursor; on `rowcount == 1` count it recovered (and `legacy_recovered` when the row had no lease); on `rowcount == 0` count nothing and log at info.
5. Phase 3: extend the conditional `WHERE` with the expected `owner_id`/`lease_expires_at` values captured by the classify step (compare-and-swap fencing).

### Method
In-place rewrite of two methods plus module-level constants and one dataclass; all SQL parameter-bound through the existing `SQLiteHelper`.

### Details
- `state_store.py` is 10171 B at baseline and stays under the 20480 B `check_module_size` limit (Plan Validation plan).
- Warning log format: `unparseable workflow attempt timestamp: attempt_id=%s value=%s` — the same line satisfies REQ-003 and the docs manual-recovery path (procedure 15).
- The failing-row branch keeps the attempt `running` (never a partial recovery) — the documented manual path owns it.

## Compatibility considerations

- `recover_stale_attempts()` return type stays `int` (Plan Risk row: 18 references in 2 test files).
- `orchestrator.py:92` call site is unchanged (Plan Reference Files).
- Task-level transition after a takeover follows the wfrecovery001 atomic-recovery procedures (Pending); this procedure must land after `implementations/20261101-145309_06_scripts_agent_workflow_state_store.py.md` so attempt+task failure stays atomic.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.
- The takeover `WHERE` clause pins status and expected ownership values, so a takeover can only ever transition the exact stale row it observed — a racing or live owner is fenced by `rowcount`.

## Rollback considerations

- Phase 1 and Phase 3 land as separate commits; each reverts independently. Reverting 02 restores the grace-period detection but the columns from 17 stay (nullable, harmless).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py tests/agent/workflow/test_state_store.py tests/agent/workflow/test_stale_recovery_lease.py -v` (procedures 09, 10, 12).
- AC-2 check: `rg "mktime|strptime" scripts/agent/workflow` returns empty.
- Full sequence per `rules/toolchain.md`: `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`.

## Completion criteria

- AC-2 through AC-7 pass with production-format timestamps under `TZ=UTC` and a non-UTC `TZ`.
- `recover_stale_attempts()` still returns the recovered count and `last_recovery_report` exposes all four counts.

## Out of Scope

- Attempt numbering, ledger semantics, task transitions (wfrecovery001, Plan Out-of-Scope).
- Retry policy and failure propagation (`issues/20261030-105723_wfretry001_timeout-retry-failure-propagation.md`, Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | RecoveryReport frozen dataclass, _classify_running_attempts helper, mark_stale_attempts_failed/recover_stale_attempts retained aliases, find_stale_running_attempts made lease-aware |
| 2 | Add or update tests per Validation plan | Completed | — | — | _STALE_GRACE_SEC and time.mktime removed (grep gate clean); unconditional takeover UPDATE replaced by conditional claim UPDATE (status='running' guard + owner_id/lease_expires_at IS ? guards); legacy 3600s fallback; started_at NULL and live-lease rows skipped |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | error_msg: 'recovered at startup: lease expired' and 'recovered at startup: legacy attempt older than 3600s' (tests assert substrings); unparseable timestamp -> single WARNING 'unparseable workflow attempt timestamp', row left running, never silently skipped |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A here: doc update is Procedure 15 (G6); engine call-site change is Procedure 05; 30s margin gate lands in Procedure 12 test |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| 1 | Phase 3 increment is Blocked until procedures 03-06 and 17 (lease columns) and the wfrecovery001 conditional-finish/atomic-recovery procedures (Pending) land | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phases 1 and 3 (interim detection; lease-based takeover)
- **Requirement ID**: `REQ-002`, `REQ-003`, `REQ-006`, `REQ-007`, `REQ-008`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `scripts/agent/workflow/state_store.py`, `scripts/shared/json_utils.py`, `scripts/agent/workflow/attempt_ops.py`, `scripts/db/schema_sql.py`, `scripts/db/migrations_workflow.py`, `tests/agent/workflow/test_workflow_state_store.py`, `tests/agent/workflow/test_state_store.py`, `tests/agent/workflow/test_stale_recovery_lease.py`