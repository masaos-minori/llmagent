# Implementation procedure: `scripts/agent/services/mcp_tool_discovery.py` (optional — defensive type-check for `enabled`)

Source plan: `plans/done/20260721-032809_plan.md` ("Fix `enabled_for_llm` never being set True
for discovered tools"), Implementation step 4 (UNK-02, optional — confirm scope with reviewer
before implementing, per the plan's own wording).

**Filename check — not a duplicate of prior docs, and distinct from the core-fix doc for this
same file**: this doc targets `_validate_and_normalize_entry()` (lines 210-275), a different
function in the same file from the core fix's `_dedupe_and_build()` (see
`implementations/20260721-162943_mcp_tool_discovery.py.md`). Direct read of the current source
confirms the type-checked field tuple at lines 250-255 is exactly
`("status", str), ("is_write", bool), ("requires_serial", bool), ("resource_scope", str)` — no
`"enabled"` entry — so this defensive check is not yet present. This is an independent,
optional change; it does not need to land in the same commit as the core fix, but should not
conflict with it either (different function, same file).

## Goal

A malformed (non-bool) `enabled` value in a server's `/v1/tools` entry is rejected as a
`WARNING`-severity finding at discovery time, instead of silently passing through Python
truthiness into `RuntimeTool.enabled_for_llm`'s declared `bool` type.

## Scope

**In scope**
- `scripts/agent/services/mcp_tool_discovery.py::_validate_and_normalize_entry()` — extend the
  existing type-checked field tuple.

**Out of scope**
- The core `enabled_for_llm` fix in `_dedupe_and_build()` — tracked separately (this doc's
  companion, `implementations/20260721-162943_mcp_tool_discovery.py.md`); this doc's change is
  purely a validation-time defense, independent of and additional to that fix.
- Any change to what happens when `enabled` is a valid bool — behavior for valid values is
  entirely defined by the core fix's `bool(entry.get("enabled", True))` expression.

## Assumptions

1. No current server sends a non-bool `enabled` value (confirmed by the source plan's own Step-4
   verification: all 4 servers implementing the schema — `file/read`, `file/write`, `file/delete`,
   `git` — send real JSON booleans). This change guards against a *future* misbehaving server, per
   the source plan's own stated risk ("6 servers without the schema could add it later with a bug
   that emits a bad `enabled` value ... echoing the original failure mode").
2. The existing per-field validation pattern (lines 250-263) already has the exact shape needed:
   iterate `(field_name, expected_type)` pairs, skip if the field is absent, reject with a
   `WARNING` `StartupCheckOutcome` if present but wrong-typed. Adding `("enabled", bool)` to this
   tuple requires no new branching logic, only a new tuple entry.
3. This check runs *before* `_dedupe_and_build()` ever sees the entry (per the existing call order:
   `_fetch_server_tools()` → `_validate_and_normalize_entry()` → accumulate → `_dedupe_and_build()`),
   so a malformed `enabled` value never reaches the core fix's `bool(entry.get("enabled", True))`
   expression at all — the entry is dropped entirely, consistent with how every other malformed
   field is handled today (excluded from the registry, one `WARNING` finding emitted).

## Implementation

### Target file

`scripts/agent/services/mcp_tool_discovery.py` (existing).

### Procedure

1. In `_validate_and_normalize_entry()` (method starting at line 210), locate the type-checked
   field tuple at lines 250-255:
   ```python
   for field_name, expected_type in (
       ("status", str),
       ("is_write", bool),
       ("requires_serial", bool),
       ("resource_scope", str),
   ):
   ```
2. Add `("enabled", bool)` as a new entry in this tuple.
3. No other lines change — the existing loop body (lines 256-263) already handles the new entry
   generically (checks `field_name in entry`, compares `isinstance(entry[field_name],
   expected_type)`, emits the same `WARNING`-severity `StartupCheckOutcome` shape on mismatch).

### Method

One-line addition to an existing tuple literal; no new branching logic, no new helper function.

### Details

Target tuple after the change:

```python
for field_name, expected_type in (
    ("status", str),
    ("is_write", bool),
    ("requires_serial", bool),
    ("resource_scope", str),
    ("enabled", bool),
):
```

The existing loop body (unchanged, shown for context, lines 256-263):

```python
if field_name in entry and not isinstance(entry[field_name], expected_type):
    msg = (
        f"{server_key}: tool {name!r} has invalid {field_name} "
        f"{entry[field_name]!r} (expected {expected_type.__name__})"
    )
    return None, StartupCheckOutcome(
        source=_SOURCE, status=StartupCheckStatus.WARNING, message=msg
    )
```

Note: `bool` is a subtype of `int` in Python, so `isinstance(1, bool)` is `False` (correct — `1`
is not a valid `enabled` value) but `isinstance(True, int)` is `True` (irrelevant here since the
check is `isinstance(value, bool)`, not the reverse). No special-casing needed beyond the
existing generic loop.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all pass, including a new case asserting a non-bool `enabled` value (e.g. `"enabled": "yes"`) produces a `WARNING` finding and excludes the tool |
| Full suite | `uv run pytest -q` | no new failures |
| Lint/format | `uv run ruff format scripts/ && uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Security | `uv run bandit -r scripts/agent/services/mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines — requires a matching test case (see Risks note in source plan: "if UNK-01/UNK-02 are implemented, add matching test assertions ... in the same commit/PR") |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
