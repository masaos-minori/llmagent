## Goal

Add guard test for security_profile fallback in config_reload.py to verify behavior when an invalid value is injected.

## Scope

**In-Scope:**
- Create a characterization test that injects an invalid `security_profile` value
- Verify the current fallback behavior (silent ignore)
- Document the expected behavior based on test results

**Out-of-Scope:**
- Changing the fallback behavior itself (would be a separate issue)
- Any changes beyond the test

## Assumptions

1. The current behavior is silent ignore (no logging, no default value)
2. This is a characterization test — documenting current behavior, not changing it

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for config reload edge cases | Search for `config_reload` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_config_reload_security_profile.py`

- **Blast Radius:**
  - Test-only change — no production code affected

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `config_reload.py`:
```python
# Current (silent ignore):
if (vs := _get_str(new_cfg, "security_profile")) is not None:
    try:
        ctx.cfg.mcp.security_profile = SecurityProfile(vs)
    except ValueError:
        pass  # invalid enum value — leave current
```

The test will verify that when an invalid `security_profile` value is provided during config reload, the existing value is preserved without error.

## Implementation

### Target file
New file: `tests/test_config_reload_security_profile.py`

### Procedure
1. Create new test file `tests/test_config_reload_security_profile.py`
2. Write test that injects invalid `security_profile` value via mock config
3. Assert that current value is preserved after reload attempt
4. Save the file

### Method
Create characterization test using mock config injection.

### Details
1. Create `tests/test_config_reload_security_profile.py`:
   ```python
   """Characterization test for security_profile fallback in config_reload."""
   
   import pytest
   
   @pytest.mark.asyncio
   async def test_invalid_security_profile_ignored() -> None:
       """Invalid security_profile value should be silently ignored."""
       # Setup: create mock context with valid security_profile
       # Inject invalid value into config
       # Call config reload
       # Assert: security_profile unchanged
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

N/A — this test documents current security behavior

## Rollback considerations

- Simple revert: delete the test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_config_reload_security_profile.py` | Invalid value silently ignored | `uv run pytest -k "config_reload" -v` | Test passes, documents current behavior |

## Out of scope

- Changing the fallback behavior itself
- Any changes beyond the test

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-125625_require.md
- Source plan: plans/20260726-171249_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/services/config_reload.py
