## Goal
Update `RagMaintenanceService.recover()` to populate `DbRecoverResult`'s new
logical-verification field from `RecoveryResult`'s new logical field (REQ-005).

## Scope
- In scope: `recover()` (lines 56-63) only — thread the new field through the
  existing `DbRecoverResult(...)` construction.
- Out of scope: `consistency()` (lines 46-54, a separate, unrelated existing feature
  using `RagConsistencyResult`, not touched by this Plan), `rebuild_fts()`,
  `rebuild_vec()`, `reconcile_url()`, `stats_rag()` — none read or construct
  `RecoveryResult`/`DbRecoverResult`.

## Assumptions
- `scripts/db/models.py`'s `RecoveryResult` gets a new field named `logical_ok: bool |
  None = None` (per seq 02's implementation procedure, already written) and
  `scripts/agent/services/models.py`'s `DbRecoverResult` gets an analogously-named
  new field (seq 04's own procedure document was empty/unwritten as of this row's
  authoring — if seq 04 lands with a different field name than `logical_ok`, update
  this row's Method/Procedure step 2 to match the actual name rather than
  implementing against a stale assumption).
- `recover_corruption(backup_path)` (called at line 58) defaults `target="rag"`,
  confirmed via direct read of `scripts/db/recovery.py:167-172` — this method already
  exercises the RAG domain path with no change needed to this call itself.

## Design decisions
- Copy the field directly (`result.logical_ok` → `DbRecoverResult(...,
  logical_ok=result.logical_ok)`), matching the existing one-to-one field-copy pattern
  already used for `integrity_ok`/`recovered`/`detail` in this same method — no
  transformation or interpretation needed, since both DTOs represent the same concept
  at different layers (`db`-layer `RecoveryResult` vs. `agent.services`-layer
  `DbRecoverResult`).

## Alternatives considered
- Compute `logical_ok` independently in this method by calling
  `check_rag_consistency()` a second time: rejected — `recover_corruption()`
  already runs the full recovery+verification sequence (seq 01) and returns the
  logical outcome on `RecoveryResult`; recomputing it here would duplicate a
  read against a database that may have just been restored, wasting the same
  read work seq 01 already performed.

## Implementation
### Target file
`scripts/agent/services/rag_maintenance_service.py`

### Procedure
1. Re-confirm `recover()`'s current line range (this cycle: lines 56-63) and its
   exact body before editing:
   ```python
   def recover(self, backup_path: str | None) -> DbRecoverResult:
       """Run integrity check; restore from backup_path if corruption found."""
       result = recover_corruption(backup_path)
       return DbRecoverResult(
           integrity_ok=result.success,
           recovered=result.action == "restored",
           detail=result.detail or "",
       )
   ```
2. Add the new field to the `DbRecoverResult(...)` construction, copying from
   `result`'s corresponding new field (per seq 01/02's naming — this cycle's
   assumption: `logical_ok=result.logical_ok`).
3. No change to the method's signature, docstring intent, or the
   `recover_corruption(backup_path)` call itself.

### Method
Confirmed this cycle (2026-09-06) via direct read: `recover()` (lines 56-63) is a
5-line pass-through — call `recover_corruption(backup_path)`, then construct
`DbRecoverResult` from 3 of `RecoveryResult`'s 4 existing fields (`success`, `action`,
`detail`; `dry_run` is not currently forwarded). `consistency()` (lines 46-54)
confirmed to use a separate, unrelated `RagConsistencyResult`/`check_rag_consistency()`
path — not modified by this row.

### Details
No behavior change to `integrity_ok`/`recovered`/`detail` — this row only adds one
new field to the existing construction, additive per seq 02/04's dataclass field
addition (default value keeps this construction valid even before this row's edit
lands, could technically be implemented in any order relative to seq 04, but the new
field would read as `None`/default until this row populates it).

## Compatibility considerations
`recover()`'s public signature (`backup_path: str | None) -> DbRecoverResult`) is
unchanged — only an additional field is populated on the return value, additive per
seq 04's DTO change.

## Security considerations
N/A: this row copies an already-computed boolean/summary field; it does not itself
construct any new log or detail string containing row content.

## Rollback considerations
Revert via `git checkout` on this file alone if seq 04's field shape changes
incompatibly — low risk, single-method, 1-line addition.

## Validation plan
- No dedicated unit test file exists for this method (confirmed via `rg` — Plan's own
  Repository Evidence column already notes this); covered indirectly via
  `tests/db/test_db_recovery.py`'s fault-injection cases exercising
  `recover_corruption(target="rag")` (seq 01/08) and manual/service-level review per
  the Plan's Testing Expectations.
- `uv run mypy scripts/agent/services/rag_maintenance_service.py`.

## Completion criteria
- `recover()`'s `DbRecoverResult(...)` construction includes the new
  logical-verification field, copied from `RecoveryResult`'s corresponding field.
- `consistency()` and all other methods in this file remain unchanged.

## Out of scope
- `scripts/db/recovery.py`'s `RecoveryResult` field itself — tracked in seq 01/02.
- `scripts/agent/services/models.py`'s `DbRecoverResult` field itself — tracked in
  seq 04.
- `scripts/agent/services/db_maintenance_service.py`'s `recover_session()` (the
  Session-domain equivalent) — tracked in seq 06.

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
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: scripts/agent/services/rag_maintenance_service.py
