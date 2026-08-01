# Resolve audit-logging description contradiction (docs/04_mcp_02_03 vs 06_07) and remove its dispatch_tool code example

## Priority
High

## Summary
`docs/04_mcp_02_03_audit-logging-and-errors.md` states cicd-mcp/git-mcp use only `logging.getLogger` (no shared audit log), while `docs/04_mcp_06_07_reading-audit-logs.md`'s table and actual source both confirm cicd-mcp/git-mcp DO call the shared `_audit_log()`. The `02_03` section also contains a near-verbatim `dispatch_tool` code transcription surrounding this incorrect claim. Separately, whether rag-pipeline-mcp writes any audit log at all is still unconfirmed and should be resolved as part of the same accuracy pass.

## Reason for Change
This is a confirmed factual contradiction between 2 files describing the same fact, with `06_07` and source code agreeing against `02_03`. Anyone relying on `02_03` for a compliance/audit-coverage review would undercount which servers are actually audited. The code example is a maintenance burden that goes stale with implementation changes and is unrelated to the design decision itself.

## Implementation Intent
Correct `02_03` to match `06_07`/source (cicd-mcp and git-mcp DO use shared `_audit_log()`), establish `06_07`'s table as canonical for audit-log coverage, remove the `dispatch_tool` code transcription in favor of a one-line fact statement, and resolve rag-pipeline-mcp's audit-log status via source inspection.

## Target Files or Areas
`docs/04_mcp_02_03_audit-logging-and-errors.md`, `docs/04_mcp_06_07_reading-audit-logs.md`

## Required Changes
- Correct `02_03`'s claim about cicd-mcp/git-mcp to match confirmed reality (they DO use shared `_audit_log()`).
- Remove the `dispatch_tool` code transcription in `02_03`; replace with a one-line/table fact: "Servers using shared `_audit_log()`: [list]" with a file-path reference, no inline code.
- Investigate rag-pipeline-mcp's actual audit-log status (currently `06_07` states it's unimplemented, same as file-read-mcp/file-write-mcp) and confirm this is still accurate; update both files consistently once confirmed.
- Establish `06_07`'s table as the canonical source for audit-log server coverage; have `02_03` reference it rather than maintaining a separate, potentially-diverging list.

## Acceptance Criteria
`02_03` and `06_07` no longer contradict each other on which servers use shared audit logging; no inline code transcription remains in `02_03`; rag-pipeline-mcp's audit-log status is explicitly confirmed (not left as an open discrepancy).

## Testing Expectations
Not required (documentation-only). Manually verify actual audit-log call sites via `grep -rn "_audit_log" scripts/mcp_servers/` before finalizing.

## Documentation Impact
Both files updated; `06_07` established as canonical for audit-log coverage.

## Out of Scope
Do not change actual audit-logging source code in this issue — documentation only.

## AI Implementation Instruction
Verify audit-log call sites directly via grep across `scripts/mcp_servers/` rather than trusting either file's existing claim — both may be stale relative to current source.

## Traceability
- Workflow phase: issue-creation
- Source: docs_review_mcp.md §1 (全体評価 item 5), §2 削除候補 item 4, §6A (監査ログ記述の矛盾), §6B (rag-pipeline-mcpの監査ログ有無)
- Generated at: 2026-08-02
