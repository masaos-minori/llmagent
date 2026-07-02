# Implementation: scripts/mcp/github/__init__.py — Remove package-level re-exports

**Plan source:** `plans/20260702-202739_plan.md` (Phase 4)
**Target file:** `scripts/mcp/github/__init__.py`

---

## Goal

Remove the re-export line and `__all__` list from `mcp/github/__init__.py` that previously exposed `_GITHUB_TOKEN`, `GitHubService`, and `build_service` at the package namespace level, then confirm no remaining callers import these symbols from the package namespace.

---

## Scope

**In:**
- Remove from `scripts/mcp/github/__init__.py`:
  - The line: `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service`
  - The `__all__` list that includes these names
- grep the full repo to confirm 0 remaining callers of `from mcp.github import GitHubService`, `from mcp.github import build_service`, or `from mcp.github import _GITHUB_TOKEN`
- Run `uv run pytest -x -q`

**Out:**
- Changing MCP tool behavior
- Refactoring unrelated code in `__init__.py`
- Introducing new tests beyond covering changed import paths

---

## Assumptions

1. Phase 3 has been completed; no caller of `mcp.github.service_dispatch`, `mcp.github.service_init`, etc. relies on the package-level re-exports.
2. The `__all__` list in `__init__.py` contains only the re-exported symbols being removed; any other content in `__all__` must be preserved.
3. After removal, `mcp/github/__init__.py` may be left empty or contain only unrelated package init code.

---

## Implementation

### Target file

`scripts/mcp/github/__init__.py`

### Procedure

1. Read `scripts/mcp/github/__init__.py` to inspect its full content.
2. Remove the re-export line: `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service`.
3. Remove the `__all__` list (or remove the three symbol names from it if other names are also listed).
4. Run grep across the full repo to confirm 0 remaining callers:
   - `grep -rn "from mcp.github import GitHubService" scripts/ tests/ docs/`
   - `grep -rn "from mcp.github import build_service" scripts/ tests/ docs/`
   - `grep -rn "from mcp.github import _GITHUB_TOKEN" scripts/ tests/ docs/`
5. Run `uv run pytest -x -q`.

### Method

Edit tool for code changes in `scripts/mcp/github/__init__.py`.

### Details

- The re-export line references `mcp.github.service`, which is the stub targeted for deletion in Phase 6; removing this re-export is a prerequisite for stub deletion.
- If `__all__` contains only the three removed symbols, delete the entire `__all__` declaration.
- If `__all__` contains other symbols, remove only `_GITHUB_TOKEN`, `GitHubService`, and `build_service` from the list.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Grep GitHubService | `grep -rn "from mcp.github import GitHubService" scripts/ tests/ docs/` | 0 results |
| Grep build_service | `grep -rn "from mcp.github import build_service" scripts/ tests/ docs/` | 0 results |
| Grep _GITHUB_TOKEN | `grep -rn "from mcp.github import _GITHUB_TOKEN" scripts/ tests/ docs/` | 0 results |
| Lint | `ruff check scripts/mcp/github/__init__.py` | 0 errors |
| Type check | `mypy scripts/mcp/github/__init__.py` | no new errors |
| Tests | `uv run pytest -x -q` | all pass |
