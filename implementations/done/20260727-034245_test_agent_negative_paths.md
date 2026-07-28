## Goal

Add guard tests for agent layer negative paths and reduce excessive mocking to establish behavioral baseline before refactoring.

## Scope

**In-Scope:**
- AGENT-1: Add security_profile invalid value injection test — verify silent ignore
- AGENT-2: Add recency_days exactly 7-day boundary test — verify boost calculation
- AGENT-3: Create integration characterization test using real DB/subprocess instead of mocks
- AGENT-4: Test that force/overwrite/clobber don't incorrectly elevate read-type tools

**Out-of-Scope:**
- Changes beyond the four specific gaps listed above

## Assumptions

1. The agent layer needs characterization tests due to multiple coverage gaps
2. Tests should verify current behavior, not expected future behavior

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether there's an existing test for agent edge cases | Search for `agent` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_agent_negative_paths.py` — AGENT-1 + AGENT-2 + AGENT-4
  - New file: `tests/integration/test_agent_integration.py` — AGENT-3

- **Blast Radius:**
  - Low churn — new test files only
  - Very low risk since changes are defensive

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the agent layer:
```python
# Key behaviors:
# - security_profile: invalid values silently ignored during config reload
# - recency_days: 7-day boundary affects memory scoring boost calculation
# - Memory scoring: uses real DB/subprocess for scoring
# - Tool policy: force/overwrite/clobber should not elevate read-type tools
```

The tests will verify all four gaps: invalid config handling, boundary conditions, real-component testing, and tool policy correctness.

## Implementation

### Target files
- New file: `tests/test_agent_negative_paths.py`
- New file: `tests/integration/test_agent_integration.py`

### Procedure
1. Phase 1: Verify no existing agent edge case tests exist
2. Phase 2: Address each gap (AGENT-1 through AGENT-4)
3. Phase 3: Verify with lint and tests

### Method
Create characterization tests using real components where possible.

### Details
1. **AGENT-1**: In `test_agent_negative_paths.py`:
   ```python
   def test_security_profile_invalid_value_ignored():
       """Invalid security_profile value should be silently ignored."""
       ...
   ```

2. **AGENT-2**: In `test_agent_negative_paths.py`:
   ```python
   def test_recency_days_boundary_7_days():
       """Exactly 7-day boundary should trigger boost calculation."""
       ...
   ```

3. **AGENT-3**: In `test_agent_integration.py`:
   ```python
   @pytest.mark.asyncio
   async def test_memory_scoring_with_real_db_and_subprocess():
       """Memory scoring with real DB and subprocess instead of mocks."""
       ...
   ```

4. **AGENT-4**: In `test_agent_negative_paths.py`:
   ```python
   def test_force_overwrite_clobber_dont_elevate_read_tools():
       """force/overwrite/clobber should not elevate read-type tools."""
       ...
   ```

## Compatibility considerations

N/A — test-only change

## Security considerations

These changes improve reliability by documenting current behavior.

## Rollback considerations

- Simple revert: delete the test files

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_agent_negative_paths.py` | Characterization tests document current behavior | `uv run pytest -k "agent" -v` | All tests pass |
| `tests/integration/test_agent_integration.py` | Integration tests document current behavior | `uv run pytest -k "integration" -v` | All tests pass |

## Out of scope

- Changes beyond the four specific gaps listed above

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-130921_require.md
- Source plan: plans/20260726-172958_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/services/config_reload.py, scripts/agent/memory/scoring.py, scripts/agent/tool_policy.py
