# Implementation procedure: `tests/agent/services/test_mcp_tool_discovery.py` (migrated-case extension)

Source plan: `plans/20260717-130506_plan.md` ("Consolidate tool startup validation into MCP discovery
service", requirement `requires/20260717_09_require.md`), Implementation step 8.

**Relationship to the existing doc for this file**: `implementations/20260717-203931_test_mcp_tool_discovery.py.md`
(requirement 03's own test design) covers schema validation, `RuntimeTool` normalization, unreachable-server
handling, and duplicate-tool-name detection with production/local severity — all for the *base* discovery
service as req-03 originally scoped it. That doc's own "Out of scope" list does **not** mention drift-vs-
registry validation (there was no registry-drift concept in req-03's scope; drift lived only in
`repl_health.py`'s `check_routing_drift_vs_live()` at that time). This doc adds the delta: test cases for
the migrated drift-vs-registry logic and the unified severity table, plus the test migration required by
`repl_health.py`'s function removal. Not a false-positive — genuinely additive, implement alongside the
existing test doc against the same file.

## Goal

Extend `tests/agent/services/test_mcp_tool_discovery.py` (created per the base req-03 test doc) with:
1. Drift-vs-registry test cases migrated from `tests/test_routing_duplicate_ownership.py`'s 3
   `check_routing_drift_vs_live` integration tests (which must be removed from that file per
   `implementations/20260717-224725_repl_health.py.md`'s Assumption 4/Procedure step 7, since the function
   they import no longer exists).
2. The 4-combination unified-severity test matrix from
   `implementations/20260717-224511_mcp_tool_discovery.py.md`'s Design section
   (`strict × security_profile -> FATAL/WARNING`).
3. A regression test confirming `_check_tool_definitions()` failures surface as a `StartupCheckOutcome`
   (not a silently-swallowed "skipped" state, per that doc's Assumption 4 discussion of the current
   exception-swallowing quirk being retired).

## Scope

**In scope**
- New test methods/classes added to `tests/agent/services/test_mcp_tool_discovery.py` (file already
  created by the base req-03 test doc — this doc appends to it, does not recreate it).

**Out of scope**
- The base schema-validation/normalization/duplicate-detection tests already specified by
  `implementations/20260717-203931_test_mcp_tool_discovery.py.md` — not repeated here.
- Removing the 3 tests from `tests/test_routing_duplicate_ownership.py` — tracked as part of
  `implementations/20260717-224725_repl_health.py.md`'s own Procedure step 7 (that doc owns the deletion
  since it owns the source-function removal); this doc only specifies what their *replacement* coverage
  in the new location must assert.
- `tests/test_startup.py`/`test_startup_consistency.py`/`test_startup_validation_pipeline.py` patch-target
  updates — tracked by `implementations/20260717-224630_startup.py.md`'s Procedure step 5.

## Assumptions

1. The 3 tests being migrated (confirmed by direct read of `tests/test_routing_duplicate_ownership.py:65-134`):
   - `test_check_routing_drift_duplicate_in_warnings`: registers `tool_a` -> `srv1` in a reset
     `ToolRegistry`; patches the per-server fetch to return `{"srv1": ["tool_a"], "srv2": ["tool_a"]}`
     (duplicate live ownership); calls with `strict=False`; asserts a warning message mentions `tool_a`.
   - `test_check_routing_drift_duplicate_strict_raises`: same setup, `strict=True`; asserts
     `pytest.raises(RuntimeError, match="Strict mode.*duplicate")`.
   - `test_check_routing_drift_no_duplicate_no_warning`: `{"srv1": ["tool_a"], "srv2": ["tool_b"]}` (no
     duplicate); `strict=False`; asserts no warning message contains "duplicate".
   These must be re-expressed against `McpToolDiscoveryService.discover_all()` (or its internal
   `_build_drift_findings`/dedup helpers per the discovery-service doc), **not** against a raised
   `RuntimeError` for the strict case — per this plan's unified design, `discover_all()` never raises for
   validation findings; the strict-duplicate scenario now asserts a `StartupCheckOutcome` with
   `status == StartupCheckStatus.FATAL` in the returned `findings` list instead of a caught exception.
2. Mocking pattern for the HTTP fetch mirrors the base test doc's own Assumption 1
   (`unittest.mock.AsyncMock(spec=httpx.AsyncClient)` with a `MagicMock` response carrying `.status_code`/
   `.json.return_value`) — these new tests configure two servers' mocked `/v1/tools` responses directly
   (one entry each, same tool name) to exercise the duplicate/drift path end-to-end through
   `discover_all()`, rather than patching a private per-server-fetch helper as the old
   `test_routing_duplicate_ownership.py` tests did (that helper — `_collect_server_tool_names_per_server`
   — no longer exists after this plan's `repl_health.py` removal).
3. `ToolRegistry` setup for the registry-drift-comparison tests reuses the same
   `_reset_registry_for_testing()` / `get_registry().register(ToolDefinition(...))` pattern the migrated
   tests already used (`shared.tool_registry` — confirmed unchanged by this plan; only its consumer moved).

## Implementation

### Target file

`tests/agent/services/test_mcp_tool_discovery.py` (extends the file created by
`implementations/20260717-203931_test_mcp_tool_discovery.py.md`).

### Procedure

1. Add a new test class `TestDriftDetection` (or extend an existing class from the base doc, matching
   whatever class structure that doc's implementation actually used) with:
   - `test_duplicate_live_tool_warns_when_local`: two mocked HTTP servers both returning a tool named
     `tool_a`; `ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL`, `ctx.cfg.tool.tool_definitions_strict
     = False`; call `discover_all()`; assert one `StartupCheckOutcome` in `findings` with
     `status == StartupCheckStatus.WARNING` and `"tool_a"` in its message; assert `tool_a` is excluded from
     `registry` (per the base doc's Assumption 5 exclude-in-both-profiles decision).
   - `test_duplicate_live_tool_fatal_when_production`: same setup, `security_profile =
     SecurityProfile.PRODUCTION`; assert `status == StartupCheckStatus.FATAL`.
   - `test_duplicate_live_tool_fatal_when_strict_even_if_local`: `security_profile = LOCAL`,
     `tool_definitions_strict = True`; assert `status == StartupCheckStatus.FATAL` (this is the migrated
     equivalent of the old `test_check_routing_drift_duplicate_strict_raises`, re-expressed as a data
     assertion instead of `pytest.raises`).
   - `test_no_duplicate_no_drift_finding`: two servers with distinct tool names; assert no finding in
     `findings` mentions "duplicate" or "drift", and `pipeline`-equivalent `add_ok` path is reachable
     (i.e. `findings == []` or contains only unrelated entries).
   - `test_drift_vs_registry_mismatch_warns`: register `tool_a -> srv1` in `ToolRegistry`; mock server
     `srv2` (not `srv1`) returning `tool_a`; assert a `StartupCheckOutcome` is produced whose message
     matches the pattern `"Live routing drift"` (mirrors old `repl_health.py:416`'s message format), with
     `status` following the unified severity rule for the given `(strict, profile)` combination under test.
2. Add a new test class `TestUnifiedSeverity` with one parametrized test covering the Design section's
   4-row table verbatim:
   ```
   @pytest.mark.parametrize(
       "strict, profile, expected_status",
       [
           (False, "local", "WARNING"),
           (False, "production", "FATAL"),
           (True, "local", "FATAL"),
           (True, "production", "FATAL"),
       ],
   )
   ```
   Each case constructs a duplicate-tool-name scenario (guaranteed to always produce at least one finding)
   and asserts the resulting `StartupCheckOutcome.status` matches `expected_status` exactly — this directly
   verifies the mitigation the plan's Risk section asked for (each of the 4 combinations deliberately
   checked, not accidental).
3. Add `test_tool_definitions_check_surfaces_as_outcome_not_exception`: mock `agent.repl_health.
   _check_tool_definitions` (imported by the discovery service per
   `implementations/20260717-224511_mcp_tool_discovery.py.md`'s Assumption 1) to raise `RuntimeError("boom")`;
   call `discover_all()`; assert it does **not** raise (unlike old `check_routing_drift_vs_live`'s
   strict-mode behavior) and instead returns a `StartupCheckOutcome` with `status` per the unified severity
   rule and `"boom"` in its message — this is the regression test for the exception-swallowing quirk
   documented in the discovery-service doc's Assumption 4.

### Method

Same as the base test doc: `pytest` + `pytest-asyncio`, `unittest.mock` patching, no new test
infrastructure/fixtures beyond what the base doc already establishes for this file.

### Details

No new production types are introduced by this doc — it only specifies test bodies. Key assertions
reference `StartupCheckOutcome.status` (`agent.shared.health_models.StartupCheckStatus`, already defined,
values `FATAL`/`WARNING`/`OK`/`SKIPPED` per `health_models.py:64-68`) and `DiscoveryResult.findings`
(`list[StartupCheckOutcome]`, per the base discovery-service doc).

## Validation plan

| Check | Command | Target |
|---|---|---|
| Targeted tests | `uv run pytest tests/agent/services/test_mcp_tool_discovery.py -v` | all base-doc tests plus this doc's new drift/severity/exception-surfacing tests pass |
| Old file cleaned up | `uv run pytest tests/test_routing_duplicate_ownership.py -v` | passes after the 3 migrated tests are removed there (per the paired `repl_health.py` doc) — no `ImportError` |
| No orphaned imports | `rg -n "check_routing_drift_vs_live" tests/` | 0 matches (fully migrated) |
| Type check | `uv run mypy tests/agent/services/test_mcp_tool_discovery.py` | 0 errors |
| Lint | `uv run ruff check tests/agent/services/test_mcp_tool_discovery.py` | 0 errors |
| Full suite | `uv run pytest -v` | no new failures |
| Diff coverage | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=main --fail-under=90` | >=90% on changed lines across this batch |
