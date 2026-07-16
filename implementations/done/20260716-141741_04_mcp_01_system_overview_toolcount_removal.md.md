# Implementation: docs/04_mcp_01_system_overview.md (remove global MCP server/tool total-count sentence)

Source plan: `plans/20260716-135355_plan.md`

## Goal

Remove the "10個のMCPサーバ、合計65個のtool" global total-count sentence
and replace it with a pointer to the two canonical, live sources of truth
(`config/agent.toml`'s `[mcp_servers.*]` sections and
`shared/tool_constants.py`'s frozensets) instead of a literal number — the
sentence was already stale (documents "65個" against the registry's actual
current total) and drifts every time a tool is added/removed anywhere.

## Scope

**In:**
- Line 30: `- 10個のMCPサーバ、合計65個のtool（すべて \`tool_constants.py\` のfrozensetで管理され、\`ToolRegistry\` 経由で登録される）`

**Out:**
- Any other line/section of this doc.
- No change to `config/agent.toml` or `shared/tool_constants.py` themselves
  — only the doc sentence referencing them changes.

## Assumptions

1. `config/agent.toml` has exactly 10 `[mcp_servers.*]` table headers today
   (per the source plan's Assumption 6), confirming this doc line was
   already stale ("65個" vs. the registry's actual different total per
   `tests/test_tool_registry_counts.py`) even before this removal — this
   is further evidence for removal, not merely a style preference.
2. The replacement sentence must not introduce a new number in place of
   the old one — per the source plan's Design section, point to the two
   live sources (`config/agent.toml`, `tool_constants.py`) by name, not by
   count.

## Implementation

### Target file

`docs/04_mcp_01_system_overview.md`

### Procedure

1. Open `docs/04_mcp_01_system_overview.md`.
2. Locate line 30:
   ```
   - 10個のMCPサーバ、合計65個のtool（すべて `tool_constants.py` のfrozensetで管理され、`ToolRegistry` 経由で登録される）
   ```
3. Replace with (per the source plan's Design section, verbatim):
   ```
   - MCPサーバは `config/agent.toml` の `[mcp_servers.*]` に定義され、各サーバが提供するtoolは `tool_constants.py` のfrozensetで管理され、`ToolRegistry` 経由で登録される
   ```

### Method

Single-line sentence replacement — no structural change to the
surrounding list or section.

### Details

- Do not add any numeric total (server count or tool count) anywhere in
  the replacement sentence — the entire point of this change is to remove
  the drift-prone literal.
- Preserve the bullet-list `-` prefix and the sentence's position within
  its surrounding list.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Sentence removed/replaced | `grep -n "65個\|10個のMCPサーバ" docs/04_mcp_01_system_overview.md` | 0 matches |
| Grep sweep (final gate, run after all 6 doc files in this plan are edited) | `rg "ツール（\d+個）\|個のMCPサーバ\|個のtool" docs/` | 0 matches |
