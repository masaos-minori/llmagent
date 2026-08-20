# Implementation Procedure: Remove dead RuntimeToolRegistry methods

## Goal
Delete the dead `RuntimeToolRegistry.is_side_effect()` and `RuntimeToolRegistry.classify_operation_type()` methods from `scripts/shared/runtime_tool_registry.py`, remove their direct-unit tests, and update the stale module/doc text that frames this as a "temporary, pending unification" duplication — without touching the unrelated, actively-used `shared.tool_executor_helpers.is_side_effect()` or the unrelated `agent.tool_policy.classify_operation_type()` free function.

## Goal
Delete the dead `RuntimeToolRegistry.is_side_effect()` and `RuntimeToolRegistry.classify_operation_type()` methods from `scripts/shared/runtime_tool_registry.py` (both have zero production callers), remove their direct-unit tests, and update the stale module/doc text that frames this as a "temporary, pending unification" duplication — without touching the unrelated, actively-used `shared.tool_executor_helpers.is_side_effect()` or the unrelated `agent.tool_policy.classify_operation_type()` free function.

## Scope
- Target files:
  - `scripts/shared/runtime_tool_registry.py`: remove `is_side_effect()` (line 168-173) and `classify_operation_type()` (line 175-181); remove the now-unused `Literal` import; update the module docstring (lines 11-19, 26-30).
  - `tests/shared/test_runtime_tool_registry.py`: remove `test_is_side_effect_reflects_is_write` (127-133) and `test_classify_operation_type_read_vs_write` (135-141).
  - `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`: fix the two now-stale Japanese notes (lines 82, 159) that describe `RuntimeToolRegistry.is_side_effect()` as an "intentionally duplicated, temporary" implementation — this framing becomes factually wrong once the method is deleted (per `rules/coding.md` "Documentation notes" classification: this is a "Documentation fix required" case).

## Assumptions
- The requirement's grep evidence (only test call-sites for both methods) is accurate as of the current `master` HEAD — re-verified independently below
- No external consumer outside this repository imports `RuntimeToolRegistry.is_side_effect`/`classify_operation_type` (this is an internal shared module, not a published package)
- Removing the two tests does not reduce `apply_policy()`/`tool_spec_for_call()` coverage, since those are separate test methods in the same class untouched by this change

## Design decisions
- Pure deletion, no migration
- Remove the two method bodies from `runtime_tool_registry.py`
- Remove `Literal` from the `typing` import (no other use in the file after `classify_operation_type()` is removed)
- Update the module docstring: remove the `classify_operation_type()` bullet from "Import-layer design decisions" list; remove the trailing paragraph about `is_side_effect()`'s "temporary, parallel duplication"
- In the test file, delete the two now-orphaned test methods verbatim
- In the docs file, remove (or rewrite to past-tense/historical framing) the two identical stale notes at lines 82 and 159

## Implementation steps
1. **Preparation**: re-run `grep -rn "is_side_effect\|classify_operation_type" scripts/ tests/ docs/` immediately before editing, to catch any drift since this plan was written.

2. **Core deletion** (`scripts/shared/runtime_tool_registry.py`):
   - Remove `is_side_effect()` and `classify_operation_type()` method definitions
   - Remove `Literal` from the `typing` import
   - Update the module docstring per Design step 2

3. **Test cleanup** (`tests/shared/test_runtime_tool_registry.py`):
   - Remove `test_is_side_effect_reflects_is_write` and `test_classify_operation_type_read_vs_write`

4. **Doc fix** (`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md`):
   - Remove the two stale notes at (originally) lines 82 and 159

5. **Deployment/verification**:
   - No `deploy/deploy.sh` change needed — no file added/removed under `scripts/`
   - Run the full validation sequence per `rules/toolchain.md` (see Validation plan below)

## Validation plan
| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `tests/shared/test_runtime_tool_registry.py` | Unit | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | All remaining tests pass; the 2 removed tests no longer collected |
| `tests/shared/test_tool_executor.py` | Unit | `uv run pytest tests/shared/test_tool_executor.py -v` | Unchanged, passes — confirms `tool_executor_helpers.is_side_effect()` path untouched |
| `tests/agent/test_tool_policy.py`, `test_tool_policy_comprehensive.py`, `test_tool_approval_risk.py` | Unit | `uv run pytest tests/agent/test_tool_policy.py tests/agent/test_tool_policy_comprehensive.py tests/agent/test_tool_approval_risk.py -v` | Unchanged, passes — confirms `agent.tool_policy.classify_operation_type()` free function untouched |
| Whole repo | Full suite | `uv run pytest` | No new failures |
| `scripts/shared/runtime_tool_registry.py` | Lint/format | `uv run ruff format scripts/ && uv run ruff check scripts/` | Clean (catches unused-import if `Literal` removal was missed) |
| `scripts/shared/runtime_tool_registry.py` | Type check | `uv run mypy scripts/` | No new errors |
| Repo-wide | Architecture | `PYTHONPATH=scripts uv run lint-imports` | Passes (no boundary change) |
| Repo-wide | Security | `uv run bandit -r scripts/ -c pyproject.toml` | No new findings |
| Repo-wide | Dead code | `uv run vulture scripts/ --min-confidence 80` | No new dead-code flags introduced by the edit |
| Repo-wide | Pre-commit | `uv run pre-commit run --all-files` | Passes |
| Docs consistency | Doc check | `uv run check-mcp-docs` | Passes (doc edit does not touch port/tool-name drift surfaces) |
| Repo-wide | Grep confirmation | `grep -rn "RuntimeToolRegistry.is_side_effect\|RuntimeToolRegistry.classify_operation_type\|\.is_side_effect(\|\.classify_operation_type(" scripts/ tests/ docs/` | Zero hits for the registry methods; only the surviving `tool_executor_helpers.is_side_effect` and unrelated `agent.tool_policy.classify_operation_type` symbols remain |

## Risks
- **Risk**: Missing the `Literal` import cleanup leaves an unused import. **Mitigation**: `ruff check` (step in Implementation step 5) catches unused imports (`F401`); explicitly verified in Design step 1 that `Literal` has no other use in the file before removal.
- **Risk**: Deleting the docstring's `classify_operation_type()` bullet accidentally removes the still-relevant `apply_policy()` bullet next to it. **Mitigation**: Design step 2 explicitly calls out leaving the `apply_policy()` bullet untouched; diff review (`git diff`) before staging per `rules/toolchain.md` step 9 catches over-deletion.
- **Risk**: A future contributor reintroduces the same duplication pattern without reading the (now-removed) docstring warning. **Mitigation**: none added beyond the deletion itself — the requirement's own rationale is that removing the confusing "two answers" surface is the fix, not preserving a warning comment for code that no longer exists. Accepted as a low-likelihood, low-impact residual risk; no issue filed.
- **Risk**: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md` update is out of the require-to-plan phase's own write permissions (this phase must not modify `docs/*.md`), so it is deferred to the implementation phase. **Mitigation**: explicitly listed in Scope/Implementation steps above so the implementation phase does not miss it; low likelihood of being skipped since it is now written into the plan.

## Traceability
- Workflow phase: requirement-to-plan
- Source issue: N/A
- Source requirement: requires/done/20260818-223342_require.md
- Source plan: plans/20260819-182209_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-151634
- Related target files: scripts/shared/runtime_tool_registry.py, tests/shared/test_runtime_tool_registry.py, docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto.md