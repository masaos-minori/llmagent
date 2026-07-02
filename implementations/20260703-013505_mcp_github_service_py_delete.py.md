# Implementation: scripts/mcp/github/service.py — Verify references and delete backward-compatible stub

**Plan source:** `plans/20260702-202857_plan.md` (Phase 3 (step 10))
**Target file:** `scripts/mcp/github/service.py`

---

## Goal

Confirm that all import references to `mcp.github.service` have been eliminated from the codebase, then delete the backward-compatible re-export stub `scripts/mcp/github/service.py`, and validate that nothing is broken afterward.

---

## Scope

**In:**
- Phase 1 prerequisite: grep to confirm the 8 files that currently import from `mcp.github.service`
- Phase 3: delete `scripts/mcp/github/service.py`
- Phase 4: confirm zero remaining references and run the full validation suite

**Out:**
- Any changes to other source files (those are handled in Phase 2)
- Changes to `service_dispatch.py` or `service_init.py`

---

## Assumptions

1. All Phase 2 edits (Targets 1 and 2) have been completed and tests pass before this step.
2. The grep pattern `from mcp.github.service import|import mcp.github.service` accurately identifies all consumers of the stub.
3. After Phase 2, the grep should return 0 matches (or only the stub file itself).

---

## Implementation

### Target file

`scripts/mcp/github/service.py`

### Procedure

1. **Phase 1 prerequisite — confirm existing references:**
   ```bash
   grep -rn "from mcp.github.service import\|import mcp.github.service" /home/masaos/llmagent/ --include="*.py"
   ```
   Confirm the output matches the expected 8 files listed in the plan. Do not proceed if unexpected files appear.

2. **Complete Phase 2 edits** (handled by Targets 1 and 2 above) so that the grep returns 0 results outside of `service.py` itself.

3. **Phase 3 — delete the stub:**
   ```bash
   rm scripts/mcp/github/service.py
   ```

4. **Phase 4 — confirm zero remaining references:**
   ```bash
   grep -rn "from mcp.github.service import\|import mcp.github.service" scripts/ tests/ docs/
   ```
   Expected: no output (exit code 1 from grep is acceptable; exit code 0 with output is a failure).

5. Run the full validation suite (see Validation plan below).

### Method

Manual grep for validation steps; Bash `rm` for deletion.

### Details

The stub `service.py` was a backward-compatible re-export shim that forwarded all public symbols
from `service_dispatch` and `service_init`. Once all consumers have been updated to import
directly from the canonical modules, the stub serves no purpose and can be removed.

Expected pre-deletion grep results (8 files):
- `scripts/mcp/github/server.py`
- `scripts/mcp/github/server_common.py`
- `scripts/mcp/github/server_file.py`
- `scripts/mcp/github/server_issues.py`
- `scripts/mcp/github/server_pull_requests.py`
- `scripts/mcp/github/server_repository.py`
- `scripts/mcp/github/__init__.py`
- `tests/test_github_mcp_service.py`

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No remaining refs | grep -rn "from mcp.github.service import\|import mcp.github.service" scripts/ tests/ docs/ | no output |
| Lint | ruff check scripts/mcp/github/ | 0 errors |
| Targeted tests | uv run pytest tests/test_github_mcp_service.py -v | all pass |
| Full tests | uv run pytest | all pass |
| Import lint | PYTHONPATH=scripts uv run lint-imports | no errors |
