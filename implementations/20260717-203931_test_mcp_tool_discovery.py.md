# Implementation procedure: `tests/agent/services/test_mcp_tool_discovery.py`

Source plan: `plans/done/20260717-124907_plan.md` (requirement `requires/20260717_03_require.md`),
Implementation step 6 (test portion for the new discovery module only).

## Goal

Create the new `tests/agent/services/` package (currently absent — confirmed via `ls` returning no such
directory) with an `__init__.py` marker, and `test_mcp_tool_discovery.py` covering
`scripts/agent/services/mcp_tool_discovery.py`'s `McpToolDiscoveryService`: schema validation (valid
entry, missing `name`, missing `description`, non-object `inputSchema`), `RuntimeTool` normalization
(safe defaults applied via `build_runtime_tool`), unreachable/malformed-server handling (warning finding,
server excluded, others still processed), and duplicate-tool-name detection with production-vs-local
severity gating (`SecurityProfile.PRODUCTION` -> fatal, `SecurityProfile.LOCAL` -> warning; duplicate
excluded from the registry in both cases per the discovery-module doc's Assumption 5 decision).

## Scope

**In scope**
- New `tests/agent/services/__init__.py` (empty package marker).
- New `tests/agent/services/test_mcp_tool_discovery.py`.

**Out of scope (tracked separately / already covered)**
- Extending `tests/test_startup.py` with discovery-step integration tests and the `/reload`
  regression-guard test (plan Implementation steps 5 and the `tests/test_startup.py` portion of step 6)
  — per this workflow's filename-match convention, a doc already exists under `implementations/done/`
  matching `test_startup.py` (confirmed via `ls`), so that file is treated as already-covered and is not
  duplicated here.
- Unit tests for `shared/runtime_tool.py` and `shared/runtime_tool_registry.py` themselves — tracked by
  `implementations/20260717-203244_test_runtime_tool.py.md` and
  `implementations/20260717-203310_test_runtime_tool_registry.py.md`.
- Running the full validation sequence — tracked by `implementations/20260717-202631_full_validation_pass.md`
  (a generic cross-cutting doc from this same batch, per this workflow's convention for that slug).

## Assumptions

1. **Mocking pattern mirrors `tests/test_repl_health.py`'s existing style** (confirmed by direct read,
   lines 1-60): `httpx.AsyncClient` is mocked via `unittest.mock.AsyncMock(spec=httpx.AsyncClient)`, with
   `.get` replaced by an `AsyncMock` whose `return_value` is a `MagicMock()` response carrying
   `.status_code` and `.json.return_value`; the file already defines a small helper,
   `_async_result(value) -> AsyncMock`, at `tests/test_repl_health.py:33-37` — this new test file should
   define its own equivalent local helper (or import it, if it is later promoted to a shared test-utils
   module — not assumed here, since no such promotion exists today) rather than depend on
   `tests/test_repl_health.py` internals.
2. **`AgentContext`/`ctx.cfg.mcp.mcp_servers`/`ctx.services_required.http` construction for tests** likely
   needs a lightweight fixture rather than a full `build_agent_context()` call (too heavyweight/slow for
   unit tests of a single service class) — mirror whatever minimal `AgentContext`-construction helper
   `tests/test_repl_health.py` uses for its `_check_tool_definitions`/`check_readiness`-style tests
   (inspect that file's fixture/helper functions when implementing, since this doc's investigation did not
   fully trace `AgentContext` test-construction helpers beyond the `http` mock itself — treat this as a
   small mechanical detail to resolve by reading `tests/test_repl_health.py` in full at implementation
   time, not a design fork).
3. **`McpServerConfig` instances for test fixtures** use `TransportType.HTTP`, a non-empty `url`, and a
   distinct `key` per server (per `scripts/shared/mcp_config.py:46-64`'s required/validated fields;
   `__post_init__` raises if `url` is empty for HTTP transport, so tests must always supply one).
4. **`SecurityProfile.PRODUCTION`/`SecurityProfile.LOCAL`** (`scripts/shared/mcp_config.py:38-42`) are set
   via `ctx.cfg.mcp.security_profile` in the test fixture to exercise both severity-gating branches.
5. Tests target the module's public surface (`McpToolDiscoveryService.discover_all()` and its returned
   `DiscoveryResult`), not private helpers directly, except where a private helper's behavior (e.g.
   `_validate_and_normalize_entry`) is only reachable through specific malformed-entry fixtures that are
   clearer to construct at that narrower level — follow `tests/test_repl_health.py`'s own mixed style
   (some tests target `_probe_mcp_health_detail` directly, a "private" module function, per line 43-59).

## Implementation

### Target file

`tests/agent/services/__init__.py` (new, empty) and `tests/agent/services/test_mcp_tool_discovery.py`
(new).

### Procedure

1. Create `tests/agent/services/__init__.py` as an empty file (package marker — confirmed needed by
   checking that sibling test packages, e.g. `tests/agent/`, follow this convention; verify at
   implementation time whether `tests/agent/` itself already has an `__init__.py` to copy the exact
   convention, since pytest may or may not require it depending on `rootdir`/`testpaths` config in
   `pyproject.toml`/`pytest.ini` — confirm before assuming it's a no-op).
2. `test_mcp_tool_discovery.py` module docstring: state scope (unit tests for
   `agent.services.mcp_tool_discovery.McpToolDiscoveryService`), state that `httpx.AsyncClient` and
   `AgentContext` are mocked (mirrors `tests/test_repl_health.py:1-6`'s own docstring convention).
3. Test class/group 1 — schema validation and normalization (happy path): one server, one well-formed
   tool entry (`name`, `description`, `inputSchema` all present and well-typed) -> `discover_all()` returns
   a `DiscoveryResult` whose `registry.get(name)` yields a `RuntimeTool` with the expected `server_key`,
   `server_url`, `description`, `input_schema`, and safe-default fields (`is_write=False`,
   `requires_serial=True` when `is_write` was omitted, per `runtime_tool.py`'s Assumption 5 default rule);
   `findings` is empty; `unreachable` is empty.
4. Test class/group 2 — malformed entries (per-entry validation): missing `name`, empty-string `name`,
   missing `description`, non-dict `inputSchema`, non-dict tool entry itself — each produces one
   `StartupCheckOutcome` with `status=StartupCheckStatus.WARNING` in `findings`, and the malformed entry is
   excluded from the registry (other valid entries from the same server are still included).
5. Test class/group 3 — unreachable/malformed server response: non-200 HTTP status, invalid top-level
   JSON (`resp.json()` raises `ValueError`), `tools` key missing or not a list, `httpx.ConnectError`/
   `OSError` raised by `http.get` — each produces a `WARNING` finding and the server's key appears in
   `unreachable`; other configured servers are still processed independently (mirrors
   `tests/test_repl_health.py`'s "partial unreachable" scenarios, e.g. around line 87).
6. Test class/group 4 — duplicate-tool-name detection: two servers both returning a tool entry with the
   same `name`; assert with `ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION` ->
   `StartupCheckStatus.FATAL` finding and the tool absent from `registry`; with
   `SecurityProfile.LOCAL` -> `StartupCheckStatus.WARNING` finding and the tool **still** absent from
   `registry` (both profiles exclude, per the discovery-module doc's Assumption 5 decision — this is the
   key behavior this test group must lock in, since it's the one place the source plan explicitly left
   underspecified and the paired implementation doc made a concrete choice).
7. Test class/group 5 — non-HTTP / empty-URL servers are skipped entirely (no fetch attempted, `http.get`
   not called for that server key) — mirrors `repl_health.py:181-184`'s existing filter, asserted via
   `http.get.assert_not_called()` or call-count checks scoped to that server.

### Method

Plain `pytest` functions/classes with `@pytest.mark.asyncio` (mirrors `tests/test_repl_health.py`'s
existing style throughout, e.g. `TestProbeMcpHealthDetail` at line 43). `unittest.mock.AsyncMock`/
`MagicMock` for `http`; hand-constructed `McpServerConfig`/minimal `AgentContext` (or a shared test
fixture/factory if one already exists for `AgentContext` in `tests/` — check `tests/conftest.py` at
implementation time) for the context object. No `Protocol`/fakes beyond what `unittest.mock` provides.

### Details

Illustrative test shapes (pseudocode — no production code):

```
def _async_result(value: object) -> AsyncMock: ...
    # m = AsyncMock(); m.return_value = value; return m


class TestDiscoverAllHappyPath:
    async def test_single_server_single_valid_tool_builds_registry(self) -> None: ...
        # http.get -> 200, {"tools": [{"name": "grep", "description": "...", "inputSchema": {...}}]}
        # result = await McpToolDiscoveryService(ctx).discover_all()
        # assert result.registry.get("grep").server_key == "search_server"
        # assert result.findings == []
        # assert result.unreachable == []


class TestDiscoverAllMalformedEntries:
    async def test_missing_name_produces_warning_and_is_excluded(self) -> None: ...


class TestDiscoverAllUnreachableServers:
    async def test_connect_error_marks_server_unreachable_others_still_processed(self) -> None: ...


class TestDiscoverAllDuplicates:
    async def test_duplicate_name_production_is_fatal_and_excluded(self) -> None: ...
    async def test_duplicate_name_local_is_warning_and_still_excluded(self) -> None: ...


class TestDiscoverAllServerFilter:
    async def test_non_http_or_empty_url_server_is_skipped(self) -> None: ...
```

## Validation plan

| Check | Command | Target |
|---|---|---|
| Format/lint | `uv run ruff format tests/agent/services/test_mcp_tool_discovery.py && uv run ruff check tests/agent/services/test_mcp_tool_discovery.py` | 0 errors |
| Type check | `uv run mypy tests/agent/services/test_mcp_tool_discovery.py` | 0 errors |
| Unit tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all pass; happy-path, malformed-entry, unreachable-server, duplicate (both profiles), and server-filter groups all covered |
| Regression | `uv run pytest tests/test_repl_health.py tests/test_repl_health_malformed.py -v` | no regressions (this new test file does not modify `repl_health.py` or its tests) |
| Coverage | `uv run diff-cover` (or project's standard coverage gate per `rules/toolchain.md`) scoped to `scripts/agent/services/mcp_tool_discovery.py` | meets project threshold |
