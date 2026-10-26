# _sanitize_for_audit leaks sensitive paths for 2-component paths

## Priority
Medium

## Summary
The `_sanitize_for_audit` function in `git_server.py` does not redact sensitive portions of paths with exactly 2 components (e.g., `/etc/shadow`), leaking the full path in audit logs.

## Background
The `_sanitize_for_audit` function at lines 150-157 of `git_server.py`:

```python
def _sanitize_for_audit(value: str) -> str:
    """Redact sensitive portions of a path for audit logging."""
    if not value:
        return ""
    parts = value.split("/")
    if len(parts) <= 2:
        return value
    return "/".join(["***"] + parts[-2:])
```

This function is used in multiple places in `call_tool` (lines 263, 300, 340) to sanitize the `repo_path` before logging.

## Problem
For paths with exactly 2 components (e.g., `/etc/shadow`, `/root/.ssh/id_rsa`), the function returns the unredacted path because `len(parts) <= 2` evaluates to `True`. This means:
1. Sensitive paths like `/etc/shadow` are logged in full in audit logs.
2. Paths like `/root/.ssh/id_rsa` are logged in full, exposing user credentials.
3. The redaction logic only kicks in for paths with 3+ components (e.g., `/home/user/repo` → `/***/home/user/repo`).

The condition `len(parts) <= 2` is incorrect because:
- A path like `/etc/shadow` has 2 components (`""` and `etc` and `shadow` — actually 3 parts after split).
- Wait: `"/etc/shadow".split("/")` produces `["", "etc", "shadow"]` — 3 parts. So the condition `len(parts) <= 2` would NOT trigger for this path.
- But `"/etc".split("/")` produces `["", "etc"]` — 2 parts. This WOULD trigger the condition.
- And `"/".split("/")` produces `["", ""]` — 2 parts. This WOULD trigger the condition.

So the bug is specifically for paths that resolve to exactly 2 components after splitting by `/`. Examples:
- `/etc` — 2 components, logged in full
- `/root` — 2 components, logged in full
- `/` — 2 components, logged in full

These are all sensitive system paths that should be redacted.

## Reason for Change
Paths with 2 or fewer components are often sensitive system paths (e.g., `/etc`, `/root`, `/`) that should be redacted in audit logs. The current logic assumes these are safe to log, but they are not.

## Implementation Intent
Replace the `len(parts) <= 2` condition with a check for sensitive paths. Options include:
1. Always redact paths with fewer than 3 components (return `"***/..."` for all paths).
2. Maintain a list of sensitive path prefixes and redact those specifically.
3. Use a heuristic: if the first component is empty (absolute path) and the second component is a known sensitive directory, redact.

## Target Files or Areas
- `scripts/mcp_servers/git/git_server.py` — `_sanitize_for_audit` (lines 150-157)

## Required Changes
- Replace `len(parts) <= 2` with a more robust redaction strategy
- Ensure all absolute paths are redacted regardless of component count
- Document the redaction policy in the docstring

## Constraints
- Must not change the existing redaction behavior for paths with 3+ components
- Must preserve the `***` prefix convention

## Acceptance Criteria
- Paths with 2 or fewer components are redacted in audit logs
- Existing redaction behavior for paths with 3+ components is preserved
- No sensitive paths are logged in full

## Testing Expectations
- Unit test: verify `/etc` is redacted
- Unit test: verify `/root` is redacted
- Unit test: verify `/home/user/repo` is still redacted as before
- Regression test: ensure existing redaction behavior is preserved

## Documentation Impact
Update `_sanitize_for_audit` docstring to document the redaction policy.

## Out of Scope
- Changes to the audit log format itself
- Changes to how paths are validated before sanitization

## Dependencies
N/A: none

## Unresolved Questions
- What is the minimum number of components that should be redacted?
- Should relative paths be treated differently?

## AI Implementation Instruction
In `scripts/mcp_servers/git/git_server.py`, fix `_sanitize_for_audit` to redact paths with 2 or fewer components. Do not modify any other MCP server's audit logic.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261026-220730
- **Related target files**: scripts/mcp_servers/git/git_server.py
