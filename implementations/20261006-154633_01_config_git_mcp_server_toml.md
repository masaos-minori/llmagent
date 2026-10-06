## Goal

Populate the empty `allowed_repo_paths` array in `config/git_mcp_server.toml` with maintainer-approved absolute repository paths, removing the git-mcp `DENY-ALL detected` warning while preserving every other setting (REQ-001, REQ-004, REQ-006).

## Scope

- **In-Scope**: `config/git_mcp_server.toml` — replace the empty `allowed_repo_paths = []` (line 6) with the maintainer-approved list of absolute paths, keeping the surrounding comment block and all other keys (`allowed_remote_urls`, `read_only`, `max_log_entries`, `auth_token`, `protected_branches`, `allow_detached_head`) unchanged.
- **Out-of-Scope**: populating `allowed_remote_urls` (separately fail-closed, not part of this change); `config/github_mcp_server.toml` and `config/cicd_mcp_server.toml` (each handled by its own procedure document); changing the fail-closed model; editing the DENY-ALL detection logic; deploying to `/opt/llm/config/` (handled by the shared deployment step).

## Assumptions

- Each approved entry is an absolute filesystem path to a real git work tree. Paths are compared after `Path.resolve()`, so store the canonical absolute path.
- `/opt/llm` is NOT a git repo and MUST NOT be added to `allowed_repo_paths` (UNK-01).
- The agent's working repo (`/home/sugimoto/llmagent`) is a plausible candidate but UNCONFIRMED — must be confirmed by a maintainer before writing.

## Design decisions

- Data-only change: replace the empty array literal with `allowed_repo_paths = ["<abs-path>", ...]`. Keep the comment block and every other key intact.
- Entries are explicit absolute paths only; no wildcards or glob patterns (REQ-006).
- The fail-closed model is preserved: populating grants access only to the listed paths; symlinks/traversals cannot escape because paths are resolved via `Path.resolve()`.

## Alternatives considered

- Adding `/opt/llm` or a broad parent directory — rejected: `/opt/llm` is not a git repo (UNK-01) and a broad path weakens the fail-closed guarantee (Risks).
- Using relative paths or globs — rejected: the field requires absolute paths resolved via `Path.resolve()`; REQ-006 forbids wildcards.
- Populating `allowed_remote_urls` alongside — rejected: out of scope; that field is separately fail-closed and not part of this change.

## Implementation

### Target file

`config/git_mcp_server.toml`

### Procedure

1. **Resolve UNK-01 with a maintainer.** Confirm the absolute repository paths to allow; verify each is a real git work tree. Do not add `/opt/llm`.
2. **Populate `allowed_repo_paths`.** Replace the empty array on line 6 with the maintainer-approved list of absolute paths, preserving the comment block and all other keys.

### Method

- Read lines 1-6 to confirm the current literal is `allowed_repo_paths = []` and the comment documents the fail-closed semantics.
- Edit line 6 to the approved list, e.g. `allowed_repo_paths = ["/abs/path/one", "/abs/path/two"]`.
- Confirm no other key changed and no wildcard/glob was introduced.

### Details

Current:
```toml
# allowed_repo_paths: absolute paths of git repositories accessible via this server.
# Empty list = deny all (fail-closed). Add repo paths explicitly.
# Example: allowed_repo_paths = ["/home/masaos/llmagent", "/opt/llm"]
allowed_repo_paths = []
```
After (entries pending maintainer approval):
```toml
allowed_repo_paths = ["/home/sugimoto/llmagent"]
```
Note: the example comment still shows `/opt/llm`; do not copy it into the live value (it is not a git repo). Candidate paths are UNCONFIRMED and require maintainer sign-off before being written.

## Compatibility considerations

- The git-mcp service parses `allowed_repo_paths` at startup; populating it removes the `security_audit.py::audit_security_defaults()` DENY-ALL warning (lines 163-164) without changing any other key.
- No schema, import, or caller change. Other keys (`read_only`, `protected_branches`, `auth_token`, ...) are untouched.

## Security considerations

- Fail-closed is preserved: only explicitly listed absolute paths are allowed; symlinks/traversals cannot escape the list because paths are resolved via `Path.resolve()`.
- REQ-006: no wildcard/glob entries. Only minimal, maintainer-approved paths are written.

## Rollback considerations

- Restore `allowed_repo_paths = []` (or the pre-edit list) to revert. The change is a single array literal with no other side effects.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `allowed_repo_paths` | Integration — DENY-ALL gone, git read works | `bash /opt/llm/start_agent.sh` + a git read tool | No DENY-ALL warning; operation succeeds |
| Other keys | Static — unchanged | diff against pre-edit copy | No change outside `allowed_repo_paths` |

## Completion criteria

- `allowed_repo_paths` contains only maintainer-approved absolute paths.
- Every other key in the file is unchanged (REQ-004).
- No wildcard/glob entry present (REQ-006).

## Out of scope

- `allowed_remote_urls` population.
- `config/github_mcp_server.toml` and `config/cicd_mcp_server.toml` (their own procedure documents).
- Deploying to `/opt/llm/config/` (shared deployment step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Resolve UNK-01 with a maintainer (confirm absolute paths; verify each is a git work tree; exclude `/opt/llm`) | Pending | — | — | Human decision gate; required before writing |
| 2 | Populate `allowed_repo_paths` per Implementation > Procedure | Pending | — | — | REQ-001, REQ-004, REQ-006 |
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
- **Requirement ID**: `REQ-001` — populate `allowed_repo_paths`; `REQ-004` — preserve every other setting; `REQ-006` — no wildcard patterns
- **Source issue**: `issues/20261005-181600_configure_deny_all_allowlists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-095454_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-154633
- **Related target files**: `config/git_mcp_server.toml`
