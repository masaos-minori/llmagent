# HttpTransport silently sends unauthenticated calls when constructed with cfg=None

## Priority
Medium

## Summary
`HttpTransport.__init__` sets `self._auth_token = cfg.auth_token if cfg is not None else ""`. When a transport is built with `cfg=None`, authentication is disabled with no warning, and `call()` omits the `Authorization` header even though the target server requires a bearer token. Make missing configuration an explicit, loud condition rather than a silent auth-off switch.

## Background
`HttpTransport` (scripts/shared/http_transport.py) POSTs to `/v1/call_tool`. Auth is applied in `call()` (lines 111-115):
```python
headers: dict[str, str] = {}
if self._auth_token:
    headers["Authorization"] = f"Bearer {self._auth_token}"
```
The token is derived in `__init__` (lines 43-46):
```python
self._auth_token: str = cfg.auth_token if cfg is not None else ""
if self._auth_token:
    register_secret(self._auth_token)
```
Currently `ToolTransportInvoker.__init__` always passes a real `cfg` (scripts/shared/tool_transport_invoker.py:61), so production transports carry their token. The `cfg=None` path is a latent footgun for any other caller or future refactor.

## Problem
If any code path constructs `HttpTransport(http, url, key, cfg=None, ...)`, the resulting transport sends requests with **no** `Authorization` header, regardless of what the server requires. This is silent: no exception, no log. Combined with the fact that scripts/shared/mcp_config.py enforces a non-empty `auth_token` for all non-disabled servers, a mis-constructed transport would leak unauthenticated access to an authenticated endpoint.

## Reason for Change
Silently disabling authentication based on a missing config object is a classic fail-open pattern. Authentication decisions should never be implicit; a missing config should surface loudly so it cannot quietly bypass auth.

## Implementation Intent
Change the `cfg=None` case so it does not silently disable auth. Options to consider: raise at construction when the caller clearly intends an authenticated transport but supplies no config, or require an explicit `auth_token`/`authenticated` flag. Prefer surfacing the misconfiguration over defaulting to no-auth. Do not change the happy path where `cfg` is provided.

## Target Files or Areas
- scripts/shared/http_transport.py (`HttpTransport.__init__`, `call`)
- Callers of `HttpTransport(...)` (scripts/shared/tool_transport_invoker.py and any others)
- Tests for HttpTransport

## Required Changes
- Remove the implicit `cfg=None → auth off` behavior. Require either a non-empty `auth_token` or an explicit opt-out for unauthenticated transports.
- Audit all `HttpTransport(...)` construction sites to ensure each carries the config/token it needs.
- Add a test asserting a transport built without credentials does not emit a valid auth path unless explicitly allowed.

## Constraints
- Must not break the existing `ToolTransportInvoker` path, which always passes `cfg`.
- Backward-compatible callers that intentionally build unauthenticated transports must be made explicit.

## Acceptance Criteria
- Constructing `HttpTransport` without a usable token neither silently succeeds nor sends unauthenticated calls without an explicit opt-in.
- Existing authenticated transports are unaffected.

## Testing Expectations
- Unit tests for `HttpTransport` covering the no-config case and the authenticated case.
- ruff + mypy + bandit on the touched file.

## Documentation Impact
Note the contract that `HttpTransport` requires explicit credentials and never defaults to anonymous.

## Out of Scope
- Changing how `ToolTransportInvoker` builds transports (beyond ensuring it still passes cfg).
- Altering retry/backoff or response parsing.

## Dependencies
N/A: none

## Unresolved Questions
- Should the fix raise, or require an explicit `authenticated: bool` constructor flag? Decide based on caller audit.

## AI Implementation Instruction
Edit only scripts/shared/http_transport.py to remove the silent `cfg=None → no auth` default, making credential requirements explicit. Audit `HttpTransport(...)` call sites first. Do not touch retry logic or response parsing. Add regression tests.

## Traceability
- **Workflow phase**: python-code-review → issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-065813
- **Related target files**: scripts/shared/http_transport.py, scripts/shared/tool_transport_invoker.py
