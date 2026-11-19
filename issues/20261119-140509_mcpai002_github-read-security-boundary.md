# Establish one enforceable GitHub read-security boundary

## Priority
High

## Summary
Create one mandatory authorization boundary for all GitHub read operations (repository-scoped reads, global searches, and file-content reads) that enforces `allowed_repos`, the path denylist, content-size limits, and a binary-content policy.

## Background
Source: consolidated review backlog (`memo-issue.md`, Issue 1). The security posture reports allowlist and denylist as configured; this issue makes posture describe actual enforcement.

Evidence checked in this session (`Explicit in code`, by `rg`): `_assert_allowed_repo` is defined in `scripts/mcp_servers/github/github_service_security.py:62` and `_get_repo` (line 160) calls `self._gh.get_repo` without it. Write methods call `_assert_allowed_repo` explicitly (for example `github_service_issues.py:66,108`), while read methods call `_get_repo` directly (for example `github_service_issues.py:46,58`). Search methods pass the caller query straight to the GitHub client (`github_service_repository.py:54,164`, `github_service_issues.py:95`). No `allow_global_search` or `max_file_read_size` setting exists. File-read controls and the HTTP behavior are `Needs confirmation`.

## Problem
Repository-scoped reads can reach the GitHub API for a repository outside `allowed_repos`, and global search can query outside the configured boundary, so private repository metadata, paths, source, credentials, issue, or pull request content reachable by the token may be disclosed. File reads may skip denied-path, size, or binary controls (`Needs confirmation`).

## Reason for Change
Security-sensitive behavior: posture checks can report a control that some read paths do not enforce. Filtering results afterwards is insufficient because an out-of-scope query can leak through errors, counts, timing, or logs.

## Implementation Intent
Make the common service boundary authoritative: the allowlist check runs inside `_get_repo()` before any client call, and all repository-scoped reads and writes obtain repositories only through it. Scope searches at query-construction time and reject qualifiers that expand beyond the boundary. Apply read-specific path, size, and binary controls before decoding. Prefer a few common guard functions over per-operation checks. Preserve existing write authorization behavior.

## Target Files or Areas
- `scripts/mcp_servers/github/github_service_security.py`
- `scripts/mcp_servers/github/github_service_issues.py`
- `scripts/mcp_servers/github/github_service_pull_requests.py`
- `scripts/mcp_servers/github/github_service_repository.py`
- `scripts/mcp_servers/github/github_service_file.py`
- `scripts/mcp_servers/github/github_models_config.py`
- GitHub security posture implementation
- `tests/mcp_servers/github/`

## Required Changes
- Move the allowlist assertion into `_get_repo()` before the client call; forbid direct `get_repo()` outside the common boundary.
- Define one case-normalization policy for `owner/repo`.
- Add `allow_global_search: bool = false`; in standard mode constrain issue, pull request, code, and repository searches to `allowed_repos`.
- Parse caller-supplied `repo:`, `org:`, and `user:` qualifiers and reject any that expand the boundary.
- Apply the path denylist to `github_get_file_contents`.
- Add a positive `max_file_read_size_kb`; check content metadata size before decoding.
- Define binary-content behavior (default: reject) and replace silent invalid UTF-8 substitution with an explicit error or a declared lossy-decoding field.
- Map each posture check to its runtime enforcement point.

## Constraints
- Authorization runs before the first GitHub API access.
- No result-filtering-only design.
- Configuration parsing must stay strict (coordinate field validation with `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md`).
- Posture documentation must name the exact runtime guard of every published check.

## Acceptance Criteria
- [ ] Every repository-scoped read and write enforces `allowed_repos` through one common boundary.
- [ ] A public or private repository outside the allowlist is rejected before data is returned.
- [ ] Default search cannot return data from repositories outside `allowed_repos`; an out-of-scope `repo:` qualifier is rejected.
- [ ] Global search requires explicit opt-in and is reported by security posture.
- [ ] Denied paths are rejected for reads and writes per the documented policy.
- [ ] Oversized content is rejected before decoding; binary and invalid UTF-8 content follow an explicit, tested policy.
- [ ] Security posture documentation identifies the runtime guard for every published check.

## Testing Expectations
- Service tests for issue, pull request, branch, commit, and file reads outside the allowlist.
- HTTP `/v1/call_tool` tests for out-of-scope public and private repository reads.
- Tests for all four search tools with no qualifier, an allowed `repo:` qualifier, and a denied `repo:` qualifier.
- Tests for denied paths, oversized files, binary files, invalid UTF-8, and directory objects.
- A regression test proving authorization runs before the first GitHub API access.
- Run ruff, mypy, and the full test suite.

## Documentation Impact
Yes. Update the GitHub security posture and design description: intent, boundaries, failure behavior, and the enforcement point per check (final sweep in `issues/20261119-140519_mcpai012_mcp-design-docs-update.md`).

## Out of Scope
- Retry, timeout, and audit behavior of GitHub writes (`issues/20261119-140513_mcpai006_github-write-retry-policy.md`).
- Schema generation (`issues/20261119-140510_mcpai003_github-pydantic-schema-source.md`).
- Resource-scope refinement (`issues/20261119-140520_mcpai013_github-resource-scope-refine.md`).
- A base64 file-read tool (may be proposed separately).

## Dependencies
- Blocks `issues/20261119-140513_mcpai006_github-write-retry-policy.md`, `issues/20261119-140517_mcpai010_github-http-contract-tests.md`, and `issues/20261119-140520_mcpai013_github-resource-scope-refine.md`.
- Independent of `issues/20261119-140508_mcpai001_atomic-dedup-state-machine.md` and `issues/20261119-140510_mcpai003_github-pydantic-schema-source.md`; may be implemented in parallel with them.
- Sibling check: archived `issues/done/20261017-115004_mcp006_implement-missing-guard-layers-for-high-risk-tool-categories.md` touched the same security module; re-verify this issue's claims against current source before planning.

## Unresolved Questions
- `不明`: case-normalization policy for `owner/repo` (casefold versus preserving the API's canonical form).
- `不明`: default value of `max_file_read_size_kb`.
- `不明`: whether write paths should also be denied by path denylist beyond the current behavior ("according to the documented policy").

## AI Implementation Instruction
Add the failing out-of-allowlist and pre-API-access regression tests first. Keep changes inside the GitHub MCP server and its tests, add no extra settings beyond those listed, and stop and report if a read path cannot be routed through `_get_repo()`.

## Traceability
- **Workflow phase**: `issue-creator`
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261119-140509
- **Related target files**: `scripts/mcp_servers/github/github_service_security.py`, `scripts/mcp_servers/github/github_service_issues.py`, `scripts/mcp_servers/github/github_service_pull_requests.py`, `scripts/mcp_servers/github/github_service_repository.py`, `scripts/mcp_servers/github/github_service_file.py`, `scripts/mcp_servers/github/github_models_config.py`, `tests/mcp_servers/github/`
