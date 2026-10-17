# Extend secret masking beyond key=value and header shapes

## Priority
High

## Summary
`agent/secrets_masker.py` masks only three secret shapes
(`key=value`, `Authorization:` header lines, standalone `Bearer` tokens). Secrets
in other common formats — JSON values, inline tokens, base64 blobs — are not
masked and can leak into subprocess failure reports and logs. Broaden masking
coverage while preserving the existing patterns.

## Background
When an MCP subprocess fails to start, the tail of its stderr is included in the
startup failure report and logged. Both pass through `agent/secrets_masker.py`
`_mask_secrets()`. Per `docs/23_agent/agent_10_01_...startup-and-health.md`
("Secret Masking in MCP Subprocess Failure Reports"), masking covers three
case-insensitive shapes: `key=value` for key names like `password`, `api_key`,
`secret`, `token`; `Authorization:` header lines; and standalone `Bearer` tokens.
`_mask_secrets` is also used in `http_lifecycle.py`, `http_lifecycle_errors.py`,
`shared/retry_helper.py`, and `startup_mcp_starter.py`.

## Problem
The regex set `SECRET_PATTERNS` matches only:
- `key = value` for a fixed list of key names,
- `Authorization: <scheme> <token>`,
- `Bearer <token>`.

It does NOT mask:
- JSON-formatted secrets such as `"token": "abc123"` or `"api_key":"xyz"` (the
  separator is `:`, not `=`),
- bare/inline tokens with no recognizable key name,
- base64 or hex API keys,
- secrets embedded in URLs (`?api_key=...` is partially covered but query strings
  without a known key name are not),
- non-ASCII or multi-line secret values.

A failed MCP subprocess that prints such a secret will leak it into the startup
failure report and logs.

## Reason for Change
Secret masking is a security control whose effectiveness is only as strong as its
coverage. The current regex surface misses common modern secret encodings, so the
control gives a false sense of protection. This is security-sensitive: leaked
credentials in logs are a direct exposure.

## Implementation Intent
Add regex patterns (or a small extension) to `SECRET_PATTERNS` for the most
common unmasked formats — at minimum JSON object values for known secret key
names (`"token"`, `"api_key"`, `"password"`, ...), both with `:` and `,`
separators. Keep the existing three patterns intact. Do not introduce over-broad
patterns that mask legitimate non-secret output (e.g. generic words). Prefer
narrow, high-confidence additions and guard against false positives.

## Target Files or Areas
- `scripts/agent/secrets_masker.py` (`SECRET_PATTERNS`, `_mask_secrets`)

## Required Changes
- Add coverage for JSON-style secret values (`"key": "value"`) for known secret
  key names.
- Consider bare high-entropy tokens only if a low-false-positive heuristic exists;
  otherwise defer and record as an open question.
- Keep the three existing patterns unchanged.

## Constraints
- Do not weaken or remove any existing pattern.
- Avoid false positives that would corrupt legitimate log content (test against
  sample non-secret stderr).
- Masking must remain reversible-safe: never unmask; only redact.

## Acceptance Criteria
- A JSON secret such as `{"token": "abc123"}` is masked by `_mask_secrets`.
- The three original patterns still mask their inputs (regression).
- A sample non-secret stderr string is left unmodified (no false positives).

## Testing Expectations
- Unit tests for `_mask_secrets` covering: existing 3 shapes (regression), JSON
  values, and a non-secret sample asserting no change.
- Confirm all call sites (`http_lifecycle.py`, `http_lifecycle_errors.py`,
  `shared/retry_helper.py`, `startup_mcp_starter.py`) still import correctly.

## Documentation Impact
Update the "Secret Masking in MCP Subprocess Failure Reports" section in
`docs/23_agent/agent_10_01_...startup-and-health.md` to list newly covered
formats, and mark the Known Limitations bullet accordingly.

## Out of Scope
- Replacing the regex approach with a structured secret detector (out of scope;
  note as a possible follow-up).
- Changing call sites or their masking invocation.

## Dependencies
- N/A: none

## Unresolved Questions
- Whether to mask bare high-entropy tokens without a key name; risk of false
  positives vs. coverage gain.
- Whether additional secret key names should be added to the recognized list and
  who owns maintaining it.

## AI Implementation Instruction
Only edit `scripts/agent/secrets_masker.py`. Add narrow patterns for JSON-style
secret values for known key names; keep the existing three patterns verbatim. Do
NOT add broad bare-token matching without a low-false-positive heuristic. Add unit
tests for the new patterns and a no-op test on non-secret input. Do not touch
call sites.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261017-123248
- **Related target files**: `scripts/agent/secrets_masker.py`
