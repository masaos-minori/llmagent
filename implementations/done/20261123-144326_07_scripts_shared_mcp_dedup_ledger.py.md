## Goal
- Make the sweep's legal-hold exclusion real in code while keeping its terminal-only eligibility exactly as it is today, and expose the read helpers the metrics module reads (REQ-002 keep the sweep terminal-only and add the legal-hold exclusion).

## Scope
**Release unit**: health exposure
- `purge_expired` (lines 457-493) keeps its terminal-only `DELETE` of completed/failed/interrupted rows and its age-based `call_attempt_history` delete, and gains the hold exclusion in its `WHERE`.
- Adds the class attributes `DEDUP_READ_TIMEOUT_SECONDS` (new) and `MAX_METRICS_ROW_STATES` (new), and `get_dedup_metrics_view()` (new) with its read helpers.
- No change to acquisition, lease renewal, finalization, `reconcile_execution()` (lines 367-434), or the terminal-only sweep scope.
- `scripts/mcp_servers/dispatch.py` and `_purge_once` stay unmodified (reference row): the store reads its own config.

## Assumptions
- The Plan records legal hold as configuration-based (`U-2`): no new column and no DDL, so the persisted-schema gate and `_config_fingerprint` are unaffected.
- Overlap with `plans/20261123-130937_mcpai001_atomic-dedup-state-machine.md`, which also targets `scripts/shared/mcp_dedup_ledger.py` and `tests/shared/test_mcp_dedup.py`: verified compatible against the current code — this row changes no sweep predicate beyond the hold exclusion, no state transition, and no `reconcile_execution()` or lease behaviour, while that Plan edits `try_acquire_execution` and the interrupted-reopen cases.
- The held states come from `self._config` set in `scripts/shared/mcp_dedup.py` (line 133); a store constructed without a config yields an empty tuple, so its sweep behaves exactly as today.

## Design decisions
- Read the hold list from the store's own config instead of a `purge_expired` argument, so the only caller (`_purge_once`) and the sweep's public signature stay unchanged.
- Keep every metrics read on the ledger's existing `_lock` and `_conn`, matching the shape of `get_execution()` (line 446): one lock, one connection.

## Alternatives considered
- Computing counts in `scripts/shared/mcp_dedup_metrics.py` with a second connection: rejected — it doubles the lock surface and ignores the store's configured `busy_timeout`.
- Widening the sweep to unresolved states: rejected by the owner's resolution of `U-3` (terminal-row-only scope).

## Implementation
### Target file
`scripts/shared/mcp_dedup_ledger.py`

### Procedure
1. Add `DEDUP_READ_TIMEOUT_SECONDS` (new) as `10` and `MAX_METRICS_ROW_STATES` (new) as `32` beside the existing `_conn`, `_lock`, `_lease_seconds`, `_max_attempts` annotations (lines 42-45).
2. Add `_legal_hold_states()` (new): read the `legal_hold_states` (new) tuple off `getattr(self, "_config", None)`, returning `()` when no config is attached.
3. In `purge_expired` (lines 457-493), append `AND status NOT IN (?,?,...)` to the terminal `DELETE`, bound from the held names, and only when the tuple is non-empty; extend the docstring so it names the hold exclusion and keeps stating that pending rows are never purged here.
4. Add `get_dedup_metrics_view()` (new), returning a small read-only view object bound to this ledger.

### Method
- The hold exclusion is additive to the existing predicate, so with no hold configured the emitted SQL and the rowcount stay byte-identical to today.
- Each view helper takes `self._lock`, issues one `SELECT` (or one file `stat` for the WAL file), and returns a JSON-safe value; none of them may call `_write_txn` or issue `BEGIN IMMEDIATE`.

### Details
- View helpers, all (new): `row_states` (new) per-status counts capped at `MAX_METRICS_ROW_STATES` (new), `pending_overdue` (new) count of `pending` rows whose `lease_expires_epoch` is past `now`, `created_since` (new) count of rows with `created_epoch` at or after its floor, `lock_wait_ms` (new) elapsed milliseconds to acquire `_lock` within `DEDUP_READ_TIMEOUT_SECONDS` (new), `wal_size_bytes` (new) size of the store's `-wal` file, and the view's `db_path` (new) property reading the same path the store's public property exposes in `scripts/shared/mcp_dedup.py`.
- The sweep's log line keeps reporting purged rows and purged history entries; held rows are simply not counted as purged, which is what makes them visible as held rather than as retained-at-large.
- Step 3b correction (deviation, user decision 20261123): the view object is defined in
  `scripts/shared/mcp_dedup_rows.py`, the read-model module that already holds `CallStateView`,
  because the measured size of this target file is 24329 B against the 24576 B gate after the
  change. `scripts/shared/mcp_dedup_ledger.py` keeps `get_dedup_metrics_view()` and
  `_legal_hold_states()`; the view still borrows the ledger's lock and connection, so the runtime
  contract of this row is unchanged.
- Step 3b correction (deviation): the helper list also includes `held_past_retention` (new), which
  the row 05 payload requires but this document's Method list did not name.
- `tests/shared/test_mcp_dedup.py` is the evidence for the pinned behaviour: `TestTtlPurge` asserts the current terminal-only sweep, `TestReopenDurability` the reopen path, and `TestDedupSectionValidation` the config contract this row depends on.

## Compatibility considerations
- `TestTtlPurge` pins the current purge behaviour and must keep passing unchanged: no config in those tests carries `legal_hold_states` (new), so the emitted `DELETE` is unchanged.
- `tests/mcp_servers/test_mcp_dispatch.py` pins the caller contract (`_purge_once` and the once-per-process flag), which this row does not touch.
- Size: the file is 19160 B against the 24576 B gate, and it is a shared target of the mcpdl004 and mcpai001 plans, so the read stays a thin view rather than a full metrics implementation.
  Measured in this cycle: 23155 B before the change and 24329 B after it, so the view could not be added here and was placed in `scripts/shared/mcp_dedup_rows.py` per the Step 3b correction above.

## Security considerations
- The view exposes counts and the store path only — never `snapshot_json`, `result_json`, key values, or owner ids.
- The helpers issue no write, so a metrics read cannot mutate the ledger or extend a lease.

## Rollback considerations
- Revert the commit: the hold exclusion and the view object have no persisted effect (no DDL, no migration), so an existing store file needs nothing after a revert.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup.py tests/mcp_servers/test_config_isolation_fail_closed.py` (unit, expect Pass).
- `uv run python tools/run_validation_gates.py` for the diff, plus the full sequence in `rules/toolchain.md`.

## Completion criteria
- With no hold configured, `purge_expired` returns the same counts and deletes the same rows as before; with a hold configured, held-state rows survive and everything else is purged as today.
- `get_dedup_metrics_view()` returns each documented value from a store holding rows in several states, without issuing a write.

## Out of Scope
- Threshold and hold key validation (row 08), the metrics payload (row 05), the facade re-export (row 06), the health wiring (row 09 and the handler rows), and the state-machine and lease work owned by mcpdl006 and mcpai001.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the hold exclusion and the metrics view per Procedure/Method/Details | Completed | — | 20261123-221637 | Changed: scripts/shared/mcp_dedup_ledger.py (class attributes DEDUP_READ_TIMEOUT_SECONDS=10 and MAX_METRICS_ROW_STATES=32, _legal_hold_states(), get_dedup_metrics_view(), hold exclusion in the purge DELETE, docstring). Deviation per user decision: the view object itself is defined in scripts/shared/mcp_dedup_rows.py because this file measured 23155 B before the change (19160 B in the document) and 24329 B after, against the 24576 B gate. Deviation: held_past_retention added as a view helper because the row 05 payload requires it. With no hold the emitted SQL and rowcount are byte-identical to before. |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261123-230806 | 20261123-230806 | No test step: the matrix and hold assertions belong to `tests/shared/test_mcp_dedup.py`, covered by the row 18 document This member Step 3e: ruff format/check pass, run_validation_gates.py fast mode all applicable gates Pass, lint-imports 6 contracts kept, bandit clean after one justified nosec B608 on the generated placeholder list. Targeted run (the Validation plan): 86 passed across tests/shared/test_mcp_dedup.py, tests/mcp_servers/test_config_isolation_fail_closed.py and the row 05 companion test, which is green now that this row and row 08 landed. Full suite runs once at end of the release unit. Note: this row was executed after row 08; the seq order deviation is reported in the final report. Correction to the earlier note: the nosec B608 justification had to be written in the em-dash form the pre-commit hook requires, so it is now on the flagged line as nosec B608 followed by the justification. End-of-unit run for the release unit: full suite with coverage 13660 passed 4 skipped, diff-scoped coverage 94 percent, all gates pass including the suppression-justification hook. Deviation: the run was executed once for the whole diff. |

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
- **Requirement ID**: REQ-002 (keep the sweep inside the terminal-row rule and add the legal-hold exclusion)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/shared/mcp_dedup_ledger.py`