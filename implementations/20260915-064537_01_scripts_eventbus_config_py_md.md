# Implementation Procedure: Migrate EventBus Configuration Loading to ConfigLoader

## Goal

Replace `scripts/eventbus/config.py`'s direct `tomllib.load()` call with `ConfigLoader`-based loading, preserving all of EventBus's existing fail-closed validation behavior (cross-field checks, required-token checks, etc.) rather than replacing it with `ConfigLoader`'s defaults.

## Scope

- Modify `scripts/eventbus/config.py`: replace `tomllib.load()` with `ConfigLoader`-based loading
- Preserve all existing validation logic in `__post_init__` and `load_config()`
- No change to EventBus's actual validation policy or supported configuration keys

## Assumptions

- `ConfigLoader.restrict_to()` is a classmethod that sets process-level file access restrictions — confirmed by `config_loader.py:40-49`
- `ConfigLoader.load()` accepts filenames and returns merged config data — confirmed by `config_loader.py:58-66`
- EventBus's validation logic in `__post_init__` and `load_config()` must be preserved exactly — confirmed by `config.py:60-94` (__post_init__) and `config.py:163-230` (load_config)
- `ConfigLoader._REQUIRED_CONFIG_FILES` is hardcoded to `("agent.toml",)` — confirmed by `config_loader.py:30`

## Design decisions

### Decision A: Preserve EventBus's validation logic alongside ConfigLoader usage

**Reason:** EventBus has unique validation requirements (cross-field checks, required-token checks) that differ from `ConfigLoader`'s defaults. Replacing the validation logic would silently relax existing checks, violating REQ-002.

### Alternative A: Replace EventBus's validation with `ConfigLoader`'s built-in validation

**Reason for rejection:** Would break REQ-002 — EventBus's validation behavior must be preserved exactly. The `ConfigLoader` default validation is insufficient for EventBus's fail-closed requirements.

### Decision B: Coordinate with `mcpagent07` for `restrict_to()` initialization

**Reason:** Both issues touch `restrict_to()` initialization requirements. If both are implemented in the same session, coordination ensures consistent behavior.

## Implementation

### Target file

`scripts/eventbus/config.py`

### Procedure

#### Step 1: Analyze current state of `config.py`

Read the current implementation to understand:
- How `tomllib.load()` is called (line 166)
- What configuration files are loaded
- What validation logic exists in `__post_init__` (lines 60-94)
- What validation logic exists in `load_config()` (lines 163-230)

#### Step 2: Import `ConfigLoader`

Add import statement at the top of the file:
```python
from scripts.shared.config_loader import ConfigLoader
```

Verify this does not violate the `.importlinter` `eventbus-is-isolated` contract. If the contract forbids importing `shared` from `eventbus`, document the exception in `ADR-002`.

#### Step 3: Replace `tomllib.load()` call with `ConfigLoader.load()`

Current code (around line 166):
```python
with open(config_path, "rb") as f:
    config = tomllib.load(f)
```

After change:
```python
config = ConfigLoader.load(config_path)
```

Or if multiple config files need to be loaded:
```python
config = ConfigLoader.load_all(["base.toml", "override.toml"])
```

#### Step 4: Preserve `__post_init__` validation logic

Ensure the `__post_init__` method (lines 60-94) remains unchanged. This contains EventBus-specific validation that must not be replaced by `ConfigLoader`'s defaults.

#### Step 5: Preserve `load_config()` validation logic

Ensure the `load_config()` function (lines 163-230) remains unchanged. This contains EventBus-specific validation that must not be replaced by `ConfigLoader`'s defaults.

#### Step 6: Initialize `restrict_to()` appropriately

If `ConfigLoader.restrict_to()` needs to be initialized for the EventBus process before production config loading, add the appropriate call. Coordinate with `mcpagent07` if both are implemented in the same session.

Example:
```python
ConfigLoader.restrict_to(process_name="eventbus")
```

#### Step 7: Remove unused `tomllib` import

Remove the `import tomllib` statement (line 6) if it is no longer used elsewhere in the file.

#### Step 8: Run static analysis

```bash
uv run ruff check scripts/eventbus/config.py
uv run mypy scripts/eventbus/config.py
```

Expected: No new errors introduced.

#### Step 9: Run existing tests

```bash
uv run pytest tests/eventbus/test_eventbus_config.py -v
```

Expected: All existing tests pass.

### Method

Surgical replacement of the `tomllib.load()` call with `ConfigLoader.load()` while preserving all existing validation logic.

### Details

#### Verification checklist

- [ ] `ConfigLoader` import added without violating `.importlinter` contract
- [ ] `tomllib.load()` replaced with `ConfigLoader.load()` or `ConfigLoader.load_all()`
- [ ] `__post_init__` validation logic preserved exactly
- [ ] `load_config()` validation logic preserved exactly
- [ ] `restrict_to()` initialized appropriately for EventBus process
- [ ] Unused `tomllib` import removed
- [ ] Static analysis passes without new errors
- [ ] Existing tests pass

## Compatibility considerations

- **Breaking change risk**: Low — `ConfigLoader.load()` should return the same config structure as `tomllib.load()`
- **Downstream consumers**: None expected — the public API surface (`load_config()`) remains unchanged
- **Migration path**: None required — the change is internal to the configuration loading layer

## Security considerations

- **Positive impact**: EventBus will now benefit from `ConfigLoader`'s process-level file-access restriction (`restrict_to()`)
- **Risk**: If `ConfigLoader`'s default validation is less strict than EventBus's current validation, this could introduce security regressions
- **Mitigation**: Preserve EventBus's existing validation logic exactly; do not rely on `ConfigLoader`'s defaults

## Rollback considerations

- Revert to original `tomllib.load()` call
- Restore `import tomllib` if removed
- Remove `ConfigLoader` import if added
- Remove `restrict_to()` call if added

## Validation plan

1. **Static analysis**: Confirm no new lint/type errors introduced
2. **Test execution**: Confirm all existing tests in `tests/eventbus/test_eventbus_config.py` pass
3. **Acceptance criteria verification**:
   - [ ] AC-1: `scripts/eventbus/config.py` loads its configuration via `ConfigLoader`, not `tomllib.load()` directly
   - [ ] AC-2: Every existing EventBus configuration validation error case still produces an equivalent error after migration
   - [ ] AC-3: EventBus configuration loading is now covered by the same process-isolation guarantee (`restrict_to()`) as other processes, or the exception is explicitly documented in `ADR-002` if EventBus cannot use it for a confirmed technical reason

## Completion criteria

- [ ] `ConfigLoader` import added without violating `.importlinter` contract
- [ ] `tomllib.load()` replaced with `ConfigLoader.load()` or `ConfigLoader.load_all()`
- [ ] `__post_init__` validation logic preserved exactly
- [ ] `load_config()` validation logic preserved exactly
- [ ] `restrict_to()` initialized appropriately for EventBus process
- [ ] Unused `tomllib` import removed
- [ ] Static analysis passes without new errors
- [ ] All existing tests pass

## Out of scope

- Modifying `ConfigLoader` itself (separate procedure per row)
- Adding new validation rules beyond what currently exists
- Changing EventBus's actual validation policy or supported configuration keys
- Updating CI-001 governance entry (separate procedure per row)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Analyze current config.py implementation | Pending | — | — | |
| 2 | Add ConfigLoader import | Pending | — | — | |
| 3 | Replace tomllib.load() with ConfigLoader.load() | Pending | — | — | |
| 4 | Preserve __post_init__ validation | Pending | — | — | |
| 5 | Preserve load_config() validation | Pending | — | — | |
| 6 | Initialize restrict_to() for EventBus | Pending | — | — | |
| 7 | Remove unused tomllib import | Pending | — | — | |
| 8 | Run static analysis | Pending | — | — | |
| 9 | Run existing tests | Pending | — | — | |

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
- **Requirement ID**: REQ-001 (replace tomllib.load() with ConfigLoader-based loading), REQ-002 (preserve existing validation behavior), REQ-003 (confirm restrict_to() initialization)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064537
- **Related target files**: scripts/eventbus/config.py
