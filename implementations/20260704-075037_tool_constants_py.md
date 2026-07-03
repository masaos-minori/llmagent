# Implementation: Add Git/GitHub sub-classifications to `scripts/shared/tool_constants.py`

## Goal

Add `GIT_READ_TOOLS`, `GIT_WRITE_TOOLS`, `GITHUB_READ_TOOLS`, `GITHUB_WRITE_TOOLS`, and
`GITHUB_DANGEROUS_TOOLS` frozensets to `scripts/shared/tool_constants.py`. Redefine `GIT_TOOLS`
and `GITHUB_TOOLS` as derived unions of their respective sub-sets. Aggregate sets remain unchanged
in name and content.

## Scope

- In-Scope: Add 5 new frozensets; redefine `GIT_TOOLS` and `GITHUB_TOOLS` as derived unions.
- Out-of-Scope: No changes to `READ_TOOLS`, `WRITE_TOOLS`, `DELETE_TOOLS`, `SHELL_TOOLS`, or
  `get_all_mcp_tool_names()`. Registry seeding, `is_side_effect()`, and `classify_risk()` updates
  are covered by separate docs.

## Assumptions

1. `GIT_TOOLS` currently contains 10 tools (5 read + 5 write as listed in plan).
2. `GITHUB_TOOLS` currently contains 21 tools (12 read + 7 write + 2 dangerous).
3. `get_all_mcp_tool_names()` unions all sets including `GIT_TOOLS` and `GITHUB_TOOLS`; since
   these become derived unions with identical elements, no change to `get_all_mcp_tool_names()`.
4. All tool names in the sub-classifications exactly match those currently in the aggregate sets.

## Implementation

### Target file

`scripts/shared/tool_constants.py` (existing)

### Procedure

1. Read `tool_constants.py` to find where `GIT_TOOLS` and `GITHUB_TOOLS` are currently defined.
2. Replace the current `GIT_TOOLS` definition with `GIT_READ_TOOLS | GIT_WRITE_TOOLS` sub-sets
   and derived union.
3. Replace the current `GITHUB_TOOLS` definition with `GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS |
   GITHUB_DANGEROUS_TOOLS` sub-sets and derived union.
4. Run `uv run ruff check scripts/shared/tool_constants.py` — expect 0 errors.
5. Verify aggregate set integrity:
   ```bash
   PYTHONPATH=scripts python -c "
   from shared.tool_constants import GIT_TOOLS, GIT_READ_TOOLS, GIT_WRITE_TOOLS, GITHUB_TOOLS, \
     GITHUB_READ_TOOLS, GITHUB_WRITE_TOOLS, GITHUB_DANGEROUS_TOOLS
   assert GIT_TOOLS == GIT_READ_TOOLS | GIT_WRITE_TOOLS
   assert GITHUB_TOOLS == GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
   assert len(GIT_TOOLS) == 10
   assert len(GITHUB_TOOLS) == 21
   print('OK')
   "
   ```

### Method

```python
# Git sub-classifications
GIT_READ_TOOLS: frozenset[str] = frozenset({
    "git_status",
    "git_log",
    "git_diff",
    "git_branch",
    "git_show",
})

GIT_WRITE_TOOLS: frozenset[str] = frozenset({
    "git_add",
    "git_commit",
    "git_checkout",
    "git_pull",
    "git_push",
})

GIT_TOOLS: frozenset[str] = GIT_READ_TOOLS | GIT_WRITE_TOOLS

# GitHub sub-classifications
GITHUB_READ_TOOLS: frozenset[str] = frozenset({
    "github_search_repositories",
    "github_list_branches",
    "github_list_commits",
    "github_get_commit",
    "github_search_code",
    "github_get_file_contents",
    "github_list_issues",
    "github_get_issue",
    "github_search_issues",
    "github_list_pull_requests",
    "github_get_pull_request",
    "github_search_pull_requests",
})

GITHUB_WRITE_TOOLS: frozenset[str] = frozenset({
    "github_create_branch",
    "github_create_or_update_file",
    "github_push_files",
    "github_create_issue",
    "github_add_issue_comment",
    "github_create_pull_request",
    "github_update_pull_request",
})

GITHUB_DANGEROUS_TOOLS: frozenset[str] = frozenset({
    "github_delete_file",
    "github_merge_pull_request",
})

GITHUB_TOOLS: frozenset[str] = GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
```

### Details

- Place sub-classification frozensets BEFORE the derived union (e.g., `GIT_READ_TOOLS` and
  `GIT_WRITE_TOOLS` must be defined before `GIT_TOOLS = GIT_READ_TOOLS | GIT_WRITE_TOOLS`).
- If `GIT_TOOLS` was previously a literal frozenset, replace it entirely with the derived union.
- `SHELL_TOOLS` should be added (if not already defined) as `frozenset({"shell_run"})` so that
  `_SIDE_EFFECT_TOOLS` in `tool_executor_helpers.py` can reference it.

## Validation plan

```bash
# Import all new symbols
PYTHONPATH=scripts python -c "
from shared.tool_constants import (
    GIT_READ_TOOLS, GIT_WRITE_TOOLS, GIT_TOOLS,
    GITHUB_READ_TOOLS, GITHUB_WRITE_TOOLS, GITHUB_DANGEROUS_TOOLS, GITHUB_TOOLS,
)
assert GIT_TOOLS == GIT_READ_TOOLS | GIT_WRITE_TOOLS
assert GITHUB_TOOLS == GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
assert len(GIT_TOOLS) == 10 and len(GITHUB_TOOLS) == 21
print('OK')
"
# Expected: OK

# Lint
uv run ruff check scripts/shared/tool_constants.py
# Expected: 0 errors

# Registry tests still pass
uv run pytest tests/test_tool_registry.py -q
# Expected: all pass

# Architecture
PYTHONPATH=scripts uv run lint-imports
# Expected: 0 violations
```
