# Implementation: tests/test_github_mcp_service.py — Update GitHubService Import

**Plan source:** `plans/20260702-202744_plan.md` (Phase 2)
**Target file:** `tests/test_github_mcp_service.py`

---

## Goal

Update line 28 of `tests/test_github_mcp_service.py` to import `GitHubService` directly from `mcp.github.service_dispatch` instead of `mcp.github.service`.

---

## Scope

**In:**
- Line 28: `from mcp.github.service import GitHubService` → `from mcp.github.service_dispatch import GitHubService`

**Out:**
- Changes to test logic or assertions
- Changes to other test files

---

## Assumptions

1. `mcp.github.service_dispatch.GitHubService` is the full combined dispatch+business class — the same class the stub was re-exporting.
2. No other lines in the test file reference `mcp.github.service`.

---

## Implementation

### Target file

`tests/test_github_mcp_service.py`

### Procedure

1. Replace line 28: `from mcp.github.service import GitHubService` with `from mcp.github.service_dispatch import GitHubService`
2. Run `uv run pytest tests/test_github_mcp_service.py -v`

### Method

Edit tool for single-line replacement.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No old import | `grep "from mcp.github.service import" tests/test_github_mcp_service.py` | 0 matches |
| Tests | `uv run pytest tests/test_github_mcp_service.py -v` | All pass |
| Full suite | `uv run pytest` | All pass |
