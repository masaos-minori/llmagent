# Implementation Procedure: Add Missing Regression Tests and Documentation for Mandatory Workflow Execution and Startup Validation Severity

Source plan: `plans/20260716-145938_plan.md`
Source requirement: `requires/20260716_14_require.md`

## Goal

Close the small number of concrete gaps between this requirement's documented invariants and the current implementation — which already satisfies ~80% of the requirement — by adding the missing explicit regression test for `WorkflowEngine.run()` invocation, documenting `plan_fn`'s no-op status, resolving one dead-code judgment call in `Orchestrator.handle_turn()`, and publishing a single-source-of-truth severity table for `agent/startup.py`'s validation checks.

## Scope

**In scope**
- Add an explicit regression test asserting `Orchestrator.handle_turn()` always invokes `WorkflowEngine.run()` (currently only implicitly exercised via `tests/test_orchestrator.py`'s autouse `_patch_workflow_loader` fixture).
- Document `plan_fn`'s current no-op behavior (`agent/orchestrator.py:199-200`) via inline comment and/or `docs/05_agent_03_01_turn-processing-flow-overview.md`.
- Resolve the dead `if self._workflow_def is None: self._log_fallback(...)` branch (`agent/orchestrator.py:169-170`) — recommend converting to an explanatory comment (cheapest, safest, avoids dead-code lint noise) but flag as a reviewer decision since full removal is also defensible; do NOT convert to a bare `assert` without first confirming no `-O`/`PYTHONOPTIMIZE` usage in `deploy/`.
- Publish a severity-mapping reference table (check name → severity → condition → rationale) in `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`, built from `agent/startup.py`'s actual `add_fatal`/`add_warning`/`add_ok` call sites, each read in full (not just call sites) to distinguish deliberate design from accidental omission.
- Add regression tests for any severity classification not already covered by `tests/test_startup.py`.

**Out of scope**
- Redesigning the workflow engine — `WorkflowEngine.run()`'s plan → execute (retry) → [approval gate] → verify sequencing already matches the requirement and needs no change.
- Implementing advanced planning behavior — `plan_fn` stays a no-op, only its status becomes documented.
- Adding unrelated startup checks.
- Changing any existing severity classification — only document what already exists, unless a classification is flagged as accidental (see Details).

## Assumptions

1. `Orchestrator.__init__` (`agent/orchestrator.py:127-133`) already raises `RuntimeError` on `WorkflowLoader().load()` failure, so `self._workflow_def` can never be `None` by the time `handle_turn()` runs — already tested via `tests/test_startup.py::TestStartupWorkflowPreflight`.
2. `handle_turn()` always calls `_handle_workflow_engine()` → `engine.run(task, plan_fn, execute_fn, verify_fn)`; no bypass path exists once the approval-pending guard passes.
3. `LLMTurnRunner` has exactly one instantiation site (`agent/orchestrator.py:122`) and its `.run()` is reachable only through `execute_fn()` inside `engine.run(...)` — no direct fallback path exists structurally.
4. `ctx.workflow.approval_pending` blocking already exists and is already tested (`tests/test_orchestrator.py::TestApprovalPendingGuard`).
5. `agent/shared/health_models.py::StartupCheckStatus` already defines all four severities (`OK`, `WARNING`, `FATAL`, `SKIPPED`) with a structured `StartupCheckOutcome`; the gap is a missing single reference table in the doc, not a data-model gap (`grep -n "FATAL\|WARNING\|SKIPPED\|severity" docs/05_agent_10_01_...md` returns no matches today).
6. `agent/startup.py` already assigns explicit, differentiated severities per check (`security_audit`, `embedding_dimensions`, `readiness`, `tool_definitions`, `routing_drift`, `routing_safety_tiers`, `routing_drift_live`, `rag_consistency`) — this plan documents existing decisions, it does not change them without separately flagging a reason.
7. `tests/test_startup.py::TestStartupRollback` already covers rollback shutdown behavior comprehensively — no new rollback test unless the doc-table cross-reference finds an uncovered severity/check combination.

## Unknowns to resolve during implementation

- **`readiness` check's exact warning-vs-fatal branching condition**: not fully traced in the plan (likely "required" vs. "optional" MCP server classification) — read the full check function during Procedure step 4.
- **Dead-code resolution for `_workflow_def is None`**: comment vs. assert vs. removal is a reviewer judgment call, not objectively determined — this document recommends comment-only but implementation should surface the choice for reviewer sign-off rather than deciding unilaterally.

## Implementation

### Target file

Primary: `scripts/agent/orchestrator.py`, `tests/test_orchestrator.py`. Secondary: `docs/05_agent_03_01_turn-processing-flow-overview.md`, `docs/05_agent_10_01_operations-and-observability-startup-and-health.md`, `tests/test_startup.py`.

### Procedure

1. **Add the explicit `WorkflowEngine.run()`-invocation test** in `tests/test_orchestrator.py`: a dedicated test asserting `mock_engine_instance.run.assert_called_once()` (or equivalent), independent of the autouse fixture's implicit exercise of the same call.
2. **Document `plan_fn`'s no-op status**: add an inline comment at the definition site (`agent/orchestrator.py:199-200`) referencing this requirement's decision. Check `docs/05_agent_03_01_turn-processing-flow-overview.md` for whether it already describes the plan stage; update it if not.
3. **Resolve the dead-code Unknown with the reviewer**, then apply the chosen resolution to `agent/orchestrator.py:169-170`. Before choosing `assert`, confirm no `-O`/`PYTHONOPTIMIZE` usage exists in `deploy/` scripts; if any doubt remains, prefer the comment-only resolution (zero behavioral risk).
4. **Read every `agent/startup.py` check function in full** (not just `add_fatal`/`add_warning`/`add_ok` call sites) to extract the exact branching condition and rationale for each severity decision, resolving the `readiness` warning-vs-fatal condition in the process. If any classification looks accidental rather than deliberate, flag it to the user before writing it into the doc as if intentional.
5. **Publish the severity-mapping table** in `docs/05_agent_10_01_operations-and-observability-startup-and-health.md` with columns `Check (source) | Severity | Condition | Rationale`, one row per check (`security_audit`, `embedding_dimensions`, `readiness`, `tool_definitions`, `routing_drift`, `routing_safety_tiers`, `routing_drift_live`, `rag_consistency`), filled in with step 4's findings.
6. **Cross-reference the table against `tests/test_startup.py`'s existing coverage**: for each row, confirm a test proves that severity is produced under that condition; add any missing test.
7. **Deployment/verification**: documentation and test-only changes plus one small orchestrator comment/simplification; no service restart needed. Run the full test suite to confirm no regression.

### Method

- Additive test writing following existing patterns in `tests/test_orchestrator.py` and `tests/test_startup.py`.
- Direct Markdown table insertion into the two named docs.
- Minimal, reviewer-gated code change to `orchestrator.py` (comment or dead-branch resolution only — no behavioral change).

### Details

- Do not change any existing severity classification in `agent/startup.py` — this is documentation of current behavior, not a redesign.
- Do not silently codify a possibly-accidental classification as if it were deliberate — flag to the user if step 4 finds one.
- Do not use `assert` for the dead-code resolution without first verifying no `-O`/`PYTHONOPTIMIZE` usage in `deploy/`.
- This plan does not re-verify `agent/workflow/state_store.py`, `task_ops.py`, `attempt_ops.py`, `idempotency_ops.py`, `artifact_ops.py`, `workflow_loader.py`, or `validate.py` — only `workflow_engine.py` and `orchestrator.py` were read in full; treat any gap surfacing there as new evidence requiring a plan update, not unplanned scope expansion.

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/orchestrator.py tests/test_orchestrator.py tests/test_startup.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/orchestrator.py` | no new errors |
| New/updated orchestrator tests | `uv run pytest tests/test_orchestrator.py -v` | all pass, including the new explicit `WorkflowEngine.run()` assertion |
| Startup severity tests | `uv run pytest tests/test_startup.py -v` | all pass, including any newly added severity-classification cases |
| Full suite | `uv run pytest -v` | no new failures beyond pre-existing unrelated failures |
| Doc accuracy (manual) | cross-read the new severity table against `agent/startup.py`'s actual `add_fatal`/`add_warning`/`add_ok` call sites | table matches code exactly |
