# Define and enforce Git remote authorization and repository-level concurrency control

## Priority
Medium

## Summary
Authorize a resolved remote identity for pull/push and preserve validated repository
assumptions throughout each write operation, serializing writes per canonical repository while
allowing safe independence between different repositories.

## Background
No existing issue was found covering remote-identity authorization or Git MCP write
concurrency. This is a new gap, not an overlap with prior Git MCP work.

## Problem
Pull and push safety depends on both the repository state and the selected remote. A remote
name can point to a changed or unauthorized URL, and concurrent requests can invalidate the
state captured during authorization before execution begins.

## Reason for Change
These concerns should be implemented together because the resolved remote identity and
repository lock must remain stable across authorization, execution, and audit.

## Implementation Intent
Define whether remote authorization is based on remote name, normalized URL, or both; add
configuration for allowed remote identities if the current policy does not define one;
normalize and validate remote URLs while redacting embedded credentials; reject unknown,
missing, changed, or unauthorized remotes. Serialize Git MCP write operations by canonical
repository path; capture the HEAD identity immediately before mutation and reject execution if
it differs from the authorized state; document the limitation that external Git processes may
not honor the MCP lock. Include the resolved remote identity in the audit record without
secrets.

## Target Files or Areas
- `scripts/mcp_servers/git/git_models.py`
- `scripts/mcp_servers/git/repository_state.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/git_server.py`
- `scripts/mcp_servers/git/format_output.py`
- `config/git_mcp_server.toml`
- `tests/test_git_security_compliance.py`
- `tests/test_git_concurrency.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Define whether remote authorization is based on remote name, normalized URL, or both.
- Add configuration for allowed remote identities if the current policy does not define one.
- Normalize and validate remote URLs while redacting embedded credentials.
- Reject unknown, missing, changed, or unauthorized remotes.
- Serialize Git MCP write operations by canonical repository path.
- Capture the HEAD identity immediately before mutation and reject execution if it differs from the authorized state.
- Document the limitation that external Git processes may not honor the MCP lock.
- Include the resolved remote identity in the audit record without secrets.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior.
- Do not introduce a second authorization or dispatch path.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- Pull and push cannot target an unauthorized remote.
- A permitted remote alias cannot be redirected to an unauthorized URL without detection.
- Credentials embedded in remote URLs are not logged.
- Concurrent writes to the same repository are serialized.
- Independent repositories are not unnecessarily serialized.
- A repository state change between authorization and execution invalidates the request.
- Concurrency and remote-authorization tests cover pull and push.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `docs/04_mcp_04_05_git.md`'s remote-authorization and concurrency description once
implementation and tests establish the current behavior; document the external-process lock
limitation explicitly.

## Out of Scope
- Protected-branch/ref authorization content itself (`gitauth`).
- The write-protection pipeline's stage ordering (`gitpipeline`).
- Repository-path containment and audit hardening (`gitpathaudit`).

## Dependencies
Should consume `gitauth`'s resolved-target model for pull/push rather than defining a second,
separate remote-resolution mechanism.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, confirm current remote-handling code and whether any allowed-remote
configuration already exists (`grep -rn "remote" scripts/mcp_servers/git/git_service.py
config/git_mcp_server.toml`), since this issue's evidence may go stale. Coordinate with
`gitauth`'s target-resolution model rather than defining a parallel one.
