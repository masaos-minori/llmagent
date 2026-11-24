## Goal
Record the strict github-mcp config parsing rules in the configuration inventory doc (docs row 19).
## Scope
**Release unit**: N/A: not part of a release unit
- Modifies only `docs/22_mcp/mcp_06_01_configuration-file-inventory.md` (Plan Phase 7/8 doc hand-off).
## Assumptions
- Lands with seq 07, so every rule described is live. The doc states rules and points at
  `github_models_config.py` as canonical source, extending the existing fail-on-empty-keys pattern.
## Design decisions
- Turn the github clause of "Non-empty required keys" into a startup-rules list: booleans must be
  booleans; `max_file_size_kb`/`max_file_read_size_kb` non-negative with `0` still unlimited;
  `default_per_page`/`max_per_page` positive with `default_per_page <= max_per_page`; every
  `allowed_repos` entry canonical lowercase `owner/repo`, duplicates collapsed.
- State the consequence once: a violating config now refuses to start `github-mcp`; the shipped
  `config/github_mcp_server.toml` satisfies all rules, so no config change accompanies this Plan.
## Alternatives considered
- N/A: prose-level edit; no key is added or removed, so the Configuration Value Ownership table gains no row.
## Implementation
### Target file
`docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
### Procedure
1. Rewrite the github clause of the "Non-empty required keys" paragraph into the startup-rules list.
2. Add one sentence naming the startup rules and pointing at
   `scripts/mcp_servers/github/github_models_config.py` as the canonical source.
## Compatibility considerations
- N/A: docs-only row; the `server.per_page_bounds` posture check stays and the doc must not claim it
  is removed.
## Security considerations
- N/A: documentation of the seq 07 fail-fast rules themselves.
## Rollback considerations
- N/A: revert the commit.
## Validation plan
- The four docs gates in `rules/tool-gates.md` (`check_docs_quality.py`, `check_docs_structure.py`, `check_docs_content_policy.py`, `check_docs_consistency.py --domain mcp`).
## Completion criteria
- The doc states all four github-mcp startup rules and the fail-fast consequence with zero findings
  from the docs gates.
## Out of Scope
- Config file content (unchanged), github-mcp tool behavior docs (seq 18).
## Execution Status
### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the github startup-rules paragraph, add the canonical-source sentence | Pending | — | — | REQ-006, REQ-007 |
| 2 | Run the docs gates | Pending | — | — | |
### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-006` (strict shared config helpers), `REQ-007` (canonical `allowed_repos` identity)
- **Source issue**: issues/20261119-140510_mcpai003_github-pydantic-schema-source.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-173306_mcpai003_github-pydantic-schema-source.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-181931
- **Related target files**: `docs/22_mcp/mcp_06_01_configuration-file-inventory.md`
