# Unify cicd-mcp workflow_allowlist to file-name form

## Priority
Medium

## Summary
Make the `workflow_allowlist` value format match what requests carry (a workflow file name such as `ci.yml`) so valid calls are no longer rejected, and reject path separators before matching.

## Background
Source: local investigation notes (memo1.md, ISSUE-11), from MCP-003.

## Problem
- The configured value is a full-path form (Explicit in code — `config/cicd_mcp_server.toml` sets a path-style value), while its own comment and the requests use file names (e.g. `ci.yml`); matching therefore fails and valid calls are rejected.

## Reason for Change
- The feature is unusable. It fails on the safe side, but users who loosen the allow-list as a workaround make it dangerous.

## Implementation Intent
- Align the config, comments, and docs with the file-name form that the tool schema and tests assume.

## Target Files or Areas
- `config/cicd_mcp_server.toml`, `scripts/mcp_servers/cicd/cicd_service_guards.py`, mcp_05_01

## Required Changes
- Align the configured value, the config comment, and the mcp_05_01 example to the file-name form.
- Before matching, reject values containing a path separator.

## Constraints
- Keep fail-closed behavior; do not widen the allow-list.

## Acceptance Criteria
- A call with `ci.yml` is allowed and `../ci.yml` is rejected (tests).

## Testing Expectations
- Unit tests for the guard; ruff, mypy, targeted pytest.

## Documentation Impact
Update mcp_05_01 examples; remove Known Issue MCP-003 from the ledger when done.

## Out of Scope
- Other cicd guards; repository allow-list.

## Dependencies
N/A: none

## Unresolved Questions
- The actual matching method in `cicd_service_guards.py` (not read).

## AI Implementation Instruction
Read the guard implementation first. Change only the allow-list format and the separator rejection.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261007-154048
- **Related target files**: `config/cicd_mcp_server.toml`, `scripts/mcp_servers/cicd/cicd_service_guards.py`
