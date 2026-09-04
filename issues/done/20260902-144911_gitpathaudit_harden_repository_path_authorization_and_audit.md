# Harden Git MCP repository-path authorization and rejection audit handling

## Priority
High

## Summary
Implement fail-closed canonical-path containment checks for Git MCP repository access and make
rejection auditing non-throwing, so only validated canonical repository identities are used for
access and authoritative audit targets.

## Background
`issues/done/20260816-160000_git_security_path_is_relative_to.md` already replaced raw
string-prefix path comparison with `Path.is_relative_to()` in the relevant helper. That issue's
scope did not cover the broader concerns this issue addresses: whether the resolved path is
proven to be within an allowed repository root after canonicalization, symlink-escape
handling, and whether the rejection/audit path can itself throw a secondary exception when
attempting to snapshot a repository after path resolution has already failed.

## Problem
Repository-path resolution and authorization are separate security boundaries. The visible path
helper canonicalizes a path but does not itself prove that the resolved path is within an
allowed repository root. In addition, the rejection path may attempt to snapshot a repository
after path resolution has already failed, causing a secondary exception or access to an
unvalidated path. Audit logging must never weaken validation or replace the original rejection
outcome.

## Reason for Change
A path-containment gap or a rejection-path exception can turn a security control into a source
of undefined behavior at exactly the moment it should fail closed.

## Implementation Intent
Verify and enforce containment within `allowed_repo_paths` after canonical path resolution,
using path-component-aware containment checks rather than raw string-prefix matching (building
on `Path.is_relative_to()`'s prior adoption). Reject missing, inaccessible, non-repository,
symlink-escaped, and unauthorized paths before creating a repository snapshot. Do not call
`RepositoryState.snapshot()` after path validation or authorization fails. Record the untrusted
requested value only in a safely redacted audit field, and use the canonical repository path as
the authoritative audit target only after successful authorization. Ensure audit failure cannot
replace or mask the original validation response.

## Target Files or Areas
- `scripts/mcp_servers/git/git_security.py`
- `scripts/mcp_servers/git/git_service.py`
- `scripts/mcp_servers/git/git_server.py`
- `scripts/mcp_servers/git/repository_state.py`
- `scripts/mcp_servers/audit.py`
- `config/git_mcp_server.toml`
- `tests/test_git_server.py`

Confirm file existence and responsibility before editing; modify only files required by the
verified implementation path.

## Required Changes
- Verify and enforce containment within `allowed_repo_paths` after canonical path resolution.
- Use path-component-aware containment checks rather than raw string-prefix matching.
- Reject missing, inaccessible, non-repository, symlink-escaped, and unauthorized paths before creating a repository snapshot.
- Do not call `RepositoryState.snapshot()` after path validation or authorization fails.
- Record the untrusted requested value only in a safely redacted audit field.
- Use the canonical repository path as the authoritative audit target only after successful authorization.
- Ensure audit failure cannot replace or mask the original validation response.

## Constraints
- Do not guess unverified behavior; record unresolved design decisions as Needs Confirmation.
- Preserve unrelated behavior, including the prior `Path.is_relative_to()` adoption.
- Do not introduce a second authorization or dispatch path.
- Update documentation only after implementation and tests establish the current behavior.
- If investigation disproves an assumption in this issue, update the issue with evidence before implementation.

## Acceptance Criteria
- A sibling path such as `/allowed-repo-evil` is not accepted for an `/allowed-repo` root.
- Symlink escape attempts are rejected.
- Invalid and unauthorized paths produce the intended rejection without a secondary exception.
- No repository access occurs after path validation fails.
- Audit records distinguish the requested target from the validated canonical target.
- Tests cover missing paths, permission errors, invalid repositories, sibling-prefix paths, and symlink traversal.

## Testing Expectations
Add focused unit tests for all changed rules. Add or update integration tests for the HTTP and
service dispatch paths. Confirm each new test fails before the fix and passes after the fix.
Run the complete existing Git MCP test suite and resolve regressions. Do not treat
documentation statements as proof of runtime behavior.

## Documentation Impact
Update `docs/04_mcp_04_05_git.md`'s path-authorization description once implementation and
tests establish the current behavior.

## Out of Scope
- Protected-branch/ref authorization content itself (`gitauth`).
- The write-protection pipeline's stage ordering (`gitpipeline`).
- Remote authorization and concurrency control (`gitremote`).

## Dependencies
Builds on `issues/done/20260816-160000_git_security_path_is_relative_to.md`'s prior
`Path.is_relative_to()` adoption.

## Unresolved Questions
N/A: none

## AI Implementation Instruction
Before editing, re-confirm the current path-canonicalization and snapshot call order
(`grep -rn "is_relative_to\|snapshot(" scripts/mcp_servers/git/`), since this issue's evidence
may go stale. Do not weaken the existing `Path.is_relative_to()` check; extend it with
containment enforcement and rejection-path safety.
