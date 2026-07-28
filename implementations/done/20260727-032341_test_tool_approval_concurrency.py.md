## Goal

Add optional concurrency test for the approval flow to verify no race conditions occur under rapid successive prompts.

## Scope

**In-Scope:**
- Create a test that patches `asyncio.to_thread` to simulate concurrent input
- Verify approval decisions are processed correctly regardless of timing

**Out-of-Scope:**
- Fixing any actual race conditions found during testing (would be a separate issue)
- Any non-concurrency-related changes to the approval flow

## Assumptions

1. The approval flow uses `asyncio.to_thread(input, ...)` which is a standard Python pattern
2. The REPL's single-threaded event loop makes actual race conditions unlikely
3. This is optional — only implement if time permits

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether the approval flow has any shared mutable state that could cause race conditions | Review `_prompt_user_approval` and related code | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `tests/test_tool_approval_concurrency.py`
  - `scripts/agent/tool_approval.py` — reference for understanding approval flow

- **Blast Radius:**
  - Very low churn — new test file only
  - Very low risk since change is test-only

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of `tool_approval.py`:
```python
# Current approval flow:
async def _prompt_user_approval(risk: RiskLevel) -> bool:
    """Prompt the user interactively; HIGH requires full word 'yes'."""
    if risk == RiskLevel.HIGH:
        answer = (await asyncio.to_thread(input, "  Execute? [yes/no]: ")).strip().lower()
        return answer == "yes"
    answer = (await asyncio.to_thread(input, "  Execute? [y/N]: ")).strip().lower()
    return answer == "y"
```

Test structure:
```python
import asyncio
from unittest.mock import AsyncMock, patch
from agent.tool_approval import _prompt_user_approval, RiskLevel

@pytest.mark.asyncio
async def test_rapid_successive_approvals_no_race():
    # Patch asyncio.to_thread to simulate concurrent input
    # Verify each approval decision is processed independently
    pass

@pytest.mark.asyncio
async def test_rapid_mixed_approvals_no_race():
    # Patch asyncio.to_thread with mixed yes/no responses
    # Verify each decision is correct regardless of timing
    pass
```

## Implementation

### Target file
`tests/test_tool_approval_concurrency.py` (new file)

### Procedure
1. Create `tests/test_tool_approval_concurrency.py`
2. Add imports for pytest, asyncio, unittest.mock, _prompt_user_approval, RiskLevel
3. Implement `test_rapid_successive_approvals_no_race` — patch `asyncio.to_thread` to simulate concurrent input, verify approval decisions are processed correctly
4. Implement `test_rapid_mixed_approvals_no_race` — patch `asyncio.to_thread` with mixed yes/no responses, verify each decision is correct
5. Save the file

### Method
Create new test file with patched `asyncio.to_thread` to simulate concurrency scenarios.

### Details
- Use `@pytest.mark.asyncio` decorator for async tests
- Use `patch("agent.tool_approval.asyncio.to_thread")` to mock thread execution
- Return pre-determined responses from the mock to simulate concurrent input
- For HIGH risk level: use "yes"/"no" responses
- For LOW/MEDIUM risk level: use "y"/"n" responses
- Verify each approval decision is processed independently without interference

## Compatibility considerations

N/A — new test file has no runtime effect

## Security considerations

N/A

## Rollback considerations

- Simple revert: delete the new test file

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `tests/test_tool_approval_concurrency.py` | Concurrency simulation via asyncio patching | `uv run pytest -k "approval" -v` | Test passes |

## Out of scope

- Fixing any actual race conditions found during testing (would be a separate issue)
- Any non-concurrency-related changes to the approval flow

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-165155_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-032341
- Related target files: scripts/agent/tool_approval.py, scripts/agent/startup.py
