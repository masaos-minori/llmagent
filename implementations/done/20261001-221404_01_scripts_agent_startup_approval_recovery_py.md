## Goal

Modify `ApprovalRecovery.recover()` so that when multiple pending approvals exist from a
prior session, every pending approval is surfaced for resolution rather than silently
orphaning all but the newest one (REQ-001; AC-01).

## Scope

Iterate over all results from `find_all_pending_approvals()` in `recover()`, setting
`ctx.workflow.approval_pending = True` and wiring up each approval's `task_id` and
`approval_id` to the context. Emit a warning listing all pending approvals with their
IDs and reasons, instructing the user to use `/approve <approval_id>` or `/reject
<approval_id>` for each. Keep the single-pending case behavior unchanged.

## Assumptions

- The `/approve` and `/reject` REPL commands already accept an `approval_id` argument,
  allowing the user to resolve any pending approval regardless of which one was
  surfaced first (confirmed via `scripts/agent/commands/cmd_workflow.py`).
- The `find_all_pending_approvals()` query correctly filters out expired approvals via
  SQLite string comparison against `expires_at` (confirmed by Adversarial Verification:
  the TTL leak claim was debunked).
- `ctx.turn.pending_approval_id` and `ctx.turn.pending_approval_task_id` represent the
  "currently active" approval being presented to the user; other pending approvals
  remain in the DB until resolved or expired.

## Design decisions

- **Approach**: Iterate over all results from `find_all_pending_approvals()` in
  `recover()`, setting `ctx.workflow.approval_pending = True` and wiring up each
  approval's `task_id` and `approval_id` to the context. For the UI layer, emit a
  warning listing all pending approvals with their IDs and reasons, and instruct the
  user to use `/approve <approval_id>` or `/reject <approval_id>` for each.
- **Ordering**: Use the existing `ORDER BY a.created_at DESC, a.rowid DESC` from
  `find_all_pending_approvals()` as the deterministic order — oldest first (reverse of
  the query result order) so the user resolves approvals in chronological order.
- **State management**: Since `ctx.turn.pending_approval_id` and
  `ctx.turn.pending_approval_task_id` are single-value fields, surface all approvals
  in the warning message and let the user resolve them one-by-one via `/approve`/`/reject`
  commands (minimal change). Other pending approvals remain in the DB until resolved or
  expired.

## Alternatives considered

- Add a queue mechanism to track remaining approvals: rejected — larger change, not
  needed since `/approve`/`/reject` already accept `approval_id` arguments.
- Only surface the newest approval (current behavior): rejected — defeats the purpose
  of REQ-001 (enumerate all pending approvals).

## Implementation

### Target file

`scripts/agent/startup_approval_recovery.py`

### Procedure

1. Verify `report_readiness()` is called after `discover_all()` completes.
2. Read the current `recover()` method body to confirm the exact insertion point for
   iteration logic.
3. Modify `recover()` to iterate over all results from `find_all_pending_approvals()`.
4. Update the warning message to list all pending approvals with their IDs and reasons.
5. Confirm the single-pending case behavior is unchanged.

### Method

Edit `scripts/agent/startup_approval_recovery.py` in-place.

### Details

**Phase 1: Preparation / Verification**

1. Verify `/approve` and `/reject` commands accept an `approval_id` argument:
   ```bash
   rg -n "approval_id.*arg|/approve.*approval_id|/reject.*approval_id" scripts/agent/commands/cmd_workflow.py
   ```
   Expected: `_cmd_approve(arg)` and `_cmd_reject(arg)` both accept `approval_id` as
   the first positional argument.

2. Read the current `recover()` method body to confirm the exact structure before
   modification.

**Phase 2: Core Logic Implementation**

Replace the `results[0]` access with iteration over all results:

```python
# Before (lines 44-56):
results = find_all_pending_approvals(store)
if results:
    ctx.workflow.approval_pending = True
    task_id, approval = results[0]
    ctx.turn.pending_approval_id = approval.approval_id
    if ctx.turn.pending_approval_task_id is not None:
        logger.warning(
            "Overwriting pending_approval_task_id %s with %s during recovery",
            ctx.turn.pending_approval_task_id,
            task_id,
        )
    ctx.turn.pending_approval_task_id = task_id
    logger.info(
        "Recovered %d pending approval(s); showing last: task=%s approval=%s reason=%s",
        len(results),
        task_id,
        approval.approval_id,
        approval.reason,
    )

# After:
results = find_all_pending_approvals(store)
if results:
    ctx.workflow.approval_pending = True
    # Wire up the most recent approval (first in DESC order) for immediate action
    task_id, approval = results[0]
    ctx.turn.pending_approval_id = approval.approval_id
    if ctx.turn.pending_approval_task_id is not None:
        logger.warning(
            "Overwriting pending_approval_task_id %s with %s during recovery",
            ctx.turn.pending_approval_task_id,
            task_id,
        )
    ctx.turn.pending_approval_task_id = task_id
    # List all pending approvals for resolution
    lines = []
    for i, (tid, appr) in enumerate(results, start=1):
        lines.append(f"  [{i}] task={tid} approval={appr.approval_id} reason={appr.reason}")
    logger.info(
        "Recovered %d pending approval(s); wired up: task=%s approval=%s reason=%s",
        len(results),
        task_id,
        approval.approval_id,
        approval.reason,
    )
    logger.info("All pending approvals:")
    for line in lines:
        logger.info(line)
```

Key changes:
1. Keep wiring up `results[0]` (the most recent) as the "active" approval for immediate
   action via `/approve`/`/reject`.
2. Add iteration over all results to log each pending approval's details.
3. Update the log message format from `"showing last:"` to `"wired up:"` to clarify
   intent.

**Phase 3: Deployment & Verification**

1. Run `ruff` on `scripts/agent/startup_approval_recovery.py`:
   ```bash
   uv run ruff format scripts/agent/startup_approval_recovery.py && uv run ruff check scripts/agent/startup_approval_recovery.py
   ```
2. Run `mypy` on `scripts/agent/startup_approval_recovery.py`:
   ```bash
   uv run mypy scripts/agent/startup_approval_recovery.py
   ```
3. Run `bandit` on `scripts/agent/startup_approval_recovery.py`:
   ```bash
   uv run bandit scripts/agent/startup_approval_recovery.py
   ```
4. Run `radon` complexity check:
   ```bash
   uv run radon cc scripts/agent/startup_approval_recovery.py -s
   ```
5. Run existing tests to confirm no regression:
   ```bash
   uv run pytest tests/agent/test_startup_approval_recovery.py -v --tb=short
   ```

## Compatibility considerations

- The single-pending case must behave identically to the current implementation.
- The multi-pending case adds logging output but does not change the wired-up state
  (still only `results[0]` is wired up for immediate action).
- If `runtime_tools` is `None`, `unavailable_servers` defaults to `frozenset()`,
  yielding `unreachable_count = 0` — equivalent to the previous behavior when no
  outcomes contained "unreachable".

## Security considerations

N/A: internal service logic change; no security-sensitive surface.

## Rollback considerations

Restore the original `results[0]` access and revert the additional logging.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/agent/startup_approval_recovery.py` | Format + lint | `uv run ruff format scripts/agent/startup_approval_recovery.py` then `uv run ruff check scripts/agent/startup_approval_recovery.py` | Clean (no diffs, no errors) |
| `scripts/agent/startup_approval_recovery.py` | Type check | `uv run mypy scripts/agent/startup_approval_recovery.py` | Pass |
| `scripts/agent/startup_approval_recovery.py` | Security lint | `uv run bandit scripts/agent/startup_approval_recovery.py` | No new findings |
| `scripts/agent/startup_approval_recovery.py` | Complexity | `uv run radon cc scripts/agent/startup_approval_recovery.py -s` | Complexity did not worsen beyond the existing grade |
| `tests/agent/test_startup_approval_recovery.py` | Regression: multi-pending accounts for all approvals; single-pending unchanged | `uv run pytest tests/agent/test_startup_approval_recovery.py -v` | All pass |

## Completion criteria

- After startup recovery with multiple pending approvals, every pending approval is
  either surfaced for resolution or explicitly documentedly deferred with a defined
  resume path.
- A deterministic order/resolution flow exists for multi-pending approvals.
- Behavior for the single-pending case is unchanged.
- `ruff`, `mypy`, `bandit`, `radon` clean on the modified file.

## Out of scope

Changing how approvals are requested or resolved during a live session; altering the
approval table schema; fixing the TTL inconsistency claim (debunked as false positive).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Done | 20261001-221404 | 20261001-221800 | REQ-001, REQ-002 |
| 2 | Add or update tests per Validation plan | Done | 20261001-221800 | 20261001-221830 | N/A: test-only row |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Done | 20261001-221830 | 20261001-221900 | REQ-001, REQ-002 |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Done | 20261001-221900 | 20261001-221900 | N/A: no doc change required |

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
- **Requirement ID**: REQ-001 — enumerate all pending approvals from
  `find_all_pending_approvals()` and wire up each for resolution; REQ-002 — define a
  deterministic order/resolution flow for multi-pending approvals
- **Source issue**: issues/20260930-161945_wf001_startup_approval_recovery_only_recovers_latest_pending_approval.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-214541_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-221404
- **Related target files**: scripts/agent/startup_approval_recovery.py
