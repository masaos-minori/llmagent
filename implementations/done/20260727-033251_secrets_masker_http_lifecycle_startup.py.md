## Goal

Add secret masking to subprocess error logs to prevent potential secret leakage through MCP server stderr output.

## Scope

**In-Scope:**
- Create `_mask_secrets(text: str) -> str` function with regex patterns for common secret types
- Apply `_mask_secrets()` to stderr content before logging in `scripts/agent/http_lifecycle.py:274-279`
- Apply `_mask_secrets()` to error log output in `scripts/agent/startup.py:156-166`

**Out-of-Scope:**
- Changes to other log output beyond subprocess stderr
- Adding new secret patterns beyond those specified

## Assumptions

1. The secret patterns specified in the requirement are sufficient for initial implementation
2. Masking should preserve enough of the original text for debugging purposes

## Unknowns

| ID | Unknown Description | Resolution Path | Blocking? (True/False) |
|---|---|---|---|
| UNK-01 | Whether existing `filter_pii()` in snippet_filter.py can be reused for secret masking | Compare PII_PATTERNS vs SECRET_PATTERNS | False |

## Affected Areas & Tool Evidence

- **Affected Files:**
  - New file: `scripts/agent/secrets_masker.py` — `_mask_secrets()` function
  - `scripts/agent/http_lifecycle.py` — apply masking to stderr log
  - `scripts/agent/startup.py` — apply masking to error log

- **Blast Radius:**
  - Very low churn — one new module plus two log line changes
  - No behavioral change for normal operation

- **Deploy Impact:**
  - Existing — no deploy.sh changes needed

## Design

Based on inspection of the affected files:
```python
# Current http_lifecycle.py:
logger.error(
    "Lifecycle: %r exited early; stderr (%s chars): %s",
    server_key,
    len(stderr_full),
    stderr_full[:500],
)

# Proposed http_lifecycle.py:
from agent.secrets_masker import _mask_secrets
logger.error(
    "Lifecycle: %r exited early; stderr (%s chars): %s",
    server_key,
    len(stderr_full),
    _mask_secrets(stderr_full[:500]),
)

# Current startup.py:
msg = f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start: {e}"
logger.error(msg)

# Proposed startup.py:
masked_msg = _mask_secrets(f"{OutputTag.FATAL} MCP subprocess {key!r} failed to start: {e}")
logger.error(masked_msg)
```

Secret masker design:
```python
import re

SECRET_PATTERNS = [
    re.compile(r"(?i)(password|passwd|pwd)\s*=\s*\S+"),
    re.compile(r"(?i)(api[_-]?key|apikey)\s*=\s*\S+"),
    re.compile(r"(?i)(secret|token)\s*=\s*\S+"),
]

def _mask_secrets(text: str) -> str:
    """Mask sensitive values in text using regex patterns."""
    masked = text
    for pattern in SECRET_PATTERNS:
        masked = pattern.sub(lambda m: m.group()[:10] + "***MASKED***", masked)
    return masked
```

## Implementation

### Target files
- `scripts/agent/secrets_masker.py` (new file)
- `scripts/agent/http_lifecycle.py`
- `scripts/agent/startup.py`

### Procedure
1. Create `scripts/agent/secrets_masker.py`
2. Add `SECRET_PATTERNS` list with regex patterns for common secret types
3. Add `_mask_secrets(text: str) -> str` function
4. Save the file
5. Open `scripts/agent/http_lifecycle.py`
6. Add `from agent.secrets_masker import _mask_secrets` to imports
7. Replace `stderr_full[:500]` with `_mask_secrets(stderr_full[:500])` on line 278
8. Save the file
9. Open `scripts/agent/startup.py`
10. Add `from agent.secrets_masker import _mask_secrets` to imports
11. Apply `_mask_secrets()` to error log messages on lines 157 and 159
12. Save the file

### Method
Create new secrets masker module and apply it to stderr/error log outputs.

### Details
- `secrets_masker.py`: Create new module with `SECRET_PATTERNS` and `_mask_secrets()` function
- `http_lifecycle.py:278`: `stderr_full[:500]` → `_mask_secrets(stderr_full[:500])`
- `startup.py:157`: `logger.error(msg)` → `logger.error(_mask_secrets(msg))`
- `startup.py:159`: Apply `_mask_secrets()` to the formatted message string

## Compatibility considerations

N/A — masking has no runtime effect unless secrets are present in stderr

## Security considerations

N/A — this change improves security posture

## Rollback considerations

- Simple revert: remove the secrets_masker module and restore original log statements from git history

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `scripts/agent/secrets_masker.py` | Verify patterns match and mask correctly | Manual verification + unit test | Patterns work as expected |
| `scripts/agent/http_lifecycle.py` | Stderr logged without secrets | Manual verification | Secrets masked in logs |

## Out of scope

- Changes to other log output beyond subprocess stderr
- Adding new secret patterns beyond those specified

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260726-165841_plan.md
- Source implementation procedure: N/A
- Generated at: 20260727-033251
- Related target files: scripts/agent/http_lifecycle.py, scripts/agent/startup.py
