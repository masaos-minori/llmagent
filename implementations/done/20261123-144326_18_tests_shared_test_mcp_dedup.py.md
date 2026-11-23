## Goal
- Extend the existing dedup test file with the matrix-shaped sweep cases and a read-only view class, pinning `REQ-001` (retention matrix per state), `REQ-002` (unresolved states outside the sweep), and `REQ-003` (legal-hold entry and the optional `[dedup]` keys) before the ledger change lands.

## Scope
**Release unit**: matrix and its test
- New cases inside `TestTtlPurge` plus one class for `get_dedup_metrics_view()` (new); rows 05, 07, 08 own the module changes.

## Assumptions
- Owner decisions `U-3` and `D-2`: terminal-only sweep scope is intentional, including the age-based `call_attempt_history` delete; unresolved rows' lifecycle belongs to `reconcile_execution()` and mcpdl006.
- Legal hold is configuration-based (`U-2` resolved): `legal_hold_states` (new) is read from the store's own `DedupStoreConfig`, and a store built without `config=` keeps today's purge behaviour.
- Overlap with plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md is additive: that plan edits the acquisition and reopen cases, this row adds sweep-eligibility and read-only view cases.
- Threshold behaviour belongs to `tests/shared/test_mcp_dedup_metrics.py` (new), the row 05 companion.

## Design decisions
- Matrix-first: the cases state expected eligibility, not current behaviour, so they can precede row 07.
- Reuse the module-level `store` fixture, `_history()`, and `_SNAP`; only the hold and view cases build a second store from a `DedupStoreConfig` passed as `config=`.

## Alternatives considered
- A separate file for the view tests: rejected, the view is a ledger verb and this file owns the store fixtures.

## Implementation
### Target file
`tests/shared/test_mcp_dedup.py`
### Procedure
- Add cases only; every existing class and assertion stays unchanged.
- In `TestTtlPurge`, first verify `test_expired_terminal_states_all_purged` already covers completed, failed, and interrupted past the cutoff before adding a per-state matrix case; then add `test_overdue_pending_never_purged` (new) — a `pending` row with an expired `lease_expires_epoch` is still not swept and the sweep returns 0; `test_reconciled_row_becomes_sweepable` (new) — the row is sweepable only after `reconcile_execution()` moves it to `interrupted` (pattern from the reconcile cases and `TestReopenDurability`); `test_held_terminal_row_not_purged` (new) — with `legal_hold_states` (new) the held-state terminal row past the retention survives while a same-age non-held terminal row is purged; and `test_no_hold_purge_behaviour_unchanged` (new).
- Add `TestDedupMetricsView` (new) for `get_dedup_metrics_view()` (new).
### Method
- Use the file's epoch injection (`now_epoch=`, `retention_days=14`) instead of sleeping, seeding with `try_acquire_execution`, `record_completed`, `record_failed`, `mark_interrupted`.
### Details
- Assert per-state counts from `row_states` (new), `pending_overdue` (new) counting only expired leases, `created_since` (new) after a floor, `wal_size_bytes` (new) and `lock_wait_ms` (new) >= 0, and `held_past_retention` (new) counting the held row as held, not retained-at-large (AC-3).
- Read-only (AC-8): row count, one `get_execution` row, and `_history()` are identical before and after the reads.

## Compatibility considerations
- `TestTtlPurge`, `TestReopenDurability`, and `TestDedupSectionValidation` keep passing; the optional-key case only shows an in-range key still opens through `open_dedup_store`, while out-of-range rejection is row 21's.

## Security considerations
- N/A: tests-only, all SQLite access stays on tmp_path files.

## Rollback considerations
- N/A: revert the commit (tests-only row, single commit).

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py` — pass, including the pre-existing cases.
- Matrix-first: the sweep cases land with or before the row 07 change per the Plan's Phase order, so some may fail until that row lands; the optional-key case lands with row 08. Then `rules/toolchain.md` in full.

## Completion criteria
- Sweep eligibility per state, the overdue-pending exception, the reconcile-then-sweep transition, and the held-row exception are each asserted by a named test.
- The view's counts, WAL size, lock wait, and held count are asserted with the read proven write-free, and every pre-existing assertion still passes.

## Out of Scope
- Changing `purge_expired`, the `[dedup]` validation, the metrics module, or the health wiring (rows 05, 07, 08, 09).
- Threshold values and per-metric status (row 19), and the classifications with no stored state (mcpdl006).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the matrix-shaped purge and lifecycle cases to `TestTtlPurge` | Completed | 20261123-230806 | 20261123-230806 | Confirmed that test_expired_terminal_states_all_purged already covers completed, failed and interrupted past the cutoff, so no matrix case duplicates it. Added to TestTtlPurge: test_overdue_pending_never_purged, test_reconciled_row_becomes_sweepable, test_held_terminal_row_not_purged, test_no_hold_purge_behaviour_unchanged. Every existing assertion is unchanged. The hold case builds a second store from a DedupStoreConfig passed as config=. Deviation: the per-state decision asserted here is state eligibility plus the hold exclusion, not a per-state threshold, because thresholds are report-only and never gate behaviour (owner decision D-6). The sweep cutoff is updated_epoch, so the reconcile case asserts eligibility at a later clock rather than at the reconcile time. |
| 2 | Add the read-only metrics-view test class | Completed | 20261123-230806 | 20261123-230806 | Added TestDedupMetricsView: per-state counts, pending_overdue counting only expired leases, created_since after a floor, wal_size_bytes and lock_wait_ms at or above 0, and held_past_retention counting the held row as held. Read-only proven by row count, one get_execution row, _history(), and the connection total_changes being identical before and after the reads. Run: tests/shared/test_mcp_dedup.py 74 passed (68 pre-existing plus 6 new). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | ruff format and check pass, run_validation_gates.py all applicable gates Pass, mypy clean on the primary invocation, bandit clean, module size pass. End-of-unit run for the release unit (matrix and its test): full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent against the 90 gate. Deviation: the end-of-unit run was executed once for the whole diff because both release units' changes are in one uncommitted diff. |

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
- **Requirement ID**: `REQ-001` (retention matrix per state), `REQ-002` (unresolved states stay outside the sweep), `REQ-003` (legal-hold entry and the optional `[dedup]` keys validated fail-closed); AC-1, AC-2, AC-3
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `tests/shared/test_mcp_dedup.py`