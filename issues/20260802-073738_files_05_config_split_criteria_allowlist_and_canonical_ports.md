# Simplify docs/01_overview-files-05-config.md file listing; document config-split criteria, allowlist-change rule, and establish it as the canonical port/server source

## Priority
High

## Summary
`docs/01_overview-files-05-config.md` (~lines 27-45) contains a manually-maintained file listing that currently matches source but carries ongoing drift risk. The document does not state (1) the criteria for deciding what belongs in `agent.toml` vs. individual MCP server TOML files, or (2) the operational rule for changing allowlists (e.g. in `file_read_mcp_server.toml`, `shell_mcp_server.toml`) safely. Separately, per this review's overall reconstruction policy, this file should become the single canonical source for MCP server port numbers, which are currently duplicated across `arch-01-process.md`, `files-03-scripts-part5.md`, and this file itself.

## Reason for Change
Config-split criteria and allowlist-change rules are security-sensitive operational knowledge not derivable from reading the code casually — getting them wrong risks unintentionally permitting file/command execution. Port-number duplication across 3 files risks drift (already confirmed elsewhere in this review — see the arch-01 server-count issue).

## Implementation Intent
Replace the manual file listing with an implementation-tree pointer. Add the config-split criteria and allowlist-change operational rule. Make this file the canonical location for MCP server port/name mapping, referenced (not repeated) by other files.

## Target Files or Areas
`docs/01_overview-files-05-config.md`

## Required Changes
- Replace the file listing (~lines 27-45) with a pointer to `config/` for the current file list.
- Add the criteria for what goes into `agent.toml` vs. an individual MCP server's TOML file — confirm this with the document's author/designer if not derivable from existing conventions; if unconfirmable, register as a Needs Confirmation item rather than asserting invented criteria.
- Add an operational rule for allowlist changes, e.g.: "Allowed-directory / allowed-command changes must go through code review and be updated consistently with `conf.d/` settings — loosening them carelessly risks permitting unintended file or command execution."
- Ensure this file contains the authoritative MCP server-name ↔ port mapping table, since other files (arch-01-process.md, files-03-scripts-part5.md) will be updated to reference it instead of repeating the numbers (tracked in separate issues).

## Acceptance Criteria
The file listing is replaced with an implementation-tree pointer; config-split criteria and the allowlist-change rule are documented (or explicitly tracked as Needs Confirmation if unconfirmable); this file holds the canonical port/server mapping.

## Testing Expectations
Not required (documentation-only).

## Documentation Impact
`docs/01_overview-files-05-config.md` updated; becomes the canonical reference target for the arch-01 and files-03-scripts-part5 port-consolidation issues.

## Out of Scope
Do not change the actual `config/*.toml` allowlist values in this issue — documentation only. Do not edit `arch-01-process.md` or `files-03-scripts-part5.md` in this issue (tracked separately, but they depend on this file's port table existing first).

## AI Implementation Instruction
Do not invent config-split criteria if the actual design rationale isn't confirmable — register as Needs Confirmation instead of asserting a plausible-sounding rule as established policy.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §1 (重複している情報の傾向, 再構成の基本方針 item 2), §2 削除候補 item 5, §4 強化候補 (files-05-config)
- Generated at: 2026-08-02
