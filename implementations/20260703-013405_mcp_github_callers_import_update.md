# Implementation: scripts/mcp/github/ — Update mcp.github.service Stub Import Callers

**Plan source:** `plans/20260702-202739_plan.md` (Phase 3)
**Target file:** `scripts/mcp/github/server.py`, `server_common.py`, `server_file.py`, `server_issues.py`, `server_pull_requests.py`, `server_repository.py`, `tests/test_github_mcp_service.py`

---

## Goal

Replace all `from mcp.github.service import ...` statements with direct imports from `mcp.github.service_dispatch` or `mcp.github.service_init`.

---

## Scope

**In:**
- `scripts/mcp/github/server.py` (line 60): replace `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service` with two-line import from `service_dispatch` and `service_init`
- `scripts/mcp/github/server_common.py` (line 13): `GitHubService` → `from mcp.github.service_dispatch import`
- `scripts/mcp/github/server_file.py` (line 24): same
- `scripts/mcp/github/server_issues.py` (line 26): same
- `scripts/mcp/github/server_pull_requests.py` (line 28): same
- `scripts/mcp/github/server_repository.py` (line 28): same
- `tests/test_github_mcp_service.py` (line 28): same

**Out:**
- Deleting `scripts/mcp/github/service.py` (Phase 6 — separate step)
- Changing `GitHubService` class behavior

---

## Assumptions

1. `GitHubService` for type annotations comes from `mcp.github.service_dispatch`.
2. `build_service` and `_GITHUB_TOKEN` come from `mcp.github.service_init`.

---

## Implementation

### Target file

`scripts/mcp/github/server.py` and related server sub-modules

### Procedure

1. `server.py` line 60: replace with:
   ```python
   from mcp.github.service_dispatch import GitHubService
   from mcp.github.service_init import _GITHUB_TOKEN, build_service
   ```
2. `server_common.py`, `server_file.py`, `server_issues.py`, `server_pull_requests.py`, `server_repository.py`: replace `from mcp.github.service import GitHubService` with `from mcp.github.service_dispatch import GitHubService  # noqa: F401`
3. `tests/test_github_mcp_service.py`: replace `from mcp.github.service import GitHubService` with `from mcp.github.service_dispatch import GitHubService`
4. Run `uv run pytest -x -q` after each file.

### Method

Edit tool for each file.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Caller check | `grep -R "from mcp.github.service import" scripts tests docs` | 0 matches |
| Lint | `ruff check scripts/mcp/github/` | 0 errors |
| Tests | `uv run pytest tests/test_github_mcp_service.py -v` | All pass |
| Full suite | `uv run pytest` | All pass |
