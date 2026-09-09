# Implementation Procedure: Add Empty Result Repeat Threshold to ToolConfig

## Goal

Add `tool_empty_result_max_repeats` field to `ToolConfig` dataclass to allow configuring the maximum number of consecutive empty results from the same tool before triggering the guard.

## Scope

- Modify `scripts/agent/config_dataclasses.py`: add new field to `ToolConfig` dataclass.
- No other files modified in this document.

## Assumptions

- Default value of `0` means disabled (no empty result repeat detection).
- Positive integer values enable the feature with the specified threshold.
- The field follows the existing pattern of other ToolConfig threshold fields (e.g., `tool_dedup_max_repeats`).

## Design decisions

- Use `int` type with default `0` (disabled), consistent with other threshold fields.
- Place the field near related dedup/error threshold fields for discoverability.
- No validation needed — any positive integer is valid; zero means disabled.

## Alternatives considered

1. **Use a separate `EmptyResultRepeatConfig`**: Would allow more complex per-tool configuration but adds unnecessary complexity for a simple threshold.
2. **Make it a boolean toggle**: Would only allow enabling/disabling without configurable thresholds. Less flexible.

## Implementation

### Target file
`scripts/agent/config_dataclasses.py`

### Procedure

1. Add `tool_empty_result_max_repeats: int = 0` field to `ToolConfig` dataclass.
2. Place it after `tool_error_retry_max` and before `progress_stagnation_window` for logical grouping.

### Method

```python
@dataclass
class ToolConfig:
    """Tool execution, approval policy, and prompt settings."""

    # ... existing fields ...

    tool_error_retry_max: int = 1
    # Max retries for an (name, args) combo that returned an error; 0 = disabled
    tool_empty_result_max_repeats: int = 0
    # Window size for progress stagnation detection; 0 disables
    progress_stagnation_window: int = 3
    # ... rest of fields ...
```

### Details

- Field name: `tool_empty_result_max_repeats`
- Type: `int`
- Default: `0` (disabled)
- Position: After `tool_error_retry_max`, before `progress_stagnation_window`
- Comment style: Follow existing comment convention ("X = disabled")

## Compatibility considerations

- Adding a new field with a default value does not break existing code that instantiates `ToolConfig` without specifying this field.
- Existing tests that create `ToolConfig` instances will continue to work unchanged.
- Downstream consumers that read `cfg.tool.tool_empty_result_max_repeats` will get `0` by default.

## Security considerations

- No security impact. This is a configuration field addition.

## Rollback considerations

- Revert: remove the field definition. No migration needed since the default value ensures backward compatibility.

## Validation plan

1. Verify `ToolConfig()` creates successfully with default value `0`.
2. Verify `ToolConfig(tool_empty_result_max_repeats=5)` sets the value correctly.
3. Verify existing code paths that don't reference this field still work.

## Completion criteria

- [ ] `ToolConfig` has `tool_empty_result_max_repeats: int = 0` field.
- [ ] Field is placed logically among other threshold fields.
- [ ] Default value is `0` (disabled).
- [ ] All existing `ToolConfig` instantiations continue to work.

## Out of scope

- Implementing the guard logic itself (covered in `scripts/agent/tool_loop_guard.py`).
- Wiring the field into the guard's behavior (covered in `scripts/agent/tool_runner.py`).
- Updating documentation or tests (covered in respective documents).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (Detect repeated empty tool results within a single turn)
- **Source issue**: issues/done/20260908-194034_toolloop002_detect-empty-tool-result-repetition.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260908-221112_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260909-181137
- **Related target files**: scripts/agent/config_dataclasses.py
