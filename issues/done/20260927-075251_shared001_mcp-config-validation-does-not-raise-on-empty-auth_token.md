# MCP config validation does not raise on empty auth_token

## Priority
Medium

## Summary
`tests/shared/test_mcp_config_validation.py::test_auth_token_empty_string_raises` expects a `ValueError` when an MCP server config's `auth_token` is an empty string, but no exception is raised.

## Background
Discovered during the post-docs-reorg full-suite validation sweep (`implementations/20260925-111411_04_tests___full_suite_.md`), which surfaced 97 failing tests; this is one root-cause cluster from that investigation.

## Problem
`Failed: DID NOT RAISE <class 'ValueError'>` — the validation path for MCP server config no longer rejects an empty-string `auth_token` where it previously did (or was intended to).

## Reason for Change
An empty `auth_token` silently accepted is a security/config-validation gap: a misconfigured server could run with no effective authentication token instead of failing fast at config-load time.

## Implementation Intent
Read the current MCP config validation logic for `auth_token` to determine whether the empty-string check was removed, weakened (e.g. changed to only check `None` rather than falsy/empty), or moved to a different validation path not exercised by this test.

## Target Files or Areas
- Shared MCP config validation module (confirm exact path, likely `scripts/shared/mcp_config.py` or similar)
- `tests/shared/test_mcp_config_validation.py`

## Required Changes
- Restore/add an explicit check rejecting an empty-string `auth_token` with `ValueError`, consistent with whatever other required-field validations in the same config already do.

## Constraints
Do not change validation for a `None` (unset) `auth_token` if that has different, intentional handling (e.g. optional-auth servers) — scope the fix to the empty-string case specifically, per the failing test.

## Acceptance Criteria
- The listed test passes.
- Existing passing tests for valid/`None` `auth_token` handling remain passing (no regression).

## Testing Expectations
Run `tests/shared/test_mcp_config_validation.py`; run full suite once after the fix.

## Documentation Impact
N/A: unless the config validation contract is documented elsewhere and needs updating (Needs confirmation).

## Out of Scope
Other unrelated failing tests from the same full-suite run.

## Dependencies
N/A: none

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Read the current validation function's full logic (not just guess based on the test name) before adding a check — confirm whether a similar check already exists for a different field so the fix follows the same pattern/error message style.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: implementations/20260925-111411_04_tests___full_suite_.md
- **Generated at**: 20260927-075330
- **Related target files**: tests/shared/test_mcp_config_validation.py
