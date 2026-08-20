# Implementation Procedure: Add sensitive_fields test to TestBuildDiagnosticsConfig

## Goal
Add a unit test to `tests/agent/test_config_builders.py`'s `TestBuildDiagnosticsConfig` verifying `_build_diagnostics_config()` includes a configured `sensitive_fields` entry in the resulting `DiagnosticsConfig`.

## Scope
- Target file: `tests/agent/test_config_builders.py`
- Add one test method to `TestBuildDiagnosticsConfig` class

## Assumptions
- The test should follow the existing `test_overrides_are_applied` pattern
- Need to verify what `_build_diagnostics_config()` actually returns for `sensitive_fields` (raw configured value vs unioned with default)
- The union with `_SENSITIVE_FIELDS` happens later in `_filter_sensitive_fields()`, not in `_build_diagnostics_config()`

## Design decisions
- Follow existing test pattern: call `_build_diagnostics_config({"diagnostics": {"sensitive_fields": ["custom_field"]}})` and assert on the returned value
- Assert on the raw configured value since union happens at use time in `_filter_sensitive_fields()`
- Insert test after `test_missing_diagnostics_table_returns_defaults` (line 385) and before the next class

## Implementation
### Target file
`tests/agent/test_config_builders.py`

### Procedure
1. Read `_build_diagnostics_config()` in `scripts/agent/config_builders.py` to confirm actual behavior
2. Add new test method `test_sensitive_fields_override_is_reflected` to `TestBuildDiagnosticsConfig`

### Method
Direct code addition using exact line matching

### Details
**Location:** After line 385 (after `test_missing_diagnostics_table_returns_defaults`)

**New test method:**
```python
    def test_sensitive_fields_override_is_reflected(self) -> None:
        cfg = _build_diagnostics_config(
            {"diagnostics": {"sensitive_fields": ["custom_field", "another_field"]}}
        )
        # Union with defaults happens in _filter_sensitive_fields() at use time,
        # not in _build_diagnostics_config(). Assert raw configured value.
        assert cfg.sensitive_fields == frozenset(["custom_field", "another_field"])
```

## Compatibility considerations
- Test-only change, no production code impact
- Uses existing `_build_diagnostics_config` function and `frozenset` comparison pattern

## Security considerations
- None - test only

## Rollback considerations
- Git revert of this file if issues arise

## Validation plan
- Run `uv run pytest tests/agent/test_config_builders.py -v` - all pass including new test
- Run full test suite `uv run pytest` - no new failures

## Out of scope
- No changes to production code

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-213537_require.md
- Source plan: plans/20260819-162837_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-124756
- Related target files: tests/agent/test_config_builders.py