# Implementation: scripts/mcp/github/__init__.py — Remove Package-Level Service Re-exports

**Plan source:** `plans/20260702-202744_plan.md` (Phase 1)
**Target file:** `scripts/mcp/github/__init__.py`

---

## Goal

Remove service symbol re-exports from `mcp/github/__init__.py` so that no code imports `GitHubService`, `build_service`, or `_GITHUB_TOKEN` via the `mcp.github` package namespace.

---

## Scope

**In:**
- Remove `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service  # noqa: F401`
- Remove `__all__ = ["GitHubService", "build_service", "_GITHUB_TOKEN"]`
- Update module docstring: remove `service — re-export stub for backward compatibility` line
- Verify file contains only module docstring after edit

**Out:**
- Removing or modifying `mcp/github/service.py` itself (separate ticket)
- Changing `GitHubService` business logic

---

## Assumptions

1. `mcp/github/service.py` continues to exist during this change; only the `__init__.py` re-export is removed.
2. No code outside `scripts/`, `tests/`, `docs/` imports from `mcp.github` (verified by grep — no matches found).
3. The correct replacement import for `GitHubService` in tests is `from mcp.github.service_dispatch import GitHubService`.

---

## Implementation

### Target file

`scripts/mcp/github/__init__.py`

### Procedure

1. Remove the re-export import line and `__all__`.
2. Update docstring to remove the `service` sub-module reference.
3. Verify the file contains only the module docstring (and `from __future__ import annotations` if needed).
4. Run `grep -R "from mcp.github import GitHubService\|from mcp.github import build_service\|from mcp.github import _GITHUB_TOKEN" scripts tests docs` — expect 0 matches.
5. Run `ruff check scripts/mcp/github/` and `uv run pytest`.

### Method

Edit tool for targeted line removal and docstring update.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| No pkg-level imports | `grep -R "from mcp.github import GitHubService\|build_service\|_GITHUB_TOKEN" scripts tests docs` | 0 matches |
| Lint | `ruff check scripts/mcp/github/` | 0 errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest` | All pass |
