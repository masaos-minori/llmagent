# Implementation Procedure: `route_resolver.py` — `_log_routing_coverage()` registry-first fix + parameter docstrings

## Goal

Fix the classification-order bug in `ToolRouteResolver._log_routing_coverage()`: it currently
counts a tool as "mapped" if it appears in `self._discovery_map` *before* consulting the
registry, which is inconsistent with `resolve()`'s actual registry-only routing contract. Also
document `server_configs`, `known_tools`, and `discovery_map` as non-routing / vestigial
constructor parameters so future readers do not assume they participate in routing.

## Scope

**In-Scope:**
- `scripts/shared/route_resolver.py`:
  - `_log_routing_coverage()` (current lines 118-141): reorder the classification so the
    registry check (`self._lookup_registry(tool_name)`) runs first, and `discovery_map`
    membership is no longer consulted for mapped/unmapped classification at all.
  - Expand the method's docstring to explain "mapped" means resolvable via `ToolRegistry`
    (same authority `resolve()` uses), not mere presence in `discovery_map`.
  - Add a note that, as of this writing, no production caller passes `known_tools` to
    `ToolRouteResolver.__init__()`, so this method does not currently execute in production.
  - `ToolRouteResolver.__init__()` (current lines 60-86): add/expand docstring text for
    `server_configs` (unused, kept only for backward-compatible signature), `discovery_map`
    (live `/v1/tools` validation data, used only by `_log_routing_coverage()`, never by
    `resolve()`), and `known_tools` (opt-in trigger for the startup coverage log; no
    production caller passes it today).

**Out-of-Scope:**
- Any change to `resolve()`, `_lookup_registry()`, or `_raise_strict_error()` — these are
  already registry-only and correct (confirmed by direct read of lines 88-116).
- Any change to `ToolExecutor` or `factory.py`'s construction call — `discovery_map` and
  `known_tools` wiring is out of scope; this plan only documents current (non-)usage.
- Removing `self._discovery_map` as a stored attribute — it remains for potential future
  diagnostic use.

## Assumptions

1. Current source (`scripts/shared/route_resolver.py` lines 118-141) confirmed by direct read:
   `_log_routing_coverage()` checks `if tool_name in self._discovery_map: mapped.append(...);
   continue` (line 123-125) *before* checking `if self._lookup_registry(tool_name) is not
   None` (line 126-128). This means a tool present in `discovery_map` but absent from the
   registry is currently miscounted as "mapped," even though `resolve()` would raise
   `ValueError` for that same tool.
2. `resolve()` (lines 88-102) is already strictly registry-only — no code change needed there.
3. This method is never invoked in production today: `shared/tool_executor.py`'s sole
   construction call never passes `known_tools=`, so the `if known_tools:` guard in
   `__init__` (line 85) is never satisfied. This is a dormant correctness fix, not an
   observable behavior change for any current caller.
4. `server_configs` (the first `__init__` parameter, line 62) is accepted but never read or
   stored anywhere in the class body (confirmed by `grep -n "server_configs"
   scripts/shared/route_resolver.py`) — it is fully vestigial.

## Implementation

### Target file

`scripts/shared/route_resolver.py`

### Procedure

1. In `_log_routing_coverage()`, swap the order of the two membership checks so the registry
   check runs first and is the sole basis for "mapped" classification:
   - Replace the `if tool_name in self._discovery_map: ... continue` / `if
     self._lookup_registry(...) ...` pair with a single registry-only check:
     `if self._lookup_registry(tool_name) is not None: mapped.append(tool_name); else:
     unmapped.append(tool_name)`.
   - Do not reintroduce any `discovery_map` membership check into this classification.
2. Update the method's docstring to state explicitly: "mapped" means resolvable via
   `ToolRegistry` (the same check `resolve()` uses) — not merely present in `discovery_map`,
   which is validation-only metadata from live `/v1/tools` responses and carries no routing
   authority. A tool present only in `discovery_map` but absent from the registry is
   UNMAPPED for this purpose, since `resolve()` would raise `ValueError` for it.
3. Add a short note to the same docstring that no production caller currently passes
   `known_tools` to `__init__`, so this method does not run in production today (see
   `shared/tool_executor.py`'s construction call) — it remains available for a future caller
   wanting startup coverage visibility.
4. Update `ToolRouteResolver.__init__()`'s docstring/inline comments:
   - `server_configs`: annotate as "accepted for backward compatibility with existing
     callers; not read or stored — routing never consults per-server config."
   - `discovery_map`: annotate as "live `/v1/tools` validation data; used only by the
     currently-unreachable `_log_routing_coverage()` diagnostic, never by `resolve()`."
   - `known_tools`: annotate as "when provided, triggers a startup coverage log via
     `_log_routing_coverage()`. No production caller passes this today."

### Method

Two targeted, self-contained edits to `scripts/shared/route_resolver.py`: one in
`_log_routing_coverage()`'s body and docstring, one in `__init__()`'s docstring/comments.
No signature changes, no new parameters, no behavior change for any code path currently
exercised in production (per Assumption 3).

### Details

Reference pseudocode for the corrected method (illustrative only — do not copy verbatim
without adapting to actual surrounding style/log format):

```python
def _log_routing_coverage(self, known_tools: frozenset[str]) -> None:
    """... (expanded docstring per Procedure step 2-3) ..."""
    mapped: list[str] = []
    unmapped: list[str] = []
    for tool_name in sorted(known_tools):
        if self._lookup_registry(tool_name) is not None:
            mapped.append(tool_name)
        else:
            unmapped.append(tool_name)
    total = len(known_tools)
    if unmapped:
        logger.warning(
            "Routing (registry-based): %d/%d tools mapped; %d unmapped: %s",
            len(mapped), total, len(unmapped), unmapped,
        )
    else:
        logger.info("Routing (registry-based): %d/%d tools mapped", total, total)
```

`self._discovery_map` remains stored on `self` (no attribute removal) — it is simply no
longer read inside this method's classification logic. Preserve the existing log-message
prefix style used elsewhere in the module (English only, per `rules/coding.md`).

## Validation plan

Filtered to checks relevant to this file, from the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/route_resolver.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/route_resolver.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest tests/test_route_resolver.py -v` | All pass, including the new coverage-classification tests added in the companion test-file doc |
| Regression | `uv run pytest tests/test_tool_executor_routing.py tests/test_rag_tools_consistency.py tests/test_github_config_consistency.py -q` | No new failures — confirms the fix doesn't affect any real caller, since none currently trigger `_log_routing_coverage()` |
