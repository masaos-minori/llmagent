## Goal

Apply message schema validation on all conversation history insertions to prevent potential manipulation through unvalidated message insertion.

## Scope

**In-Scope:**
- Add `validate_message()` wrapper around all `ctx.conv.history.append()` calls
- Reject invalid messages with warning log and skip insertion

**Out-of-Scope:**
- Changes to `validate_message()` itself beyond what's needed for integration
- Sanitization logic — invalid messages are simply rejected

## Assumptions

1. Rejection (skip) is preferred over sanitization for invalid messages
2. The validation should be applied consistently across all insertion points

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether any existing tests reference specific message structures that would fail validation | Search for `conv.history.append` in tests | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - `scripts/agent/orchestrator.py` — wrap 1 insert call
  - `scripts/agent/services/conversation_service.py` — wrap 1 insert call

- **Blast Radius:**
  - Medium — 2 insert calls across 2 files need wrapping
  - Risk of breaking valid message structures during validation

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the codebase:
```python
# Current (no validation before insert):
ctx.conv.history.insert(0, {"role": "system", "content": ctx.conv.system_prompt_content})

# Proposed (with validation):
msg = {"role": "system", "content": ctx.conv.system_prompt_content}
result = validate_message(msg)
if not result.success:
    logger.warning("Skipping invalid system prompt: %s", result.reason)
else:
    ctx.conv.history.insert(0, msg)
```

Note: Some files already have validation (`orchestrator.py:_sync_system_prompt()` at line 602 validates before insert). The remaining unprotected insert is in `conversation_service.py:60`.

## Implementation

### Target files
- `scripts/agent/services/conversation_service.py`

### Procedure
1. Open `scripts/agent/services/conversation_service.py`
2. Ensure `from agent.message_schema import validate_message` is imported
3. Locate lines 60-62: `ctx.conv.history.insert(0, {"role": "system", ...})`
4. Replace with validated version using `validate_message()` before insert
5. Save the file

### Method
Add `validate_message()` call before each `ctx.conv.history.insert()` or `ctx.conv.history.append()` call.

### Details
1. In `scripts/agent/services/conversation_service.py`, add import:
   ```python
   from agent.message_schema import validate_message
   ```
2. Replace lines 60-62:
   ```python
   # Before:
   ctx.conv.history.insert(
       0, {"role": "system", "content": ctx.conv.system_prompt_content}
   )
   
   # After:
   msg = {"role": "system", "content": ctx.conv.system_prompt_content}
   result = validate_message(msg)
   if not result.success:
       logger.warning("Skipping invalid system prompt: %s", result.reason)
   else:
       ctx.conv.history.insert(0, msg)
   ```

## Compatibility considerations

N/A — validation prevents invalid messages from entering history

## Security considerations

This change improves security by ensuring all history insertions go through schema validation.

## Rollback considerations

- Simple revert: restore original insert without validation from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| All affected files | Validation rejects invalid messages | Manual verification + existing tests | No regressions |

## Out of scope

- Changes to `validate_message()` itself
- Sanitization logic — invalid messages are simply rejected

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/20260726-124945_require.md
- Source plan: plans/20260726-170841_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-034245
- Related target files: scripts/agent/orchestrator.py, scripts/agent/message_schema.py
