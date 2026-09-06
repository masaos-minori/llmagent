## Goal
Update `DbMaintenanceService.recover_session()` to populate the new
`DbRecoverResult` logical-verification field from `RecoveryResult`'s new logical
field (REQ-005), so the Session-domain recovery producer surfaces the same
physical/logical distinction the CLI layer (`db_session_ops.py`, seq 07) will render.

## Scope
- In scope: `recover_session()` (`scripts/agent/services/db_maintenance_service.py`,
  confirmed at lines 76-83 this cycle — no drift from the Plan's citation) — add one
  line copying the new `RecoveryResult` field into the `DbRecoverResult` construction.
- Out of scope: `stats()`, `health()`, `checkpoint()`, `vacuum()`, `purge()`,
  `_build_retention_config()` — none touch recovery; not modified by this row.

## Assumptions
- `scripts/db/models.py`'s `RecoveryResult` (seq 02) adds `logical_ok: bool | None =
  None` (and possibly `logical_detail: str | None = None`) — this row's field name
  assumes that naming. If seq 02 lands with different field name(s), update this
  row's one-line change to match at implementation time; the shape of the change
  (copy one new field through) does not otherwise depend on the exact name chosen.
- `scripts/agent/services/models.py`'s `DbRecoverResult` (seq 04) adds a
  correspondingly-named field (e.g. `logical_ok: bool | None = None`) — this row
  populates that field from `raw.logical_ok` (seq 02's field on the `RecoveryResult`
  `recover_corruption()` returns). Seq 04's document was not yet written at the time
  of this row's investigation (2026-09-06); if it lands with a different field name,
  update this row's one-line change to match.

## Design decisions
- Copy the field directly (`logical_ok=raw.logical_ok`), matching this method's
  existing pattern of copying `RecoveryResult` fields onto `DbRecoverResult`
  one-to-one (`integrity_ok=raw.success`, `recovered=raw.action == "restored"`) — no
  additional transformation needed, since both DTOs' logical field is a plain
  `bool | None`.

## Alternatives considered
- Wrap the logical result in a nested object on `DbRecoverResult` instead of a flat
  field: rejected — seq 04 (assumed) mirrors seq 02's flat-field decision (see that
  row's own Design decisions on `RecoveryResult`); this row follows the same DTO for
  consistency across the two layers.

## Implementation
### Target file
`scripts/agent/services/db_maintenance_service.py`

### Procedure
1. Re-confirm `recover_session()`'s current body before editing (this cycle: lines
   76-83, `raw = recover_corruption(backup_path, target="session")` followed by
   `return DbRecoverResult(integrity_ok=raw.success, recovered=raw.action ==
   "restored", detail=raw.detail or "")`).
2. Add the new field to the `DbRecoverResult(...)` construction:
   `logical_ok=raw.logical_ok` (adjust the right-hand-side attribute name to match
   whatever seq 02 actually names the field on `RecoveryResult`, and the
   keyword name to match whatever seq 04 actually names the field on
   `DbRecoverResult`, if either differs from this document's assumption).
3. Do not change `integrity_ok`/`recovered`/`detail`'s existing construction —
   additive only.

### Method
Confirmed this cycle (2026-09-06) via direct read: `recover_session()`
(`scripts/agent/services/db_maintenance_service.py:76-83`) matches the Plan's
citation exactly, no line-number drift. **Adversarial-verification finding
(discrepancy from the Plan, not corrected here per this row's own scope — flagged for
the Plan owner)**: the Plan's Repository Evidence column cites
`tests/integration/test_session_recovery.py` as this row's Related Test, but direct
read of that file plus `rg "recover_session|DbMaintenanceService|recover_corruption"
tests/integration/test_session_recovery.py` found zero matches — that file exercises
`recover_corruption()` directly (`db.recovery`), never through this
`DbMaintenanceService.recover_session()` wrapper. The only other reference to
`recover_session` found repository-wide is
`tests/agent/commands/test_agent_cmd_session.py`, which mocks
`DbMaintenanceService` wholesale (`mock_svc.recover_session.return_value = ...`) —
it verifies `db_session_ops.py`'s CLI-layer branching (seq 07's own test coverage),
never this method's actual body. **This method currently has no test exercising its
real implementation** — a pre-existing gap, not introduced by this row's change.

### Details
No behavior change to `recover_corruption()`'s own logic (seq 01) or to
`stats()`/`health()`/`checkpoint()`/`vacuum()`/`purge()` in this file.

## Compatibility considerations
Additive field on an existing return-value DTO — no signature change to
`recover_session(backup_path: str | None) -> DbRecoverResult`.

## Security considerations
`raw.logical_ok`/`raw.logical_detail` (if present) must already carry only
counts/category labels per seq 01/02's own constraint (REQ-010) — this row does not
introduce a new content-leakage risk, it only forwards an already-sanitized value.

## Rollback considerations
Revert via `git checkout` on this file alone if seq 02/04's field naming changes
after this row lands — low risk, single-line change.

## Validation plan
- Given the testing gap found in Method, add a minimal direct unit test for
  `DbMaintenanceService.recover_session()` (not mocking `recover_corruption()`,
  calling the real method against a fixture DB) as part of seq 08's or seq 10's test
  additions — REQ-008's Session fault-injection tests are the natural home, since they
  already exercise the equivalent `_restore_from_backup()` path; alternatively extend
  `tests/agent/commands/test_agent_cmd_session.py`'s existing mock-based tests to
  additionally assert on the new field being passed through, without removing the
  existing mock-based CLI-branching coverage.
- `uv run mypy scripts/agent/services/db_maintenance_service.py`.
- `uv run pytest tests/agent/commands/test_agent_cmd_session.py -v` — confirm the
  existing mock-based tests still pass unmodified (they mock the whole method, so are
  unaffected by this row's internal change).

## Completion criteria
- `recover_session()` populates the new `DbRecoverResult` field from
  `RecoveryResult`'s new field.
- `integrity_ok`/`recovered`/`detail` construction is unchanged.
- At least one test exercises `recover_session()`'s real body with the new field
  populated (closing the gap found in Method), per Validation plan.

## Out of scope
- `scripts/db/models.py`'s `RecoveryResult` field itself — tracked in seq 02.
- `scripts/agent/services/models.py`'s `DbRecoverResult` field itself — tracked in
  seq 04.
- `RagMaintenanceService.recover()` — tracked in seq 05.
- `db_session_ops.py`'s CLI output — tracked in seq 07.

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
| Method finding | Plan's Repository Evidence cites `tests/integration/test_session_recovery.py` as this row's Related Test, but that file never calls `recover_session()`/`DbMaintenanceService` — no test currently exercises this method's real body. Not fixed by this document alone (test addition deferred to seq 08/10 or a Plan correction). | No | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: scripts/agent/services/db_maintenance_service.py
