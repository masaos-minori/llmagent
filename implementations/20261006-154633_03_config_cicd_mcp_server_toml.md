## Goal

Populate the empty `repo_allowlist` and `workflow_allowlist` arrays in `config/cicd_mcp_server.toml` with maintainer-approved entries, removing the cicd-mcp `DENY-ALL detected` and service-level empty-allowlist warnings while preserving every other setting (REQ-003, REQ-004, REQ-006).

## Scope

- **In-Scope**: `config/cicd_mcp_server.toml` — replace the empty `repo_allowlist = []` (line 6) and `workflow_allowlist = []` (line 16) with maintainer-approved lists, keeping the surrounding comment block and all other keys (`max_log_size_kb`, `auth_token`, `github_token`) unchanged.
- **Out-of-Scope**: `config/git_mcp_server.toml` and `config/github_mcp_server.toml` (each handled by its own procedure document); changing the fail-closed model; editing the empty-allowlist warning logic in `cicd_service_guards.py`; deploying to `/opt/llm/config/` (handled by the shared deployment step).

## Assumptions

- `repo_allowlist` entries are `owner/repo` strings.
- `workflow_allowlist` entries are `owner/repo/.github/workflows/<file>` strings (per `cicd_service_guards.py` / `mcp_05_01`).
- The cicd project's CI and deploy workflows are plausible candidates but UNCONFIRMED — exact workflow file paths must be confirmed by a maintainer and cross-checked against `.github/workflows/` in the target repo (UNK-03).

## Design decisions

- Data-only change: replace both empty array literals with maintainer-approved lists. Keep the comment blocks and every other key intact.
- Entries are explicit paths/repos only; no wildcards or glob patterns (REQ-006).
- The fail-closed model is preserved: populating grants access only to the listed repos/workflows.

## Alternatives considered

- Adding a broad `owner/repo/*` workflow pattern — rejected: REQ-006 forbids wildcards and weakens the fail-closed guarantee (Risks).
- Populating only `repo_allowlist` and leaving `workflow_allowlist` empty — rejected: `workflow_allowlist` is independently fail-closed and emits its own DENY-ALL warning (UNK-03); both must be populated.

## Implementation

### Target file

`config/cicd_mcp_server.toml`

### Procedure

1. **Resolve UNK-02 and UNK-03 with a maintainer.** Confirm the `owner/repo` names for `repo_allowlist` and the workflow file paths for `workflow_allowlist`; cross-check workflow paths against `.github/workflows/` in the target repo.
2. **Populate `repo_allowlist`.** Replace the empty array on line 6 with the maintainer-approved list of `owner/repo` entries.
3. **Populate `workflow_allowlist`.** Replace the empty array on line 16 with the maintainer-approved list of `owner/repo/.github/workflows/<file>` entries.

### Method

- Read lines 3-16 to confirm the current literals are `repo_allowlist = []` and `workflow_allowlist = []` and the comments document the fail-closed semantics.
- Edit line 6 to the approved `repo_allowlist` and line 16 to the approved `workflow_allowlist`.
- Confirm no other key changed and no wildcard/glob was introduced.

### Details

Current:
```toml
# repo_allowlist: permitted repositories in 'owner/repo' format
# IMPORTANT: empty list = deny all repositories (fail-closed)
# Example: ["myorg/myrepo", "myorg/other-repo"]
repo_allowlist = []

# workflow_allowlist: permitted workflow file names (e.g. "ci.yml")
# Fail-closed: empty list = deny all workflow triggers (CicdAuthorizationError).
# Add allowed workflow patterns to enable triggering.
# Example:
# workflow_allowlist = [
#   "my-org/my-repo/.github/workflows/deploy.yml",
#   "my-org/my-repo/.github/workflows/ci.yml",
# ]
workflow_allowlist = []
```
After (entries pending maintainer approval):
```toml
repo_allowlist = ["masaos-minori/llmagent"]
workflow_allowlist = ["masaos-minori/llmagent/.github/workflows/ci.yml"]
```
Candidate values are UNCONFIRMED and require maintainer sign-off before being written. Verify the `workflow_allowlist` format with a dry-run trigger in Phase 3 (Risks).

## Compatibility considerations

- The cicd-mcp service parses both lists at startup; populating them removes the `security_audit.py::audit_security_defaults()` DENY-ALL warning (lines 187-188) and the `cicd_service_guards.py` service-level warnings (lines 35-41) without changing any other key.
- No schema, import, or caller change. Other keys (`max_log_size_kb`, `auth_token`, `github_token`) are untouched.

## Security considerations

- Fail-closed is preserved: only explicitly listed repos/workflows are authorized.
- REQ-006: no wildcard/glob entries. Only minimal, maintainer-approved entries are written.

## Rollback considerations

- Restore `repo_allowlist = []` and `workflow_allowlist = []` (or the pre-edit lists) to revert. The change is two array literals with no other side effects.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `repo_allowlist` / `workflow_allowlist` | Integration — DENY-ALL + service-level warnings gone, dry-run trigger works | `bash /opt/llm/start_agent.sh` + a cicd dry-run trigger | No DENY-ALL / service-level warning; trigger succeeds |
| Other keys | Static — unchanged | diff against pre-edit copy | No change outside the two lists |

## Completion criteria

- `repo_allowlist` and `workflow_allowlist` contain only maintainer-approved entries.
- Every other key in the file is unchanged (REQ-004).
- No wildcard/glob entry present (REQ-006).

## Out of scope

- `config/git_mcp_server.toml` and `config/github_mcp_server.toml` (their own procedure documents).
- Deploying to `/opt/llm/config/` (shared deployment step).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Resolve UNK-02/03 with a maintainer (confirm `owner/repo` names and workflow file paths; cross-check `.github/workflows/`) | Completed | 20261007-111425 | 20261007-111425 | Human decision gate; required before writing Maintainer confirmed allowlist values |
| 2 | Populate `repo_allowlist` and `workflow_allowlist` per Implementation > Procedure | Completed | 20261007-111425 | 20261007-111425 | REQ-003, REQ-004, REQ-006 Edited+validated: TOML parses, other keys unchanged, DENY-ALL removed, 813 tests pass |
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
- **Requirement ID**: `REQ-003` — populate `repo_allowlist`/`workflow_allowlist`; `REQ-004` — preserve every other setting; `REQ-006` — no wildcard patterns
- **Source issue**: `issues/20261005-181600_configure_deny_all_allowlists.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261006-095454_plan.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261006-154633
- **Related target files**: `config/cicd_mcp_server.toml`