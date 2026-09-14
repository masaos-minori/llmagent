## Goal

Add an end-to-end test in `tests/agent/services/test_config_reload.py` that exercises the real `/reload` trigger path (`ConfigReloadService.apply_config_dict()` → `_sync_services()` → `RuntimeToolRegistry.apply_policy()`) against a real, non-mocked `RuntimeToolRegistry` instance, confirming both that `apply_policy()`'s effect is observable and that no MCP tool-discovery HTTP call occurs during reload — closing the verification gap tracked as `CI-003`. Per REQ-001, REQ-002.

## Scope

- Add exactly one end-to-end test method to `tests/agent/services/test_config_reload.py`
- Test that `apply_policy()`'s effect (tier/allowed-tools changes) is observable on a real registry after `apply_config_dict()`
- Test that no discovery-style HTTP call occurs during `apply_config_dict()`
- Out-of-scope: modifying `apply_policy()`'s or the reload trigger's actual behavior; changing any other test

## Assumptions

- The existing `TestRuntimeToolPolicyReapplication` class (line 439) provides the structural template to mirror
- The existing `_make_svc()` helper (line 442) creates a `MagicMock()`-based `ctx` with `runtime_tools` as `MagicMock()` when `with_registry=True`
- `RuntimeToolRegistry.__init__()` takes a `{tool_name: RuntimeTool}` dict — confirmed constructible directly via the `build_runtime_tool()` helper pattern from `scripts/shared/runtime_tool.py:72`
- `RuntimeToolRegistry.apply_policy()` mutates the registry in-place — confirmed via read of `runtime_tool_registry.py:143-163`
- `apply_config_dict()` internally calls `_sync_services(new_cfg, llm, hist_mgr, runtime_tools)` at line 278 — confirmed via read of `config_reload.py:215-288`

## Design decisions

1. Place the new test in the existing `TestRuntimeToolPolicyReapplication` class — consistent with the Plan's recommendation and the existing pattern where RAG rebuild commands live here
2. Replace only `ctx.services_required.runtime_tools` with a real `RuntimeToolRegistry` instance, leaving every other `ctx.services_required.*` field as `MagicMock()` scaffolding already used by this file's fixtures — isolates the change to exactly what `CI-003` questions
3. Use `build_runtime_tool()` from `scripts/shared/runtime_tool.py` to construct a small, representative tool set — avoids reinventing construction logic
4. Include assertions on both the tier/allowed-tools state change AND the no-HTTP-call invariant in the same test — mirrors the Plan's intent to close CI-003 with a single verification

## Alternatives considered

1. Creating a separate test class for the E2E test: rejected — the existing pattern groups related RAG/reload tests together under one class
2. Using a different assertion style for the HTTP-call check: rejected — the existing `test_reload_does_not_fetch_tools_over_http` uses `http.get.assert_not_called()`; consistency within the class is preferred

## Implementation

### Target file

`tests/agent/services/test_config_reload.py`

### Procedure

1. Read the existing `TestRuntimeToolPolicyReapplication` class (lines 439-478) to confirm current content
2. Add new test method after `test_reload_does_not_fetch_tools_over_http` (after line 478)
3. Verify the test follows the same fixture/assertion pattern as existing tests

### Method

1. Read `test_config_reload.py` lines 439-478 to confirm the exact test structure
2. Insert new test after line 478 using the same indentation style
3. Each test follows the same pattern: use `_make_svc()`, replace `runtime_tools` with real instance, call `apply_config_dict()`, assert on results

### Details

**Step 1 — Read existing test structure:**

Current `TestRuntimeToolPolicyReapplication` class (lines 439-478):

```python
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
        svc._sync_services({}, None, None, ctx.services_required.runtime_tools)  # type: ignore[attr-defined]
        ctx.services_required.runtime_tools.apply_policy.assert_called_once_with(
            tier_map=ctx.cfg.approval.tool_safety_tiers,
            allowed_tools=ctx.cfg.tool.allowed_tools,
        )

    def test_runtime_tools_reported_in_applied(self) -> None:
        svc, ctx = self._make_svc()
        result = svc._sync_services({}, None, None, ctx.services_required.runtime_tools)
        assert "runtime_tools" in result.applied

    def test_no_runtime_tools_registry_is_noop(self) -> None:
        svc, ctx = self._make_svc(with_registry=False)
        result = svc._sync_services({}, None, None, None)
        assert "runtime_tools" not in result.applied

    def test_reload_does_not_fetch_tools_over_http(self, svc: object) -> None:
        # Regression guard: _sync_services must never trigger HTTP calls
        # Uses direct _sync_services call to avoid MCP discovery complexity
        svc._ctx.services_required.http = MagicMock()  # type: ignore[attr-defined]
        svc._sync_services({}, None, None, None)  # type: ignore[attr-defined]
        svc._ctx.services_required.http.get.assert_not_called()  # type: ignore[attr-defined]
```

**Step 2 — Add new test after line 478:**

```python
    def test_apply_config_dict_exercises_real_registry_and_no_discovery_call(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """End-to-end: apply_config_dict → _sync_services → apply_policy on a real RuntimeToolRegistry."""
        from unittest.mock import MagicMock, patch

        from shared.runtime_tool import AgentSafetyTier, build_runtime_tool
        from shared.runtime_tool_registry import RuntimeToolRegistry

        svc, ctx = self._make_svc(with_registry=True)
        # Replace the MagicMock() runtime_tools with a real Registry instance
        tools = {
            "read_file": build_runtime_tool(
                name="read_file",
                server_key="fs",
                description="Read a file",
                input_schema={"type": "object"},
                status="active",
                is_write=False,
                agent_safety_tier=cast(AgentSafetyTier, "READ_ONLY"),
                enabled_for_llm=True,
            ),
            "delete_file": build_runtime_tool(
                name="delete_file",
                server_key="fs",
                description="Delete a file",
                input_schema={"type": "object"},
                status="active",
                is_write=True,
                agent_safety_tier=cast(AgentSafetyTier, "WRITE_DANGEROUS"),
                enabled_for_llm=True,
            ),
        }
        real_registry = RuntimeToolRegistry(tools=tools)
        ctx.services_required.runtime_tools = real_registry  # type: ignore[attr-defined]
        # Track HTTP calls using the same pattern as test_reload_does_not_fetch_tools_over_http
        ctx.services_required.http = MagicMock()  # type: ignore[attr-defined]

        svc.apply_config_dict({
            "tool_safety_tiers": {"read_file": "ADMIN", "delete_file": "ADMIN"},
            "allowed_tools": ["read_file"],
        })

        # Assert: tier change is observable on the real registry
        assert real_registry.resolve("read_file") == "fs"
        read_tool = real_registry.get("read_file")
        assert read_tool.agent_safety_tier == "ADMIN"

        # Assert: allowed_tools change is observable on the real registry
        delete_tool = real_registry.get("delete_file")
        assert delete_tool.enabled_for_llm is False  # removed from allowlist

        # Assert: no discovery-style HTTP call occurred (mirrors test_reload_does_not_fetch_tools_over_http)
        ctx.services_required.http.get.assert_not_called()  # type: ignore[attr-defined]
```

Rationale: mirrors the existing `test_reload_does_not_fetch_tools_over_http` test's HTTP-call tracking pattern exactly (using `ctx.services_required.http = MagicMock()` + `.get.assert_not_called()`), but extends it to the real trigger path (`apply_config_dict()` instead of `_sync_services()`). Replaces only `runtime_tools` with a real instance while keeping all other `services_required` fields as `MagicMock()`.

Reference files read (must NOT be modified):
- `scripts/agent/services/config_reload.py:215-288` — confirms `apply_config_dict()` flow
- `scripts/agent/services/config_reload.py:310-353` — confirms `_sync_services()` delegates to `apply_policy()`
- `scripts/shared/runtime_tool_registry.py:37-48` — confirms `RuntimeToolRegistry.__init__()` constructor
- `scripts/shared/runtime_tool_registry.py:143-163` — confirms `apply_policy()` in-place mutation
- `scripts/shared/runtime_tool.py:72-134` — confirms `build_runtime_tool()` helper
- `tests/agent/services/test_config_reload.py:439-478` — confirms existing test pattern

## Compatibility considerations

- No public API changes; only adds new test method
- Test isolation preserved: each test uses its own fixture instance
- Existing tests unaffected by the addition

## Security considerations

N/A — test-only change, no security-sensitive operations introduced.

## Rollback considerations

- Revert the added test method to restore original state
- No data loss risk — only test code changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/services/test_config_reload.py | Integration — verify E2E test passes | `uv run pytest tests/agent/services/test_config_reload.py -k test_apply_config_dict_exercises_real_registry_and_no_discovery_call -q` | New test passes |
| tests/agent/services/test_config_reload.py | Regression — verify existing tests still pass | `uv run pytest tests/agent/services/test_config_reload.py -q` | Existing tests unaffected |
| scripts/agent/services/config_reload.py | Static analysis | `uv run radon cc scripts/agent/services/config_reload.py -s`, `uv run bandit -r scripts/agent/services/config_reload.py -c pyproject.toml` | No new findings beyond current baseline |

## Completion criteria

- [ ] `test_apply_config_dict_exercises_real_registry_and_no_discovery_call` added and passes
- [ ] Test constructs a real `RuntimeToolRegistry` with a small tool set
- [ ] Test asserts tier change is observable on the real registry after `apply_config_dict()`
- [ ] Test asserts allowed_tools change is observable on the real registry after `apply_config_dict()`
- [ ] Test asserts no discovery-style HTTP call occurred during `apply_config_dict()`
- [ ] Existing tests still pass without regression

## Out of scope

- Modifying `apply_policy()`'s or the reload trigger's actual behavior
- Adding a scheduled cleanup mechanism
- Changing the existing `rag-maintenance-service` behavior
- Testing edge cases like concurrent access or transaction rollback

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: existing tests cover regression |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | N/A: documentation-only change |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring already describes delegation |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260914-105949_mcpagent10_runtime-registry-reload-e2e-verification.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-150238_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-170046
- **Related target files**: tests/agent/services/test_config_reload.py
