# Startup approval recovery logs "Keeping existing pending_approval_task_id" but still overwrites it

## Priority
Medium

## Summary
In `ApprovalRecovery.recover()` (scripts/agent/startup_approval_recovery.py), commit 10308ed7f changed the log message to "Keeping existing pending_approval_task_id ... instead of overwriting ..." when the existing and recovered task ids differ, but the unconditional assignment `ctx.turn.pending_approval_task_id = task_id` still runs right after. Behavior is unchanged (overwrite) while the log claims otherwise, and one test fails.

## Background
- Commit 10308ed7f changed this block following procedure `implementations/20261004-195608_01_scripts_agent_startup_approval_recovery_py.md`, whose Source plan is `plans/20261004-182816_plan.md` (not yet in plans/done/). A different plan from the same source issue (ar009), `plans/done/20261004-113000_plan.md`, was NOT the basis of the procedure; the earlier statement that plan 113000 and this procedure were "applied together" is corrected here.
- The two plans differ in approach: plan 113000 (REQ-001) uses a StateStore existence check of the current approval record (pseudo-code `return`s early when the record exists, which would also skip wiring and the user-facing warning); plan 182816 and the procedure use a plain comparison ("keep current value when both exist and differ"). REQ-002/REQ-003 in both require tests for preservation and stale overwrite; neither set of tests exists (plan 113000 and 182816 both say "Create tests/agent/test_startup_approval_recovery.py", but that file already exists with other tests).
- The procedure's pseudo-code assigns `pending_approval_task_id` only in the None/equal branch. The committed code instead leaves the assignment unconditional (outside the branches), so the code deviates from its own procedure; the defect is an implementation slip, not a design choice.
- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md states: if a restoration value is set while a `pending_approval_task_id` is already configured, a WARNING is logged, "but the value is overwritten (the process does not abort)".
- The sibling path in scripts/agent/commands/cmd_workflow.py also logs "Overwriting pending_approval_task_id ..." and then assigns.

## Problem
Adversarial verification (against current source, tests, docs, git history, 2026-10-05):
- Confirmed: the "Keeping existing ..." log is untruthful. `git show 10308ed7f` shows the only changes are the new if/else around the warning; the assignment at line 66 has no conditional, early return or later restore, and `recover()` has no other path touching the field.
- Corrected: `pending_approval_id` and `approval_pending` are set before the branch (lines 48-49), so even a truthful "keep" for the task id would leave a mismatched triple (old task id, new approval id, `approval_pending=True`).
- Corrected/narrowed: the module run `tests/agent/test_startup_approval_recovery.py` shows 7 failures, not 1. Six are in TestStartupOrchestratorStartServers / TestStartupVerifyMcpHealth (MCP health check, "HTTP 503" / retry behavior; related to the stp001 issue and/or environment) and are outside this issue; only the one named test is attributable to apr001.
- Confirmed: the sibling `cmd_workflow.py` `_cmd_approve` (lines 153-159) logs "Overwriting pending_approval_task_id %s with %s" and assigns; docs/23_agent/agent_07_10_cli-and-commands-slash-commands-workflow-debug.md line 48 documents it as a known single-field constraint (warning for observability). Note the semantic difference: that path sets the resume target after an explicit user decision, while startup recovery has no user decision.
- Unreachability (strengthened from "unknown"): by static analysis, `pending_approval_task_id` is written only in `cmd_workflow.py` `_cmd_approve` (REPL, after startup) and cleared in `workflow_engine_adapter.py` line 165; `TurnState` default is None and `StartupOrchestrator.run()` (startup.py lines 68-77) runs `_recover_pending_approvals()` after `ComponentInitializer.initialize()` and before the REPL, with no writer in between. So the "differs" branch cannot execute in production; it runs only in tests that preset a MagicMock value. Not proven at runtime.
- Additional finding: no production code under scripts/ reads `ctx.turn.pending_approval_task_id` (grep: only assignment, clear, and the log check); `pending_approval_id` is read by `repository_gateway.py` (lines 98-107, denies writes while set), `orchestrator.py` line 186 and `services/context_view.py` line 196. So the practical effect of `pending_approval_id`/`approval_pending` consistency is larger than that of the task id.
Evidence (re-verified):
- Explicit in code: in `recover()`, `ctx.workflow.approval_pending = True` and `ctx.turn.pending_approval_id = approval.approval_id` are set first; then, if `pending_approval_task_id` is not None, one of two warnings is logged ("Keeping existing ..." when ids differ, "Overwriting ..." when equal); then `ctx.turn.pending_approval_task_id = task_id` runs unconditionally. So the "Keeping" message is false: the value is always replaced, and `pending_approval_id` is already replaced too.
- Verified by test: `.venv/bin/python -m pytest tests/agent/test_startup_approval_recovery.py -q -p no:cacheprovider -p no:randomly` fails TestStartupOrchestratorRecoverPendingApprovals::test_startup_recovery_warns_on_pending_approval_task_id_overwrite at `assert len(overwrite_calls) == 1` (0 != 1): the test sets existing "task-old", recovers "task-456", expects the "Overwriting pending_approval_task_id" warning with args ("task-old", "task-456") and the value "task-456" after recovery. The value assertion passes; the log assertion fails.
- The plan 113000 REQ-001 (preservation with StateStore check) and the REQ-002/REQ-003 regression tests were not implemented; confirmed that plan 113000's pseudo-code queries `approvals` by `ctx.turn.pending_approval_id`, which `recover()` has already overwritten at line 49 when the check would run, so it needs reordering (check before line 49) if implemented.
- Pinned contract: in TestStartupOrchestratorRecoverPendingApprovals only test_startup_recovery_warns_on_pending_approval_task_id_overwrite (existing "task-old", asserts final value "task-456" and an "Overwriting pending_approval_task_id" warning with args old/new) and test_startup_recovery_no_warning_when_task_id_not_already_set (None start, no overwrite warning) touch the existing value; the others start from MagicMock/None and only assert wiring. No test pins preservation.
- Documentation (quoted): docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md line 72: "If a restoration value is set while a `pending_approval_task_id` is already configured, a `WARNING` level log is emitted, but the value is overwritten (the process does not abort)." The same section says restoration uses `StateStore.find_latest_pending_approval()` and tracks "only one" approval, whereas code uses `find_all_pending_approvals()` and wires `results[0]`; this doc/code mismatch is minor and outside this issue. Under governance_01 (Claim Type Taxonomy), runtime-behavior is canonical in source under `scripts/` with tests as evidence, and plans/procedures are not canonical for runtime behavior; docs describe overwrite, so the documented and tested contract currently favors Option B, while a preservation requirement could only come from an Accepted ADR or Registry entry (none found for it).

## Reason for Change
The log message contradicts the behavior (misleading diagnostics) and the current test and docs describe overwrite semantics. The code must either implement the stated preservation or state the actual behavior.

## Implementation Intent
- Option A: implement preservation. Assign `pending_approval_task_id` (and decide consistently about `pending_approval_id` and `approval_pending`) only when the existing value is None, equal to the recovered one, or stale (for example, per plan REQ-001, its approval record no longer exists in StateStore). Add the plan's tests for preservation and stale overwrite, and update the failing test (its overwrite expectation changes), docs/23_agent/agent_10_01_... and keep both sibling paths consistent. Higher cost and behavior change; needs a decision on which approval is wired for `/approve` when two exist. Risk: preserving only the task id while `pending_approval_id` points to the recovered approval (as the procedure's design would) leaves resume target and displayed/gated approval mismatched, and `repository_gateway.py` write denial keys on `pending_approval_id`. Since the branch is unreachable at startup (see Problem), Option A would add untested-in-production code.
- Option B: keep overwrite semantics (matches current docs, the sibling cmd_workflow.py path, and the existing test) and revert the log to the "Overwriting pending_approval_task_id %s with %s during recovery" message for all differing/equal cases, removing the "Keeping" branch and the misleading code comment ("Only overwrite if the current value is stale ... prefer the current value"). The failing test then passes unchanged. Option B consequence: behavior stays as before commit 10308ed7f (overwrite; `approval_pending`, `pending_approval_id`, `pending_approval_task_id` all consistently point to the newest pending approval).

Recommendation (survived adversarial verification, and is strengthened by the unreachability finding and by the docs/test contract favoring overwrite): the plan and procedure documents point to Option A (their stated goal is preservation), but because the plan and procedure disagree on the staleness criterion, the docs describe overwrite, and the preservation branch may be unreachable at startup, Option B is the lower-risk way to restore a truthful log immediately. If the owner confirms the preservation requirement, choose A. The owner decides.

## Target Files or Areas
- scripts/agent/startup_approval_recovery.py (`ApprovalRecovery.recover`)
- tests/agent/test_startup_approval_recovery.py (unchanged under Option B; updated and extended under Option A)
- scripts/agent/commands/cmd_workflow.py, scripts/agent/context.py (read-only reference)
- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md (see Documentation Impact)

## Required Changes
- Option B: remove the "Keeping existing" branch so the warning reads "Overwriting pending_approval_task_id %s with %s during recovery" with old and new values as positional args (matching the test's `call_args[0][1]`/`[0][2]`).
- Option A: implement the conditional assignment and consistent handling of `pending_approval_id`/`approval_pending`, add tests for REQ-002 and REQ-003 of the plan, update the failing test and the docs.

## Constraints
- Log message arguments must keep the old and new task ids (plan REQ-004).
- Do not change `find_all_pending_approvals()` or the StateStore API.
- Under Option B no test change.

## Acceptance Criteria
- tests/agent/test_startup_approval_recovery.py::TestStartupOrchestratorRecoverPendingApprovals::test_startup_recovery_warns_on_pending_approval_task_id_overwrite passes (unchanged under Option B; under Option A the owner-updated version passes).
- The log message never claims "Keeping" unless the value is actually preserved.
- The neighbouring recovery tests (for example test_startup_recovery_no_warning_when_task_id_not_already_set) still pass.
- `.venv/bin/python -m pytest tests/agent tests/shared tests/integration -q -p no:cacheprovider -p no:randomly` shows no failures related to this issue.

## Testing Expectations
- Run the failing test, the module tests/agent/test_startup_approval_recovery.py, and the regression command above.
- Option A: add tests for preservation of an active approval and overwrite of a stale one.
- Run ruff and mypy on the changed file.

## Documentation Impact
- Option B: no change; docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md already states a WARNING is logged and the value is overwritten.
- Option A: that statement must be updated to the preservation rule (and the staleness criterion). Docs are not edited by this issue filing.

## Out of Scope
- Redesigning approval state ownership between `ctx.workflow` and `ctx.turn`.
- Changes to cmd_workflow.py's overwrite behavior.
- Timestamp or session-id based staleness detection (rejected by the procedure as over-engineering).

## Dependencies
N/A: none (the failing test shares a module with stp001 but is independent).

## Unresolved Questions
- Is preservation of an existing `pending_approval_task_id` during startup recovery actually required? Plan REQ-001 says yes; docs say overwrite. Owner decision.
- Can `pending_approval_task_id` be non-None at startup recovery time? Static analysis says no (see Problem); not verified at runtime. Unverifiable here: whether any out-of-tree or future caller presets it.
- Unverifiable: whether the 6 other failures in tests/agent/test_startup_approval_recovery.py are caused by the environment (HTTP 503 in the retry path) or by the stp001 change; not investigated here.
- Which plan is authoritative (113000 in plans/done/ vs 182816 in plans/) given both derive from issue ar009 and disagree on the staleness criterion; neither is canonical for runtime behavior. Owner decision.
- Option A nuance: should a StateStore-confirmed active approval cause early return (plan 113000) or only skip the task-id assignment (procedure)?
- If preserved, should `pending_approval_id` and `approval_pending` also be preserved to stay consistent with the task id? Unknown.

## AI Implementation Instruction
Implement only the option the owner selects. Under Option B change only the log branch in scripts/agent/startup_approval_recovery.py and do not touch tests. Under Option A add tests and docs updates as listed, without altering unrelated recovery output. Report the test results.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261004-113000_plan.md (originating change; this issue is a follow-up)
- **Source implementation procedure**: implementations/20261004-195608_01_scripts_agent_startup_approval_recovery_py.md (originating change)
- **Generated at**: 20261005-121411
- **Related target files**: scripts/agent/startup_approval_recovery.py, tests/agent/test_startup_approval_recovery.py
