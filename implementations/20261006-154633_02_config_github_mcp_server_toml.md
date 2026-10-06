## Goal

Populate the empty `allowed_repos` array in `config/github_mcp_server.toml` with maintainer-approved `owner/repo` entries, removing the github-mcp `DENY-ALL detected` warning while preserving every other setting (REQ-002, REQ-004, REQ-006).

## Scope

- **In-Scope**: `config/github_mcp_server.toml` — replace the empty `allowed_repos = []` (line 16) with the maintainer-approved list of `owner/repo` entries, keeping the surrounding comment block and all other keys (`max_per_page`, `protected_branches`, `allow_force_push`, `require_pr_review`, `path_denylist`, `max_file_size_kb`, `audit_log_path`) unchanged.
- **Out-of-Scope**: populating `path_denylist` (separately fail-closed, not part of this change); `config/git_mcp_server.toml` and `config/cicd_mcp_server.toml` (each handled by its own procedure document); changing the fail-closed model; editing the DENY-ALL detection logic; deploying to `/opt/llm/config/` (handled by the shared deployment step).

## Assumptions

- Each approved entry is an `owner/repo` string in the format documented in `docs/22_mcp/mcp_05_01_access-control-and-allowlists.md`.
- The GitHub remote for this project (`masaos-minori/llmagent`) is a plausible candidate but UNCONFIRMED — must be confirmed by a maintainer before writing (UNK-02).

## Design decisions

- Data-only change: replace the empty array literal with `allowed_repos = ["<owner>/<repo>", ...]`. Keep the comment block and every other key intact.
- Entries are explicit `owner/repo` strings only; no wildcards or glob patterns (REQ-006).
- The fail-closed model is preserved: populating grants write authorization only to the listed repos.

## Alternatives considered

- Adding a broad org-level wildcard (e.g. `masaos-minori/*`) — rejected: REQ-006 forbids wildcards and weakens the fail-closed guarantee (Risks).
- Populating `path_denylist` alongside — rejected: out of scope; that field is separately managed and not part of this change.

## Implementation

### Target file

`config/github_mcp_server.toml`

### Procedure

1. **Resolve UNK-02 with a maintainer.** Confirm the `owner/repo` names authorized for write operations.
2. **Populate `allowed_repos`.** Replace the empty array on line 16 with the maintainer-approved list of `owner/repo` entries, preserving the comment block and all other keys.

### Method

- Read lines 14-16 to confirm the current literal is `allowed_repos = []` and the comment documents the fail-closed semantics.
- Edit line 16 to the approved list, e.g. `allowed_repos = ["masaos-minori/llmagent"]`.
- Confirm no other key changed and no wildcard/glob was introduced.

### Details

Current:
```toml
# allowed_repos: whitelist of repos permitted for write operations (owner/repo format)
# Empty list = deny all (fail-closed)
allowed_repos = []
```
After (entries pending maintainer approval):
```toml
allowed_repos = ["masaos-minori/llmagent"]
```
Candidate `masaos-minori/llmagent` is UNCONFIRMED and requires maintainer sign-off before being written.

## Compatibility considerations

- The github-mcp service parses `allowed_repos` at startup; populating it removes the `security_audit.py::audit_security_defaults()` DENY-ALL warning (lines 174-175) without changing any other key.
- No schema, import, or caller change. Other keys (`max_per_page`, `protected_branches`, `require_pr_review`, `audit_log_path`, ...) are untouched.

## Security considerations

- Fail-closed is preserved: only explicitly listed `owner/repo` repos are authorized for writes.
- REQ-006: no wildcard/glob entries. Only minimal, maintainer-approved repos are written.

## Rollback considerations

- Restore `allowed_repos = []` (or the pre-edit list) to revert. The change is a single array literal with no other side effects.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `allowed_repos` | Integration — DENY-ALL gone, GitHub read/write works | `bash /opt/llm/start_agent.sh` + a GitHub read tool | No DENY-ALL warning; operation succeeds |
| Other keys | Static — unchanged | diff against pre-edit copy | No change outside `allowed_repos` |

## Completion criteria

- `allowed_repos` contains only maintainer-approved `owner/repo` entries.
- Every other key in the file is unchanged (REQ-004).
- No wildcard/glob entry present (REQ-006).

## Out of scope

- `path_denylist` population.
- `config/git_mcp_server.toml` and `config/cicd_mcp_server.toml` (their own procedure documents).
- Deploying to `/opt/llm/config/` (shared deployment step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Resolve UNK-02 with a maintainer (confirm `owner/repo` names) | Pending | — | — | Human decision gate; required before writing |
| 2 | Populate `allowed_repos` per Implementation > Procedure | Pending | — | — | REQ-002, REQ-004, REQ-006 |
| 3 | Deploy via `bash deploy/deploy.sh` + startup verification | Pending | — | — | REQ-005; shared deployment step across all three config docs |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` — populate `allowed_repos`; `REQ-004` — preserve every other setting; `REQ-006` — no wildcard patterns
- **Source issue**: `issues/20261005-181600_configure_deny_all_allowlists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-095454_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-154633
- **Related target files**: `config/github_mcp_server.toml`
