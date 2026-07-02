# Implementation: scripts/mcp/github/ — Update all callers of mcp.github.service stub

**Plan source:** `plans/20260702-202739_plan.md` (Phase 3)
**Target file:** `scripts/mcp/github/`

---

## Goal

Replace all imports from the `mcp.github.service` compatibility stub with direct imports from `mcp.github.service_dispatch`, `mcp.github.service_business`, or `mcp.github.service_init` so that the stub can safely be deleted.

---

## Scope

**In:**
- Update `scripts/mcp/github/server.py`:
  - Replace `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service` with imports from `service_dispatch` and `service_init`
- Update these server sub-modules to replace `from mcp.github.service import GitHubService` with `from mcp.github.service_dispatch import GitHubService`:
  - `scripts/mcp/github/server_repository.py`
  - `scripts/mcp/github/server_issues.py`
  - `scripts/mcp/github/server_file.py`
  - `scripts/mcp/github/server_pull_requests.py`
  - `scripts/mcp/github/server_common.py`
- Update `tests/test_github_mcp_service.py`: same replacement as server sub-modules
- Run `uv run pytest -x -q` after each file change

**Out:**
- Changing MCP tool behavior
- Refactoring unrelated dependency boundaries
- Introducing new tests beyond covering changed import paths

---

## Assumptions

1. `GitHubService` is defined in `mcp.github.service_dispatch`.
2. `build_service` and `_GITHUB_TOKEN` are defined in `mcp.github.service_init`.
3. The stub `mcp/github/service.py` is NOT deleted in this phase (deletion occurs in Phase 6).

---

## Implementation

### Target file

`scripts/mcp/github/` (multiple files)

### Procedure

1. Inspect `scripts/mcp/github/service.py` to confirm which sub-module each symbol (`_GITHUB_TOKEN`, `GitHubService`, `build_service`) originates from.
2. Update `scripts/mcp/github/server.py`:
   - Replace: `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service`
   - With: `from mcp.github.service_init import _GITHUB_TOKEN, build_service` and `from mcp.github.service_dispatch import GitHubService`
   - Run `uv run pytest -x -q`
3. For each of the 5 server sub-modules:
   - Replace: `from mcp.github.service import GitHubService`
   - With: `from mcp.github.service_dispatch import GitHubService`
   - Run `uv run pytest -x -q` after each file
4. Update `tests/test_github_mcp_service.py`:
   - Apply the same replacement as step 3
   - Run `uv run pytest -x -q`
5. After all files are updated, grep to confirm no remaining references:
   `grep -rn "from mcp.github.service import\|import mcp.github.service" scripts/ tests/`

### Method

Edit tool for code changes in each target file.

### Details

- `server.py` imports all three symbols: `_GITHUB_TOKEN`, `GitHubService`, `build_service`
- The 5 server sub-modules and the test file each import only `GitHubService`
- All `GitHubService` references redirect to `mcp.github.service_dispatch`
- `_GITHUB_TOKEN` and `build_service` redirect to `mcp.github.service_init`

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| After each file | `uv run pytest -x -q` | all pass, no new failures |
| MCP server importability | `uv run pytest tests/test_mcp_server_base.py -v` | all pass |
| Grep residual imports | `grep -rn "from mcp.github.service import\|import mcp.github.service" scripts/ tests/` | 0 results |
| Lint | `ruff check scripts/mcp/github/` | 0 errors |
| Type check | `mypy scripts/mcp/github/` | no new errors |
| Tests | `uv run pytest` | all pass |
