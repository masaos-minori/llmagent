# Implementation Doc: `/mcp` Status — Show `UNAVAILABLE` Servers with Reason

## Goal

Make restart exhaustion (and any other `UNAVAILABLE`-with-reason condition)
actionable in `/mcp` status output by displaying `UNAVAILABLE` servers with
their recorded degraded reason, mirroring the existing `DEGRADED` block.

## Scope

**In scope:**
- `scripts/agent/commands/cmd_mcp.py`: extend the `/mcp` status handler to add
  a new "Unavailable servers" display block, parallel to the existing
  `DEGRADED`-servers-with-reason block.

**Out of scope:**
- Any change to how `_degraded_reasons` is populated (Phase 1/2 —
  `mcp_health.py`, `repl_health.py`).
- The generic "N unreachable" count line (unchanged; the new block is
  additive alongside it).

## Assumptions

- The `/mcp` status handler (lines ~90-103 per plan Assumption 4) currently
  only surfaces `registry.get_degraded_reason(key)` for servers whose
  `get_state(key) == DEGRADED`. `UNAVAILABLE` servers get no reason line
  today, only appearing in the generic unreachable count.
- `registry.get_degraded_reason(key)` works identically regardless of the
  server's current state (state-independent dict lookup, plan Assumption 5)
  — so it is safe to call it for `UNAVAILABLE` servers too, including ones
  whose reason is `"restart_limit_reached"` (set by Phase 1's
  `record_restart_exhausted()`).
- The new block must be purely additive: when no server is `UNAVAILABLE`,
  output must be byte-identical to today (plan Risks table, row 2) — this
  is verified by existing tests `tests/test_cmd_mcp.py` /
  `tests/test_cmd_registry_note_removal.py`, which must continue to pass
  unmodified.

## Implementation

### Target file

`scripts/agent/commands/cmd_mcp.py`

### Procedure

1. Locate the existing `degraded_keys` block in the `/mcp` status handler
   (the method that builds `DEGRADED`-servers-with-reason output).
2. Immediately after that block, add a new `unavailable_keys` block following
   the same structure: filter `ctx.cfg.mcp.mcp_servers` keys by
   `registry.get_state(key) == McpServerHealthState.UNAVAILABLE`.
3. If `unavailable_keys` is non-empty, write a blank line, a
   `"  Unavailable servers:"` header, then one line per key in the format
   `    [UNAVAILABLE] {key}{reason_str}` where `reason_str` is
   `": {reason}"` if a reason exists, else empty string.
4. Guard all `registry` accesses with the same `None`-check pattern already
   used for the `degraded_keys` block (registry may be `None`).

### Method

```python
unavailable_keys = [
    key
    for key in ctx.cfg.mcp.mcp_servers
    if registry is not None
    and registry.get_state(key) == McpServerHealthState.UNAVAILABLE
]
if unavailable_keys:
    self._out.write("")
    self._out.write("  Unavailable servers:")
    for key in unavailable_keys:
        reason = registry.get_degraded_reason(key) if registry else None
        reason_str = f": {reason}" if reason else ""
        self._out.write(f"    [UNAVAILABLE] {key}{reason_str}")
```

### Details

- Re-verify at implementation time that `registry`, `McpServerHealthState`,
  and `self._out` are the actual names in current source — the plan
  explicitly notes this needs reconfirming (plan Design section note).
- Place the new block directly after the existing `degraded_keys` block so
  status output groups `DEGRADED` then `UNAVAILABLE` sections consistently.
- Do not alter the existing `degraded_keys` block or the generic unreachable
  count line.
- No new imports expected; `McpServerHealthState` should already be imported
  in this module (used for the `DEGRADED` comparison).

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_mcp.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/cmd_mcp.py` | No new errors |
| Tests | `uv run pytest tests/test_cmd_mcp.py tests/test_cmd_registry_note_removal.py -v` | All pass; output unchanged when no server is `UNAVAILABLE` (byte-identical), new block appears only when at least one server is `UNAVAILABLE` |
| Manual | Build a registry with one `UNAVAILABLE` server bearing reason `"restart_limit_reached"`, run `/mcp` status, confirm the new block renders `[UNAVAILABLE] <key>: restart_limit_reached` | Matches Design |
