# Implementation procedure: `tests/test_mcp_tool_discovery.py` (disabled-tool diagnostics variant)

Source plan: `plans/20260717-175327_plan.md` ("RuntimeToolRegistry — represent disabled MCP tools
without exposing them to the LLM", requirement 17), Implementation step 5.

## Goal

Create `tests/test_mcp_tool_discovery.py` (flat path, per this plan's own Assumptions: the actual
`tests/` layout is flat, not `tests/agent/services/...`) covering
`scripts/agent/services/mcp_tool_discovery.py`'s `McpToolDiscoveryService.discover()`: mock
`/v1/tools` responses with and without `enabled`/`disabled_reason` present (to cover the
backward-compat default path), and assert the resulting `RuntimeToolRegistry` state.

**Filename note**: four other docs target either `tests/agent/services/test_mcp_tool_discovery.py`
or `tests/test_mcp_tool_discovery.py` —
`implementations/20260717-203931_test_mcp_tool_discovery.py.md` (base, requirement 03),
`implementations/20260717-224812_test_mcp_tool_discovery.py.md` (consolidation extension),
`implementations/20260718-084145_test_mcp_tool_discovery.py.md` (schema_version tests),
`implementations/20260718-084859_test_mcp_tool_discovery.py.md` (capabilities tests). All test the
*other* `McpToolDiscoveryService` design (13-field `RuntimeTool`, drift-detection consolidation).
Checked each Goal directly — none tests `enabled`/`disabled_reason` defaulting for LLM-visibility
the way this requirement needs. Same cross-plan collision already flagged for the paired source
docs; not reused here.

## Scope

**In scope**
- New file `tests/test_mcp_tool_discovery.py` (flat, per this plan's Assumptions section, which
  explicitly overrides the requirement's literal nested path — confirmed via
  `find tests -iname test_cmd_mcp.py` showing the real `tests/` layout has only `tests/shared/`,
  `tests/integration/`, `tests/docs/` as subdirectories).
- Tests for `McpToolDiscoveryService.discover()` only, against this plan's 6-field
  `RuntimeTool`/`RuntimeToolRegistry`.

**Out of scope**
- Any test of the *other* discovery-service lineage (requirement 03 and its extensions) — those
  live in their own already-written test docs and, per this plan's own Out-of-scope section, are
  not this plan's concern.
- Real network calls — all `/v1/tools` responses are mocked (e.g. via `httpx.MockTransport` or a
  monkeypatched `ctx.services_required.http.get`, matching the mocking style implied by this
  codebase's existing `tests/shared/test_tool_transport_invoker.py` and `mcp_status.py`'s own
  probe-based design, without needing a live server).

## Assumptions

- `ctx.services_required.http` is the shared `httpx.AsyncClient` the discovery service is designed
  to reuse (per the paired implementation doc's Assumptions); tests construct a minimal
  `AgentContext`-like fixture or monkeypatch `ctx.services_required.http.get` to return a
  pre-built `httpx.Response` (via `httpx.Response(200, json=[...])`) per server key, following the
  same fixture style this codebase already uses for `AgentContext`-dependent service tests (e.g.
  `tests/test_llm_turn_runner.py`, confirmed to exist via `find`).
- Test doubles for `ctx.cfg.mcp.mcp_servers` need at least 2 entries (one HTTP server whose
  response includes `enabled`/`disabled_reason`, one HTTP server whose response omits them
  entirely) to exercise both the "modern" and "backward-compat default" code paths in the same
  test module.

## Implementation

### Target file

`tests/test_mcp_tool_discovery.py` (new).

### Procedure

1. Import `McpToolDiscoveryService` from `agent.services.mcp_tool_discovery`; build a minimal
   `AgentContext` fixture (or reuse an existing test helper if one already exists for
   `ctx.cfg.mcp.mcp_servers` + `ctx.services_required.http` — check `tests/conftest.py` /
   `tests/test_llm_turn_runner.py` for a reusable fixture before writing a new one).
2. `test_discover_reads_enabled_and_disabled_reason_when_present`: mock one server's `/v1/tools`
   returning a tool dict with `"enabled": False, "disabled_reason": "missing API key"`; assert the
   resulting registry's `diagnostics()` (or direct lookup) shows that tool with `enabled=False`,
   `disabled_reason="missing API key"`, `enabled_for_llm=False`.
3. `test_discover_defaults_enabled_true_when_field_absent`: mock a server's `/v1/tools` returning a
   tool dict with no `enabled`/`disabled_reason` keys at all (simulating a not-yet-updated server);
   assert the resulting `RuntimeTool` has `enabled=True`, `disabled_reason=""`,
   `enabled_for_llm=True` — the backward-compat default path.
4. `test_discover_reads_config_dependent_from_new_or_old_key`: one mocked tool dict with
   `"config_dependent": True`, another with only the legacy `"requires_config": True` (no
   `config_dependent` key); assert both produce `RuntimeTool.config_dependent == True`.
5. `test_discover_skips_unreachable_server`: mock one server raising `httpx.ConnectError` (or
   returning HTTP 500); assert `discover()` completes without raising and the registry contains no
   entries from that server (while still containing entries from other, reachable mocked servers).
6. `test_discover_skips_malformed_entry`: mock a `/v1/tools` response containing one valid tool dict
   and one entry missing `name`; assert the registry contains only the valid tool (the malformed
   entry is skipped with a warning, not raised).
7. `test_discover_only_probes_http_transport_servers`: include one non-HTTP-transport server config
   entry; assert `discover()` does not attempt to fetch from it (no mocked call registered for that
   key, or assert the mock was never invoked for it).

### Method

`pytest` async tests (`pytest.mark.asyncio` or this codebase's existing async test convention —
confirm the marker/plugin already used in `tests/test_llm_turn_runner.py` and reuse it verbatim
rather than introducing a second async-test pattern).

### Details

Pseudocode sketch (no production code):

```
async def test_discover_defaults_enabled_true_when_field_absent(monkeypatch) -> None:
    # ctx = build_test_agent_context(mcp_servers={"file_read": ...})
    # mock_get = AsyncMock(return_value=httpx.Response(200, json=[
    #     {"name": "read_file", "description": "...", "inputSchema": {}}
    # ]))
    # monkeypatch.setattr(ctx.services_required.http, "get", mock_get)
    # registry = await McpToolDiscoveryService(ctx).discover()
    # tool = registry.get("read_file")  # or equivalent lookup
    # assert tool.enabled is True
    # assert tool.disabled_reason == ""
    # assert tool.enabled_for_llm is True
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/test_mcp_tool_discovery.py && uv run ruff check tests/test_mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy tests/test_mcp_tool_discovery.py` | 0 errors |
| Unit tests | `uv run pytest tests/test_mcp_tool_discovery.py -v` | all pass |
| Security | `uv run bandit -r tests/test_mcp_tool_discovery.py -c pyproject.toml` | 0 high/medium |
| Coverage | `diff-cover` on `scripts/agent/services/mcp_tool_discovery.py` | ≥90% on changed lines |
