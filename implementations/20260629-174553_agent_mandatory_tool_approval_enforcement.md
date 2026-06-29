# Implementation: Enforce mandatory tool approval checks in execute_all_tool_calls()

## Goal

Enforce mandatory tool approval checks inside `execute_all_tool_calls()` so that write, delete, shell, and GitHub write tools cannot execute without passing `run_approval_checks()`.

## Scope

- **In-Scope**:
  - Verify `scripts/agent/tool_runner.py` — approval gate integration (`_run_approval_gate`, `_build_denied_messages`)
  - Verify `scripts/agent/tool_approval.py` — `run_approval_checks()`, plan-mode block, gitops block
  - Verify `scripts/agent/llm_turn_runner.py` — calls `execute_all_tool_calls()` with no bypass
  - Verify `tests/test_tool_runner.py` — four approval-enforcement tests exist
- **Out-of-Scope**:
  - DB schema changes
  - New module/package creation
  - Workflow-level approval logic (kept separate per requirement)
  - `agent/tool_policy.py`, `agent/tool_audit.py` (no changes needed)

## Assumptions

- The implementation has been verified as **already complete** at the time of planning.
- All 21 tests in `tests/test_tool_runner.py` and 88 tests in approval test files pass without modification.
- `ctx.cfg.workflow_require_approval` correctly guards the `skip_in_workflow_mode` path to prevent double-prompting in workflow scenarios.
- The `_GITHUB_WRITE_TOOLS` frozenset in `tool_approval.py` is the authoritative list of GitHub write operations subject to `gitops_push_blocked`.

## Unknowns Resolution

| ID | Description | Resolution |
|---|---|---|
| UNK-01 | Whether `ctx.workflow.approval_pending` attribute is always present on all AgentContext implementations | Attribute accessed via `getattr` with default `False` in `_run_approval_gate`; no static typing guarantee — acceptable for runtime safety |
| UNK-02 | Coverage of `llm_turn_runner.py` for the approval path — no direct test that the runner cannot bypass approval | Verified: `execute_all_tool_calls()` is called from `llm_turn_runner.py:92` with no bypass; approval gate runs before execution |

## Verification Results

### 1. Approval Gate Integration (VERIFIED COMPLETE)

**`scripts/agent/tool_runner.py`:**
- `_run_approval_gate()` at line 471 — calls `run_approval_checks()` with correct `skip_in_workflow_mode` logic
- `_build_denied_messages()` at line 490 — builds history entries and tool_msgs for denied calls
- Integrated into `execute_all_tool_calls()` at line 454 — approval gate runs BEFORE DAG or standard execution
- Denied results persisted via `ctx.session.save_many(tool_msgs)` at line 468
- Denied history extended via `ctx.conv.history.extend(denied_history)` at line 466

### 2. Approval Logic (VERIFIED COMPLETE)

**`scripts/agent/tool_approval.py`:**
- `run_approval_checks()` at line 156 — handles plan-mode blocking (`plan_blocked_tools`) and gitops block (`gitops_push_blocked`)
- `check_approval()` at line 100 — handles risk-based approval for individual tool calls
- `skip_in_workflow_mode` flag at line 159 — preserves workflow-level approval separation
- `_GITHUB_WRITE_TOOLS` frozenset at line 115 — authoritative list of GitHub write operations

### 3. Tests (VERIFIED COMPLETE)

**`tests/test_tool_runner.py`:**
- `test_write_tool_requires_approval_without_gateway` — line 337
- `test_denied_tool_call_is_returned_as_tool_message` — line 365
- `test_plan_mode_blocked_tool_is_not_executed` — line 394
- `test_execute_all_tool_calls_does_not_bypass_approval` — line 419
- `test_all_calls_execute_without_gateway` updated to patch `run_approval_checks` — line 303

### 4. Call Chain (VERIFIED COMPLETE)

**`scripts/agent/llm_turn_runner.py`:**
- Calls `execute_all_tool_calls()` at line 92 with no bypass path
- No alternative execution path that skips approval gate

## Remaining Actions

If any gap is found during Phase 3 review:

1. **Coverage gap fix**
   - [ ] Add `test_execute_all_tool_calls_does_not_bypass_approval` variant that directly inspects `_run_approval_gate` is called (integration-level, no mock)

2. **Type safety**
   - [ ] Verify `ctx.workflow` type annotation covers `approval_pending` attribute without `getattr` fallback

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `agent/tool_runner.py` | Unit: approval gate called before execution | `uv run --no-sync pytest tests/test_tool_runner.py -v` | 21 tests pass |
| `agent/tool_approval.py` | Unit: plan-mode block, gitops block, risk-based approval | `uv run --no-sync pytest tests/test_tool_approval_paths.py tests/test_tool_approval_preflight.py tests/test_tool_approval_risk.py tests/test_tool_approval_repos.py -v` | 88 tests pass |
| `agent/llm_turn_runner.py` | Unit: runner calls execute_all_tool_calls with approval | `uv run --no-sync pytest tests/test_llm_turn_runner.py -v` | All pass |
| Import layer contract | Architecture lint | `uv run --no-sync lint-imports` | No violations |
| Security | Static analysis | `uv run --no-sync bandit -r scripts/ -c pyproject.toml -q` | 0 High severity |
| Full suite | Regression guard | `uv run --no-sync pytest -x -q` | All pass |

## Risks & Mitigations

- **Risk**: `skip_in_workflow_mode=True` when `workflow_require_approval=True` and no pending approval could silently bypass per-tool approval in edge cases → **Mitigation**: The condition also checks `not getattr(ctx.workflow, "approval_pending", False)` so approval is only skipped when workflow approval is active and not pending; add integration test covering this branch if gaps found.
- **Risk**: High cyclomatic complexity in `_execute_with_dag` (D=26) could hide edge cases where approved_calls bypass is missed → **Mitigation**: Approval gate runs before `_execute_with_dag` is entered; no path inside the DAG executor can re-introduce unapproved calls.
- **Risk**: Future callers of `execute_all_tool_calls()` could set `ctx.cfg.workflow_require_approval=True` to bypass per-tool approval unintentionally → **Mitigation**: Document the `skip_in_workflow_mode` contract in the docstring; consider adding an assertion or warning when both flags are set unexpectedly.
