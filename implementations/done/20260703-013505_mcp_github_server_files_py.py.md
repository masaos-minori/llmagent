# Implementation: scripts/mcp/github/ — Update all remaining files to remove service.py dependency

**Plan source:** `plans/20260702-202857_plan.md` (Phase 2 (steps 3-7))
**Target file:** `scripts/mcp/github/`

---

## Goal

Update all server sub-modules, the test file, and the package `__init__.py` so that no file imports from `mcp.github.service`; each import is redirected to `mcp.github.service_dispatch` or `mcp.github.service_init`.

---

## Scope

**In:**
- `scripts/mcp/github/server_common.py` line 13
- `scripts/mcp/github/server_file.py` line 24
- `scripts/mcp/github/server_issues.py` line 26
- `scripts/mcp/github/server_pull_requests.py` line 28
- `scripts/mcp/github/server_repository.py` line 28
- `tests/test_github_mcp_service.py` line 28
- `scripts/mcp/github/__init__.py` line 17: update import and module docstring

**Out:**
- Changes to `scripts/mcp/github/server.py` (handled in step 2 / previous target)
- Changes to any logic or runtime behavior
- Deletion of `service.py` (handled in Phase 3)

---

## Assumptions

1. Each of the five server sub-modules imports only `GitHubService` from `mcp.github.service`.
2. The test file imports `GitHubService` from `mcp.github.service` at line 28.
3. `__init__.py` re-exports symbols from `service` and mentions it in the module docstring.

---

## Implementation

### Target file

`scripts/mcp/github/`

### Procedure

1. **server_common.py (line 13):** Replace
   ```python
   from mcp.github.service import GitHubService
   ```
   with
   ```python
   from mcp.github.service_dispatch import GitHubService  # noqa: F401
   ```
   Run `uv run pytest -x -q`.

2. **server_file.py (line 24):** Replace
   ```python
   from mcp.github.service import GitHubService
   ```
   with
   ```python
   from mcp.github.service_dispatch import GitHubService  # noqa: F401
   ```
   Run `uv run pytest -x -q`.

3. **server_issues.py (line 26):** Replace
   ```python
   from mcp.github.service import GitHubService
   ```
   with
   ```python
   from mcp.github.service_dispatch import GitHubService  # noqa: F401
   ```
   Run `uv run pytest -x -q`.

4. **server_pull_requests.py (line 28):** Replace
   ```python
   from mcp.github.service import GitHubService
   ```
   with
   ```python
   from mcp.github.service_dispatch import GitHubService  # noqa: F401
   ```
   Run `uv run pytest -x -q`.

5. **server_repository.py (line 28):** Replace
   ```python
   from mcp.github.service import GitHubService
   ```
   with
   ```python
   from mcp.github.service_dispatch import GitHubService  # noqa: F401
   ```
   Run `uv run pytest -x -q`.

6. **tests/test_github_mcp_service.py (line 28):** Replace
   ```python
   from mcp.github.service import GitHubService
   ```
   with
   ```python
   from mcp.github.service_dispatch import GitHubService
   ```
   Run `uv run pytest -x -q`.

7. **scripts/mcp/github/__init__.py (line 17):** Replace the `service` import with direct imports from `service_dispatch` and `service_init`. Update the module docstring to remove `service` from the sub-modules list.
   Run `uv run pytest -x -q`.

### Method

Edit tool for code changes.

### Details

For the five server sub-modules the replacement pattern is uniform:

```python
# Before
from mcp.github.service import GitHubService

# After
from mcp.github.service_dispatch import GitHubService  # noqa: F401
```

The `# noqa: F401` suppression is added because `GitHubService` may be imported for
re-export / type annotation purposes and ruff would otherwise flag the import as unused.

For the test file, no `# noqa` is needed because the symbol is actively used.

For `__init__.py`:
- Remove any `from mcp.github.service import ...` line.
- Add equivalent imports from `mcp.github.service_dispatch` and/or `mcp.github.service_init`.
- Remove `service` from the list of sub-modules mentioned in the module docstring.

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| After each file | uv run pytest -x -q | all pass |
| Lint | ruff check scripts/mcp/github/ | 0 errors |
| Type check | mypy scripts/mcp/github/ | no new errors |
| Tests | uv run pytest | all pass |
