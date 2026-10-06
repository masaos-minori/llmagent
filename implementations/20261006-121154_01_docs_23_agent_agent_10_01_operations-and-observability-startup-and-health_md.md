## Goal

Update `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` to describe preservation semantics (not overwrite) when an existing `pending_approval_task_id` differs from the recovered id. (REQ-001 / AC-1)

## Scope

- Rewrite the "Restoration of Pending Post-Execution Approvals" paragraph in the doc
- Replace "the value is overwritten" with preservation semantics: preserve when existing differs from recovered, WARNING logged accordingly, process does not abort

## Assumptions

- Option B is the adopted policy (issue recommendation); the code's preservation behavior is correct and intentional
- The "overwrite" statement at line 72 is the only substantive doc inconsistency in this section
- The doc's `find_latest_pending_approval()` / "only one" wording vs. the code's `find_all_pending_approvals()` / `results[0]` mismatch is minor and left as-is (out of scope)

## Design decisions

- Adopt Option B: keep the current conditional assignment (preservation via value equality) and update the doc to describe preservation
- Preserve the wording nuance: preservation applies when values differ; equal values are re-assigned idempotently ("Overwriting … with …" warning fires but value unchanged); `None` starting value assigned recovered value

## Alternatives considered

- Option A: implement the StateStore-based staleness check — rejected because it changes runtime behavior, requires an owner decision on which approval is wired for `/approve` when two exist, and static analysis indicates the "differs" branch is unreachable at startup in production

## Implementation

### Target file

`docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md`

### Procedure

1. Rewrite the "Restoration of Pending Post-Execution Approvals" paragraph to describe preservation semantics

### Method

- Edit the paragraph directly
- Ensure the doc specifies preservation applies when values differ; equal values are re-assigned idempotently; `None` starting value assigned recovered value; process never aborts

### Details

**Before (line 72):**
```markdown
If a restoration value is set while a `pending_approval_task_id` is already configured, a `WARNING` level log is emitted, but the value is overwritten (the process does not abort).
```

**After:**
```markdown
If a restoration value is set while a `pending_approval_task_id` is already configured, a `WARNING` level log is emitted and the process does not abort. When the existing value differs from the recovered id, the existing value is preserved (the log reads "Keeping existing pending_approval_task_id X instead of overwriting with Y"). When the values are equal, the assignment is idempotent (the log reads "Overwriting pending_approval_task_id X with Y" but the value is unchanged). When the existing value is `None`, the recovered value is simply assigned (no overwrite log).
```

## Compatibility considerations

- This is a documentation-only change — no code, test, or API impact
- The doc belongs to the agent operations/observability doc per `routing.md` Docs mapping
- Per `AGENTS.md` Global Rule 9/10, the doc edit must be validated with the applicable `docs/` checker before completion

## Security considerations

- This change aligns the documented contract with the implemented and tested contract
- No security implications — the behavioral defect was already fixed in commit `c0a589e19`

## Rollback considerations

- Reverting would restore the contradiction between the doc and the code
- If the owner later chooses Option A (StateStore staleness), this doc wording would need revision — UNK-01 captures the decision

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md` | Documentation review | Read updated section vs `startup_approval_recovery.py:50-70` | No "overwrite" claim; preservation described; process-does-not-abort noted |
| `scripts/agent/startup_approval_recovery.py` (behavior) | Integration: recovery tests | `.venv/bin/python -m pytest tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals -q -p no:cacheprovider -p no:randomly` | 11 passed |
| Full suite | Regression: no new failures | `.venv/bin/python -m pytest tests/agent tests/shared tests/integration -q -p no:cacheprovider -p no:randomly` | No new failures attributable to this issue |

## Completion criteria

- Doc no longer claims the value is overwritten
- Doc describes preservation when the existing `pending_approval_task_id` differs from the recovered id
- Doc notes the process does not abort
- All 11 `TestStartupOrchestratorRecoverPendingApprovals` tests pass
- No new failures in regression command

## Out of scope

- Any change to `scripts/agent/startup_approval_recovery.py` behavior (current conditional assignment retained)
- Implementing the StateStore-based staleness criterion from plan `20261004-113000` (Option A) — owner decision, separate larger change
- Changing the sibling overwrite path in `scripts/agent/commands/cmd_workflow.py`
- Resolving the `pending_approval_id` / `approval_pending` consistency question
- Changing `find_all_pending_approvals()` or the StateStore API
- Reconciling the doc's `find_latest_pending_approval()` / "only one" wording vs. the code's `find_all_pending_approvals()` / `results[0]` (minor, explicitly out of scope in the issue)
- Deploying the `/opt/llm/scripts/` copy (deployment step only — no direct edit of the deployed copy)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update doc preservation semantics in `agent_10_01_operations-and-observability-startup-and-health.md` | Completed | 20261006-220753 | 20261006-220753 | REQ-001 |
| 2 | Add or update tests per Validation plan | Completed | 20261006-220753 | 20261006-220753 |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261006-220753 | 20261006-220753 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261006-220753 | 20261006-220753 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261005-121411_apr001_startup-approval-recovery-logs-keeping-pending_approval_task_id-but-still-overwrites-it.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261006-070805_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-121154
- **Related target files**: docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md