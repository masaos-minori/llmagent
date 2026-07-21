# Implementation procedure: `tests/test_startup_validation_pipeline.py` (regression test for `routing_drift_strict`)

Source plan: `plans/20260721-094454_plan.md` ("Restore `[[tool_definitions]]` coverage for git/mdq/file_write
tools; fix inert `routing_drift_strict`"), Implementation step Phase 3.

One existing implementations doc matches this filename:
`implementations/done/20260706-105837_test_startup_validation_pipeline.py.md` — its Goal states it adds
tests "including ... strict-mode drift", but on inspection that scenario in its Method section
(`test_skipped_live_routing_no_raise` and the surrounding tests) exercises `check_routing_drift_vs_live`
(the *live* routing check, a different function/step) under `tool_definitions_strict`, not the *static*
`check_routing_drift(ctx)` call this plan's Phase 2 fix touches. Confirmed against the actual current file
`tests/test_startup_validation_pipeline.py` (253 lines): `grep -n "strict"` → only one hit,
`ctx.cfg.tool.tool_definitions_strict = False` in the `mock_ctx` fixture; every `check_routing_drift`
patch in the file uses `return_value=[]` unconditionally, with no test varying
`ctx.cfg.tool.routing_drift_strict` or asserting a fatal/warning split for the static drift check. This
item is **not yet implemented**.

## Goal

Add a test (or tests) to `tests/test_startup_validation_pipeline.py` that exercises the real
`StartupOrchestrator._check_services()` code path and proves: (a) `routing_drift_strict=True` +
`check_routing_drift()` raising `RuntimeError` (simulated drift) → `_check_services()` raises with a fatal
`routing_drift` outcome; (b) `routing_drift_strict=False` + the same injected drift (as a returned warning
list, not a raise) → only a warning outcome, no raise. This proves the Phase 2 `startup.py` fix (passing
`strict=` and routing `RuntimeError` to `pipeline.add_fatal`) actually takes effect end-to-end, which the
pre-existing `test_routing_drift_strict_raises`-style unit test (a direct `check_routing_drift(strict=True)`
call, not through `startup.py`) does not cover.

## Scope

**In scope:**
- `tests/test_startup_validation_pipeline.py`: add 2 new `_check_services()`-level tests following the
  existing `startup_instance` fixture pattern (lines 70-78 of the current file).

**Out of scope:**
- `tests/test_startup_routing_drift.py` — already has the direct-call unit test per the plan's own note;
  not modified.
- Any other existing test in this file — not modified.
- Adding `routing_drift_strict` to any fixture default beyond the new tests' local patches.

## Assumptions

1. `startup_instance` fixture (current file, lines 70-78) constructs `StartupOrchestrator.__new__(...)`
   with a `MagicMock` `_ctx`, bypassing `__init__`. New tests reuse this fixture.
2. `mock_ctx` fixture (lines 62-67) sets `ctx.cfg.mcp.security_profile = "local"` and
   `ctx.cfg.tool.tool_definitions_strict = False`. New tests must additionally set
   `ctx.cfg.tool.routing_drift_strict` (`True` in one test, `False` in the other) — either by adding it to
   the shared fixture (default `False`, matching production default) or by setting it directly on
   `startup_instance._ctx.cfg.tool.routing_drift_strict` inside each new test body. Prefer setting it
   directly in each test to keep the shared fixture's default behavior unchanged for all other existing
   tests (avoids any risk of altering their behavior).
3. `MODULE = "agent.startup"` (line 16) is the patch-target prefix used throughout the file; new tests
   follow the same `patch(f"{MODULE}.<name>", ...)` convention.
4. Existing tests patch `check_routing_drift` via `patch(f"{MODULE}.check_routing_drift", return_value=[])`
   — a plain (non-async) `MagicMock` return, since `check_routing_drift` is a sync function. The new
   fatal-path test instead needs `side_effect=RuntimeError("...")` to simulate the strict-mode raise from
   `repl_health.check_routing_drift`.
5. All other dependencies (`audit_security_defaults`, `check_readiness`, `McpToolDiscoveryService`,
   `check_routing_safety_tiers`, `RagMaintenanceService`) must be patched to their "all clear" return values
   in the new tests too (mirroring `test_all_checks_pass_no_raise`), so the only variable under test is the
   routing_drift step.

## Implementation

### Target file

`tests/test_startup_validation_pipeline.py`

### Procedure

1. Add a new test `test_routing_drift_strict_true_raises_fatal` (or equivalent name) after the existing
   `_check_services()` integration tests:
   - Sets `startup_instance._ctx.cfg.tool.routing_drift_strict = True` (or passes it via a dedicated
     `mock_ctx`-derived fixture parameter).
   - Patches `check_routing_drift` with `side_effect=RuntimeError("routing drift detected: ...")`.
   - Patches all other dependencies to "all clear" (mirrors `test_all_checks_pass_no_raise`'s patch set).
   - Asserts `pytest.raises(RuntimeError, match="Startup validation failed")` around
     `await startup_instance._check_services()`.
   - Optionally asserts the fatal message contains the routing-drift-specific text (e.g. via
     `exc_info.value` string check), to distinguish this from other fatal sources.
2. Add a new test `test_routing_drift_strict_false_warns_only` (or equivalent name):
   - Sets `startup_instance._ctx.cfg.tool.routing_drift_strict = False`.
   - Patches `check_routing_drift` with `return_value=["drift: tool foo missing from tool_definitions"]`
     (a non-raising warning list — matches the non-strict behavior of `check_routing_drift()`).
   - Patches all other dependencies to "all clear".
   - Asserts `await startup_instance._check_services()` does **not** raise.
3. Confirm both new tests would fail against the pre-fix `startup.py` (i.e., before Phase 2's edit): with
   the old code, `check_routing_drift(ctx)` is called without `strict=`, so passing
   `side_effect=RuntimeError(...)` on the mock would still raise via the mock's side_effect regardless of
   the missing kwarg (the mock doesn't care what kwargs it's *not* given), but the raised `RuntimeError`
   would land in the old broad `except Exception` and be downgraded to `pipeline.add_warning(...)` — so
   `test_routing_drift_strict_true_raises_fatal` would fail (no raise from `_check_services()`) against the
   pre-fix code, correctly proving the test exercises the bug. Confirm this reasoning holds by mentally
   tracing the pre-fix except block, or by running the new test against a temporarily-reverted `startup.py`
   during implementation if verification is desired.

### Method

```python
@pytest.mark.asyncio
async def test_routing_drift_strict_true_raises_fatal(startup_instance) -> None:
    startup_instance._ctx.cfg.tool.routing_drift_strict = True
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(
            f"{MODULE}.check_routing_drift",
            side_effect=RuntimeError("routing drift detected: tool_names mismatch"),
        ),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            await startup_instance._check_services()


@pytest.mark.asyncio
async def test_routing_drift_strict_false_warns_only(startup_instance) -> None:
    startup_instance._ctx.cfg.tool.routing_drift_strict = False
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(
            f"{MODULE}.check_routing_drift",
            return_value=["drift: tool foo missing from tool_definitions"],
        ),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()  # must not raise
```

### Details

- Both new tests reuse the exact patch set of `test_all_checks_pass_no_raise` (current file lines 81-102)
  for all non-routing-drift dependencies, varying only `check_routing_drift`'s patch and
  `routing_drift_strict`.
- `startup_instance._ctx` is a `MagicMock`, so setting `.cfg.tool.routing_drift_strict = True/False`
  directly on the instance in each test does not require touching the shared `mock_ctx` fixture or
  affecting other tests.
- Place the two new tests near the other `_check_services()` integration tests (after
  `test_skipped_live_routing_no_raise` or at the end of the file), keeping the file's existing test grouping
  (unit tests for `StartupValidationResult` first, then `_check_services()` integration tests).

## Validation plan

| Target | Testing strategy | Tool / command | Expected outcome |
|---|---|---|---|
| New tests | Targeted run | `uv run pytest tests/test_startup_validation_pipeline.py -v -k routing_drift_strict` | Both new tests pass against the post-fix `startup.py` (see companion doc `implementations/20260721-141303_startup.py.md`) |
| Pre-fix sanity | Manual/optional | Temporarily revert the Phase 2 `startup.py` change and re-run the strict-true test | Test fails (proves it exercises the real bug, not a tautology) |
| Full file | Regression | `uv run pytest tests/test_startup_validation_pipeline.py -v` | All tests (existing + new) pass |
| Type check | `mypy` | `uv run mypy tests/test_startup_validation_pipeline.py` | No new type errors |
| Full suite | `pytest` | `uv run pytest` | No new failures |
| Diff coverage | `diff-cover` | `uv run coverage run -m pytest tests/ && uv run coverage xml && uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines (both `startup.py` strict/non-strict branches now covered) |
