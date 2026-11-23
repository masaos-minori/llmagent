## Goal
- Add one read-only function that reports the dedup store's state counts, growth, WAL size, lock wait, lease health, legal-hold rows, and threshold status, so an operator can tell normal from degraded (REQ-004 read-only store metrics; REQ-008 no write, no migration, no new service).

## Scope
**Release unit**: health exposure
- Creates `scripts/shared/mcp_dedup_metrics.py` (new) as a leaf module in `scripts/shared/`.
- Issues `SELECT` and `PRAGMA` read queries on the store's own connection only; no `INSERT`, `UPDATE`, `DELETE`, or `BEGIN IMMEDIATE`.
- Reports per-metric status (`ok`, `warning`, `fail`) only when the matching `[dedup]` threshold key is set; a breach never changes store or dispatcher behaviour.
- Out of scope: the facade re-export (row 06), the health `details` wiring (row 09), and the threshold/hold keys themselves (row 08).

## Assumptions
- `scripts/shared/` is the leaf of the import contract, so this module never imports `mcp_servers`; the read flows from `shared` toward the handler.
- The read helpers this module calls are created by the sibling row `scripts/shared/mcp_dedup_ledger.py` — `get_dedup_metrics_view()` (new) — and both rows land in the same Plan phase (Phase 4), so the names exist before either is exercised.
- Threshold and hold values come from `scripts/shared/mcp_dedup_config.py` (row 08): an absent key means unset, so no status block is computed for that metric.
- `U-1`: numeric threshold values are operator-supplied; nothing in this module hard-codes a number.

## Design decisions
- Reuse the store's existing connection and its `busy_timeout` set in `open_dedup_store` in `scripts/shared/mcp_dedup.py` (line 411): no second sqlite connection, so the read cannot add a new writer or a second lock.
- Return a plain `dict[str, object]` rather than a dataclass, because the only consumer is the health `details` block and JSON-safety is the contract.
- A lock that cannot be acquired inside the deadline is reported as a status field, never raised: `/health` must answer even when the store is busy.

## Alternatives considered
- Putting the read in `scripts/shared/mcp_dedup_ledger.py`: rejected for the 24576 B module-size gate (the ledger is already 19160 B and is a shared target of two other Plans).
- Extending `scripts/shared/mcp_health.py`: rejected, it is server availability health for dispatch gating, a distinct concern the Plan says this module must not be conflated with.
- A module inside `scripts/mcp_servers/`: the Plan names `scripts/mcp_servers/web_search/metrics.py` as the existing metrics-module placement pattern, but the import contract keeps `scripts/shared/` a leaf and the read needs the store, so the new module goes in `scripts/shared/`.
- A separate status endpoint or service: rejected out of scope by the Plan (`tests/mcp_servers/_route_inventory.py` allows one execution route per app).

## Implementation
### Target file
`scripts/shared/mcp_dedup_metrics.py` (new)

### Procedure
1. Module header docstring stating the read-only contract (AC-8) and the module family it belongs to.
2. Define `METRICS_SCHEMA_VERSION` (new) as `1` and `collect_dedup_metrics` (new) with the signature `collect_dedup_metrics(store, config, *, now_epoch=None) -> dict[str, object]`.
3. Type `store` as `DedupLedger` from `scripts/shared/mcp_dedup_ledger.py` (typing only) and `config` as `DedupStoreConfig`; take `now_epoch` defaulting to the current epoch like `purge_expired` in `scripts/shared/mcp_dedup_ledger.py` (lines 457-493) does.
4. Obtain the read helpers through `get_dedup_metrics_view()` (new) on the store, then assemble the payload.

### Method
- One read pass per call: `row_states` (new), `pending_overdue` (new), `created_since` (new), `lock_wait_ms` (new), `wal_size_bytes` (new) on the view object; each is one `SELECT` or a `stat` of the `-wal` file.
- Threshold blocks are computed only when the config value is not `None`: `max_dedup_rows` (new) against the total row count, `max_dedup_growth_per_hour` (new) against the growth count, `max_dedup_wal_mb` (new) against the WAL size in MB.

### Details
- Returned JSON-safe keys: `schema_version` (new), `db_path`, `generated_epoch` (new), `row_states` (new) (per-status counts from `SELECT status, COUNT(*)`), `pending_overdue` (new) (`pending` rows with `lease_expires_epoch < now`), `growth_rows_per_hour` (new) (`created_epoch >= now - 3600`), `wal_size_bytes` (new), `lock_wait_ms` (new), `legal_hold_states` (new) (the configured held states), and `held_past_retention` (new) (held-state rows past the retention cutoff, so held rows read as held, not as retained-at-large: AC-3).
- Per-threshold blocks `rows`, `growth`, `wal` each hold `value`, `threshold`, `status`, where `status` is `ok` below the warning fraction, `warning` at or above it, and `fail` at or above the fail-closed threshold; when a threshold is unset its block is omitted entirely.
- `lock_wait_ms` (new) is the elapsed milliseconds to acquire the store lock and run the reads under `DEDUP_READ_TIMEOUT_SECONDS` (new); a deadline miss sets the lock status instead of raising.
- Evidence for the read pattern: `get_execution()` in `scripts/shared/mcp_dedup_ledger.py` (line 446) shows the `self._lock` plus `self._conn.execute` `SELECT` shape this module must follow.

### Companion test files
- `tests/shared/test_mcp_dedup_metrics.py` (new)
  - Procedure: pytest unit tests mirroring the fixture pattern of `tests/shared/test_mcp_dedup.py` (store under `tmp_path`, opened through `open_dedup_store` or `DedupStore`, rows in several states), asserting every documented field of `collect_dedup_metrics` (new), that absent thresholds produce no status block, that a breached threshold produces `warning` or `fail`, and that the read is read-only by comparing row counts and row content before and after the call.
  - Validation: `uv run pytest tests/shared/test_mcp_dedup_metrics.py`

## Compatibility considerations
- No existing caller: this is a new module, so nothing currently imports it until rows 06 and 09 land.
- `tests/shared/test_mcp_dedup.py::TestTtlPurge` pins the current purge behaviour and is untouched by this row; `TestDedupSectionValidation` pins the current key validation, which row 08 must keep passing for configs that carry none of the optional keys.

## Security considerations
- The payload exposes the store path and counts only — no `snapshot_json`, `result_json`, key values, or owner ids.
- The read path issues no write, so it cannot mutate the store or extend a lease.

## Rollback considerations
- Revert the commit: a new file with no other importer, so reverting leaves the store and the health payload exactly as before.

## Validation plan
- `uv run pytest tests/shared/test_mcp_dedup_metrics.py` (unit, expect Pass, read-only).
- `uv run python tools/run_validation_gates.py` for the diff, plus the full sequence in `rules/toolchain.md`.

## Completion criteria
- The function returns every documented key for a store holding rows in each state, JSON-serializable without extra conversion.
- Threshold blocks appear only when the config carries the matching key, and a breach changes only the reported status.
- The before/after comparison in the companion test shows the read issued no write.

## Out of Scope
- Threshold or hold key definitions and their validation (row 08), the facade re-export (row 06), health-handler wiring (rows 09-17), and the retention matrix documents (rows 1-4).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement `scripts/shared/mcp_dedup_metrics.py` (new) per Procedure/Method/Details | Pending | — | — | |
| 2 | Add `tests/shared/test_mcp_dedup_metrics.py` (new) per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (read-only metrics module reporting store state, growth, WAL size, lock wait, lease health, and threshold status), REQ-008 (keep the metrics path free of writes, migrations, and new services)
- **Source issue**: issues/20261120-115844_mcpdl005_retention-capacity-monitoring.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-120131_mcpdl005_retention-capacity-monitoring.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-144326
- **Related target files**: `scripts/shared/mcp_dedup_metrics.py`, `tests/shared/test_mcp_dedup_metrics.py`
