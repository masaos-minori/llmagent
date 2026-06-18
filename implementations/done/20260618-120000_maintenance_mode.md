# Implementation: MaintenanceMode / MaintenanceResult for maintenance ops (req 76)

## Goal

Add STRICT/BEST_EFFORT mode to db/maintenance.py mutation operations so callers
can choose between exception propagation (STRICT, default) and structured failure
results (BEST_EFFORT).

## Changes

### `scripts/db/maintenance.py`
- Add `MaintenanceMode(StrEnum)`: STRICT="strict", BEST_EFFORT="best_effort"
- Add `MaintenanceResult(frozen=True)`: success, action, mode, detail, data
- `vacuum_db()`: was `-> None`, now `-> MaintenanceResult`; raises in STRICT, returns failure in BEST_EFFORT
- `purge_old_sessions()`: was `-> PurgeCounts`, now `-> MaintenanceResult`; data={"age_deleted", "count_deleted"}
- `prune_old_memories()`: was `-> int`, now `-> MaintenanceResult`; data={"deleted"}
- Remove unused `PurgeCounts` import

### `tests/test_db_maintenance.py`
- Add imports: `MaintenanceMode`, `MaintenanceResult`, `prune_old_memories`
- Update existing assertions: `result.age_deleted` → `result.data["age_deleted"]` etc.
- Update `test_vacuum_db_delegates`: verify `result.success is True`
- Add `TestMaintenanceMode` class: 7 tests covering STRICT/BEST_EFFORT for all 3 functions

### `docs/06_shared_05_db_api_and_operations.md`
- Update §7 function signature table
- Add `MaintenanceMode` / `MaintenanceResult` reference with usage example
- Update error handling table and AI Reference Guide
