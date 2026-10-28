# web_search import-time refusal claim contradicts `require_auth_token` at import

## Priority
Medium

## Summary
The docstring of `_build_security_posture()` in
`scripts/mcp_servers/web_search/web_search_server.py` states that the module has "no
import-time refusal for an empty token" and that an empty `auth_token` becomes visible
"as a warning rather than a failure." This directly contradicts `attach_auth_middleware(...)`
calling `require_auth_token(...)` at import time, which raises
`RuntimeError` on an empty token.

## Background
web_search loads its config via a module-level singleton (`_cfg = WebSearchConfig.load()`)
and builds its posture at import. It also wires auth middleware at import via
`attach_auth_middleware`, whose second argument is `require_auth_token(...)`. Other
servers (shell, git, github, file, mdq) refuse at import via a module-level
`if not <token>: raise` guard; web_search refuses via the middleware helper instead.

## Problem
Docstring:

> Unlike Shell, this module has no import-time refusal for an empty token, so the
> posture is where an empty auth_token first becomes visible, as a warning rather than
> a failure.

Actual code:

```python
attach_auth_middleware(
    cast(_FastAPIApp, app),
    require_auth_token("web-search-mcp", "MCP_WEB_SEARCH_AUTH_TOKEN", _cfg.auth_token),
)
```

`require_auth_token` validates the token at call time, i.e. at import. An empty token
therefore raises at import — exactly the "import-time refusal" the docstring denies.

## Reason for Change
A security-behavior claim in the docstring is the opposite of reality. Operators or
readers relying on the docstring would wrongly believe an empty token degrades to a
warning, which could lead to deploying the server with no auth.

## Implementation Intent
Rewrite the docstring to describe the true behavior: web_search refuses at import via
`require_auth_token` inside `attach_auth_middleware`, not via a module-level guard, and
an empty token is a failure, not a warning. Optionally add a short note distinguishing
the mechanism (middleware helper vs. shell-style guard) so the comparison to Shell is
accurate.

## Target Files or Areas
- `scripts/mcp_servers/web_search/web_search_server.py` (`_build_security_posture`
  docstring; import-time `attach_auth_middleware` wiring)

## Required Changes
- Correct the docstring to reflect that an empty `auth_token` raises at import.
- Preserve the accurate part of the comparison (mechanism differs from Shell) while
  fixing the false "no refusal / warning-only" claim.

## Constraints
- Do not change runtime auth behavior; this is a documentation correction only.
- Do not alter `require_auth_token` / `attach_auth_middleware` semantics.

## Acceptance Criteria
- The docstring no longer claims an empty token is a warning or that there is no
  import-time refusal.
- The docstring accurately describes the middleware-based import refusal.

## Testing Expectations
Documentation consistency check (no behavioral tests required). Confirm the described
behavior matches `require_auth_token` by reading the shared security module.

## Documentation Impact
This is a documentation correction. Ensure the docstring matches actual import-time
failure behavior.

## Out of Scope
Other servers' docstrings and the auth implementation itself.

## Dependencies
N/A: none

## Unresolved Questions
Whether the same class of doc/behavior mismatch exists in other servers' docstrings
(see report).

## AI Implementation Instruction
Fix only the `_build_security_posture` docstring to match the import-time refusal
performed by `require_auth_token`. Do not change any executable code.

## Traceability
- **Workflow phase**: `python-code-review`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261029-012525
- **Related target files**: `scripts/mcp_servers/web_search/web_search_server.py`
