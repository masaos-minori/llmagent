# secrets_masker does not mask bare-password URL userinfo (`scheme://token@host`)

## Priority
High

## Summary
`agent/secrets_masker.py` masks userinfo of the form `scheme://user:password@host` but leaves a bare-password URL `scheme://token@host` (userinfo containing only a credential, no `username:` prefix) unmasked. Secrets embedded this way in URLs can leak into MCP subprocess failure reports and logs. Extend the masking patterns so bare-password userinfo is masked like the colon-separated form, without changing the `_mask_secrets(text: str) -> str` signature or any call site.

## Background
`_mask_secrets` centralizes secret redaction for the agent's log output and MCP subprocess failure reports. Per `docs/23_agent/agent_10_01_...startup-and-health.md` ("Secret Masking in MCP Subprocess Failure Reports"), masking covers three case-insensitive shapes: `key=value` for keys like `password`, `api_key`, `secret`, `token`; `Authorization:` header lines; and standalone `Bearer` tokens. `_mask_secrets` is also used in `http_lifecycle.py`, `http_lifecycle_errors.py`, `shared/retry_helper.py`, and `startup_mcp_starter.py`.

Two prior items hardened this module:
- `issues/done/20261017-123248_mask01_extend-secret-masking-nonjson-and-header-formats.md` — broadened coverage to JSON values, inline tokens, base64 blobs, and non-JSON/header formats.
- `plans/done/20261101-140116_secmask001_secrets-masker-leaks-unmasked-value.md` / follow-up — added colon-form `key: value` masking for the existing key names.

Neither addressed URL userinfo carrying a bare credential.

## Problem
URLs routinely embed credentials in the authority component. Two shapes exist:
- `https://user:password@host/path` — username + password.
- `https://token@host/path` — a single credential with no username (common for API tokens, OAuth bearer-in-URL, service URLs).

Empirical verification against the current source confirms the asymmetry:

| Input | Result |
|---|---|
| `endpoint=https://user:supersecret@api.example.com/path` | masked (`user:***MASKED***@...`) |
| `endpoint=https://MYBEARTOKENEXAMPLETOKEN@api.example.com/path` | **NOT masked** |
| `raw=https://RAWJWTTOKENEXAMPLE...@svc.io/x` | **NOT masked** |

The existing pattern matches userinfo only when a `username:` segment precedes the credential. A bare credential before `@` is not matched, so the raw token is written through unchanged. Because these strings flow through `_mask_secrets` into subprocess failure reports and logs, a bare-password URL leaks the secret verbatim.

## Reason for Change
The residual gap is a direct security regression surface: once an operator enables any masking, URLs with bare credentials still bypass it. The fix closes the gap without widening the public contract of `_mask_secrets`.

## Implementation Intent
Add a focused pattern (or extend the existing userinfo handling) that matches an optional `username:` prefix followed by a credential up to the terminating `@` inside a scheme-prefixed URL, e.g. `(https?|ftp|...)://(?:[^/@]+:)?([^/@]+)@`. Keep it anchored to a URL scheme so ordinary `word@word` text (e.g. email addresses, plain identifiers) is not over-matched. Preserve the existing behavior for the colon-separated form and the already-masked cases. Do not change the function signature or any call site.

## Target Files or Areas
- `scripts/agent/secrets_masker.py`
- `scripts/agent/tests/test_secrets_masker.py` (or the repo's masker test file)
- Operator-facing docs describing the masked shapes (`docs/23_agent/...startup-and-health.md`)

## Required Changes
- Add masking for bare-password URL userinfo (`scheme://token@host`) and confirm the colon-separated form (`scheme://user:token@host`) remains masked.
- Constrain the new pattern to scheme-prefixed URLs to avoid false positives on emails/plain identifiers.
- Add regression tests covering: bare-password URL, colon-separated URL, and a no-false-positive email/identifier case.
- Update the documentation section listing the masked shapes to mention URL userinfo.

## Constraints
- Must not change the `_mask_secrets(text: str) -> str` signature or any call site.
- Must not regress the three existing shapes (`key=value`, `Authorization:`, `Bearer`).
- Must avoid false positives on common non-secret `x@y` text (email addresses, usernames).
- Pattern additions must remain case-insensitive and consistent with the existing composite-name alternation.

## Acceptance Criteria
- `https://token@host/path` (bare credential) is masked.
- `https://user:token@host/path` (colon form) is still masked.
- Email addresses and plain `word@word` identifiers are not masked (no false positive).
- Existing `key=value`, `Authorization:`, and `Bearer` cases still pass their tests.
- No call site or signature of `_mask_secrets` changes.

## Testing Expectations
Unit tests for the new bare-password URL form, the preserved colon-separated form, a no-false-positive email case, and a full regression sweep of the existing shapes. Confirm the pinned pattern-count assertion (if any) is updated.

## Documentation Impact
Update the operator-facing description of the masker's masked shapes to include URL userinfo (both bare-password and colon-separated forms), noting the constraint that it applies only to scheme-prefixed URLs.

## Out of Scope
- Any change to the masking call sites or their callers.
- Redacting other URL components (host, path, query) beyond the credential.
- Adding new key names to the keyed alternation.

## Dependencies
N/A: none

## Unresolved Questions
- Should the pattern also cover non-HTTP schemes (`ftp://`, custom schemes)? Needs confirmation on intended scope.
- Does the masking need to handle credentials that themselves contain `@` (rare, percent-encoded)? Needs confirmation.

## AI Implementation Instruction
Do not change `_mask_secrets`'s signature or any call site. Add a scheme-anchored pattern for optional-username userinfo and keep the colon form working. Guard against email/false positives. Update the pinned pattern-count test if one exists.

## Traceability
- **Workflow phase**: python-code-review
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261107-191833
- **Related target files**: scripts/agent/secrets_masker.py