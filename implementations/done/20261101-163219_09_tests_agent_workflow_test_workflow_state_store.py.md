## Goal

Replace naive-format seeds and grace-based expectations in `tests/agent/workflow/test_workflow_state_store.py` with production-format, lease-based recovery tests (REQ-002, REQ-006, REQ-007, REQ-009 / AC-2..AC-7).

## Scope

- Replace the naive seeds `"2026-01-01T00:00:00"` at `:277`, `:327`, `:351`, `:378` and the `time.localtime`-formatted seeds at `:301`, `:353`, `:401`, `:454`, `:494` (whole recovery region `:250-562`, classes `TestRecoverStaleAttempts` and `TestStaleRecoveryConcurrency`) with the production format (`...Z`) produced by `json_utils.now_iso`-equivalent literals.
- Re-point the recovery tests (`test_stale_attempt_marked_failed` `:265`, `test_find_stale_returns_only_old_attempts` `:339`, `test_recovered_attempt_has_ended_at_set` `:366`, `test_recover_multiple_stale_attempts` `:390`, `test_recover_no_stale_attempts` `:443`) onto lease semantics: expired-lease seeds are stale; unexpired-lease seeds are live; legacy seeds (NULL lease) follow the 3600 s age rule.
- Add host-timezone independence: the same seed set recovers identically under `TZ=UTC` and a non-UTC `TZ` set via `monkeypatch` + `time.tzset()` (REQ-002 / AC-2).

## Assumptions

- Plan `plans/20261030-114516_wflease001_stale-attempt-lease.md` is Frozen; its 18-row `Implementation Target Files` table (rows 17-18 added by the 2026-11-01 amendment) is the canonical scope and every target of this procedure is a row of that table.
- All baseline cites below were re-verified against branch `master` on 2026-11-01 (Plan Assumptions 'Re-verification record').
- Canonical semantics come from the Plan REQs (Plan `:37-46`): `parse_iso_utc` rejects naive input (REQ-001); no `mktime`/`strptime`/local time in recovery (REQ-002); unparseable timestamps are reported with distinct counts (REQ-003); nullable `owner_id`/`lease_expires_at` via a registered migration (REQ-004); owner and lease stamped at attempt start from the stage timeout plus a 30 s margin constant (REQ-005); staleness means lease expiry and `_STALE_GRACE_SEC` is removed (REQ-006); takeover is a conditional update requiring one row (REQ-007); legacy rows without a lease use the 3600 s age (REQ-008); tests use the production timestamp format (REQ-009); docs and ADR-001 INV-07 are amended (REQ-010).
- Owner decision (Plan UNK-02, 2026-10-30): deadline lease only — no heartbeat renewal, because `asyncio.wait_for` already bounds a normal stage.
- Ledger landing order (Plan UNK-06; fixed by the 2026-11-01 pre-execution verification): wftaskapi001 procedure 12 has landed (`implementations/done/20261101-140834_12_scripts_db_migrations_workflow.py.md`) and registered code 3 / "1.3.0" (`migrations_workflow.py:42`, `WORKFLOW_TARGET_VERSION` = 3 at `:49`). This Plan takes code 4 / "1.4.0": procedure 17 registers `workflow_attempt_lease` with `from_version=3, to_version=4`, and procedure 06 sets `WORKFLOW_SCHEMA_VERSION` to "1.4.0". The still-Pending wfrecovery001 procedure 26 (`implementations/20261101-145309_26_scripts_db_migrations_workflow.py.md`) takes 5 / "1.5.0" when it lands after this Plan.
- Fencing dependency (Plan UNK-06): REQ-007's rejection of a late finish by the fenced owner lands with the wfrecovery001 conditional `finish_attempt` procedure (`implementations/20261101-145309_04_scripts_agent_workflow_attempt_ops.py.md`, Pending); at `master` `finish_attempt` is still unconditional (`attempt_ops.py:44-45`).
- The seed helper that inserts attempt rows must also seed `owner_id`/`lease_expires_at` after procedures 06/17 land; before that, Phase 1 seeds exercise only the legacy-age branch.

## Design decisions

- Phase 1 rewrites land with the legacy branch only (no lease columns in the fixture DB yet); Phase 3 extends the same tests with lease fixtures — the file keeps one fixture helper so both phases reuse it.

## Alternatives considered

- Rewriting the file from scratch — rejected: 84 blast-radius references are elsewhere, but this file's passing structure is reused; only seeds and expectations change.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
1. Switch every seeded timestamp literal to the `Z` format.
2. Convert grace-based expectations to lease/legacy expectations.
3. Add the two `TZ` variants for the find/recover pair.
4. Add an unparseable-seed case asserting the `RecoveryReport.unparseable` count and that the row stays `running`.

### Method
Seed-literal replacement plus expectation edits inside the existing test classes.

### Details
- `time.tzset()` is POSIX-only; tests are skipped on non-POSIX platforms exactly like the Plan's Tests section prescribes `TZ` via `monkeypatch` and `tzset`.
- Assertions compare parsed instants (`parse_iso_utc`), not raw strings, except the format-literal seeds themselves.

## Compatibility considerations

- Mock-free: these tests keep using the real fixture DB (`workflow_db` fixture) they already use.

## Security considerations

- All recovery/attempt SQL stays parameter-bound; owner and lease values are produced by the server (clock, host identity), never by caller-supplied strings.

## Rollback considerations

- Characterize: pre-change tests pass on old code only with naive seeds; revert keeps them green on old code.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v`

## Completion criteria

- AC-2, AC-4..AC-7 covered through the lease fixtures in this file.

## Out of Scope

- Task-transition expectations (wfrecovery001 procedures, already landed or pending per `implementations/20261101-145309_*`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | TestRecoverStaleAttempts rewritten: Z-format seeds via _iso/_iso_future, _open_store helper, lease-aware _insert_task_and_attempt |
| 2 | Add or update tests per Validation plan | Completed | — | — | added test_expired_lease_attempt_marked_failed, test_live_lease_attempt_not_recovered, test_unparseable_timestamp_reported_and_row_left_running, parametrized test_recovery_is_timezone_independent (UTC and Asia/Tokyo via tzset, TZ restored via addfinalizer); concurrency test seed switched to _iso(7200) |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | pytest tests/agent/workflow/test_workflow_state_store.py -q green; whole tests/agent/workflow/ 109 passed; full suite 10898 passed; diff-cover 100% |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: test-only procedure, no docs in scope |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: Phases 1 and 3
- **Requirement ID**: `REQ-002`, `REQ-006`, `REQ-007`, `REQ-009`
- **Source issue**: issues/20261030-105723_wflease001_stale-attempt-lease.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114516_wflease001_stale-attempt-lease.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-163219
- **Related target files**: `tests/agent/workflow/test_workflow_state_store.py`, `scripts/agent/workflow/state_store.py`, `scripts/shared/json_utils.py`, `tests/agent/workflow/test_stale_recovery_lease.py`