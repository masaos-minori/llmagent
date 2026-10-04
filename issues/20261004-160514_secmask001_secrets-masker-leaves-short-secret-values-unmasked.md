# Secrets masker leaves short secret values unmasked

## Priority
High

## Summary
`agent.secrets_masker._mask_secrets()` is meant to mask secret values in text that is logged, but it keeps the first 10 characters of every match and masks only the rest. A short `key=value` match is therefore not masked at all, and longer matches leak the leading part of the secret value.

## Background
`_mask_secrets()` is used when the Agent reports MCP subprocess startup failures (stderr tail) and when it logs a failed first startup attempt for an MCP subprocess. It was found while documenting the module; it had no documentation and no tests.

## Problem
- The replacement keeps `match[:10]` and appends `***MASKED***`. The match includes the key name and the `=` sign, so the number of value characters that survive depends on the key length.
- Observed with the current code: `password=hunter2` becomes `password=h***MASKED***` (one value character leaks), `api_key=sk-1234567890abcdef` becomes `api_key=sk***MASKED***`, `GITHUB_TOKEN=ghp_abcdef123` becomes `GITHUB_TOKEN=ghp_***MASKED***`, and `token=abc` and `secret=x` are returned with the full value visible (the match is shorter than 10 characters).
- Values that are not written as `key=value` (for example an `Authorization: Bearer ...` header) are not matched at all.

## Reason for Change
Secret values must not appear in logs or error reports. A masker that leaks short values and the start of long ones gives a false sense of protection in a security-sensitive path.

## Implementation Intent
Mask the whole value of a matched secret and keep only the key name, so the output no longer depends on the length of the match. Decide explicitly which additional forms (for example bearer tokens) are in scope. Keep the helper's public behavior (replace secrets in a string) and its call sites unchanged.

## Target Files or Areas
- scripts/agent/secrets_masker.py
- tests for the masker (none exist today)
- docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md (documents the current behavior and this limitation)

## Required Changes
- Change the replacement so the secret value is fully masked regardless of its length.
- Decide and document whether `Authorization`/bearer values are masked.
- Add unit tests covering short values, long values, mixed case keys and text with no secrets.

## Constraints
- The masker must not raise on arbitrary text, including empty strings.
- It is applied to log output; it must stay cheap.

## Acceptance Criteria
- For each key name the masker supports, no character of the secret value appears in the output.
- Text without secrets is returned unchanged.
- Unit tests cover the cases above and pass.

## Testing Expectations
- New unit tests for `_mask_secrets()`.
- `ruff`, `mypy` and the existing agent tests pass.

## Documentation Impact
Update the secret-masking description in the startup and health document: remove the limitation note once fixed and state the final set of masked forms.

## Out of Scope
- Changing which call sites apply the masker.
- Introducing a general log-redaction framework.

## Dependencies
N/A: none

## Unresolved Questions
- Should bearer/authorization header values be masked as well?
- Are there other places that log subprocess output without passing it through the masker?

## AI Implementation Instruction
Keep the change minimal and limited to the masker and its tests. Do not change call sites. Stop and report if the intended masked forms are unclear.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261004-160514
- **Related target files**: scripts/agent/secrets_masker.py, docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md
