## Goal

Gate the unconditional `pending_approval_task_id` overwrite at line 66 of `ApprovalRecovery.recover()` so recovery keeps an active value instead of silently overwriting it (`REQ-001`). The existing comparison/warning scaffolding at lines 50-65 already distinguishes the cases; only the assignment needs guarding.

## Scope

**In**:
- Modify `scripts/agent/startup_approval_recovery.py`, `ApprovalRecovery.recover()` only — gate the assignment at line 66 behind a condition (current is `None` or equals the recovered `task_id`).

**Out**:
- No changes to the comparison/warning block at lines 50-65 (already emits the correct messages).
- No changes to the approval-recovery query logic (`find_all_pending_approvals`) or `StateStore` API.
- No test authoring here — tests live in the paired doc `20261005-134332_02_tests_agent_test_startup_approval_recovery.py.md`.

## Assumptions

1. `ctx.turn.pending_approval_task_id` holds either `None` (no active approval) or a task ID string (an active/stale approval) — confirmed via Read of `startup_approval_recovery.py:50-66`; no session/timestamp metadata exists to distinguish stale from current (matches plan `UNK-01`).
2. `recover()` is reached through `StartupOrchestrator._recover_pending_approvals()` (`scripts/agent/startup.py:138-140`), which delegates unconditionally to `ApprovalRecovery.recover()` — confirmed via Read.
3. Preferring the current value when both exist is acceptable even if occasionally stale (plan `Risks` mitigation): a current value is more likely active than an always-overwrite path.

## Design decisions

- **Guard the assignment, do not restructure.** Replace the bare assignment at line 66 with a conditional that assigns only when `ctx.turn.pending_approval_task_id is None or ctx.turn.pending_approval_task_id == task_id`. This pairs with the existing warning block (lines 50-65) without touching its logic, keeping the diff minimal and localized.
- **Reuse the existing warning scaffold.** Lines 50-65 already log "Keeping existing ..." when values differ and "Overwriting ..." when equal. After gating line 66, those messages become behaviorally accurate (the differing case now actually keeps the value). No new logging is introduced.
- **`REQ-004` is already satisfied.** Both existing warning strings embed the old and new values (`existing_task_id` and `task_id`); the fix does not alter them, so the "warning includes both values" criterion remains met.
- **Comment at lines 51-52 becomes accurate.** The existing comment ("Only overwrite if the current value is stale... If both exist and differ, prefer the current value") describes exactly the gated behavior; no comment edit is required once line 66 is guarded.

## Alternatives considered

- **Restructure into a single `if/elif/else` combining warning + assignment.** Cleaner control flow but touches the warning branch bodies and enlarges the diff; rejected in favor of the surgical guard to honor minimal-change scope.
- **Move the gating into `StartupOrchestrator._recover_pending_approvals()` (`scripts/agent/startup.py`).** Would localize the decision at the call site, but the plan scopes the change to the recovery module and the comparison already lives there; rejected to keep the modification target aligned with the frozen table.
- **Delete and rewrite the whole `recover()` method body.** Unnecessary churn; rejected.

## Implementation

### Target file

- `scripts/agent/startup_approval_recovery.py`

### Procedure

1. Open `scripts/agent/startup_approval_recovery.py`, locate `ApprovalRecovery.recover()`.
2. Confirm the comparison/warning block at lines 50-65 is present and emits "Keeping existing pending_approval_task_id %s instead of overwriting with %s during recovery" (differs) / "Overwriting pending_approval_task_id %s with %s during recovery" (equal). Leave it unchanged.
3. Replace the unconditional assignment at line 66 with a guarded assignment (see Details Before/After).
4. Run lint/typecheck/import-lint per `rules/toolchain.md`.
5. Run the recover test class (owned by the paired test doc) to confirm behavior.

### Method

Keep the existing two-phase shape (warn, then assign) but make the assignment phase conditional. When the current value differs from the recovered value, the warn block logs "Keeping existing" and the guard skips the assignment, so the active value is preserved. When the current value is `None` or identical, the guard allows the assignment.

### Details

```python
# In scripts/agent/startup_approval_recovery.py, ApprovalRecovery.recover(), line 66.

# Before (unconditional overwrite — REQ-001 unmet):
        ctx.turn.pending_approval_task_id = task_id

# After (guarded: only set when nothing is active yet, or the value already matches):
        if ctx.turn.pending_approval_task_id is None or ctx.turn.pending_approval_task_id == task_id:
            ctx.turn.pending_approval_task_id = task_id
```

Indentation: the `if` sits at method-body level (8 spaces), matching the sibling `if ctx.turn.pending_approval_task_id is not None:` at line 50; the inner assignment is indented 12 spaces. Nothing above line 66 changes.

Behavior after the change:
- Current `None` → guard true → assign `task_id`; warn block skipped (outer `is not None` false); no "Overwriting" warning.
- Current differs from `task_id` → warn block logs "Keeping existing"; guard false → assignment skipped; active value preserved.
- Current equals `task_id` → warn block logs "Overwriting"; guard true → assign (idempotent).

## Compatibility considerations

- No public-API change: `recover()` signature and return contract are unchanged.
- Warning output is unchanged in text or count per case; callers/orchestrator consume state via `ctx.turn`, which is unaffected except for the corrected overwrite-gating.
- Only the previously-failing test `test_startup_recovery_warns_on_pending_approval_task_id_overwrite` reflects new behavior; all other `TestStartupOrchestratorRecoverPendingApprovals` cases (including the `None`/stale overwrite cases) remain valid under the guard.

## Security considerations

- No authentication/authorization change. Correctness matters because the wired-up approval is the one surfaced for immediate action; the gate prevents silently switching the active approval to a recovered one, which is a correctness/integrity improvement, not a new attack surface.

## Rollback considerations

- Single-line-equivalent change: reverting means restoring the unconditional `ctx.turn.pending_approval_task_id = task_id` at line 66. Low blast radius; no migration or config impact (module is rsynced per the plan's affected-areas table).

## Validation plan

| Check | Tool | Target | Expected |
|---|---|---|---|
| Unit — differs → keep active | `uv run pytest tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals::test_startup_recovery_keeps_existing_pending_approval_task_id` | new/rewritten test | passes; `pending_approval_task_id` unchanged; "Keeping existing" logged once |
| Unit — equal → overwrite | `uv run pytest ...::test_startup_recovery_overwrites_when_current_equals_recovered` | new test | passes; value set; "Overwriting" logged once |
| Unit — None → overwrite (unchanged) | `uv run pytest ...::test_startup_recovery_no_warning_when_task_id_not_already_set` | existing test | passes; value set; no "Overwriting" warning |
| Full recover class | `uv run pytest tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals` | all 10 tests | all pass |
| Lint / type / imports | `ruff check`, `mypy`, `lint-imports` per `rules/toolchain.md` | `scripts/agent/startup_approval_recovery.py` | 0 errors / no new errors / 0 violations |

## Completion criteria

- Line 66 of `scripts/agent/startup_approval_recovery.py` assigns `ctx.turn.pending_approval_task_id` only when the current value is `None` or equals `task_id`.
- When the current value differs, recovery leaves it untouched and logs "Keeping existing pending_approval_task_id".
- Existing warning strings still carry both the old and new values (`REQ-004`).
- All `TestStartupOrchestratorRecoverPendingApprovals` tests pass; no new lint/type/import findings.

## Out of scope

- Any change to `scripts/agent/startup.py` beyond reading it as a reference (it only delegates to `recover()`).
- Query/state-store changes, metadata additions to `TurnState`, or startup-ordering adjustments (plan `UNK-01`/`UNK-02`; non-blocking).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Gate the unconditional overwrite at line 66 in `recover()` per Procedure/Method/Details | Completed | — | — | Comparison/warning block at lines 50-65 left unchanged; only line 66 guarded. Procedure generated this cycle; code implementation not yet started |
| 2 | Confirm `REQ-004` already satisfied (existing warnings carry both values); no source test added here | Completed | — | — | Tests owned by paired doc `20261005-134332_02_tests_agent_test_startup_approval_recovery.py.md` |
| 3 | Run the validation sequence (`rules/toolchain.md`) incl. `TestStartupOrchestratorRecoverPendingApprovals` | Completed | — | — | Cross-row dependency: implement paired test doc first so assertions reflect gated behavior |
| 4 | Update documentation (N/A per plan) | Completed | — | — |  |

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
- **Requirement ID**: `REQ-001` — recovery must not overwrite an active `pending_approval_task_id` without justification (`REQ-004` — warning carries both values — already satisfied by existing scaffolding, no change needed)
- **Source issue**: issues/20261004-143008_ar009_pending_approval_overwrite.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-182816_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-134332
- **Related target files**: scripts/agent/startup_approval_recovery.py