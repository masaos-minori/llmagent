## Goal

Add guard tests for llm_hot_config.py before refactoring to establish behavioral baseline for all public methods.

## Scope

**In-Scope:**
- Create `tests/shared/test_llm_hot_config.py` with tests for:
  - `apply_config()`: normal config application, partial updates, rollback scenarios
  - `apply_one()`: individual field application, validation failures, edge cases
  - Hot reload scenario: changes applied without restarting process
  - Error handling: invalid configs produce appropriate errors

**Out-of-Scope:**
- Changing the behavior of `LlmHotConfigHandler` itself
- Any changes beyond the test

## Assumptions

1. The handler needs characterization tests since it has zero coverage
2. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test directory structure for shared modules | Check `tests/shared/` directory | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/shared/test_llm_hot_config.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `llm_hot_config.py`:
```python
# apply_one: simple setattr
@staticmethod
def apply_one(instance: object, field: str, kwarg: str, value: Any) -> None:
    setattr(instance, field, value)

# apply_config: iterates over HOT_CONFIG_FIELDS and applies non-None values
@staticmethod
def apply_config(instance: object, *, temperature=None, ...) -> None:
    args = dict(temperature=temperature, ...)
    for attr, kwarg in LlmHotConfigHandler.HOT_CONFIG_FIELDS:
        if (value := args.get(kwarg)) is not None:
            LlmHotConfigHandler.apply_one(instance, attr, kwarg, value)
```

The test will verify that `apply_config()` correctly applies only non-None values and leaves other fields unchanged.

## Implementation

### Target file
New file: `tests/shared/test_llm_hot_config.py`

### Procedure
1. Verify `tests/shared/` directory exists
2. Create new test file `tests/shared/test_llm_hot_config.py`
3. Write tests for `apply_one()` and `apply_config()`
4. Save the file

### Method
Create characterization tests using mock objects to verify current behavior.

### Details
1. Create `tests/shared/test_llm_hot_config.py`:
   ```python
   """Characterization tests for LlmHotConfigHandler."""
   
   import pytest
   from shared.llm_hot_config import LlmHotConfigHandler
   
   @pytest.fixture
   def mock_instance():
       class MockInstance:
           _temperature = 0.7
           _max_tokens = 100
           _max_retries = 3
           _retry_base_delay = 1.0
           _sse_heartbeat_timeout = 30.0
           _sse_malformed_retry = 3
           _sse_reconnect_max = 5
           _llm_stream_retry_on_heartbeat_timeout = True
           _llm_stream_retry_on_malformed_chunk = True
       return MockInstance()
   
   def test_apply_one_sets_field(mock_instance):
       LlmHotConfigHandler.apply_one(mock_instance, "_temperature", "temperature", 0.9)
       assert mock_instance._temperature == 0.9
   
   def test_apply_config_applies_only_non_none_values(mock_instance):
       LlmHotConfigHandler.apply_config(mock_instance, temperature=0.9)
       assert mock_instance._temperature == 0.9
       assert mock_instance._max_tokens == 100  # unchanged
   
   def test_apply_config_partial_update(mock_instance):
       LlmHotConfigHandler.apply_config(mock_instance, temperature=0.9, max_tokens=200)
       assert mock_instance._temperature == 0.9
       assert mock_instance._max_tokens == 200
       assert mock_instance._max_retries == 3  # unchanged
   
   def test_apply_config_all_fields(mock_instance):
       LlmHotConfigHandler.apply_config(
           mock_instance,
           temperature=0.9,
           max_tokens=200,
           max_retries=5,
           retry_base_delay=2.0,
           sse_heartbeat_timeout=60.0,
           sse_malformed_retry=5,
           sse_reconnect_max=10,
           stream_retry_on_heartbeat_timeout=False,
           stream_retry_on_malformed_chunk=False,
       )
       assert mock_instance._temperature == 0.9
       assert mock_instance._max_tokens == 200
       assert mock_instance._max_retries == 5
       assert mock_instance._retry_base_delay == 2.0
       assert mock_instance._sse_heartbeat_timeout == 60.0
       assert mock_instance._sse_malformed_retry == 5
       assert mock_instance._sse_reconnect_max == 10
       assert mock_instance._llm_stream_retry_on_heartbeat_timeout is False
       assert mock_instance._llm_stream_retry_on_malformed_chunk is False
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current behavior

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/shared/test_llm_hot_config.py` | Characterization tests document current behavior | `uv run pytest -k "llm_hot" -v` | All tests pass |

## Out of scope

- Changing the behavior of `LlmHotConfigHandler` itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-125726_require.md
- Source plan: plans/20260726-171409_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/shared/llm_hot_config.py, tests/shared/test_llm_hot_config.py
