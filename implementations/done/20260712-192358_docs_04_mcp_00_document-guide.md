# Implementation Procedure: docs/04_mcp_00_document-guide.md

Source plan: `plans/20260712-191723_plan.md`
Source requirement: `requires/done/20260712_17_require.md`

## Goal

`docs/04_mcp_00_document-guide.md`'s "Navigation to Major Known Issues" table no longer links
to `MCP-09`, an entry that was resolved and removed from
`docs/04_mcp_90_inconsistencies_and_known_issues.md` back in commit `1c744de9`.

## Scope

**In scope:** the "Navigation to Major Known Issues" table (originally lines 50-55) of
`docs/04_mcp_00_document-guide.md`.

**Out of scope:** every other section of the file (Quick Reference table, Canonical Source
Rules, File Index); `docs/04_mcp_90_inconsistencies_and_known_issues.md` itself (not touched —
it is already correctly empty and stays that way, per the requirement's explicit note not to
delete it).

## Assumptions

1. No other `docs/*.md` file links to the specific `MCP-09` anchor
   (`#mcp-09-cicd-workflow_allowlist-policy-mismatch--runtimeerror-vs-warning`) — verified via
   `grep -n "MCP-09" docs/*.md` returning no matches after the edit.
2. The remaining row in the same table
   ("mdq-mcpは本番稼働可能（FTS5検索とインデックスが実装済み）" → `04_mcp_04_04_mdq.md`) is
   unrelated to MCP-09 and stays untouched.

## Implementation

### Target file

`docs/04_mcp_00_document-guide.md`

### Procedure

*(This edit was already applied directly during the investigation that produced the source
requirement — see requirement §"AI実装者への注記". This document formalizes it retroactively.)*

1. Removed this row from the "Navigation to Major Known Issues" table:
   ```markdown
   | cicd workflow_allowlistのRuntimeErrorに関する記載の不整合 | [MCP-09](04_mcp_90_inconsistencies_and_known_issues.md#mcp-09-cicd-workflow_allowlist-policy-mismatch--runtimeerror-vs-warning) |
   ```
2. Left the table's header row and the one remaining data row (`mdq-mcpは本番稼働可能...`)
   intact — the table is not emptied, only the stale row is removed.

### Method

Direct Markdown table-row deletion. No table restructuring needed since one valid row
remains.

### Details

- Do not remove the table itself — it still has a legitimate current entry
  (mdq-mcp production-readiness note pointing to `04_mcp_04_04_mdq.md`, a real file with real
  content, not a resolved-issue anchor).
- MCP-09 is not replaced with a resolved-note placeholder (unlike the `UNDOC-02` convention
  used elsewhere) because this table's purpose is pure navigation to *currently open* items —
  a resolved item has nothing left to navigate to.

## Validation Plan

| Check | Command | Expected |
|---|---|---|
| Dangling reference scan | `grep -n "MCP-09" docs/*.md` | no output |
| Docs consistency | `uv run python tools/check_docs_consistency.py` | All checks passed |
| MCP docs consistency | `uv run python tools/check_mcp_docs_consistency.py` | no new warnings (github-mcp count + stale-language warnings pre-exist and are unrelated) |
