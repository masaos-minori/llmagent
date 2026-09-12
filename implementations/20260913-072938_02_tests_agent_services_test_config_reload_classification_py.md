# Implementation Procedure: Update test_config_reload_classification.py after config_reload refactor

## Goal

Update `tests/agent/services/test_config_reload_classification.py` to reflect the removal of `_detect_startup_only` and consolidation of `_reload_*` methods.

## Scope

- Delete tests for `_detect_startup_only` (lines 44-51) since the method is removed
- Verify `_detect_diagnostics_live_fields` tests (lines 57-84) still pass
- Update any assertions that depend on `.field_name` accesses

## Assumptions

- The four `_reload_*` methods are fully consolidated into `_reload_section_fields`; no external callers exist
- `_detect_diagnostics_live_fields` remains unchanged (not part of this refactor)
- Tests use `MagicMock` fixtures that remain compatible with the refactored code

## Design decisions

- Delete `_detect_startup_only` tests entirely (they test a removed method); do not migrate them to the new `_classify_startup_only` method unless new tests are needed
- Keep `_detect_diagnostics_live_fields` tests as-is; they should continue to pass since that method is not being changed

## Alternatives considered

- Migrate `_detect_startup_only` tests to `_classify_startup_only` — rejected because the refactor does not require adding new tests for existing behavior; only removing obsolete ones
- Add new tests for `_reload_section_fields` — rejected because the consolidation is internal; existing integration tests cover the public contract

## Implementation

### Target file

`tests/agent/services/test_config_reload_classification.py`

### Procedure

##### Method 1: Delete `_detect_startup_only` tests

Remove lines 44-51:
```python
def test_detect_startup_only_empty_dict(svc: ConfigReloadService) -> None:
    result = svc._detect_startup_only({})
    assert result == []

def test_detect_startup_only_non_startup_keys_ignored(svc: ConfigReloadService) -> None:
    result = svc._detect_startup_only({"llm_temperature": 0.3, "llm_max_tokens": 8192})
    assert result == []
```

Also remove the comment line above them (line 41):
```python
# --- Direct unit tests of _detect_startup_only ---
```

##### Method 2: Update `.field_name` references in test assertions

The remaining tests use `svc._apply_tool_params` which is a removed method. These tests (lines 90-103) reference `_apply_tool_params` which no longer exists. They must be updated or removed.

Looking at the test file:
- Lines 90-95: `test_apply_tool_params_ignores_tool_cache_ttl` — calls `svc._apply_tool_params`, which is removed
- Lines 98-103: `test_apply_tool_params_still_collects_serial_tool_calls` — calls `svc._apply_tool_params`, which is removed

These tests must be deleted because:
1. `_apply_tool_params` is removed (it's one of the four `_reload_*` methods being consolidated)
2. `tool_cache_ttl` is not in `CONFIG_FIELD_REGISTRY` — it's handled separately outside the registry-driven loop

##### Method 3: Keep `_detect_diagnostics_live_fields` tests

Lines 57-84 remain unchanged. These tests verify `_detect_diagnostics_live_fields` which is not being modified by this refactor.

## Compatibility considerations

- Test file changes are backward-compatible: removing obsolete tests does not break any existing test contracts
- No new test dependencies introduced

## Security considerations

- No security impact: test file changes only affect test coverage, not production security

## Rollback considerations

- If deleting `_apply_tool_params` tests causes test suite failures, restore them temporarily and investigate whether `_apply_tool_params` should be preserved as an alias to `_reload_section_fields`

## Validation plan

| Target File | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| tests/agent/services/test_config_reload_classification.py | Unit: verify remaining tests pass | uv run pytest tests/agent/services/test_config_reload_classification.py -v | All tests pass |
| tests/agent/services/test_config_reload_classification.py | Integration: verify full agent test suite passes | uv run pytest tests/agent/ -v --tb=short | All tests pass |

## Completion criteria

- [ ] `_detect_startup_only` tests deleted
- [ ] `_apply_tool_params` tests deleted (method removed)
- [ ] `_detect_diagnostics_live_fields` tests still pass
- [ ] No `.field_name` references remain in test file
- [ ] Existing tests (`test_config_reload_classification.py`) still pass
- [ ] Full agent test suite passes

## Out of scope

- Adding new tests for `_classify_startup_only`
- Modifying `_detect_diagnostics_live_fields` tests
- Changing test fixture structure
- Adding tests for `_reload_section_fields` consolidation

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Delete _detect_startup_only tests | Pending | — | — | REQ-001 |
| 2 | Delete _apply_tool_params tests | Pending | — | — | REQ-002 |
| 3 | Verify _detect_diagnostics_live_fields tests still pass | Pending | — | — | REQ-001, REQ-002 |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | REQ-005, REQ-006 |
| 5 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: no documentation files need updating |

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
- **Source issue**: issues/20260913-064743_refactor_config_reload_eliminate_duplication.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260913-070431_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260913-072938
- **Related target files**: tests/agent/services/test_config_reload_classification.py
