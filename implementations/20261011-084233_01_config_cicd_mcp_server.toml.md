## Goal

Set `workflow_allowlist` in `config/cicd_mcp_server.toml` to file-name form so the guard's exact-match comparison succeeds for requests carrying a file name such as `ci.yml` (`REQ-001`: align the checked-in config value to the file-name form the tool schema and tests assume).

## Scope

- Modify only `config/cicd_mcp_server.toml`: the `workflow_allowlist` value (line 16) and its comment/example (lines 8 header, 12-15 example block).
- No code change: the guard reads the allowlist as-is and compares by exact match.

## Assumptions

- The tool schema already expects file names (not paths) for workflow values (plan assumption; confirmed by the guard using `ci.yml` in tests).
- Fail-closed behavior (empty allowlist denies all workflow triggers) is unchanged.

## Design decisions

- Change the single value `"masaos-minori/llmagent/.github/workflows/ci.yml"` to `"ci.yml"` so it matches the request form and the existing line-8 header comment (`permitted workflow file names (e.g. "ci.yml")`).
- Update the commented example block (lines 12-15) from full-path entries (`my-org/my-repo/.github/workflows/*.yml`) to file-name entries (`deploy.yml`, `ci.yml`) so config value, comment, and example agree.

## Alternatives considered

- Keep the full-path form and change the guard to compare on full path: rejected — the tool schema and existing tests already use file names; aligning the config is the smaller, consistent change.
- Normalize at runtime by stripping the directory prefix: rejected — `REQ-002` adds explicit path-separator rejection instead, so traversal is blocked rather than silently rewritten.

## Implementation

### Target file

`config/cicd_mcp_server.toml`

### Procedure

1. Line 16: change `workflow_allowlist = ["masaos-minori/llmagent/.github/workflows/ci.yml"]` to `workflow_allowlist = ["ci.yml"]`.
2. Lines 12-15: rewrite the commented example from full-path forms to file-name forms (`deploy.yml`, `ci.yml`) so the example matches the value form.
3. Confirm the line-8 header comment (`permitted workflow file names (e.g. "ci.yml")`) still states the file-name form; leave it as-is.

### Method

Edit the two locations above in place. Do not touch other keys (`repo_allowlist`, `max_log_size_kb`, `auth_token`, `github_token`).

### Details

- Current evidence: line 16 holds the full-path value; line 8 header already states file-name form; lines 12-15 comment block holds full-path examples.
- The guard (`_assert_allowed_workflow`) compares the request's `workflow` value against this list by exact match, so a file-name value now matches a `ci.yml` request.

## Compatibility considerations

- Existing deployments that stored a full-path value stop matching after this change; document the migration in `mcp_05_01` (`REQ-003`) so operators know the accepted form is now a file name.

## Security considerations

- Fail-closed preserved: an empty list still denies all workflow triggers. Only the value format changes; no widening of the allow-list.

## Rollback considerations

- Revert line 16 to the previous full-path string and restore the lines 12-15 example. Guard behavior is unchanged, so rollback restores the prior (broken-but-safe) matching.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| config/cicd_mcp_server.toml | Integration: startup test reloads config, `ci.yml` now allowed | pytest | Startup/integration test passes |
| config/cicd_mcp_server.toml | Config still valid TOML | parse | TOML parses without error |

## Completion criteria

- Line 16 contains `"ci.yml"` (file-name form); the commented example (lines 12-15) uses file-name forms; config parses as valid TOML; empty-allowlist fail-closed behavior unchanged.

## Out of scope

- Guard logic (`REQ-002`), documentation (`REQ-003`). Other cicd guards and the repository allow-list.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Set `workflow_allowlist` to file-name form in config/cicd_mcp_server.toml (REQ-001) | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001 — set `workflow_allowlist` to file-name form so matching succeeds
- **Source issue**: issues/done/20261007-154047_cicdallow01_unify-cicd-mcp-workflow_allowlist-to-file-name-form.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261008-162442_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261011-084233
- **Related target files**: config/cicd_mcp_server.toml
