# EventBus Deprecated Config Cleanup

## Goal

Clean up deprecated Event Bus configuration fields (`poll_interval_ms` and `offset_checkpoint_interval`) to reduce operator confusion by retaining them with explicit deprecation warnings rather than removing them entirely.

## Scope

**In-Scope**:
- Retain both deprecated fields in EventBusConfig with explicit warning on load
- Emit a `warnings.warn()` when deprecated fields are set to non-default values in TOML config
- Document both fields as no-op compatibility fields
- Remove `poll_interval_ms = 500` from the active TOML config example (config/eventbus.toml)
- Update reference API docs with deprecation notes for both fields

**Out-of-Scope**:
- Reintroducing polling subscribe delivery
- Reintroducing automatic offset checkpointing
- Removing the validation checks (`< 1`) on deprecated fields — kept as-is for backward compatibility

## Assumptions

1. `poll_interval_ms` is deprecated because subscribe delivery switched from polling to EventBroker push (push-mode) — confirmed by existing doc comment in config.py line 29
2. `offset_checkpoint_interval` is deprecated because offset checkpointing was replaced with ack-only model — confirmed by existing doc comment in config.py line 32
3. These fields are no-op: search of all files in `scripts/eventbus/` confirms neither field is read or used outside of config.py (broker.py, app.py, db.py, dlq.py, offsets.py have zero references)
4. Existing TOML configs (e.g., `config/eventbus.toml`) may set these fields — removal would break them, so retention with warning is the safer choice

## Implementation

### Phase 1: Add deprecation warnings in config.py

**Target file**: `scripts/eventbus/config.py`

**Procedure**:
1. Import `warnings` module at the top of the file
2. In `EventBusConfig.__post_init__`, add `warnings.warn()` calls when deprecated fields are set to non-default values
3. Update field docstrings/comments to clarify no-op status

**Method**: Edit config.py to add warnings import and deprecation logic in `__post_init__`.

**Details**:
- Add `import warnings` after existing imports (line 4)
- Add warning checks in `__post_init__` after the existing validation checks (after line 47):
```python
if self.poll_interval_ms != 500:
    warnings.warn(
        "poll_interval_ms is deprecated and has no effect; push-mode delivery via EventBroker",
        DeprecationWarning,
        stacklevel=2,
    )
if self.offset_checkpoint_interval != 10:
    warnings.warn(
        "offset_checkpoint_interval is deprecated and has no effect; ack-only model in place",
        DeprecationWarning,
        stacklevel=2,
    )
```

**Rationale for non-default threshold**: Only emit warning when the value differs from the default. Setting `poll_interval_ms = 500` (the default) produces a warning even though it has no effect — this would be noisy for operators who already set it to the default. The default values are acceptable because they have no runtime effect anyway.

### Phase 2: Remove deprecated field from active TOML config

**Target file**: `config/eventbus.toml`

**Procedure**:
1. Remove line 7 (`poll_interval_ms = 500`) from the TOML config

**Method**: Direct edit — remove the single line.

**Details**:
- Current config/eventbus.toml:
```toml
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
poll_interval_ms = 500
```
- After removal:
```toml
port = 8015
db_path = "/opt/llm/db/eventbus.sqlite"
storage_dir = "/opt/llm/storage"
offsets_dir = "/opt/llm/offsets"
deadletter_dir = "/opt/llm/deadletter"
max_retry = 3
```

**Rationale**: The TOML example should not include deprecated fields that have no effect. Operators copying this config won't inadvertently set a no-op field.

### Phase 3: Update reference API docs

**Target file**: `docs/06_eventbus_06_reference_api.md`

**Procedure**:
1. Add deprecation notes next to both field definitions in the EventBusConfig dataclass example (lines 35-36)
2. Clarify that setting these fields has no runtime effect

**Method**: Edit lines 35-36 to add `[deprecated]` annotations and descriptions.

**Details**:
- Current:
```python
poll_interval_ms: int = 500
offset_checkpoint_interval: int = 10
```
- After edit:
```python
poll_interval_ms: int = 500  # [deprecated] no-op; push-mode delivery via EventBroker
offset_checkpoint_interval: int = 10  # [deprecated] no-op; ack-only model in place
```

**Target file**: `docs/06_eventbus_05_configuration_deploy_and_operations.md`

**Procedure**:
1. Update the deprecation column for both fields (lines 24-25) to explicitly state they are no-op and that setting them will emit a warning

**Method**: Edit the deprecation descriptions in the config table.

**Details**:
- Current line 24: `[deprecated] Subscribe polling interval — no longer used; push-mode delivery via EventBroker`
- After edit: `[deprecated] No-op compatibility field. Setting this emits a DeprecationWarning. Subscribe polling was replaced with push-mode delivery via EventBroker.`
- Current line 25: `[deprecated] Mid-stream offset checkpoint interval — removed; ack-only model in place`
- After edit: `[deprecated] No-op compatibility field. Setting this emits a DeprecationWarning. Offset checkpointing was replaced with ack-only model.`

**Target file**: `docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md`

**Procedure**:
1. Update the deprecated notice (line 40) to mention the warning behavior

**Method**: Edit line 40 to add warning detail.

**Details**:
- Current: `**Deprecated**: offset_checkpoint_interval config field is no longer used.`
- After edit: `**Deprecated**: offset_checkpoint_interval config field is no-op. Setting this in TOML emits a DeprecationWarning. Offset checkpointing was replaced with ack-only model.`

### Phase 4: Add config validation tests

**Target file**: `tests/test_eventbus_config.py` (new)

**Procedure**:
1. Create test file with tests for deprecated field handling
2. Test that EventBusConfig loads without deprecated fields (no error, no warning)
3. Test that EventBusConfig emits DeprecationWarning when deprecated fields are set to non-default values
4. Test that EventBusConfig accepts default values without warning

**Method**: Use pytest with direct dataclass instantiation and `pytest.warns()` for warning assertions.

**Details**:
```python
import warnings
import pytest
from scripts.eventbus.config import EventBusConfig

def test_no_warning_without_deprecated_fields():
    cfg = EventBusConfig(
        port=8015, db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter", max_retry=3
    )
    # No warning for default values
    assert cfg.poll_interval_ms == 500
    assert cfg.offset_checkpoint_interval == 10

def test_no_warning_with_default_values():
    cfg = EventBusConfig(
        port=8015, db_path="/tmp/eventbus.sqlite",
        storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
        deadletter_dir="/tmp/deadletter", max_retry=3,
        poll_interval_ms=500, offset_checkpoint_interval=10
    )
    # No warning when set to defaults
    assert cfg.poll_interval_ms == 500
    assert cfg.offset_checkpoint_interval == 10

def test_warning_poll_interval_ms_non_default():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015, db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter", max_retry=3,
            poll_interval_ms=1000
        )
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "poll_interval_ms" in str(w[0].message)

def test_warning_offset_checkpoint_interval_non_default():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015, db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter", max_retry=3,
            offset_checkpoint_interval=30
        )
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "offset_checkpoint_interval" in str(w[0].message)

def test_both_warnings_when_both_non_default():
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        EventBusConfig(
            port=8015, db_path="/tmp/eventbus.sqlite",
            storage_dir="/tmp/storage", offsets_dir="/tmp/offsets",
            deadletter_dir="/tmp/deadletter", max_retry=3,
            poll_interval_ms=1000, offset_checkpoint_interval=30
        )
        assert len(w) == 2
        assert any("poll_interval_ms" in str(warn.message) for warn in w)
        assert any("offset_checkpoint_interval" in str(warn.message) for warn in w)
```

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/config.py | Verify deprecation warnings added | Check for `warnings.warn()` calls on deprecated fields with non-default values | Warnings emitted when deprecated fields set to non-default values |
| config/eventbus.toml | Verify deprecated field removed | Check for absence of `poll_interval_ms` in TOML | No deprecated fields in active config example |
| docs/06_eventbus_06_reference_api.md | Verify deprecation notes added | Check for `[deprecated]` annotations next to both fields | Docs clearly mark fields as no-op with warning behavior |
| docs/06_eventbus_05_configuration_deploy_and_operations.md | Verify deprecation descriptions updated | Check for "no-op" and "DeprecationWarning" in field descriptions | Docs explicitly state warning behavior |
| docs/06_eventbus_04_dlq_offsets_and_delivery_semantics.md | Verify deprecated notice updated | Check for mention of DeprecationWarning in deprecated section | Notice includes warning behavior detail |
| tests/test_eventbus_config.py (new) | Verify deprecated field handling tests pass | `uv run pytest tests/test_eventbus_config.py` | All 5 deprecated field tests pass |

## Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Warning may be too noisy if set to default value (e.g., poll_interval_ms = 500 in existing config) | Low | Only emit warning when the value differs from the default. Default values are acceptable since they have no effect anyway. |
| Existing TOML configs that set these fields will get warnings after deployment | Medium | This is the intended behavior — operators should be aware the fields are deprecated. The warning is a signal to clean up their config. |
| Warning stacklevel=2 may not point to the correct source file in all callers | Low | `stacklevel=2` points to the caller of `EventBusConfig.__post_init__`, which is typically where the config is loaded (e.g., `load_config`). If needed, adjust based on actual call site. |
| Validation checks (`< 1`) remain on deprecated fields — may confuse operators | Low | These checks are harmless for backward compatibility. They can be removed in a future cleanup phase if desired. |
