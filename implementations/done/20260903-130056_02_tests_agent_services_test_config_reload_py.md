# Implementation Procedure: Update tests for ConfigReloadService refactor

## Goal

Update and extend unit tests in `tests/agent/services/test_config_reload.py` to reflect the structural changes made to `ConfigReloadService` while preserving behavioral coverage. Specifically: update `_sync_services()` call signatures, remove pre-validation assertions, add regression tests for consolidated field collection, and verify all validator scenarios still pass.

## Scope

- Update `_sync_services()` call sites to match new explicit parameter signature
- Remove assertions about `_validate_request()` being called
- Add regression tests for `_collect_field_changes()` consolidation
- Verify all validator scenarios still pass without pre-validation layer
- Update fixture setup if needed for new method signatures

## Assumptions

- Tests use `MagicMock` for `AgentContext` and its nested attributes
- Post-application validation replaces pre-validation — all validator scenarios must still raise `ConfigReloadValidationError`
- No behavioral changes to public API contract (`apply_config()`, `apply_config_dict()`)
- `_classify_mcp_server_changes()` remains untouched — no test changes needed there

## Design decisions

- Keep existing test class structure; only modify affected methods
- Add new test class `TestCollectFieldChangesConsolidation` for regression tests
- Preserve all existing validator error-path tests — they should still pass because validators run post-application
- Update `_make_svc()` fixtures where `_sync_services()` is called directly

## Alternatives considered

- Rewrite entire test suite from scratch — rejected because REQ-006 requires preserving public API contract
- Move some tests to integration level — rejected because REQ-007 requires keeping behavioral tests at unit level

## Implementation

### Target file

`tests/agent/services/test_config_reload.py`

### Procedure

#### Step 1: Update `_sync_services()` call sites

In `TestRuntimeToolPolicyReapplication`:

```python
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
```

This fixture already creates `ctx.services_required.*` as `None` or `MagicMock` — no change needed here since `_sync_services()` now receives these as explicit parameters.

However, the direct calls to `svc._sync_services({})` need updating:

```python
# In test_apply_policy_called_with_current_tier_map_and_allowed_tools:
svc, ctx = self._make_svc()
svc._sync_services({}, None, None, ctx.services_required.runtime_tools)

# In test_runtime_tools_reported_in_applied:
svc, ctx = self._make_svc()
result = svc._sync_services({}, None, None, ctx.services_required.runtime_tools)

# In test_no_runtime_tools_registry_is_noop:
svc, ctx = self._make_svc(with_registry=False)
result = svc._sync_services({}, None, None, None)

# In test_reload_does_not_fetch_tools_over_http:
svc._ctx.services_required.http = MagicMock()
svc._sync_services({}, None, None, None)
```

#### Step 2: Remove pre-validation assertions

Search for any assertions about `_validate_request()` being called. Currently none exist in the test file — the method was never mocked or asserted in tests. No changes needed here.

#### Step 3: Add regression tests for consolidated field collection

Add new test class:

```python
class TestCollectFieldChangesConsolidation:
    """Regression tests for _collect_field_changes() replacing _collect_request_values() + _apply_llm_prompt_params()."""

    def _make_svc(self) -> object:
        from agent.services.config_reload import ConfigReloadService

        ctx = MagicMock()
        ctx.cfg.llm = MagicMock()
        ctx.cfg.rag = MagicMock()
        ctx.cfg.tool = MagicMock()
        return ConfigReloadService(ctx)

    def test_consolidated_method_collects_all_llm_fields(self) -> None:
        svc = self._make_svc()
        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}
        
        new_cfg = {
            "llm_temperature": 0.7,
            "llm_max_tokens": 1000,
            "llm_url": "http://localhost:8080",
            "http_timeout": 30.0,
            "llm_max_retries": 3,
            "llm_retry_base_delay": 1.0,
            "sse_heartbeat_timeout": 30.0,
            "sse_malformed_retry": 1,
            "sse_reconnect_max": 5,
            "llm_stream_retry_on_heartbeat_timeout": True,
            "llm_stream_retry_on_malformed_chunk": False,
        }
        
        svc._collect_field_changes(new_cfg, llm_changes, rag_changes, tool_changes)
        
        assert len(llm_changes) == 11
        assert len(rag_changes) == 0
        assert len(tool_changes) == 0

    def test_consolidated_method_collects_all_rag_fields(self) -> None:
        svc = self._make_svc()
        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}
        
        new_cfg = {
            "embed_url": "http://localhost:8080/embed",
            "use_semantic_cache": True,
            "web_search_url": "http://localhost:8080/search",
            "semantic_cache_threshold": 0.92,
            "semantic_cache_max_size": 100,
            "use_refiner": True,
            "refiner_max_tokens": 512,
            "refiner_timeout": 30.0,
            "refiner_max_chars_per_chunk": 300,
        }
        
        svc._collect_field_changes(new_cfg, llm_changes, rag_changes, tool_changes)
        
        assert len(llm_changes) == 0
        assert len(rag_changes) == 9
        assert len(tool_changes) == 0

    def test_consolidated_method_collects_all_tool_fields(self) -> None:
        svc = self._make_svc()
        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}
        
        new_cfg = {
            "max_tool_turns": 10,
            "tool_result_max_llm_chars": 4000,
            "tool_definitions": ["tool_a", "tool_b"],
            "system_prompt_tool": "You are helpful.",
            "system_prompts": {"default": "Hello"},
            "serial_tool_calls": True,
            "tool_definitions_strict": True,
            "plan_blocked_tools": ["dangerous_tool"],
        }
        
        svc._collect_field_changes(new_cfg, llm_changes, rag_changes, tool_changes)
        
        assert len(llm_changes) == 0
        assert len(rag_changes) == 0
        assert len(tool_changes) == 8

    def test_consolidated_method_skips_missing_fields(self) -> None:
        svc = self._make_svc()
        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}
        
        new_cfg = {}
        
        svc._collect_field_changes(new_cfg, llm_changes, rag_changes, tool_changes)
        
        assert len(llm_changes) == 0
        assert len(rag_changes) == 0
        assert len(tool_changes) == 0

    def test_consolidated_method_handles_partial_updates(self) -> None:
        svc = self._make_svc()
        llm_changes: dict[str, Any] = {}
        rag_changes: dict[str, Any] = {}
        tool_changes: dict[str, Any] = {}
        
        new_cfg = {
            "llm_temperature": 0.5,
            "use_semantic_cache": True,
            "max_tool_turns": 5,
        }
        
        svc._collect_field_changes(new_cfg, llm_changes, rag_changes, tool_changes)
        
        assert "llm_temperature" in llm_changes
        assert "use_semantic_cache" in rag_changes
        assert "max_tool_turns" in tool_changes
        assert len(llm_changes) == 1
        assert len(rag_changes) == 1
        assert len(tool_changes) == 1
```

#### Step 4: Verify all validator scenarios still pass

No code changes needed — but ensure the following tests still pass after refactor:

- `test_out_of_range_llm_temperature_rejected` — validates post-application rejection
- `test_valid_llm_temperature_applied` — validates post-application acceptance
- `test_invalid_llm_temperature_raises` — validates error path
- `test_invalid_llm_max_tokens_raises` — validates error path
- `test_invalid_http_timeout_raises` — validates error path
- `test_invalid_max_tool_turns_raises` — validates error path
- `test_invalid_tool_result_max_llm_chars_raises` — validates error path
- `test_invalid_context_token_limit_raises` — validates error path

These tests use `svc.apply_config_dict()` which triggers post-application validation — they should continue to work because `_apply_rag_tool_params()` already contains all necessary validators.

#### Step 5: Update fixture setup if needed

The existing `svc` and `svc_with_ctx` fixtures create `MagicMock` objects for `ctx.services_required`. Since `_sync_services()` now receives explicit service parameters instead of accessing `ctx.services_required.*`, the fixtures remain valid — no changes needed.

However, add a note in the fixture docstring:

```python
@pytest.fixture()
def svc() -> object:
    # NOTE: After refactor, _sync_services() receives explicit service parameters
    # instead of accessing ctx.services_required.*. This fixture remains valid
    # because it provides the same mock structure.
    ...
```

## Compatibility considerations

- Public API contract preserved: `apply_config(req: ConfigReloadRequest) -> ConfigReloadOutcome` and `apply_config_dict(new_cfg: dict[str, Any]) -> ConfigReloadOutcome` signatures unchanged (REQ-006)
- `ConfigReloadOutcome` field semantics intact (applied, needs_restart, skipped, startup_only, always_live) (REQ-007)
- MCP server classification logic (`_classify_mcp_server_changes()`) remains untouched — no test changes needed there (REQ-009)
- No behavioral changes to restart detection or live-field detection (REQ-010)

## Security considerations

- All existing validators must still be called; no validator removal (REQ-008)
- Post-application validation replaces pre-application — verify all validator scenarios are covered
- Retain existing `#nosec` justifications; document any new suppressions with rationale

## Rollback considerations

- If post-application validation does not cover all cases, revert to dual-validation pattern temporarily
- Keep `_validate_request()` as an optional pre-validation layer until regression tests confirm equivalence
- If `_collect_field_changes()` introduces bugs, restore individual methods

## Validation plan

- Run `ruff check tests/agent/services/test_config_reload.py` (REQ-012)
- Run `mypy tests/agent/services/test_config_reload.py` (REQ-012)
- Run `uv run pytest tests/agent/services/test_config_reload.py -v` comparing against baseline (REQ-013)
- Verify all existing validator error-path tests still raise `ConfigReloadValidationError`
- Verify new consolidation regression tests pass

## Completion criteria

- All `_sync_services()` call sites updated to match new explicit parameter signature
- New regression tests added for `_collect_field_changes()` covering all three change dicts
- All existing validator error-path tests still pass without modification
- `ruff`, `mypy`, and `bandit` are clean on modified file
- All tests pass without modification

## Out of scope

- Adding new validator scenarios beyond what exists today
- Changing test coverage depth or adding integration tests
- Modifying `_diff_mcp_server_config` tests
- Modifying MCP server classification tests
- Performance optimization beyond what refactor naturally achieves

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update _sync_services() call sites to match new explicit parameter signature | Completed | 2026-09-03 | 2026-09-03 | REQ-005 |
| 2 | Remove assertions about _validate_request() being called | Completed | 2026-09-03 | 2026-09-03 | REQ-002 |
| 3 | Add regression tests for _collect_field_changes() consolidation | Completed | 2026-09-03 | 2026-09-03 | REQ-001 |
| 4 | Verify all validator scenarios still pass | Completed | 2026-09-03 | 2026-09-03 | REQ-008 |
| 5 | Update fixture setup if needed | Completed | 2026-09-03 | 2026-09-03 | REQ-006 |
| 6 | Run validation sequence (ruff, mypy, bandit) | Completed | 2026-09-03 | 2026-09-03 | REQ-012 |
| 7 | Run regression tests | Completed | 2026-09-03 | 2026-09-03 | REQ-013 |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001 through REQ-005, REQ-008 through REQ-012
- **Source issue**: issues/20260831-232522_refactor_001_config_reload_service_refactor.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260902-070422_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260903-130056
- **Related target files**: tests/agent/services/test_config_reload.py
