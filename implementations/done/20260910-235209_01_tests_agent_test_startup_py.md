# Delete `TestStartupOrchestratorRecoverPendingApprovals` from `tests/agent/test_startup.py`

## Goal

Remove the orphaned `TestStartupOrchestratorRecoverPendingApprovals` class from `tests/agent/test_startup.py` (lines 240-528), eliminating dead test debt after its 9 scenario coverages are ported to `tests/agent/test_startup_approval_recovery.py`.

## Scope

- Delete the entire `class TestStartupOrchestratorRecoverPendingApprovals:` definition and all 9 test methods within it (lines 240-528).
- Preserve surrounding code: the `TestStartupOrchestratorSetupPrompt` class starting at line 534 and any subsequent content.

## Assumptions

- The 9 scenarios covered by this class are being ported separately (see `tests/agent/test_startup_approval_recovery.py` row).
- No other test class or function references `TestStartupOrchestratorRecoverPendingApprovals` directly.
- The class's mock patch targets (`agent.startup.find_all_pending_approvals`, `agent.startup.StateStore`) are incorrect because `ApprovalRecovery.recover()` uses local imports from `agent.workflow.approval_ops` and `agent.workflow.state_store`.

## Design decisions

- Delete the class as a single contiguous block (lines 240-528) rather than removing individual methods, since the entire class is orphaned.
- Do not modify any other part of `test_startup.py` — the porting of coverage is handled in the separate row for `test_startup_approval_recovery.py`.

## Alternatives considered

- Removing individual test methods instead of the whole class: rejected because the class itself is orphaned and removing it entirely avoids leaving behind unused scaffolding.
- Renaming the class and fixing its mock targets: rejected because the class duplicates coverage already exercised in `test_startup_approval_recovery.py`.

## Compatibility considerations

- `uv run pytest tests/agent/test_startup.py -q` will no longer report the `AttributeError`s caused by broken mock patches against `agent.startup.find_all_pending_approvals` and `agent.startup.StateStore`.
- The ~36 pre-existing failures in `test_startup.py` remain unaffected.

## Security considerations

- No security surface change. This is a test-only cleanup.

## Rollback considerations

- Reverting means restoring the deleted class definition. The class can be recovered from git history if needed.

## Validation plan

- Run `uv run pytest tests/agent/test_startup.py -q` and confirm no `AttributeError` related to `find_all_pending_approvals` or `StateStore`.
- Confirm `grep -c "class TestStartupOrchestratorRecoverPendingApprovals" tests/agent/test_startup.py` returns 0.

## Completion criteria

- `TestStartupOrchestratorRecoverPendingApprovals` no longer exists in `tests/agent/test_startup.py`.
- `uv run pytest tests/agent/test_startup.py -q` runs without AttributeError for `find_all_pending_approvals`/`StateStore`.
- Surrounding test classes remain intact.

## Out of scope

- Porting the 9 scenarios to `test_startup_approval_recovery.py` (handled separately).
- Fixing the ~36 unrelated pre-existing failures in `test_startup.py`.
- Changes to `scripts/agent/startup.py` or `scripts/agent/startup_approval_recovery.py`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete TestStartupOrchestratorRecoverPendingApprovals class (lines 240-528) | Completed | 20260911-14:37 | 20260911-14:37 | |
| 2 | Verify pytest passes without AttributeError | Completed | 20260911-14:37 | 20260911-14:37 | No AttributeError for find_all_pending_approvals/StateStore |

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
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260909-105724_startup02_recover-pending-approvals-test-targets-removed-module-attribute.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-192919_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-235209
- **Related target files**: tests/agent/test_startup.py
