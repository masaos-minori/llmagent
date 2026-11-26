## Goal

State the actual stderr log location, the `0o600` file mode, and the retention policy in the MCP
lifecycle documentation (REQ-008 — documentation matches the implemented diagnostic policy).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions

- Line 73 currently documents `<log_dir>/scripts/mcp_servers/{server_key}.stderr.log`, which does not
  match the code path `tempfile.gettempdir()/mcp_server_logs/{server_key}/stderr.log`
  (`scripts/agent/http_lifecycle_stderr_log_manager.py` lines 67-68).
- The retention values to state are the configured defaults `max_stderr_log_size_mb = 100.0` and
  `max_stderr_log_files = 3` (`scripts/shared/mcp_config.py` lines 140-141).
- Docs-only row: no code change, and the companion test row is not applicable.

## Design decisions

- Document the location as the code's actual root rather than changing the code to match the doc, per
  the Plan's decision to keep the log root as it is (Plan UNK-01).

## Alternatives considered

- N/A: the Plan already chose documentation alignment over changing the log root.

## Implementation
### Target file
`docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
### Procedure
- Correct the stderr log path at line 73 to the actual location.
- Add the file mode (`0o600`), the configured size limit, generation retention with expired-generation
  purge, and the copy-and-truncate rotation rule.

### Method
- One sentence for the location, one for mode, and one for retention and rotation, in the existing
  lifecycle section; no new section is added.

### Details
- Keep the existing code-fence diagram; only the path inside it changes.

## Compatibility considerations

- N/A: documentation only.

## Security considerations

- N/A: no new disclosure surface; the doc states the mode that protects the log.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- Documentation gates per `rules/tool-gates.md`: `uv run python tools/check_docs_quality.py`,
  `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`,
  and `uv run python tools/check_docs_consistency.py --domain mcp`.

## Completion criteria

- The documented path, mode, size limit, and retention match the implementation, and the doc gates pass.

## Out of Scope

- The implementation change itself (document 04).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Run the documentation gates (`rules/tool-gates.md`) | Pending | — | — | |

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
- **Requirement ID**: `REQ-008` (documentation states the diagnostic policy and log location)
- **Source issue**: `issues/20261119-145307_cliplc009_redaction-stderr-diagnostics.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261126-210258_cliplc009_redaction-stderr-diagnostics.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261126-225455
- **Related target files**: `docs/22_mcp/mcp_03_04_tool-call-tracing-and-lifecycle.md`
