## Goal

Make `ToolTransportInvoker.__init__` (`scripts/shared/tool_transport_invoker.py:54-58`) pass
`McpServerConfig.call_timeout_sec` straight through to `HttpTransport` unchanged, so that
`call_timeout_sec=0` ("no timeout", per the field's own documented contract at
`scripts/shared/mcp_config.py:55`) is honored instead of being silently overridden to `60.0` by a
truthy check that treats `0` as "unset." Remove the now-provably-dead
`hasattr(cfg, "call_timeout_sec")` guard in the same change.

## Scope

In scope:
- `scripts/shared/tool_transport_invoker.py` — `ToolTransportInvoker.__init__`, the `timeout_sec`
  resolution expression only (lines 54-58).

Out of scope:
- `scripts/shared/http_transport.py` — `HttpTransport`'s `self._timeout > 0` handling
  (`http_transport.py:104`) is already correct and is not touched.
- `scripts/shared/mcp_config.py` — `McpServerConfig`'s dataclass default (`call_timeout_sec: float
  = 60.0`, line 55) and `__post_init__` validation (`>= 0`, lines 113-115) are already correct and
  are not touched.
- `scripts/shared/tool_executor.py` (`ToolExecutor`, the sole subclass of `ToolTransportInvoker`)
  — it calls `super().__init__(http, server_configs, concurrency_limits, lifecycle)`
  (`tool_executor.py:61`) unchanged and needs no code change; it inherits the fix for free.
- `tests/shared/test_tool_transport_invoker.py` — covered by a separate implementation procedure
  (`implementations/20260814-004851_test_tool_transport_invoker.py.md`).
- Any `docs/*.md` file — `docs/04_mcp_06_03_mcpserverconfig-fields-agenttoml-mcp_servers.md:28`
  already documents `call_timeout_sec`'s "0 = no timeout" contract correctly.
- Any `config/*.toml` file — no shipped config currently sets `call_timeout_sec`.

## Assumptions

- No other code path between `McpServerConfig.call_timeout_sec` and `HttpTransport.__init__`'s
  `timeout_sec` parameter exists besides `ToolTransportInvoker.__init__`.
- This is a behavior fix, not a new feature: no new public API, no signature change, no DB schema
  change.

## Design decisions

- Do not add any new fallback/default logic in `ToolTransportInvoker`. Centralize "what does an
  unset/zero timeout mean" downstream in `HttpTransport.call`
  (`timeout = httpx.Timeout(self._timeout) if self._timeout > 0 else None`,
  `http_transport.py:104`), which already treats `0` as "no timeout" correctly.
- `McpServerConfig`'s dataclass default (`60.0`, `mcp_config.py:55`) plus the config loader's
  default (`mcp_config.py:218`, `float(v.get("call_timeout_sec", 60.0))`) remain the single source
  of truth for "what's the default when unset." No second default is introduced in
  `ToolTransportInvoker`, avoiding drift between two defaults over time.

## Alternatives considered

N/A — the plan specifies the exact expression to remove and its replacement; no alternative
resolution strategy was considered necessary for a one-line pass-through fix.

## Implementation

### Target file

`scripts/shared/tool_transport_invoker.py`

### Procedure

1. In `ToolTransportInvoker.__init__` (`scripts/shared/tool_transport_invoker.py:53-61`), replace
   the `timeout_sec` resolution expression at lines 54-58.
2. Run `uv run pytest tests/shared/test_tool_transport_invoker.py -v` and confirm all tests pass
   (see the companion test-file procedure for the new/flipped assertions this depends on).
3. Run `uv run ruff check scripts/shared/tool_transport_invoker.py` and
   `uv run mypy scripts/shared/tool_transport_invoker.py` and confirm both pass.

### Method

Direct, minimal-diff pass-through: delete the `hasattr(...) and cfg.call_timeout_sec ... else
60.0` conditional and assign `cfg.call_timeout_sec` directly. No new imports, no signature change,
no new branches.

### Details

Current code (`scripts/shared/tool_transport_invoker.py:53-61`):
```python
        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = (
                cfg.call_timeout_sec
                if hasattr(cfg, "call_timeout_sec") and cfg.call_timeout_sec
                else 60.0
            )
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )
```

Target shape after fix:
```python
        self._transports: dict[str, HttpTransport] = {}
        for key, cfg in server_configs.items():
            timeout_sec = cfg.call_timeout_sec
            self._transports[key] = HttpTransport(
                http, cfg.url, key, cfg, timeout_sec=timeout_sec
            )
```

The `hasattr(cfg, "call_timeout_sec")` guard is dead: `cfg` is always typed as `McpServerConfig`
(the dict value type of `server_configs: dict[str, McpServerConfig]`), and `call_timeout_sec` is a
dataclass field with a default (`mcp_config.py:55`), so the attribute is always present. The
`and cfg.call_timeout_sec` truthy check is the actual bug: `0.0` is falsy in Python, so it silently
fell through to `else 60.0`, overriding the caller's explicit "no timeout" request.

## Compatibility considerations

No public signature change on `ToolTransportInvoker.__init__` — same parameters, same return type
(`None`). Callers (`ToolExecutor` and any test double) are unaffected except for the corrected
internal `timeout_sec` value passed to `HttpTransport`. `ToolExecutor` inherits the fix with zero
code change of its own (`tool_executor.py:61`, unchanged `super().__init__(...)` call).

## Security considerations

N/A — no change to authentication, authorization, network surface, or error content. The change
only affects how long an HTTP call to an already-configured MCP server may run before timing out;
it does not disable any existing safety check that wasn't already opt-in via explicit
`call_timeout_sec=0` configuration.

## Rollback considerations

Single-expression, single-file change. `git revert` (or manually restoring the
`hasattr(...)`-guarded conditional) fully restores prior behavior. No data migration, no config
migration, and no coordinated multi-file rollback is required — `ToolExecutor` requires no
companion revert since it made no change.

## Validation plan

`uv run pytest tests/shared/test_tool_transport_invoker.py -v` — all tests pass, with the
`call_timeout_sec=0` case asserting `_timeout == 0` (post-fix), not `60.0`. Follow with
`uv run ruff check scripts/shared/tool_transport_invoker.py`,
`uv run mypy scripts/shared/tool_transport_invoker.py`,
`uv run pytest tests/shared/test_mcp_config_validation.py tests/shared/test_mcp_config.py -v` (no
regression expected in `McpServerConfig` itself), and `uv run pytest tests/shared/ -q` for the
broader shared-module regression net (covers `ToolExecutor`-reachable paths via inheritance).

## Out of scope

- `tests/shared/test_tool_transport_invoker.py` — separate implementation procedure
  (`implementations/20260814-004851_test_tool_transport_invoker.py.md`).
- `scripts/shared/http_transport.py`, `scripts/shared/mcp_config.py`,
  `scripts/shared/tool_executor.py` — read-only regression checks only, no code change.
- Any `docs/*.md` or `config/*.toml` file.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260813-192935_plan.md
- Source implementation procedure: N/A
- Generated at: 20260814-004820
- Related target files: tool_transport_invoker.py
