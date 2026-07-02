# Implementation: scripts/mcp/github/server.py — Update import to use service_dispatch and service_init

**Plan source:** `plans/20260702-202857_plan.md` (Phase 2 (step 2))
**Target file:** `scripts/mcp/github/server.py`

---

## Goal

Replace the import of `_GITHUB_TOKEN`, `GitHubService`, and `build_service` from the backward-compatible stub `mcp.github.service` with direct imports from the two canonical modules `mcp.github.service_dispatch` and `mcp.github.service_init`.

---

## Scope

**In:**
- Line 60 of `scripts/mcp/github/server.py`: replace the single combined import with two separate imports

**Out:**
- Changes to any other file in this phase
- Changes to logic or runtime behavior of server.py

---

## Assumptions

1. `mcp.github.service_dispatch` exports `GitHubService`.
2. `mcp.github.service_init` exports `_GITHUB_TOKEN` and `build_service`.

---

## Implementation

### Target file

`scripts/mcp/github/server.py`

### Procedure

1. Open `scripts/mcp/github/server.py`.
2. Locate line 60 containing the import `from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service`.
3. Replace that single line with two lines:
   ```python
   from mcp.github.service_dispatch import GitHubService
   from mcp.github.service_init import _GITHUB_TOKEN, build_service
   ```
4. Save the file.
5. Run `uv run pytest -x -q` and confirm all tests pass.

### Method

Edit tool for code changes.

### Details

Old line (line 60):
```python
from mcp.github.service import _GITHUB_TOKEN, GitHubService, build_service
```

New lines:
```python
from mcp.github.service_dispatch import GitHubService
from mcp.github.service_init import _GITHUB_TOKEN, build_service
```

---

## Validation plan

| Step | Command | Expected outcome |
|---|---|---|
| Tests | uv run pytest -x -q | all pass |
| Lint | ruff check scripts/mcp/github/server.py | 0 errors |
| Type check | mypy scripts/mcp/github/server.py | no new errors |
