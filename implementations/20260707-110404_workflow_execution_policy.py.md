## Goal
Delete `scripts/agent/workflow_execution_policy.py` entirely after all importers have been cleaned up.

## Scope
**In**: `git rm scripts/agent/workflow_execution_policy.py`; remove cp line from `deploy/deploy.sh` if present; add `WorkflowExecutionPolicy` import pattern to `check_no_compat.py` forbidden list.
**Out**: Any replacement policy class.

## Assumptions
- All importers (`orchestrator.py`, `startup.py`, `repl_health.py`) have already had their imports removed (see respective implementation docs).
- `tests/test_workflow_execution_policy.py` is deleted separately (see test cleanup doc).
- `deploy/deploy.sh` may have `cp scripts/agent/workflow_execution_policy.py` — check first.

## Implementation

**Target file**: `scripts/agent/workflow_execution_policy.py` (deletion)

**Procedure**:
1. Confirm no remaining imports: `grep -rn "workflow_execution_policy\|WorkflowExecutionPolicy" scripts/ | grep -v __pycache__` → must be 0 results
2. `git rm scripts/agent/workflow_execution_policy.py`
3. `grep "workflow_execution_policy" deploy/deploy.sh` — if found, remove that cp line
4. `grep "workflow_execution_policy" scripts/llmagent.egg-info/SOURCES.txt` — file is auto-generated, no action needed (pip install -e . regenerates)

**Method**: `git rm` (not `rm`) to stage the deletion for commit.

**Details**:
- Do NOT delete until all importers are confirmed clean.
- Pre-deletion checklist:
  ```bash
  grep -rn "WorkflowExecutionPolicy" scripts/ tests/ | grep -v __pycache__  # must be 0
  grep -rn "workflow_execution_policy" scripts/ tests/ | grep -v __pycache__ # must be 0
  ```

## Validation plan
- `uv run python -c "from agent import workflow_execution_policy"` → `ModuleNotFoundError` (expected)
- `uv run mypy scripts/` — no errors from deleted file
- `uv run pytest -x -q` — all pass

---
*Plan: 20260707-095938 (req01) Phase 2 / 20260707-105309 (req13) Phase 5*
