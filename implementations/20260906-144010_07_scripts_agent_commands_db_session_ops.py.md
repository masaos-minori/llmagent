## Goal
Update `DbSessionOps.recover()`'s CLI output to print the logical-verification result
distinctly from the physical `integrity_ok` result (REQ-006, AC-2).

## Scope
- In scope: `DbSessionOps.recover()` (`scripts/agent/commands/db_session_ops.py:60-66`)
  only — add a second, distinct output line for the logical-verification outcome.
- Out of scope: `health()`, `checkpoint()`, `vacuum()`, `purge()` (other methods in the
  same class, unrelated to this Plan); `DbMaintenanceService.recover_session()` itself
  (tracked in seq 06); `DbRecoverResult`'s field definition (tracked in seq 04).

## Assumptions
- `DbRecoverResult` gains `logical_ok: bool | None` (`None` = no logical check
  applicable/run) per seq 04's implementation (`implementations/20260906-144010_04_scripts_agent_services_models.py.md`)
  — this row's Procedure references that exact field name; if seq 04's final field
  name differs at implementation time, substitute it here without changing this row's
  intent.
- `logical_ok is None` (e.g. a pre-existing failure path that never reached the new
  logical-verification stage) should print a distinct "not applicable"/omitted line
  rather than a misleading `True`/`False` — `recover()`'s current code has no such
  three-state branch today (only `if result.integrity_ok`), so this is new branching
  logic, not a one-line edit.

## Design decisions
- Print the logical result as a second `self._out.write_*` line, not by concatenating
  it into the existing single message — keeps the two outcomes visually and
  programmatically distinct at the CLI layer, matching AC-2's "distinguishable at
  every layer" requirement literally at the final layer.
- Use `write_no_data` (already imported/used for the physical-failure branch) for a
  logical failure too, and `write_success`/`write_kv` (already used elsewhere in this
  same class, e.g. `health()`) for a logical pass — no new `OutputPort` method needed.

## Alternatives considered
- Fold the logical result into the existing single message string (e.g. `f"Recovery
  succeeded: {result.detail}, logical={result.logical_ok} [Session]"`): rejected —
  AC-2 requires distinguishability, and a single concatenated string is harder for a
  human operator to parse at a glance than two separate lines, especially once
  `logical_ok is None` (not applicable) is added as a third state.

## Implementation
### Target file
`scripts/agent/commands/db_session_ops.py`

### Procedure
1. Re-confirm `recover()`'s current body (this cycle: lines 60-66, branches only on
   `result.integrity_ok`) before editing.
2. After the existing `if result.integrity_ok: ... else: ...` block (or restructured
   to accommodate it), add a second branch on `result.logical_ok`:
   - `True` → `self._out.write_success(f"Logical verification passed [Session]")` (or
     fold a short summary from `result.logical_detail` if seq 04 adds that field).
   - `False` → `self._out.write_no_data(f"Logical verification failed:
     {result.logical_detail or 'see logs'} [Session]")`.
   - `None` → no additional line (logical check did not run — e.g. the physical check
     already failed, so the stage in `_restore_from_backup()` was never reached).
3. Do not change the existing `integrity_ok` branch's messages or the `[Session]`
   suffix convention already used throughout this file.

### Method
Confirmed this cycle (2026-09-06) via direct read: `recover()` (lines 60-66)
currently reads exactly:
```
def recover(self, backup_path: str | None) -> None:
    """Run integrity check on session.sqlite; restore from backup_path if corruption found."""
    result = DbMaintenanceService().recover_session(backup_path)
    if result.integrity_ok:
        self._out.write_success(f"Recovery succeeded: {result.detail} [Session]")
    else:
        self._out.write_no_data(f"Recovery failed: {result.detail} [Session]")
```
— matches the Plan's citation exactly, no line-number or content drift.
`DbRecoverResult` (`scripts/agent/services/models.py:192-197`) confirmed today to have
only `integrity_ok: bool`, `recovered: bool`, `detail: str` — the `logical_ok`/
`logical_detail` field(s) this row references do not exist yet; this row depends on
seq 04 landing first (or in the same implementation pass).

### Details
No change to `DbMaintenanceService.recover_session()`'s call signature or `recover()`'s
own method signature — purely additive output-formatting logic inside the existing
method body.

## Compatibility considerations
`recover()` has no return value and is not called by any other production code
(confirmed via `rg "\.recover(" scripts/` limited to this cycle's investigation scope —
re-confirm at implementation time) — output-only change, no API surface affected.

## Security considerations
Per REQ-010/AC-7, `result.logical_detail` (if seq 04 adds it) must already carry only
counts/category labels (enforced upstream at seq 01/03) — this row must not
additionally format in any row content; pass the string through as-is.

## Rollback considerations
Revert via `git checkout` on this file alone if manual `/session recover` verification
finds the new output confusing or malformed — no other file depends on this method's
exact print format.

## Validation plan
- Manual CLI verification: run `/session recover <backup_path>` against a
  known-healthy backup and against a backup engineered to fail Session logical
  verification (per seq 10's fault-injection fixtures); confirm both output lines
  appear correctly and distinctly.
- `uv run mypy scripts/agent/commands/db_session_ops.py` — confirm `result.logical_ok`
  type-checks against `DbRecoverResult`'s new field.
- `uv run ruff check scripts/agent/commands/db_session_ops.py`.

## Completion criteria
- `recover()` prints a second, distinct line for the logical-verification outcome
  whenever `result.logical_ok` is not `None`.
- The existing physical `integrity_ok` branch's messages are unchanged.
- Manual verification confirms both physical and logical outcomes are visible and
  distinguishable in CLI output.

## Out of scope
- `DbRecoverResult`'s field definition — tracked in seq 04.
- `DbMaintenanceService.recover_session()` — tracked in seq 06.
- Any other method in `DbSessionOps` (`health`, `checkpoint`, `vacuum`, `purge`).

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260903-110305_h0707_add-rag-session-recovery-verification.md
- **Source plan**: plans/20260905-163508_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260906-144010
- **Related target files**: scripts/agent/commands/db_session_ops.py
