# Startup approval recovery: "Keeping existing pending_approval_task_id" log is now truthful (fixed by c0a589e19)

## Priority
Medium

## Summary
In `ApprovalRecovery.recover()` (scripts/agent/startup_approval_recovery.py), commit 10308ed7f changed the log message to "Keeping existing pending_approval_task_id ... instead of overwriting ..." when the existing and recovered task ids differ, but the unconditional assignment `ctx.turn.pending_approval_task_id = task_id` still ran right after — making the log untruthful. This was fixed by commit c0a589e19 which added a conditional assignment at lines 66-70, so the current code correctly preserves the existing value when they differ. The core defect is resolved; remaining items are design-level decisions about staleness criteria and documentation consistency.

## Background
- Commit 10308ed7f changed this block following procedure `implementations/20261004-195608_01_scripts_agent_startup_approval_recovery_py.md`, whose Source plan is `plans/20261004-182816_plan.md` (not yet in plans/done/). A different plan from the same source issue (ar009), `plans/done/20261004-113000_plan.md`, was NOT the basis of the procedure; the earlier statement that plan 113000 and this procedure were "applied together" is corrected here.
- The two plans differ in approach: plan 113000 (REQ-001) uses a StateStore existence check of the current approval record (pseudo-code `return`s early when the record exists, which would also skip wiring and the user-facing warning); plan 182816 and the procedure use a plain comparison ("keep current value when both exist and differ"). REQ-002/REQ-003 in both require tests for preservation and stale overwrite; neither set of tests existed at the time of filing, but REQ-002 and REQ-003 tests were later added in commit c0a589e19 (they test value equality, not StateStore existence).
- The procedure's pseudo-code assigns `pending_approval_task_id` only in the None/equal branch. The committed code initially left the assignment unconditional (outside the branches), so the code deviated from its own procedure; the defect was an implementation slip, not a design choice.
- **FIXED**: Commit c0a589e19 added the conditional assignment at lines 66-70:
  ```python
  if (
      ctx.turn.pending_approval_task_id is None
      or ctx.turn.pending_approval_task_id == task_id
  ):
      ctx.turn.pending_approval_task_id = task_id
  ```
  This makes the "Keeping existing" log truthful — the value is preserved when they differ.
- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md states: if a restoration value is set while a `pending_approval_task_id` is already configured, a WARNING is logged, "but the value is overwritten (the process does not abort)". This doc is now inconsistent with the current code behavior (value is preserved when they differ).
- The sibling path in scripts/agent/commands/cmd_workflow.py also logs "Overwriting pending_approval_task_id ..." and then assigns.

## Problem
Adversarial verification (against current source, tests, docs, git history, 2026-10-05):
- **FIXED**: The "Keeping existing ..." log is now truthful. Commit c0a589e19 added the conditional assignment at lines 66-70, so when `pending_approval_task_id` differs from the recovered value, the existing value is actually preserved. Verified by running the full test suite: all 11 tests in TestStartupOrchestratorRecoverPendingApprovals pass.
- Corrected: `pending_approval_id` and `approval_pending` are set before the branch (lines 48-49), so even a truthful "keep" for the task id leaves a mismatched triple (old task id, new approval id, `approval_pending=True`). This remains an open design question.
- Corrected/narrowed: the module run `tests/agent/test_startup_approval_recovery.py` shows 0 failures (all 11 tests pass), not 7 as originally reported. Six were in TestStartupOrchestratorStartServers / TestStartupVerifyMcpHealth (MCP health check, "HTTP 503" / retry behavior; related to the stp001 issue and/or environment) and are outside this issue; only the one named test is attributable to apr001.
- Confirmed: the sibling `cmd_workflow.py` `_cmd_approve` (lines 153-159) logs "Overwriting pending_approval_task_id %s with %s" and assigns; docs/23_agent/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md line 48 documents it as a known single-field constraint (warning for observability). Note the semantic difference: that path sets the resume target after an explicit user decision, while startup recovery has no user decision.
- Unreachability (strengthened from "unknown"): by static analysis, `pending_approval_task_id` is written only in `cmd_workflow.py` `_cmd_approve` (REPL, after startup) and cleared in `workflow_engine_adapter.py` line 165; `TurnState` default is None and `StartupOrchestrator.run()` (startup.py lines 68-77) runs `_recover_pending_approvals()` after `ComponentInitializer.initialize()` and before the REPL, with no writer in between. So the "differs" branch cannot execute in production; it runs only in tests that preset a MagicMock value. Not proven at runtime.
- Additional finding: no production code under scripts/ reads `ctx.turn.pending_approval_task_id` (grep: only assignment, clear, and the log check); `pending_approval_id` is read by `repository_gateway.py` (lines 98-107, denies writes while set), `orchestrator.py` line 186 and `services/context_view.py` line 196. So the practical effect of `pending_approval_id`/`approval_pending` consistency is larger than that of the task id.
Evidence (re-verified):
- Explicit in code: in `recover()`, `ctx.workflow.approval_pending = True` and `ctx.turn.pending_approval_id = approval.approval_id` are set first; then, if `pending_approval_task_id` is not None, one of two warnings is logged ("Keeping existing ..." when ids differ, "Overwriting ..." when equal); then the conditional assignment at lines 66-70 runs. When ids differ, the assignment does NOT execute — the "Keeping" message is now true.
- Verified by test: `.venv/bin/python -m pytest tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals -xvs -p no:cacheprovider -p no:randomly` passes all 11 tests. The previously failing test (`test_startup_recovery_warns_on_pending_approval_task_id_overwrite`) was renamed to `test_startup_recovery_keeps_existing_pending_approval_task_id` in commit c0a589e19 and now passes.
- The plan 113000 REQ-001 (preservation with StateStore check) and the REQ-002/REQ-003 regression tests were not implemented per the plan's design (StateStore existence check); confirmed that plan 113000's pseudo-code queries `approvals` by `ctx.turn.pending_approval_id`, which `recover()` has already overwritten at line 49 when the check would run, so it needs reordering (check before line 49) if implemented.
- Pinned contract: in TestStartupOrchestratorRecoverPendingApprovals only `test_startup_recovery_keeps_existing_pending_approval_task_id` (existing "task-old", asserts final value "task-old" and a "Keeping existing pending_approval_task_id" warning with args old/new) and `test_startup_recovery_no_warning_when_task_id_not_already_set` (None start, no overwrite warning) touch the existing value; the others start from MagicMock/None and only assert wiring. No test pins StateStore-based staleness.
- Documentation (quoted): docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md line 72: "If a restoration value is set while a `pending_approval_task_id` is already configured, a `WARNING` level log is emitted, but the value is overwritten (the process does not abort)." This doc is now inconsistent with the current code. The same section says restoration uses `StateStore.find_latest_pending_approval()` and tracks "only one" approval, whereas code uses `find_all_pending_approvals()` and wires `results[0]`; this doc/code mismatch is minor and outside this issue. Under governance_01 (Claim Type Taxonomy), runtime-behavior is canonical in source under `scripts/` with tests as evidence, and plans/procedures are not canonical for runtime behavior; docs describe overwrite, so the documented and tested contract currently favors Option B, while a preservation requirement could only come from an Accepted ADR or Registry entry (none found for it).

## Reason for Change
The log message was misleading (fixed by c0a589e19). The remaining issues are:
1. The docs still state "the value is overwritten" but the code now preserves the value when they differ.
2. Plan 113000's StateStore-based staleness criterion was never implemented; the current code uses simple value equality.
3. The `pending_approval_id`/`approval_pending` consistency question remains unresolved.

## Implementation Intent
- Option A (partial): implement StateStore-based staleness check. Assign `pending_approval_task_id` (and decide consistently about `pending_approval_id` and `approval_pending`) only when the existing value is None, equal to the recovered one, or stale (per plan REQ-001, its approval record no longer exists in StateStore). Add the plan's tests for preservation and stale overwrite, update the failing test (its overwrite expectation changes), update docs/23_agent/agent_10_01_... and keep both sibling paths consistent. Higher cost and behavior change; needs a decision on which approval is wired for `/approve` when two exist. Risk: preserving only the task id while `pending_approval_id` points to the recovered approval (as the procedure's design would) leaves resume target and displayed/gated approval mismatched, and `repository_gateway.py` write denial keys on `pending_approval_id`. Since the branch is unreachable at startup (see Problem), Option A would add untested-in-production code.
- Option B (current state): keep the current conditional assignment (value preservation when they differ) and accept the docs inconsistency. The current code implements preservation via value equality (not StateStore existence check). The failing test was fixed by renaming and adjusting assertions in commit c0a589e19. Option B consequence: behavior is now preservation (not overwrite) when values differ; `approval_pending`, `pending_approval_id`, `pending_approval_task_id` may be inconsistent (old task id, new approval id).

Recommendation: The current code (Option B variant) is correct and lower-risk. The core defect (untruthful log + unconditional overwrite) is fixed. If the owner confirms the StateStore-based staleness criterion from plan 113000, choose Option A. The owner decides.

## Target Files or Areas
- scripts/agent/startup_approval_recovery.py (`ApprovalRecovery.recover`) — core fix applied in c0a589e19
- tests/agent/test_startup_approval_recovery.py (unchanged under Option B; updated and extended under Option A)
- scripts/agent/commands/cmd_workflow.py, scripts/agent/context.py (read-only reference)
- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md (see Documentation Impact)

## Required Changes
- Option B (current): no further changes needed to the code. Optionally update docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md to reflect preservation semantics.
- Option A: implement the StateStore-based staleness check, add tests for REQ-002 and REQ-003 of the plan, update the failing test and the docs.

## Constraints
- Log message arguments must keep the old and new task ids (plan REQ-004).
- Do not change `find_all_pending_approvals()` or the StateStore API.
- Under Option B no test change.

## Acceptance Criteria
- tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals::test_startup_recovery_keeps_existing_pending_approval_task_id passes (already passing since c0a589e19).
- The log message never claims "Keeping" unless the value is actually preserved (already satisfied since c0a589e19).
- The neighbouring recovery tests (for example test_startup_recovery_no_warning_when_task_id_not_already_set) still pass (already passing).
- `.venv/bin/python -m pytest tests/agent tests/shared tests/integration -q -p no:cacheprovider -p no:randomly` shows no failures related to this issue.

## Testing Expectations
- Run the full TestStartupOrchestratorRecoverPendingApprovals suite (11 tests, all passing).
- Option A: add tests for preservation of an active approval and overwrite of a stale one (StateStore-based).
- Run ruff and mypy on the changed file.

## Documentation Impact
- Option B (current): docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md line 72 states "the value is overwritten" but the code now preserves the value when they differ. This is a documentation inconsistency that should be addressed.
- Option A: that statement must be updated to the preservation rule (and the staleness criterion). Docs are not edited by this issue filing.

## Out of Scope
- Redesigning approval state ownership between `ctx.workflow` and `ctx.turn`.
- Changes to cmd_workflow.py's overwrite behavior.
- Timestamp or session-id based staleness detection (rejected by the procedure as over-engineering).

## Dependencies
N/A: none (the failing test shares a module with stp001 but is independent).

## Unresolved Questions
- Is preservation of an existing `pending_approval_task_id` during startup recovery actually required? Plan REQ-001 says yes (with StateStore staleness check); the current code preserves via value equality; docs say overwrite. Owner decision.
- Can `pending_approval_task_id` be non-None at startup recovery time? Static analysis says no (see Problem); not verified at runtime. Unverifiable here: whether any out-of-tree or future caller presets it.
- Unverifiable: whether the 6 other failures in tests/agent/test_startup_approval_recovery.py are caused by the environment (HTTP 503 in the retry path) or by the stp001 change; not investigated here.
- Which plan is authoritative (113000 in plans/done/ vs 182816 in plans/) given both derive from issue ar009 and disagree on the staleness criterion; neither is canonical for runtime behavior. Owner decision.
- Option A nuance: should a StateStore-confirmed active approval cause early return (plan 113000) or only skip the task-id assignment (procedure)?
- If preserved, should `pending_approval_id` and `approval_pending` also be preserved to stay consistent with the task id? Unknown.
- **New**: The docs state "the value is overwritten" but the code now preserves it. Should the docs be updated to match the current behavior?

## AI Implementation Instruction
Implement only the option the owner selects. Under Option B (current state), no code changes are needed; optionally update docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md to reflect preservation semantics. Under Option A add tests and docs updates as listed, without altering unrelated recovery output. Report the test results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261004-113000_plan.md (originating change; this issue is a follow-up)
- **Source implementation procedure**: implementations/20261004-195608_01_scripts_agent_startup_approval_recovery_py.md (originating change)
- **Generated at**: 20261005-121411
- **Related target files**: scripts/agent/startup_approval_recovery.py, tests/agent/test_startup_approval_recovery.py
- **Fix commit**: c0a589e19 (conditional assignment added at lines 66-70)
