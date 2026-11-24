## Goal

Add the two settings this Plan introduces to the shipped configuration with the documented defaults (REQ-003: `allow_global_search` default `false` scopes searches; REQ-006: `max_file_read_size_kb` default `0` = unlimited), and correct the `allowed_repos` comment so it no longer states write-only permission (REQ-011: documentation states the boundary the code implements).

## Scope
**Release unit**: N/A: not part of a release unit (Plan Phase 4 is validated on its own)

## Assumptions

- The shipped values keep current behavior: `false` is the value that scopes searches, `0` is the value that changes nothing on the read path (Plan Assumptions).
- `path_denylist` stays empty and remains the registered ADR-004 exception; nothing is added here for it (Plan Assumptions, UNK-04).
- `tests/mcp_servers/github/test_github_server_auth.py` is not a companion of this document: the Plan names it from two rows (this row and `scripts/mcp_servers/github/github_models_config.py`), so it has its own procedure document (`implementations/20261124-103302_18_tests_mcp_servers_github_test_github_server_auth.py.md`).

## Design decisions

- Each new key gets its own short comment block in the existing style (`# key: meaning`, one line, plus the `0 = unlimited` note where the value has a special meaning), which keeps `tools/check_config_comment_length.py` inside the 5-line threshold.
- Key names must match the field names in `scripts/mcp_servers/github/github_models_config.py` (row 3) exactly, because `check_docs_consistency.py --domain mcp` resolves the documented keys against this file.

## Alternatives considered

- Adding the keys without comments — rejected: the file documents every security setting, and an uncommented control key is the pattern this Plan exists to remove.

## Implementation
### Target file
`config/github_mcp_server.toml`

### Procedure
1. Add `allow_global_search = false` with a comment stating that the default scopes the four search tools to `allowed_repos` at query-construction time and that `true` is an explicit opt-in reported by the posture.
2. Add `max_file_read_size_kb = 0` with a comment stating `0 = unlimited` and that the check uses the content metadata size before decoding.
3. Correct the `allowed_repos` comment at lines 15-16 from "permitted for write operations" to the read-and-write boundary the code implements after Phase 3; keep the existing "Empty list = deny all (fail-closed)" line.
4. Place the two new keys with the other policy settings (after `path_denylist`/`max_file_size_kb`), matching the file's grouping, and change no existing value.

### Method
- The file is data only: no code change. The values are read by `GitHubConfig.from_dict()` through the shared strict helpers (row 3).

### Details
- The comment blocks must stay within the 5-line threshold enforced by `tools/check_config_comment_length.py`.
- This is a deployed file: `deploy.sh` syncs configs to `/opt/llm/`, and the github-mcp service must be restarted to pick up the new keys (Plan Risks, deploy.sh Impact).

## Compatibility considerations

- The shipped values reproduce today's behavior for the read size; only search behavior becomes scoped, which is the intended change (Plan Risks).

## Security considerations

- A security setting that is not present in the shipped config is a control the documentation claims and the deployment does not set; adding the keys with the documented defaults makes the posture's claims about them meaningful (REQ-009).

## Rollback considerations

- High: removing the two keys restores the defaults from `GitHubConfig`; the comment correction is a text revert.

## Validation plan

| Target | Strategy | Command | Expected outcome |
|---|---|---|---|
| `config/github_mcp_server.toml` | Config gate + startup read | `uv run python tools/check_config_comment_length.py` | New comment blocks are within the 5-line threshold; shipped values keep current behavior |
| Same file | Cross-check | `uv run python tools/check_docs_consistency.py --domain mcp` | The documented keys resolve against this file and against `scripts/` |

## Completion criteria

- The shipped config carries the two keys with the documented default values, and its `allowed_repos` comment no longer claims write-only enforcement.

## Out of Scope

- Changing any existing value, and the ADR-004 `path_denylist` exception itself.
- The documentation files (rows 21-23) and the config-builder tests (row 18).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two keys and correct the `allowed_repos` comment per Procedure | Pending | — | — | |
| 2 | Run the config gate `uv run python tools/check_config_comment_length.py` | Pending | — | — | Test coverage is executed by row 18's document |
| 3 | Deployment step: `deploy.sh` syncs this file; restart github-mcp and confirm `/health` reports the two new checks with the shipped values | Pending | — | — | Plan Phase 5, an unmapped step in the Plan's Execution Status |

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
- **Requirement ID**: REQ-003 (search-boundary default), REQ-006 (read-size default), REQ-011 (the shipped comment states the boundary the code implements)
- **Source issue**: issues/done/20261119-140509_mcpai002_github-read-security-boundary.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261124-095007_mcpai002_github-read-security-boundary.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261124-103302
- **Related target files**: `config/github_mcp_server.toml`
