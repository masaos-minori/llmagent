# Implementation Procedure: docs/04_mcp_06_15_new-mcp-server-addition-checklist.md

## Goal

- Correct the factual error in the new-MCP-server-addition checklist: the entry-point file is
  named `<name>_server.py`, not the bare `server.py` currently shown.

## Scope

- In scope: `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`, line 20 only (the
  `scripts/mcp_servers/<name>/server.py` reference).
- Out of scope: any other line in this document, any other doc, any source code under
  `scripts/mcp_servers/`.

## Assumptions

- The established, current convention across the codebase is `<name>_server.py` /
  `<name>_tools.py` (confirmed by grep against existing `scripts/mcp_servers/*/`. entries and
  by the sibling fixes already applied in
  `implementations/done/20260722-180209_04_mcp_06_14_new-tool-registration-procedure.md` and
  `implementations/done/20260701-172000_04_mcp_07_tool_schema_export_policy.md`, filenames only
  — contents not read per Step 3 instructions).

## Design decisions

- Pure find-and-replace on the single stale path string; no structural or wording change to
  the surrounding checklist item.
- Keep the checklist item's parenthetical guidance (`MCPServer` inheritance, `dispatch()`
  override) untouched — only the filename token is wrong.

## Alternatives considered

- Rewrite the whole checklist line for clarity: rejected, out of scope and increases diff size
  without fixing an additional defect.
- Leave as-is and file a doc-accuracy issue instead: rejected — this is a simple, unambiguous
  "Documentation fix required" case per `rules/coding.md` §Documentation notes, so fix directly.

## Implementation

### Target file

- `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`

### Procedure

1. Open line 20.
2. Replace `scripts/mcp_servers/<name>/server.py` with
   `scripts/mcp_servers/<name>/<name>_server.py`.
3. Re-grep the file to confirm no bare `server.py`/`tools.py` reference remains.

### Method

- Direct text edit (single-line find-and-replace); no script or codemod needed given the single
  occurrence confirmed by `grep -n "server\.py\|tools\.py" docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`.

### Details

- Current line 20 (verified via grep + limited read, lines 1-35):
  `` - [ ] `scripts/mcp_servers/<name>/server.py`を作成する(`MCPServer`を継承し、`dispatch()`をオーバーライドする) ``
- This is the only `server.py`/`tools.py` occurrence in the file; no other lines are affected.

## Compatibility considerations

- Documentation-only change; no runtime, API, or config compatibility impact.
- Matches the naming convention already reflected in `rules/coding.md` (`MCP server addition`
  row) and in the two sibling docs fixed under the same source plan.

## Security considerations

- N/A — no code, credentials, or executable content involved.

## Rollback considerations

- Single-line diff; revert via `git checkout -- docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`
  or a follow-up commit reverting the one line if the change is found incorrect.

## Validation plan

- `grep -n "server\.py\|tools\.py" docs/04_mcp_06_15_new-mcp-server-addition-checklist.md` —
  expect only the corrected `<name>_server.py` form, no bare `server.py`/`tools.py`.
- `uv run check-mcp-docs` (per `rules/toolchain.md` §MCP documentation consistency) — confirm no
  new broken-link or drift findings introduced by the edit.
- Manual diff review (`git diff docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`) before
  staging.

## Out of scope

- Any change to `docs/04_mcp_06_14_new-tool-registration-procedure.md` or
  `docs/04_mcp_07_tool_schema_export_policy.md` — already implemented (see
  `implementations/done/20260722-180209_04_mcp_06_14_new-tool-registration-procedure.md`,
  `implementations/done/20260722-175125_04_mcp_06_14_new-tool-registration-procedure.md`,
  `implementations/done/20260701-172000_04_mcp_07_tool_schema_export_policy.md`,
  `implementations/done/20260720-085916_04_mcp_07_tool_schema_export_policy.md.md`).
- Any source code change under `scripts/mcp_servers/`.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260804-064703_plan.md
- Source implementation procedure: N/A
- Generated at: 20260805-130043
- Related target files: docs/04_mcp_06_15_new-mcp-server-addition-checklist.md
