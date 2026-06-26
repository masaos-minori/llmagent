# Implementation: Add fail-closed tests to test_service_guards.py

Steps covered: Plan 20260626-091914 — Steps 3-1, 3-2

---

## Goal

Add tests verifying that `_check_workflow()` raises `CicdAuthorizationError` when `workflow_allowlist` is empty (fail-closed), and allows requests when a matching pattern is in the allowlist.

---

## Scope

- **In scope**: `tests/test_service_guards.py` — add/update test functions
- **Out of scope**: production code changes (steps 1-1, 1-2 must be completed first)

---

## Implementation

### Target file
`tests/test_service_guards.py`

### Procedure
1. Read existing tests to understand fixture patterns.
2. Step 3-1 (Fail-closed test):
   ```python
   def test_check_workflow_raises_when_allowlist_empty():
       guards = ServiceGuards(workflow_allowlist=[])
       with pytest.raises(CicdAuthorizationError, match="workflow_allowlist is empty"):
           guards._check_workflow("my-org/my-repo/.github/workflows/deploy.yml")
   ```
3. Step 3-2 (Allowlist match test):
   ```python
   def test_check_workflow_allows_matching_pattern():
       guards = ServiceGuards(workflow_allowlist=["my-org/my-repo/*"])
       guards._check_workflow("my-org/my-repo/.github/workflows/deploy.yml")  # no exception
   
   def test_check_workflow_denies_non_matching_pattern():
       guards = ServiceGuards(workflow_allowlist=["other-org/*"])
       with pytest.raises(CicdAuthorizationError):
           guards._check_workflow("my-org/my-repo/.github/workflows/deploy.yml")
   ```
4. Update any existing test that expected allow-all-when-empty behavior.

### Method
Unit tests. No async needed.

---

## Validation plan

- Run: `uv run pytest tests/test_service_guards.py -x -v` — all new tests pass.
- Run: `uv run pytest tests/ -x` — no regressions.
