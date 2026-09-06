## Goal
Extend `DbRecoverResult` with a field surfacing the logical-verification outcome
REQ-001 adds to `scripts/db/models.py`'s `RecoveryResult`, so the CLI-facing DTO can
express "physically fine but logically broken" distinctly from a physical failure
(REQ-005, AC-2).

## Scope
- In scope: `DbRecoverResult` (currently `integrity_ok: bool`, `recovered: bool`,
  `detail: str`) — add one additive field mirroring the field seq 02 adds to
  `RecoveryResult` (e.g. `logical_ok: bool | None = None`).
- Out of scope: `integrity_ok`/`recovered`/`detail` — unchanged in meaning;
  `RagConsistencyResult` (same file, lines 200-206) — an unrelated existing type used
  only by `RagMaintenanceService.consistency()`, not by `recover()`; populating the
  new field — tracked in seq 05/06 (`rag_maintenance_service.py`,
  `db_maintenance_service.py`); printing it — tracked in seq 07
  (`db_session_ops.py`).

## Assumptions
- The field name/shape mirrors whatever seq 02 (`scripts/db/models.py`'s
  `RecoveryResult` extension) actually lands as — if seq 02 adds
  `logical_ok: bool | None` (+ optionally `logical_detail: str | None`), this row adds
  the same shape to `DbRecoverResult` for consistency across the two DTOs; if seq 02's
  implementation differs from its own document's Assumptions, mirror the landed shape
  here instead of this document's default.

## Design decisions
- Add a plain additive field to the existing flat, frozen dataclass rather than a
  nested type — matches seq 02's own reasoning exactly (`RecoveryResult` and
  `DbRecoverResult` are both flat 3-4 field DTOs today; a 4th/5th field keeps every
  existing keyword-style construction site working unchanged).
- Default the new field to `None` (meaning "no logical check applicable/run") so the
  two existing `DbRecoverResult(...)` construction sites
  (`rag_maintenance_service.py:59`, `db_maintenance_service.py:79`) do not require
  changes to compile — those sites are updated to actually populate the field under
  seq 05/06, but this row's own change must not force that update to land atomically.

## Alternatives considered
- Reuse `RagConsistencyResult` (already defined in this same file, lines 200-206) as
  the vehicle for the new field: rejected — confirmed via `rg` that
  `RagConsistencyResult` is constructed only by `RagMaintenanceService.consistency()`
  (an unrelated, pre-existing feature), not by `recover()`; conflating the two would
  couple an unrelated method's return type to this Plan's recovery-result change.

## Implementation
### Target file
`scripts/agent/services/models.py`

### Procedure
1. Re-confirm `DbRecoverResult`'s current field list and line numbers (this cycle:
   class at line 192, fields `integrity_ok: bool`, `recovered: bool`, `detail: str` at
   lines 195-197) before editing.
2. Add one new field with a default value (e.g. `logical_ok: bool | None = None`),
   appended after the existing three fields — matching seq 02's field name/shape once
   that row lands (see Assumptions).
3. If seq 02 also adds a `logical_detail`-style second field, mirror it here too for
   consistency between the two DTOs, rather than collapsing both into `detail`.

### Method
Confirmed this cycle (2026-09-06) via direct read: `DbRecoverResult`
(`scripts/agent/services/models.py:192-197`) has exactly the 3 fields the Plan cites,
no drift. Confirmed via `rg "DbRecoverResult("` that both existing construction sites
(`rag_maintenance_service.py:59`, `db_maintenance_service.py:79`) use keyword-style
construction — an appended field with a default value requires no change to either
site for this row alone to compile.

### Details
This is an additive, backward-compatible dataclass change with no behavior change on
its own — the new field's value stays `None` until seq 05/06 populate it.

## Compatibility considerations
Additive-only: `integrity_ok`/`recovered`/`detail` unchanged. Re-confirm via `rg
"DbRecoverResult("` before finalizing that no caller constructs it positionally
(mitigated by appending the new field at the end with a default).

## Security considerations
Any new detail-carrying field must follow the same no-content-leakage constraint as
`RecoveryResult`'s own new field (REQ-010) — counts/category labels only, never
row content.

## Rollback considerations
Revert via `git checkout` on this file alone if seq 05/06's population logic finds the
field shape insufficient — low risk, additive field with a default value.

## Validation plan
- `uv run pytest tests/integration/test_session_recovery.py -v` (seq 10, exercises
  `DbRecoverResult` construction via `DbMaintenanceService.recover_session()`).
- `uv run mypy scripts/agent/services/models.py`.
- `rg "DbRecoverResult(" scripts/ tests/` — confirm every construction site still
  type-checks with the new optional field.

## Completion criteria
- `DbRecoverResult` has a new field mirroring `RecoveryResult`'s new logical-outcome
  field.
- Both existing `DbRecoverResult(...)` construction sites compile and type-check
  unchanged (field left at its default until seq 05/06 populate it).

## Out of scope
- `scripts/db/models.py`'s `RecoveryResult` — tracked in seq 02.
- Populating the new field in `RagMaintenanceService.recover()` /
  `DbMaintenanceService.recover_session()` — tracked in seq 05/06.
- Printing the new field in CLI output — tracked in seq 07.

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
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: scripts/agent/services/models.py
