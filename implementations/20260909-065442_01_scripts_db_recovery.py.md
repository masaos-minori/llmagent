## Goal

Move the `workflow`/`eventbus` domain-policy rejection (`action="no_recovery_allowed"`) to the top of `recover_corruption()` before `_run_integrity_check()` is called, preventing unintended database access on protected domains when they are healthy.

## Scope

In scope: reordering the control flow in `recover_corruption()` so that the workflow/eventbus domain-policy check occurs immediately after the existing `unsupported_target` check (line ~329), before the `_run_integrity_check(db_path, target)` call (line 332). Out of scope: changing the domain recovery policy itself; changing the `unsupported_target` handling; adding new `action` values; modifying documentation under `docs/*.md`.

## Assumptions

- The `action="no_recovery_allowed"` value and detail message wording are correct as-is and need no change — only positional change in control flow.
- The `unsupported_target` check's existing position and behavior is correct and should remain unchanged.
- No existing caller of `recover_corruption(target="workflow"/"eventbus", dry_run=True)` depends on the current post-integrity-check rejection point's behavior for dry-run mode.

## Design decisions

The relocated check returns the same `action="no_recovery_allowed"` response regardless of integrity result, so CORRUPTION-path behavior is improved (now rejected before integrity check rather than after), not degraded. The change is symmetric between workflow and eventbus — both are treated identically.

## Alternatives considered

- Adding a new `action` value for pre-integrity rejection — rejected: Plan explicitly states "Keep `action` values as-is".
- Modifying `_run_integrity_check()` to reject workflow/eventbus internally — rejected: would conflate integrity checking with domain policy enforcement; domain policy belongs at the entry point.

## Implementation
### Target file
`scripts/db/recovery.py`

### Procedure
1. Move the `if target in ("workflow", "eventbus")` block from lines 367-375 to immediately after the `unsupported_target` check (after line 329), before `_run_integrity_check(db_path, target)` at line 332.
2. Verify the relocated check handles both HEALTHY and CORRUPTION paths correctly — the function now returns early for workflow/eventbus regardless of integrity result.
3. Verify `dry_run` mode also rejects workflow/eventbus before any database access — the relocated check runs before `_run_integrity_check()` so dry_run callers get the same rejection.

### Method
```python
def recover_corruption(
    backup_path: str | Path | None = None,
    *,
    target: str = "rag",
    dry_run: bool = False,
) -> RecoveryResult:
    db_cfg = build_db_config()
    target_db_path = getattr(db_cfg, f"{target}_db_path", None)
    if target_db_path is None:
        return RecoveryResult(
            success=False,
            action="unsupported_target",
            detail=f"unsupported target: {target!r}",
            dry_run=dry_run,
        )
    
    # Domain policy check — moved here, before _run_integrity_check()
    if target in ("workflow", "eventbus"):
        return RecoveryResult(
            success=False,
            action="no_recovery_allowed",
            detail=f"Automatic recovery is prohibited for {target}. Manual intervention required.",
            dry_run=dry_run,
        )
    
    db_path = Path(target_db_path)
    condition, detail = _run_integrity_check(db_path, target)
    # ... rest of function unchanged
```

### Details
- The relocation moves the workflow/eventbus check from line 368 to immediately after line 329 (the unsupported_target guard).
- The check returns `RecoveryResult(success=False, action="no_recovery_allowed", ...)` — identical to the original but now executes before any database access.
- Both HEALTHY and CORRUPTION branches are covered by this single early return — no additional logic needed.
- The `dry_run` parameter is passed through unchanged — it was already included in the original return.

## Compatibility considerations

N/A: `recover_corruption()`'s public API signature remains unchanged. The `action="no_recovery_allowed"` value and its detail message are preserved exactly. Callers expecting this action value will receive it earlier in the control flow, which is strictly better (no database access before rejection).

## Security considerations

N/A: no credential access, network operations, or filesystem writes introduced. The change only affects control flow ordering within an existing security boundary.

## Rollback considerations

Revert is a single-file change: move the `if target in ("workflow", "eventbus")` block back to its original position (lines 367-375). The original code serves as rollback-safe baseline since it was the previous implementation.

## Validation plan

- Unit: verify `recover_corruption(target="workflow")` returns `action="no_recovery_allowed"` without calling `_run_integrity_check()` — `uv run pytest tests/db/test_db_recovery.py::test_recover_corrupt_workflow_prohibited -v`.
- Unit: verify `recover_corruption(target="eventbus")` returns `action="no_recovery_allowed"` without calling `_run_integrity_check()` — `uv run pytest tests/db/test_db_recovery.py::test_recover_eventbus_uses_correct_db_path -v`.
- Regression: existing `recover_corruption()` tests still pass — `uv run pytest tests/db/test_db_recovery.py -v`.

## Completion criteria

- `recover_corruption(target="workflow")`/`"eventbus"` returns `action="no_recovery_allowed"` without calling `_run_integrity_check()` for both healthy and corrupt underlying databases (REQ-001, REQ-002).
- `_vacuum_db()` is never called for `target="workflow"`/`"eventbus"`, regardless of the underlying database's actual state (REQ-003).
- `dry_run` mode also rejects workflow/eventbus before any database access (REQ-006).

## Out of scope

Changing the domain recovery policy itself (workflow/eventbus remain prohibited from automatic recovery); changing the `unsupported_target` handling; adding new `action` values; modifying documentation under `docs/*.md`; implementing operator-runbook changes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Move workflow/eventbus domain-policy check to top of recover_corruption() | Pending | — | — | |
| 2 | Verify relocated check works for all paths | Pending | — | — | |
| 3 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-006
- **Source issue**: issues/20260907-124049_h0706_recovery_target_check_before_vacuum.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-075615_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-065442
- **Related target files**: scripts/db/recovery.py
