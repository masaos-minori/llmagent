# Implementation: Remove or make fail-closed github allowed_workflows in service_security.py

Steps covered: Plan 20260626-091915 — Step 1-1

---

## Goal

Audit `scripts/mcp/github/service_security.py` for the `allowed_workflows` feature. If the feature is unimplemented (check is a no-op or always passes), remove it from the code and config rather than making it fail-closed.

---

## Scope

- **In scope**: `scripts/mcp/github/service_security.py` — `allowed_workflows` check
- **Out of scope**: config (step 2A-1); docs (steps 2A-2, 3-1)

---

## Assumptions

- `service_security.py` has an `allowed_workflows` check that is either (a) fail-open by default or (b) entirely unimplemented.
- The plan recommends: if unimplemented → delete from config and docs; if implemented but fail-open → make fail-closed.
- `grep -n "allowed_workflows" scripts/mcp/github/` will reveal the current state.

---

## Implementation

### Target file
`scripts/mcp/github/service_security.py`

### Procedure
1. Read `scripts/mcp/github/service_security.py` — find `allowed_workflows` references.
2. If the check is `if not self._allowed_workflows: return` (fail-open):
   - Change to fail-closed:
     ```python
     if not self._allowed_workflows:
         raise GitHubAuthorizationError(
             "allowed_workflows is empty — all workflow triggers denied (fail-closed)."
         )
     ```
3. If the check is completely absent (field exists in config but never checked):
   - Remove the `allowed_workflows` field from the class.
   - Document in step 2A-2 that this was removed as unimplemented.
4. In both cases: if `_allowed_workflows` is initialized from config, keep that wiring.

### Method
Audit-first; one of two outcomes: fail-closed change or removal.

---

## Validation plan

- Run: `uv run pytest tests/test_mcp_github_security.py -x -v` — pass.
- Pre-commit: `pre-commit run --all-files` — ruff + mypy must pass.
