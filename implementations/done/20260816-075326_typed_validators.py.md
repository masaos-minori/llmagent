# Implementation Procedure: Add required parameter to _get_* helper functions

## Goal

Add a `required` parameter to `_get_*` helper functions in `scripts/agent/services/typed_validators.py` so callers can distinguish between "key absent" and "key present but None".

## Scope

- `scripts/agent/services/typed_validators.py`: Add `required` parameter to `_get_int`, `_get_float`, `_get_bool`, `_get_str`, `_get_list`, `_get_dict`
- Update all callers in `config_builders.py` and `config_reload.py` to use the new parameter where needed

## Assumptions

1. The `required` parameter should default to `False` for backward compatibility with existing callers
2. When `required=True` and the key is absent or None, raise `ConfigReloadValidationError` instead of returning None
3. Existing callers don't need changes unless they explicitly want the new behavior
4. The `_get_*` helpers are imported by `config_reload.py` and `config_builders.py` only — NOT `rag/ingestion/pipeline_utils.py`

## Design decisions

- Add `required: bool = False` as the second positional parameter after `key`
- When `required=True` and value is missing/None, raise `ConfigReloadValidationError` with a descriptive message
- Keep the existing signature compatible — all existing callers continue working without modification
- Use `ConfigReloadValidationError` consistently for validation failures

## Alternatives considered

1. **Create separate `_get_required_*` functions**: Would duplicate code and make it harder to maintain. A single parameterized function is cleaner.

2. **Use a sentinel value instead of `required` parameter**: Would require changing every call site to pass the sentinel. Less intuitive than a boolean flag.

3. **Change return type to `Optional[T] | Sentinel`**: Would break existing callers that rely on `is None` checks. A parameter is less disruptive.

## Compatibility considerations

- Adding a required parameter changes the function signature. All callers must be updated to pass the new parameter.
- If a caller doesn't update their call, Python will raise `TypeError` at runtime, which is acceptable since it's a clear signal that the change is incomplete.
- No database or config changes to revert.

## Security considerations

N/A — no security implications. Only adds a validation parameter.

## Rollback considerations

- Remove the `required` parameter from all `_get_*` functions
- Revert all caller updates to original signatures
- No database or config changes to revert

## Validation plan

- Unit test: `_get_int(cfg, "missing_key", required=True)` raises `ConfigReloadValidationError`
- Unit test: `_get_int(cfg, "present_key", required=False)` returns None when key is absent (backward compatible)
- Unit test: `_get_int(cfg, "present_key", required=True)` returns value when key is present
- Integration test: Verify no regressions in normal operation
- Manual: Check that no existing tests break after the change

## Out of scope

- Changes to `_apply_*` helpers (they already handle None correctly via the `if (v := _get_*) is not None:` pattern)
- Changes to how `required` is validated (always raise on missing/None when True)
- Changes to error message formatting beyond adding the key name
- Integration tests for lifecycle transitions (only unit tests for typed validators)

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260815-162431_require.md
- Source plan: plans/20260815-175557_plan.md
- Source implementation procedure: N/A
- Generated at: 20260816-075326
- Related target files: scripts/agent/services/typed_validators.py

---

## Implementation

### Target file: `scripts/agent/services/typed_validators.py`

#### Procedure

1. Read `scripts/agent/services/typed_validators.py` to confirm current `_get_*` function signatures
2. Add `required: bool = False` parameter to each `_get_*` function
3. Update each function body to check `required` and raise `ConfigReloadValidationError` when appropriate
4. Search for existing callers of `_get_*` functions to assess impact
5. Run lint and typecheck to verify no regressions

#### Method

Modify each `_get_*` function to accept an optional `required` parameter. When `required=True` and the value is missing/None, raise `ConfigReloadValidationError`.

#### Details

Current `_get_int` function (lines 19-28):
```python
def _get_int(d: dict[str, object], key: str) -> int | None:
    """Validate and extract an integer value from a config dict."""
    v = d.get(key)
    if v is None:
        return None
    if not isinstance(v, int) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be int, got {type(v).__name__}"
        )
    return v
```

New `_get_int` function:
```python
def _get_int(d: dict[str, object], key: str, *, required: bool = False) -> int | None:
    """Validate and extract an integer value from a config dict.

    Args:
        d: Config dictionary to extract from.
        key: Key to look up in the dictionary.
        required: If True and the key is missing or None, raise
            ConfigReloadValidationError instead of returning None.
    """
    v = d.get(key)
    if v is None:
        if required:
            raise ConfigReloadValidationError(
                f"config key {key!r} is required but missing"
            )
        return None
    if not isinstance(v, int) or isinstance(v, bool):
        raise ConfigReloadValidationError(
            f"config key {key!r} must be int, got {type(v).__name__}"
        )
    return v
```

Similar changes apply to all other `_get_*` functions:
- `_get_float` (lines 31-40)
- `_get_bool` (lines 43-52)
- `_get_str` (lines 55-64)
- `_get_list` (lines 67-76)
- `_get_dict` (lines 79-88)

Key changes:
- Line 19: Add `*, required: bool = False` parameter (keyword-only for clarity)
- Lines 22-25: Add conditional check for `required` before returning None
- Lines 23-25: Raise `ConfigReloadValidationError` with descriptive message when required and missing

Note: Using keyword-only parameter (`*`) ensures the new parameter is always passed by name, preventing accidental positional argument confusion.
