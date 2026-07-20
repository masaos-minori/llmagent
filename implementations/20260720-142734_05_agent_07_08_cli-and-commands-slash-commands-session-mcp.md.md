# Implementation procedure: `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` (verify `/mcp tools` description for stale fallback wording)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 6, resolving
part of UNK-04).

Three prior docs target this filename — the two most recent
(`implementations/done/20260719-103155_...` and `20260719-103809_...`) were read in full: both add
new `/session` DB-operations subcommand table rows (`rag-consistency`, `rag-rebuild-fts`), unrelated
to the `/mcp tools` description this plan concerns. This is a new document.

## Goal

Verify the plan's concern ("verify `/mcp tools` description doesn't reference fallback") and edit
only if stale two-tier wording is found.

## Scope

**In scope**: `docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`, the `/mcp tools`
table row (line 66) and its accompanying explanatory sentence (line 71).

**Out of scope**: The rest of the `/session`/`/mcp` command reference table — unaffected.

## Assumptions

1. Direct grep of the current file for `RuntimeToolRegistry|ToolRegistry|フォールバック` around the
   `/mcp tools` entry returns exactly two hits:
   - Line 66: `| \`/mcp tools\` | なし | RuntimeToolRegistryのツール一覧を表示 |`
   - Line 71: "`/mcp tools` は McpToolDiscoveryService によってライブ検出された RuntimeToolRegistry"
     (sentence continues beyond what was captured in the grep excerpt — full line should be re-read
     before concluding).
   Neither hit mentions `ToolRegistry` (the legacy class) or "フォールバック" at all — both describe
   `/mcp tools` purely in terms of `RuntimeToolRegistry`, which is already consistent with the
   sole-authority model this plan establishes.
2. Therefore this file likely requires **no edit** — its `/mcp tools` description was already
   written assuming `RuntimeToolRegistry` is the tool-list source, with no fallback-registry mention
   to remove.

## Implementation

### Target file

`docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md`

### Procedure

1. Re-read line 71 in full (not just the grep-truncated excerpt) to confirm it does not, later in
   the sentence, introduce a `ToolRegistry`-fallback qualifier.
2. If confirmed clean (expected outcome): **no edit**.
3. If line 71's full sentence does mention a fallback qualifier not visible in the excerpt: rewrite
   to remove it, matching the sole-authority phrasing used in the companion `04_mcp_03_01`/
   `04_mcp_03_02` docs.

### Method

Verification pass; conditional single-line edit only if the full-sentence re-read (step 1) surfaces
something the grep excerpt did not show.

### Details

- This item mirrors `04_mcp_08_tool_capability_naming_convention.md`'s companion verify-only doc in
  this same plan phase — both resolve UNK-04's two named files with the same "verify, edit only if
  stale language is found" discipline.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Full-line re-read | `grep -n -A1 "/mcp tools" docs/05_agent_07_08_cli-and-commands-slash-commands-session-mcp.md` | Full sentence at line 71 contains no `ToolRegistry`/fallback qualifier |
| Docs consistency | `uv run check-mcp-docs` | Passes |
