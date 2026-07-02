# Implementation: scripts/mcp/github/__init__.py — Remove Service Re-exports (Validation Plan Phase 4)

**Plan source:** `plans/20260702-202739_plan.md` (Phase 4)
**Target file:** `scripts/mcp/github/__init__.py`

---

## Goal

Remove the re-export line for `GitHubService`, `build_service`, and `_GITHUB_TOKEN` from `mcp/github/__init__.py` and confirm no remaining callers use the package-level namespace.

---

## Scope

**In:**
- Remove `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service` and `__all__` from `__init__.py`
- grep for remaining `from mcp.github import GitHubService|build_service|_GITHUB_TOKEN` across full repo

**Out:**
- Removing `mcp/github/service.py` itself (Phase 6 / plan 202857)
- Changing `GitHubService` business logic

---

## Assumptions

1. All callers have been updated to direct sub-module imports in Phase 3.
2. Leaving `__init__.py` with only a docstring is the intended end-state.

---

## Implementation

### Target file

`scripts/mcp/github/__init__.py`

### Procedure

1. Remove the line: `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service  # noqa: F401`
2. Remove `__all__ = ["GitHubService", "build_service", "_GITHUB_TOKEN"]`
3. Update docstring: remove `service — re-export stub for backward compatibility` line
4. Run `grep -R "from mcp.github import GitHubService\|from mcp.github import build_service\|from mcp.github import _GITHUB_TOKEN" scripts tests docs` — expect 0 matches.
5. Run `uv run pytest -x -q`.

### Method

Edit tool. Bash for verification grep.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No pkg-level imports | `grep -R "from mcp.github import GitHubService\|build_service\|_GITHUB_TOKEN" scripts tests docs` | 0 matches |
| Lint | `ruff check scripts/mcp/github/` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest` | All pass |
