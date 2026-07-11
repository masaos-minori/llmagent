# Implementation Procedure: get_tool_names() sorted-order guarantee (tool_registry.py)

## Goal

Make `ToolRegistry.get_tool_names()` explicitly guarantee alphabetically-sorted output, instead of
relying on the accidental fact that today's only caller (`_register_set()` / `_populate_default_registry()`)
happens to insert tools in sorted order. This closes a latent determinism gap: any future caller that
registers tools out of order would otherwise silently get non-deterministic snapshot-test output.

## Scope

**In-Scope:**
- `scripts/shared/tool_registry.py`: `ToolRegistry.get_tool_names()` (currently lines 70-72)
  - Change the return statement from `list(self._by_server.get(server_key, []))` to
    `sorted(self._by_server.get(server_key, []))`
  - Expand the method docstring to state the sorted-order guarantee as a documented contract of the
    method itself, not an artifact of caller behavior

**Out-of-Scope:**
- `shared/tool_constants.py` — no changes
- `_populate_default_registry()` / `_register_set()` — registration order and the 10 server_key names
  are unchanged
- `get_servers()` (lines 78-80) — already returns `sorted(self._by_server.keys())`; no change needed
- `validate_tool_names_match()` / `validate_live_tools_match()` (lines 82-132) — both already convert
  `get_tool_names()`'s result to a `set()` before comparing, so this change cannot affect their behavior

## Assumptions

- `get_tool_names()` today returns registration order (`list(...)`), which happens to be sorted only
  because the default registry population path (`_register_set()`) iterates `sorted(tool_names)`.
- The change is behavior-preserving for every existing caller: all current registration paths already
  insert in sorted order, so the returned list's contents and order do not change for any existing test
  or code path — only the contract becomes explicit and enforced independent of caller behavior.
- No caller relies on `get_tool_names()`'s *registration* order specifically (as opposed to sorted
  order) — confirmed during planning by reading every call site.

## Implementation

### Target file

`scripts/shared/tool_registry.py`

### Procedure

1. Locate `ToolRegistry.get_tool_names()` (current lines 70-72).
2. Replace the return expression `list(self._by_server.get(server_key, []))` with
   `sorted(self._by_server.get(server_key, []))`.
3. Rewrite the docstring to state:
   - The method returns tool names sorted alphabetically.
   - This ordering is a guaranteed contract of the method (not just an artifact of default
     registration order); callers and tests may rely on it directly without re-sorting.

### Method

Single-line logic change plus docstring expansion — no new parameters, no new control flow, no change
to the method signature (`def get_tool_names(self, server_key: str) -> list[str]`).

### Details

Target end state (for reference only — do not write this code in this design step):

```python
def get_tool_names(self, server_key: str) -> list[str]:
    """Return all tool names for a server_key, sorted alphabetically.

    Ordering is a guaranteed contract of this method (not just an artifact of
    default registration order) — callers and tests may rely on it directly
    without re-sorting.
    """
    return sorted(self._by_server.get(server_key, []))
```

Notes for the implementer:
- Keep the return type `list[str]` unchanged (`sorted()` on a `list[str]` returns `list[str]`).
- Do not change `_by_server`'s internal storage type or the `register()` method.
- This is an independently revertable, single-file change (Phase 1 of the plan) — do not bundle it
  with the test additions from Phase 2 in the same commit if commit granularity matters downstream.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_registry.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_registry.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Tests (existing regressions) | `uv run pytest tests/test_tool_registry_counts.py tests/test_tool_registry.py tests/test_tool_constants.py -v` | All pass (this change alone should not break any existing test, since sorted order matches current registration order) |
| Regression | `uv run pytest tests/test_routing_duplicate_ownership.py tests/test_startup_routing_drift.py tests/test_github_tool_registry.py tests/test_mdq_routing.py -q` | No new failures (confirms the sort-order change doesn't affect any dependent test) |
| Manual count re-verify | `PYTHONPATH=scripts uv run python -c "from shared.tool_registry import get_registry; r = get_registry(); print(len(r.get_all_tool_names())); [print(k, len(r.get_tool_names(k))) for k in r.get_servers()]"` | Matches the 10 counts recorded in the plan's Assumption 1 exactly |
