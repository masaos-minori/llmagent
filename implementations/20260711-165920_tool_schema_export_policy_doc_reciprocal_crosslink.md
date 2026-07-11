# Implementation: Add reciprocal cross-link in `04_mcp_07_tool_schema_export_policy.md`

## Goal

Add a reciprocal cross-link from `docs/04_mcp_07_tool_schema_export_policy.md` back to
`docs/04_mcp_03_02_tool-registry.md`, so both documents point at each other and clarify
their distinct roles (schema export policy vs. ownership/routing).

## Scope

**In-Scope:**
- `docs/04_mcp_07_tool_schema_export_policy.md`: add one short cross-link line/paragraph
  referencing `04_mcp_03_02_tool-registry.md` for ToolRegistry's ownership/routing role.

**Out-of-Scope:**
- No other content change to this file — per the plan, this doc already correctly
  documents `TOOL_LIST` as the canonical LLM-visible tool schema source; that content is
  accurate and untouched.
- Any change to `scripts/shared/tool_registry.py` or
  `docs/04_mcp_03_02_tool-registry.md`'s own content (covered by separate implementation
  documents for this plan).
- Fixing the stale `mcp/<name>/tools.py` path references in this doc's "移行履歴"
  (migration history) section (lines 28-36, e.g. `scripts/mcp_servers/git/tools.py`
  listed correctly, but the doc's earlier reference at line 17 uses the older
  `mcp/<name>/tools.py` form) — this is flagged by the plan itself as pre-existing,
  unrelated drift from the `scripts/mcp` → `scripts/mcp_servers` rename, explicitly
  out of scope to avoid scope creep into an already-completed body of work.

## Assumptions

1. The doc is written in Japanese (confirmed by direct read). The added cross-link
   should match this convention.
2. Confirmed by direct read: the doc has a "Related Documents" section near the end
   (currently only listing `04_mcp_00_document-guide.md`) and a YAML frontmatter
   `related:` list (currently only `04_mcp_00_document-guide.md`). Both should gain
   `04_mcp_03_02_tool-registry.md` for consistency with how `04_mcp_03_02_tool-registry.md`
   itself lists its related docs.
3. Per the plan's Design section, the added line's intent is: "See also:
   [04_mcp_03_02_tool-registry.md] for ToolRegistry's ownership/routing role (distinct
   from this doc's schema-export role)." This should be placed in the document body
   (not just the Related Documents list) so a reader scanning the top of the doc
   immediately understands the scope boundary between the two docs.

## Implementation

### Target file

`docs/04_mcp_07_tool_schema_export_policy.md`

### Procedure

1. Read the full current file to confirm exact line numbers for the title/intro
   section (lines 13-17, "正規のエクスポート名: `TOOL_LIST`"), the YAML frontmatter
   `related:` list (lines 9-11), and the "Related Documents" section (lines 44-46).
2. Insert a short cross-link sentence immediately after the intro paragraph (after line
   17, before "### 根拠"), stating that `04_mcp_03_02_tool-registry.md` documents
   `ToolRegistry`'s distinct ownership/routing role, which this document does not cover.
3. Add `04_mcp_03_02_tool-registry.md` to the YAML frontmatter `related:` list.
4. Add `04_mcp_03_02_tool-registry.md` to the "Related Documents" bullet list.

### Method

- Single or small number of targeted Markdown insertions; do not alter the "根拠"
  (Rationale), "移行履歴" (Migration history), or "検証" (Verification) sections.
- Match existing Japanese technical-writing style and Markdown link syntax
  `[text](file.md)`.

### Details

- Suggested inserted sentence (Japanese, adapted from the plan's English draft):
  > "関連: [04_mcp_03_02_tool-registry.md](04_mcp_03_02_tool-registry.md) —
  > ToolRegistry の所有権・ルーティングの役割について説明している（本ドキュメントの
  > スキーマエクスポートの役割とは異なる）。"
- Do not modify the "移行履歴" section's server-by-server list or its stale
  `mcp/<name>/tools.py` reference at line 17 — explicitly out of scope per the plan.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep (cross-link present) | `grep -n "04_mcp_03_02_tool-registry" docs/04_mcp_07_tool_schema_export_policy.md` | At least one match in body, one in frontmatter `related:`, one in "Related Documents" |
| No unrelated changes | `git diff docs/04_mcp_07_tool_schema_export_policy.md` | Only the described insertions appear; "移行履歴", "根拠", "検証" sections unchanged |
