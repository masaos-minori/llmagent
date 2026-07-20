# Implementation procedure: `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` (browser_fetch merge references — verification, no edit)

Source plan: `plans/20260720-135137_plan.md`, Implementation step 11; Affected areas doc-files row
(UNK-04).

No prior implementation doc targets this filename for the browser-merge concern. New document.

## Goal

Verify whether this doc's frozenset-list prose needs updating for the `BROWSER_TOOLS` →
`WEB_SEARCH_TOOLS` fold (per the `tool_constants.py` doc), and record the finding.

## Scope

**In scope**: line 104 (confirmed via direct grep/read) — the only line in this file mentioning
tool-set frozensets by name.
**Out of scope**: the rest of the file's `ToolExecutor`/runtime-registration discussion.

## Assumptions

1. Line 104: "- デフォルト登録は `tool_constants.py` の
   `READ_TOOLS`/`WRITE_TOOLS`/`DELETE_TOOLS`/`RAG_TOOLS`/`CICD_TOOLS`/`MDQ_TOOLS`/`GIT_TOOLS`/
   `SHELL_TOOLS`/`GITHUB_TOOLS`/`WEB_SEARCH_TOOLS` を対応するserver_keyに登録する" — this list
   already includes `WEB_SEARCH_TOOLS` and, notably, **already omits `BROWSER_TOOLS`** (confirmed
   via full-file grep for "BROWSER" — zero matches). This means the doc was already inconsistent
   with the pre-merge code (which does have a separate `BROWSER_TOOLS` frozenset today) — but that
   pre-existing gap is coincidentally resolved *by* this merge, not something this merge newly
   breaks: once `BROWSER_TOOLS` is folded into `WEB_SEARCH_TOOLS` (per the `tool_constants.py` doc),
   this line becomes fully accurate without any edit.

## Implementation

### Target file

`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure

1. Confirm (re-grep at implementation time, after the `tool_constants.py` doc's edit has landed)
   that `BROWSER_TOOLS` no longer exists in code and `browser_fetch` is reachable only via
   `WEB_SEARCH_TOOLS` — at that point, line 104's list is accurate as-is.
2. No text edit required in this file.

### Method

Verification only — this is a case where the merge's *code*-side change (folding `BROWSER_TOOLS`
into `WEB_SEARCH_TOOLS`) makes a previously-stale doc line become accurate, rather than requiring
the doc to be edited to match the code.

### Details

- This is a useful cross-check for the `tool_constants.py` doc's implementer: after that edit
  lands, re-run the scoped grep below to confirm this file's list needed no touch-up, closing the
  loop on this file's Affected-areas entry.

## Validation plan

| Check | Command | Target |
|---|---|---|
| Scoped grep | `grep -n "BROWSER_TOOLS" docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | 0 matches (confirms no stale reference exists before or after the merge) |
| MCP docs consistency | `uv run check-mcp-docs` | passes (this file requires no change to keep passing) |
