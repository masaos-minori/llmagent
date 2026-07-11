# Implementation Procedure: fix stale server count (docs/04_mcp_02_01_endpoints-and-transport.md)

## Goal

Correct the stale claim "全11サーバー" (all 11 servers) to the accurate "全10サーバー" (all 10
servers), matching the actual number of registered MCP servers.

## Scope

**In-Scope:**
- `docs/04_mcp_02_01_endpoints-and-transport.md` line 33: change
  `全11サーバーがこれらのエンドポイントを公開する。` to
  `全10サーバーがこれらのエンドポイントを公開する。`

**Out-of-Scope:**
- Any other file under `docs/04_mcp_04_01_web-search-file-read-github.md` through
  `..._05_git.md` (hand-written server-catalog docs; confirmed no generator script exists for these,
  so no automated regeneration is needed or possible)
- Any other stale-count reference outside this one confirmed line (a targeted grep was run at
  planning time; see Validation plan below for the same grep to re-run post-fix)
- Any source code change — this is a documentation-only fix

## Assumptions

- `docs/04_mcp_02_01_endpoints-and-transport.md:33` currently reads
  "全11サーバーがこれらのエンドポイントを公開する。" — confirmed present at this exact line by
  direct read during planning.
- The correct count is 10, cross-checked against two independent sources during planning:
  `config/agent.toml`'s `[mcp_servers.*]` sections (`shell, git, web_search, file_delete, file_write,
  file_read, github, cicd, rag_pipeline, mdq` — 10 entries), and `ToolRegistry`'s 10 server_keys
  populated by `_populate_default_registry()`. Both match exactly. The documentation is wrong; the
  implementation (10) is correct.
- This fix is independent of Phase 1-2 (registry code/tests) and can be applied/reviewed separately.

## Implementation

### Target file

`docs/04_mcp_02_01_endpoints-and-transport.md`

### Procedure

1. Open `docs/04_mcp_02_01_endpoints-and-transport.md` and locate line 33.
2. Replace the substring `全11サーバー` with `全10サーバー` in that line, leaving the rest of the
   sentence (`がこれらのエンドポイントを公開する。`/`\`/health\` のレスポンスは...` etc.) unchanged.
3. Re-run the stale-reference grep (see Validation plan) to confirm no other file in `docs/*.md`
   contains a related stale count that was missed.

### Method

Single-line text substitution in a Markdown file. No structural changes, no other content on the line
or in the surrounding paragraph should be touched.

### Details

Before:
```
全11サーバーがこれらのエンドポイントを公開する。`/health` のレスポンスはサーバーごとに異なる（§Server-specific health を参照）。
```

After:
```
全10サーバーがこれらのエンドポイントを公開する。`/health` のレスポンスはサーバーごとに異なる（§Server-specific health を参照）。
```

Notes for the implementer:
- This is a documentation-only change; no code, docstring, or test file is touched by this phase.
- Do not alter the surrounding sentence structure, only the digit and the character count word
  ("11"→"10").

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_docs_consistency.py` | Passes |
| MCP docs check | `uv run check-mcp-docs` | Passes — includes tool count consistency against canonical frozensets |
| Residual stale-reference sweep | `grep -rln "11サーバー\|11 servers\|10個のMCP\|11個のMCP" docs/*.md` | Only file(s) already fixed should match, or zero matches; treat any additional unexpected hit as a follow-up rather than blocking this phase |
