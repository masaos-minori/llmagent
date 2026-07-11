# Tool Registry: Live-Tools Drift Message Differentiation

## Goal

Make `ToolRegistry.validate_live_tools_match()` distinguish, in its returned mismatch
messages, between a live tool name that is **truly unknown** (not registered to any
server) and a live tool name that **is registered but to a different server** than the
one whose live `/v1/tools` response reported it. Today both cases produce the identical
generic message `"[{server_key}] tool {t!r} in live response but not in registry"`,
which hides useful diagnostic information already available via `get_server_for_tool()`.

## Scope

**In scope:**
- `scripts/shared/tool_registry.py`: `ToolRegistry.validate_live_tools_match()` method body only.

**Out of scope:**
- `get_server_for_tool()` itself — already exists and returns the correct owner (or
  `None`); no change needed.
- The "registry but not in live" branch of the same method — behavior unchanged, message
  text unchanged.
- Cross-server duplicate-live-ownership detection (`shared/route_resolver.py::build_discovery_map()`,
  `agent/repl_health.py::check_routing_drift_vs_live()`) — already implemented and tested
  elsewhere; not touched by this phase.
- Any caller of `validate_live_tools_match()` — return type (`list[str]`) is unchanged;
  callers only log/collect these strings, they do not pattern-match on message content.

## Assumptions

- `ToolRegistry.get_server_for_tool(tool_name: str) -> str | None` already exists (currently
  at `tool_registry.py:65-68`) and returns the true global owner of a tool name, or `None`
  if the tool is genuinely unregistered anywhere. Confirmed by direct read in the plan.
- `validate_live_tools_match()` currently lives at `tool_registry.py:108-132` and computes
  `in_live_not_registry = live_set - registry_tools` where `registry_tools` is this
  server's own tool list via `self.get_tool_names(server_key)`.
- No caller inspects the exact text of returned mismatch strings beyond logging/collecting
  them as opaque strings (confirmed for `agent/repl_health.py` in the plan's Risks section).

## Implementation

### Target file

`scripts/shared/tool_registry.py`

### Procedure

1. Locate `ToolRegistry.validate_live_tools_match()`.
2. Keep the existing `registry_tools` / `live_set` computation and the
   `in_registry_not_live` branch unchanged.
3. Replace the single generic message emitted for each tool in `in_live_not_registry`
   with a two-branch message, keyed on the result of `self.get_server_for_tool(t)`:
   - If the owner is `None`: emit a message stating the tool is unknown / not registered
     to any server.
   - If the owner is a non-`None` server key: emit a message stating the tool is
     registered to that owner, not to `server_key`.
4. Preserve the existing iteration order (`sorted(in_live_not_registry)`) so message
   ordering stays deterministic for tests.
5. Preserve the docstring's description of the "registry but not in live" branch; extend
   the docstring to describe the new unknown-vs-wrong-owner differentiation.

### Method

Modify the loop that builds `mismatches` for `in_live_not_registry` so that for each tool
`t`:
- Call `owner = self.get_server_for_tool(t)`.
- Branch on whether `owner is None`.
- Append the appropriate formatted string in each branch instead of the current single
  format string.

No new method, no new parameter, no change to the function signature or return type
(`list[str]`).

### Details

- Unknown-tool message should include the tool name and clearly state it is unknown /
  not registered to any server, e.g. embedding the substring `unknown` and the tool name,
  so it is distinguishable both by a human reader and by a test asserting on message
  content.
- Wrong-owner message should include the tool name, the actual owning server key (from
  `get_server_for_tool()`), and the `server_key` under validation, so both server keys are
  visible in the message text (e.g. quoting the owner key so a test can assert the exact
  owner string appears, such as `'server_a'`).
- Keep both messages prefixed with `[{server_key}]` for consistency with the existing
  "registry but not in live" message format.
- Do not alter the function's return type, exception behavior, or the "registry but not in
  live" message text/order.
- Follow `rules/coding.md`: f-strings for formatting, English-only text, line length <=120.

## Validation plan

Filtered to checks relevant to `scripts/shared/tool_registry.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_registry.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_registry.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Manual | `grep -n "not registered to any server\|registered to.*not" scripts/shared/tool_registry.py` | Confirms both new message branches are present |
| Tests (cross-check only; full test changes belong to the sibling test-file phase) | `uv run pytest tests/test_tool_registry.py -v` | All pre-existing tests in `TestValidateLiveToolsMatch` pass unmodified against the new message wording where they don't assert exact text, and the strengthened tests (added in the test-file phase) pass against the new wording |
