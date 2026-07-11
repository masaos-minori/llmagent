# Implementation Procedure: `tests/test_tool_registry.py` — tool_constants frozenset membership completeness test

## Goal

Add a set-membership test verifying that every tool name declared in each of
`tool_constants.py`'s frozensets is actually present in `ToolRegistry`, as a defense against
drift that a pure count-based test could miss (e.g. two independent additions/removals
canceling out numerically).

## Scope

**In-Scope:**
- `tests/test_tool_registry.py`: add one new test function asserting the union of all
  `tool_constants.py` frozensets is a subset of the registry's full set of registered tool
  names.

**Out-of-Scope:**
- Any change to `shared/tool_constants.py` or `shared/tool_registry.py` production code.
- Per-server count tests (already handled by the sibling plan covering
  `tests/test_tool_registry_counts.py` per-server snapshot coverage — not duplicated here).
- The drift-guard docstring addition to `tests/test_tool_registry_counts.py` (separate doc in
  this same plan).

## Assumptions

1. `ToolRegistry` exposes a way to retrieve all registered tool names — assumed to be
   `get_all_tool_names()` (or equivalent; confirm the exact method name by reading
   `shared/tool_registry.py` at implementation time before writing the test).
2. `shared/tool_constants.py` exports (at minimum) `CICD_TOOLS`, `DELETE_TOOLS`, `GIT_TOOLS`,
   `GITHUB_TOOLS`, `MDQ_TOOLS`, `RAG_TOOLS`, `READ_TOOLS`, `SHELL_TOOLS`, `WEB_SEARCH_TOOLS`,
   `WRITE_TOOLS` as `frozenset[str]` constants — confirm the full/current list by reading
   `shared/tool_constants.py` at implementation time, since new frozensets may have been added
   by other, unrelated plans processed earlier.
3. `get_registry()` (module-level accessor, confirmed used elsewhere in the codebase, e.g.
   in the plan's own Design section) returns the singleton/default `ToolRegistry` instance
   already populated with all production tool registrations.
4. This test complements, but does not replace, the fixed-count tests in
   `tests/test_tool_registry_counts.py` — a count match alone cannot detect the case where
   one tool is silently removed from a frozenset while an unrelated tool is added elsewhere,
   keeping the total count unchanged; a full membership/subset check catches this.

## Implementation

### Target file

`tests/test_tool_registry.py`

### Procedure

1. Read `shared/tool_constants.py` in full to get the current, authoritative list of all
   exported frozensets (do not assume the list in the plan's Design section is exhaustive —
   other unrelated plans processed earlier in this session may have added new tool categories).
2. Read `tests/test_tool_registry.py`'s existing imports and fixtures to match established
   conventions (e.g. how the registry singleton is obtained in other tests in this file).
3. Add a new test function that:
   - Imports all current frozensets from `shared.tool_constants`.
   - Computes their union.
   - Obtains the registry's full set of registered tool names via `get_registry()` and its
     tool-name accessor.
   - Asserts the union is a subset of (`<=`) the registry's tool names.
4. If the assertion fails when first run (e.g. due to a genuinely unregistered tool constant
   found during this exercise), do not silently adjust the test to pass — investigate and
   report the discrepancy rather than loosening the assertion. (This is a pre-existing-code
   defect check, not part of this plan's Design-approved behavior change — flag it back to the
   plan owner rather than resolving it unilaterally, since resolving it may be out of this
   plan's scope.)

### Method

Single new test function appended to `tests/test_tool_registry.py`, following existing file
conventions for registry access. No production code changes.

### Details

Reference pseudocode (illustrative signature only):

```python
def test_all_tool_constants_frozensets_are_registered() -> None:
    """Every tool named in every tool_constants.py frozenset is in the registry.

    Complements the fixed-count tests in tests/test_tool_registry_counts.py: two independent
    additions/removals could cancel out a count check numerically without this membership
    check catching the actual drift.
    """
    from shared.tool_constants import (
        CICD_TOOLS, DELETE_TOOLS, GIT_TOOLS, GITHUB_TOOLS, MDQ_TOOLS,
        RAG_TOOLS, READ_TOOLS, SHELL_TOOLS, WEB_SEARCH_TOOLS, WRITE_TOOLS,
        # add/remove per the actual current export list confirmed in Procedure step 1
    )
    registry = get_registry()
    all_expected = (
        CICD_TOOLS | DELETE_TOOLS | GIT_TOOLS | GITHUB_TOOLS | MDQ_TOOLS
        | RAG_TOOLS | READ_TOOLS | SHELL_TOOLS | WEB_SEARCH_TOOLS | WRITE_TOOLS
    )
    assert all_expected <= registry.get_all_tool_names()
```

Adjust the exact registry tool-names accessor name to match the real API (confirm at
implementation time — do not guess if `get_all_tool_names()` does not exist verbatim).

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_tool_registry.py` | 0 errors |
| Tests | `uv run pytest tests/test_tool_registry.py tests/test_tool_registry_counts.py -v` | All pass, including the new membership test |
