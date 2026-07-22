# Implementation procedure: `scripts/shared/runtime_tool_registry.py` (optional — `diagnostics()` sourced `disabled_reason`)

Source plan: `plans/done/20260721-032809_plan.md` ("Fix `enabled_for_llm` never being set True
for discovered tools"), Implementation step 5 / Design §2 (UNK-01, optional — confirm scope with
reviewer before implementing, per the plan's own wording).

**Filename check — not a duplicate of prior docs**: `implementations/done/` contains 3 docs whose
filenames match `runtime_tool_registry.py` (`20260717-203200_runtime_tool_registry.py.md`,
`20260717-203310_test_runtime_tool_registry.py.md`, `20260720-142312_runtime_tool_registry.py.md`).
Read in full: `20260717-203200` designs the *original* class creation (9 base methods, no
`diagnostics()` at all — confirmed, `grep -c diagnostics` on that doc → 0). `20260720-142312` was
not opened in full text here but its filename/timestamp corresponds to the routing-layer wiring
cycle that (per commit `d510c87f`, confirmed via `git log -- scripts/shared/runtime_tool_registry.py`)
introduced the `diagnostics()` method as it exists in the *current* real source — sourcing
`disabled_reason` from `tool.status` (`""` if `"active"` else the status string), **not** from
`tool.raw_definition.get("disabled_reason")`. Direct read of the current real source
(`scripts/shared/runtime_tool_registry.py:173-191`) confirms this: the method body computes
`disabled_reason = "" if tool.status == "active" else tool.status` — the status-derived value the
prior cycle intentionally implemented, not the raw_definition-derived value this plan's Design §2
calls for. This doc is not a duplicate; it changes an existing method's internal logic to source a
different (and, per this plan, more accurate) value for one field.

## Goal

`RuntimeToolRegistry.diagnostics()`'s `disabled_reason` field reflects the discovery-time
`disabled_reason` string a server actually sent in its `/v1/tools` entry (when present), instead of
a value synthesized from `tool.status`, giving `/mcp status`'s diagnostics table (already wired,
see Scope) a real audit trail for *why* a tool is `enabled_for_llm=False` due to the
`enabled`/`disabled_reason` schema — not just a generic "not active" status string.

## Scope

**In scope**
- `scripts/shared/runtime_tool_registry.py::diagnostics()` — change how the `disabled_reason`
  value in each returned row is computed.

**Out of scope**
- `scripts/agent/commands/cmd_mcp.py` — its `_format_tool_diagnostics_table()` and
  `_cmd_mcp_status()` wiring already display a `DISABLED_REASON` column sourced from
  `registry.diagnostics()`'s `disabled_reason` key (confirmed by direct read of current source,
  lines 69-94 and 183-189; landed in commit `d510c87f`, "feat: wire RuntimeToolRegistry into
  routing layer and add diagnostics"). **No change needed there** — once this doc's fix changes
  what `diagnostics()` returns for `disabled_reason`, the existing display column picks it up
  automatically with zero changes to `cmd_mcp.py`.
- `diagnostics()`'s hardcoded `"enabled": True` (line 188) — the source plan's own UNK-03 flags
  this as a separate, narrower, out-of-scope gap (display-only, does not affect the LLM payload
  this plan's core fix targets); not touched here.
- The `config_dependent` field's derivation (`tool.status != "active"`) — unrelated to
  `disabled_reason`, unchanged.

## Assumptions

1. `RuntimeTool.raw_definition: dict[str, object]` (per `scripts/shared/runtime_tool.py`'s
   `RuntimeTool` dataclass) already holds the original, unmodified `/v1/tools` entry dict for every
   tool, including any `disabled_reason` key a server sent — confirmed:
   `_dedupe_and_build()`'s `build_runtime_tool(..., raw_definition=entry, ...)` call
   (`scripts/agent/services/mcp_tool_discovery.py:317`) always passes the full raw entry, so
   `tool.raw_definition.get("disabled_reason")` is a safe, always-available lookup for any tool
   built via real discovery.
2. Tools with no `disabled_reason` key in their raw entry (i.e. every tool from the 6 servers that
   do not implement the `enabled`/`disabled_reason` schema, or any tool whose owning server sent
   `enabled: true`/omitted `enabled` without a reason string) must not regress to an empty/missing
   diagnostic — falling back to the existing `status`-derived value when `raw_definition` has no
   `disabled_reason` key preserves current behavior for every tool that never had a
   `disabled_reason` key, per this plan's Design §2 ("falling back to the existing status-derived
   value when absent").
3. `raw_definition.get("disabled_reason")`'s value, when present, should be coerced to `str` before
   being placed in the returned row dict — `diagnostics()`'s declared return type is
   `list[dict[str, object]]` (loosely typed), but the display code in `cmd_mcp.py`
   (`row.get("disabled_reason", "-") or "-"`) expects a falsy-or-string value; a non-string
   `disabled_reason` from a malformed entry would already have been caught by this plan's UNK-02
   defensive type-check (`implementations/20260721-163326_mcp_tool_discovery.py.md`) if that
   optional change lands, but this doc adds its own `str(...)` coercion regardless for defense in
   depth, since UNK-02 does not currently type-check `disabled_reason` itself (only `enabled`).

## Implementation

### Target file

`scripts/shared/runtime_tool_registry.py` (existing).

### Procedure

1. In `diagnostics()` (method starting at line 173), locate the current `disabled_reason`
   computation inside the `for tool in sorted(...)` loop:
   ```python
   config_dep = tool.status != "active"
   disabled_reason = "" if tool.status == "active" else tool.status
   ```
2. Replace the `disabled_reason` line with a lookup into `tool.raw_definition`, falling back to
   the existing status-derived expression when the key is absent or empty:
   ```python
   raw_reason = tool.raw_definition.get("disabled_reason")
   disabled_reason = (
       str(raw_reason)
       if isinstance(raw_reason, str) and raw_reason
       else ("" if tool.status == "active" else tool.status)
   )
   ```
3. Leave `config_dep` and every other field in the returned row dict (`name`, `server_key`,
   `enabled`, `enabled_for_llm`) unchanged.
4. Update the method's docstring (lines 174-177) to state the new sourcing rule explicitly (raw
   `disabled_reason` preferred, `status`-derived value as fallback), so a future reader does not
   "fix" this back to the status-only version.

### Method

In-place edit to an existing method body; no new helper function, no new class, no signature
change (`diagnostics()` keeps its `-> list[dict[str, object]]` return type).

### Details

Current method body (verbatim, `scripts/shared/runtime_tool_registry.py:173-191`):

```python
def diagnostics(self) -> list[dict[str, object]]:
    """Return per-tool diagnostics rows for display in /mcp status.

    Each row contains: name, server_key, config_dependent, enabled,
    disabled_reason, enabled_for_llm. Sorted by name.
    """
    rows: list[dict[str, object]] = []
    for tool in sorted(self._tools.values(), key=lambda t: t.name):
        config_dep = tool.status != "active"
        disabled_reason = "" if tool.status == "active" else tool.status
        rows.append(
            {
                "name": tool.name,
                "server_key": tool.server_key,
                "config_dependent": config_dep,
                "enabled": True,
                "disabled_reason": disabled_reason,
                "enabled_for_llm": tool.enabled_for_llm,
            }
        )
    return rows
```

Target method body after the change:

```python
def diagnostics(self) -> list[dict[str, object]]:
    """Return per-tool diagnostics rows for display in /mcp status.

    Each row contains: name, server_key, config_dependent, enabled,
    disabled_reason, enabled_for_llm. Sorted by name.

    `disabled_reason` prefers the discovery-time reason a server sent in its
    /v1/tools entry (`raw_definition["disabled_reason"]`), falling back to a
    status-derived value for tools whose entry never carried that key.
    """
    rows: list[dict[str, object]] = []
    for tool in sorted(self._tools.values(), key=lambda t: t.name):
        config_dep = tool.status != "active"
        raw_reason = tool.raw_definition.get("disabled_reason")
        disabled_reason = (
            str(raw_reason)
            if isinstance(raw_reason, str) and raw_reason
            else ("" if tool.status == "active" else tool.status)
        )
        rows.append(
            {
                "name": tool.name,
                "server_key": tool.server_key,
                "config_dependent": config_dep,
                "enabled": True,
                "disabled_reason": disabled_reason,
                "enabled_for_llm": tool.enabled_for_llm,
            }
        )
    return rows
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted unit tests | `uv run pytest tests/shared/test_runtime_tool_registry.py -v` | all pass, including a new case: a tool built with `raw_definition={"disabled_reason": "quota exceeded"}` yields that exact string from `diagnostics()`, and a tool with no such key falls back to the pre-existing status-derived value |
| `cmd_mcp.py` display regression | `uv run pytest tests/test_cmd_mcp.py -v` | all pass unchanged — confirms the existing `DISABLED_REASON` column renders the new value with no code change to `cmd_mcp.py` |
| Full suite | `uv run pytest -q` | no new failures |
| Lint/format | `uv run ruff format scripts/ && uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no new imports) |
| Security | `uv run bandit -r scripts/shared/runtime_tool_registry.py -c pyproject.toml` | 0 high/medium |
| Diff-scoped coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |
| Pre-commit | `uv run pre-commit run --all-files` | pass |
