# Fix confirmed server-count error in docs/01_overview-arch-01-process.md and defer to agent.toml/files-05-config as canonical

## Priority
High

## Summary
`docs/01_overview-arch-01-process.md` (~line 47) states "11 サーバ (:8004〜:8014)" but `config/agent.toml`'s `[mcp_servers.*]` actually defines 10 servers (port `:8011` unused/skipped) — a confirmed count error, also inconsistent with the file's own 10-row service table (~lines 70-84).

## Reason for Change
Model names and port numbers are inherently volatile and `config/agent.toml` is the ultimate authority; hardcoding a count here has already drifted from reality once, causing operator confusion about whether something is expected to run on port 8011.

## Implementation Intent
Replace the specific server count and the detailed service table with a note that the table shows a representative configuration and that `config/agent.toml` (or `docs/01_overview-files-05-config.md`, once it becomes canonical per the related config-consolidation issue) is authoritative for the exact count/port mapping. Determine and state whether port 8011 is reserved-for-future-use or a fully retired assignment.

## Target Files or Areas
`docs/01_overview-arch-01-process.md`

## Required Changes
- Correct or remove the "11 サーバ" count claim (~line 47).
- Add a note at the top of the service table (~lines 70-84): "以下は代表的な構成例であり、正確なポート・モデル対応は `config/agent.toml` を正本とする。"
- Confirm with the document owner (or via commit history / config comments) whether port 8011 is reserved for future use or fully retired; state this explicitly rather than leaving it ambiguous.

## Acceptance Criteria
No specific server count is asserted as fixed fact in this file without a canonical-source disclaimer; the status of port 8011 is explicitly stated (reserved or retired), not left implicit.

## Testing Expectations
Not required (documentation-only). Verify current server count via `grep -c` on `config/agent.toml`'s `[mcp_servers.*]` sections before finalizing.

## Documentation Impact
`docs/01_overview-arch-01-process.md` updated; depends on (or coordinates with) the related files-05-config canonical-source issue.

## Out of Scope
Do not change `config/agent.toml` in this issue. Do not consolidate the port table into `files-05-config.md` in this issue (tracked separately) — only add the disclaimer/reference here.

## AI Implementation Instruction
Verify the current server count directly against `config/agent.toml` before writing the disclaimer. If port 8011's status (reserved vs. retired) cannot be confirmed from config comments or commit history, register it as a Needs Confirmation item rather than guessing.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_overview_architecture.md §3 要約候補 item 1, §5 例1, §6A (arch-01-process.md「11サーバ」)
- Generated at: 2026-08-02
