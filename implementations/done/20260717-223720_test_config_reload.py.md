# Implementation procedure: `tests/test_config_reload.py`

Source plan: `plans/20260717-130341_plan.md` (requirement `requires/20260717_08_require.md`),
Implementation step 3 ("Add tests").

Paired with: `implementations/20260717-223600_config_reload.py.md` (the source-file change this test
suite locks down).

## Goal

Add tests asserting that `ConfigReloadService._sync_services()` calls
`ctx.services_required.runtime_tools.apply_policy(tier_map=..., allowed_tools=...)` after a reload, and
add a regression guard proving `/reload` never triggers MCP tool (re)discovery (no `/v1/tools` fetch).

## Scope

**In scope**
- `tests/test_config_reload.py` (the real, existing file — confirmed at
  `/home/sugimoto/llmagent/tests/test_config_reload.py`, 308 lines, flat `tests/` directory; the
  plan's/requirement's stated `tests/agent/services/test_config_reload.py` path does not exist,
  matching the already-documented path-mismatch pattern from requirements 04-07).

**Out of scope**
- Any change to `scripts/agent/services/config_reload.py` (covered by the paired implementation doc).
- `RuntimeToolRegistry.apply_policy()`'s own internal unit tests — those belong to requirement 02's
  test doc for `scripts/shared/runtime_tool_registry.py` (already exists:
  `implementations/20260717-203310_test_runtime_tool_registry.py.md`).

## Assumptions

1. **Existing fixture/mocking convention** (confirmed by direct read of `tests/test_config_reload.py:13-39`,
   the `svc` fixture): `ctx = MagicMock()`, with specific attribute paths pre-set
   (`ctx.cfg.tool.system_prompts`, `ctx.cfg.approval.tool_safety_tiers = {}`,
   `ctx.services_required.llm = None`, etc.) before constructing `ConfigReloadService(ctx)`. New tests
   for this requirement follow the same style: a `MagicMock()` context with
   `ctx.services_required.runtime_tools` set to either `None` (no-op path) or a `MagicMock()` spy (call
   assertion path).
2. **`apply_policy()`'s real signature** is `apply_policy(tier_map: Mapping[str, AgentSafetyTier],
   allowed_tools: Sequence[str] = ())` (per requirement 02's finalized doc,
   `implementations/20260717-203200_runtime_tool_registry.py.md`) — **not** `apply_policy(cfg)` as the
   plan's text states (see the paired implementation doc's Assumption 1 for the full discrepancy note).
   Tests must assert the call was made with `tier_map=`/`allowed_tools=` keyword arguments matching
   `ctx.cfg.approval.tool_safety_tiers` / `ctx.cfg.tool.allowed_tools`, not a single positional `ctx.cfg`.
3. Since `_sync_services()` is a private method, it can be exercised directly (as
   `TestMcpServerChangeClassification`/`TestStartupOnlyDetection` already do for other private methods
   in this same file, e.g. `svc._classify_mcp_server_changes(...)`, `svc._detect_startup_only(...)`) or
   indirectly via `apply_config_dict()`. Direct `_sync_services()` calls are simpler here since the
   policy-reapplication behavior is entirely local to that method and does not depend on the earlier
   `apply_config_dict()` steps (MCP classification, masked fields, etc.) — this avoids over-mocking
   unrelated `ctx.cfg` attributes that `apply_config_dict()`'s other steps would otherwise require.
4. The no-rediscovery regression guard (Implementation step 3(b) in the plan) is best expressed as: no
   attribute/method resembling `/v1/tools` fetch is invoked. Since the actual discovery module
   (`scripts/agent/services/mcp_tool_discovery.py`, requirement 03) is a separate, not-yet-existing
   module, and `config_reload.py` has zero import of it (confirmed by grep — no `mcp_tool_discovery`
   reference in `config_reload.py`), the simplest and most robust regression guard does not need to
   patch/mock anything from that module at all: asserting that `ctx.services_required.http.get` (or
   equivalent HTTP client) is never called during `apply_config_dict()`/`_sync_services()` is sufficient,
   since `/v1/tools` fetching is inherently an HTTP call and `config_reload.py` has no code path that
   performs one. This mirrors requirement 03's own plan (`plans/done/20260717-124907_plan.md`,
   "`/reload` regression guard" section), which already establishes the same style of guard for the
   discovery side.

## Implementation

### Target file

`tests/test_config_reload.py`

### Procedure

1. Add a new test class `TestRuntimeToolPolicyReapplication` after the existing
   `TestStartupOnlyDetection` class (end of file, after line 308).
2. Add a helper `_make_svc()` (local to the new class, following the existing per-class helper
   convention seen in `TestMcpServerChangeClassification._make_svc()` and
   `TestStartupOnlyDetection._make_svc()`) that builds a `MagicMock()` ctx with:
   - `ctx.cfg.approval.tool_safety_tiers = {"delete_file": "ADMIN"}` (a representative, non-empty tier
     map so the call-assertion test has a concrete value to check against).
   - `ctx.cfg.tool.allowed_tools = []` (empty = all allowed, matching `apply_policy()`'s convention).
   - `ctx.services_required.llm = None`, `ctx.services_required.hist_mgr = None`,
     `ctx.services_required.tools = None` (silence the three pre-existing `_sync_services()` blocks so
     only the new block under test executes).
   - `ctx.services_required.runtime_tools = MagicMock()` (the spy under test) for the positive-path
     tests, or `None` for the no-op test.
3. Add these tests:
   - `test_apply_policy_called_with_current_tier_map_and_allowed_tools`: build a `svc` with
     `runtime_tools` as a `MagicMock()`, call `svc._sync_services({})`, then assert
     `ctx.services_required.runtime_tools.apply_policy.assert_called_once_with(
     tier_map=ctx.cfg.approval.tool_safety_tiers, allowed_tools=ctx.cfg.tool.allowed_tools)`.
   - `test_runtime_tools_reported_in_applied`: same setup; assert `"runtime_tools" in result.applied`
     where `result = svc._sync_services({})`.
   - `test_no_runtime_tools_registry_is_noop`: build `svc` with `ctx.services_required.runtime_tools =
     None`; call `svc._sync_services({})`; assert no exception is raised and `"runtime_tools" not in
     result.applied`.
   - `test_reload_does_not_fetch_tools_over_http` (the no-rediscovery regression guard): build `svc`
     with `ctx.services_required.http = MagicMock()` (an HTTP-client spy) plus the other required
     `ctx.cfg.*` attributes the existing `svc` fixture already sets (reuse the module-level `svc`
     fixture from `TestApplyConfig` rather than the new class's own minimal mock, since this test needs
     the full `apply_config_dict()` path, not just `_sync_services()`); call
     `svc.apply_config_dict({})`; assert `ctx.services_required.http.get.assert_not_called()` (and, if
     an HTTP `post`/`request` method is also plausible, assert those too, or use
     `ctx.services_required.http.assert_not_called()`-style broad assertion if `http` is a single
     mock whose only expected use is `.get`).
4. Do not remove or modify any existing test in this file.

### Method

Plain `pytest` test functions grouped in one new `unittest.mock.MagicMock`-based test class, matching
the file's existing style exactly (no new fixtures at module scope needed beyond what already exists;
each test class in this file already defines its own `_make_svc()` helper rather than sharing one).

### Details

Pseudocode (no production code — illustrative only):

```
class TestRuntimeToolPolicyReapplication:
    """After /reload, RuntimeToolRegistry.apply_policy() is re-applied via _sync_services()."""

    def _make_svc(self, with_registry: bool = True) -> tuple[object, object]:
        from agent.services.config_reload import ConfigReloadService

        ctx = MagicMock()
        ctx.cfg.approval.tool_safety_tiers = {"delete_file": "ADMIN"}
        ctx.cfg.tool.allowed_tools = []
        ctx.services_required.llm = None
        ctx.services_required.hist_mgr = None
        ctx.services_required.tools = None
        ctx.services_required.runtime_tools = MagicMock() if with_registry else None
        return ConfigReloadService(ctx), ctx

    def test_apply_policy_called_with_current_tier_map_and_allowed_tools(self) -> None:
        svc, ctx = self._make_svc()
        svc._sync_services({})
        ctx.services_required.runtime_tools.apply_policy.assert_called_once_with(
            tier_map=ctx.cfg.approval.tool_safety_tiers,
            allowed_tools=ctx.cfg.tool.allowed_tools,
        )

    def test_runtime_tools_reported_in_applied(self) -> None:
        svc, ctx = self._make_svc()
        result = svc._sync_services({})
        assert "runtime_tools" in result.applied

    def test_no_runtime_tools_registry_is_noop(self) -> None:
        svc, ctx = self._make_svc(with_registry=False)
        result = svc._sync_services({})  # must not raise
        assert "runtime_tools" not in result.applied

    def test_reload_does_not_fetch_tools_over_http(self, svc: object) -> None:
        # uses the module-level `svc` fixture (full apply_config_dict() path)
        svc.apply_config_dict({})  # type: ignore[attr-defined]
        svc._ctx.services_required.http.get.assert_not_called()  # type: ignore[attr-defined]
```

Note: the last test's exact `http` mock wiring depends on what the module-level `svc` fixture already
sets for `ctx.services_required.http` (currently unset in the fixture at lines 13-39 — a `MagicMock()`
attribute is auto-created on access, so `.get` is itself a `MagicMock` callable and
`.assert_not_called()` works without extra setup).

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| New tests | `uv run pytest tests/test_config_reload.py -v -k RuntimeToolPolicy` | all new tests pass |
| Full file | `uv run pytest tests/test_config_reload.py -v` | all existing + new tests pass, no regressions |
| Lint/format | `uv run ruff format tests/test_config_reload.py && uv run ruff check tests/test_config_reload.py` | 0 errors |
| Type check | `uv run mypy tests/test_config_reload.py` | 0 errors (or consistent with existing `# type: ignore[attr-defined]` usage already in this file) |
| Full suite | `uv run pytest -v` | no new failures |
| Pre-commit | `uv run pre-commit run --all-files` | pass |

**Blocking prerequisite note**: same as the paired implementation doc — these tests target
`ctx.services_required.runtime_tools`, a field that does not exist on `AppServices` in the repo as of
this doc (requirement 03, not yet landed). Since the tests operate entirely on a `MagicMock()` ctx, they
do not require the real `AppServices`/`RuntimeToolRegistry` classes to exist to be written or to pass —
but they document behavior for an attribute name (`runtime_tools`) that is still provisional (see the
paired implementation doc's Assumption 4). If requirement 03 lands with a different field name, update
this doc's fixture attribute name to match before implementing.
