# Implementation: docs/04_mcp_03_01_dispatch-and-routing.md (add layer-responsibility note)

Source plan: `plans/20260716-123746_plan.md`

Note: this is a distinct change from the `MDQ_TOOLS`-list update covered in
`implementations/20260716-131157_04_mcp_03_01_dispatch-and-routing.md.md`
(source plan `plans/20260716-123031_plan.md`). Both target the same doc
file; apply both — that doc edits the routing table row, this doc adds a
new explanatory paragraph anchored near that same row. Apply the table-row
edit first (it lands with plan 02), then this addition (plan 03), so the
anchor text this doc references already reflects the 7-tool state.

## Goal

Add a short paragraph documenting the single responsibility of each of the
four layers involved in MDQ tool definition (`tools.py`, `server.py`'s
`_DISPATCH_TABLE`, `tool_constants.py`'s `MDQ_TOOLS`, `config/agent.toml`'s
`tool_names`), so future contributors understand why all four must stay in
sync — the guardrail tests in the companion
`tests/test_mdq_tool_layer_consistency.py` doc enforce this at test time;
this doc note explains *why* in prose.

## Scope

**In:**
- Add one new paragraph to `docs/04_mcp_03_01_dispatch-and-routing.md`,
  anchored near the existing `MDQ_TOOLS` table row (line 79, per the source
  plan's Affected areas: "existing MDQ_TOOLS line 79 already present as
  anchor").

**Out:**
- The routing table itself — already updated by the companion doc for plan
  02 (`implementations/20260716-131157_...md`); do not re-edit the table
  row here.
- Any other section of this doc.

## Assumptions

1. This note is purely explanatory (docs-only, no code, no deploy impact)
   per the source plan's Affected areas ("none (docs)").
2. The note should reference all four layers by their concrete
   file/symbol names so a reader can jump directly to each: `tools.py`
   (schema), `server.py::_DISPATCH_TABLE` (runtime dispatch),
   `tool_constants.py::MDQ_TOOLS` (registry population source),
   `config/agent.toml::tool_names` (deployed/active tool allowlist) — this
   exact framing is specified in the source plan's Scope section.

## Implementation

### Target file

`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

1. Open `docs/04_mcp_03_01_dispatch-and-routing.md`.
2. Locate the routing table and its trailing "重要:" note plus code example
   (the block immediately following the table, per the file structure
   already read: table → "重要: 未知のツールは..." note → Python code
   example → `---`).
3. Insert a new paragraph immediately after the existing "重要:" note (and
   its code example), before the next `---` section break, e.g.:
   ```markdown
   **MDQ ツール定義の4層責務:** MDQ (`mdq`) のツール定義は4つの独立したファイル
   に分散しており、それぞれが単一の責務を持つ。いずれか1つを変更する際は、
   他の3つも同期して更新する必要がある（`tests/test_mdq_tool_layer_consistency.py`
   がこの整合性を検証する）。

   | レイヤー | ファイル・シンボル | 責務 |
   |---|---|---|
   | スキーマ定義 | `scripts/mcp_servers/mdq/tools.py::TOOL_LIST` | LLM に公開するツール名・入力スキーマ・ステータス |
   | 実行時ディスパッチ | `scripts/mcp_servers/mdq/server.py::_DISPATCH_TABLE` | ツール名 → ハンドラ関数のマッピング |
   | レジストリ登録 | `scripts/shared/tool_constants.py::MDQ_TOOLS` | `ToolRegistry` にツールを登録するための正典集合 |
   | デプロイ許可リスト | `config/agent.toml` の `[mcp_servers.mdq].tool_names` | 実際に起動・利用可能なツール名の一覧 |
   ```
4. Confirm the new paragraph does not duplicate the existing "重要:" note's
   content (that note is about unknown-tool `ValueError` behavior in
   `ToolRouteResolver`; this new paragraph is about cross-layer consistency
   for MDQ specifically) — keep them as separate, adjacent but distinct
   paragraphs.

### Method

Single new paragraph + small reference table insertion — no changes to
existing prose, tables, or code examples in the file.

### Details

- Keep the note MDQ-specific — do not generalize it to "all MCP servers"
  prose, since the guardrail test itself (companion doc) is MDQ-only per
  the source plan's explicit scope boundary.
- Match this doc's existing heading/bold-label Japanese prose style (e.g.
  "**重要:**").

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Note present | `grep -n "MDQ ツール定義の4層責務\|tool_layer_consistency" docs/04_mcp_03_01_dispatch-and-routing.md` | at least 1 match |
| Doc consistency | `uv run check-mcp-docs` | passes |
| No duplication with existing note | manual read-through of the section after edit | the new paragraph is distinct from the existing "重要:" ValueError note |
