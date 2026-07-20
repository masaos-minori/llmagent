# Implementation procedure: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` (rewrite RuntimeToolRegistry fallback line)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 7).

No prior implementation doc targets this filename (content-grep across `implementations/` and
`implementations/done/` for "90_shared_02_02_types_and_protocols" returns only unrelated hits: a
tool-source doc sweep, plugin-documentation removal, and a `CacheEntry` disambiguation doc — none
touch the `RuntimeToolRegistry` bullet this plan concerns). This is a new document.

## Goal

Rewrite the bullet describing `ToolRouteResolver.resolve()`'s fallback behavior so it states
`RuntimeToolRegistry` is the sole routing authority, with no fallback to `ToolRegistry`.

## Scope

**In scope**: `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`, the bullet
(current, ~line 214 by the plan's citation; confirmed present in the "Explicit in code" bullet list
near the end of the `RuntimeToolRegistry` discussion):
> **[Explicit in code]** MCP ディスカバリ（`McpToolDiscoveryService`）がレジストリを実データで投入し、
> `ToolExecutor.set_runtime_registry()` で接続済み。`ToolRouteResolver.resolve()` は
> RuntimeToolRegistry を最優先で解決し、見つからない場合に `ToolRegistry` にフォールバックする

**Out of scope**: The rest of the `RuntimeToolRegistry` interface description in this file (the
`resolve`/`get`/`is_side_effect`/`classify_operation_type`/`apply_policy` signature block, the
Import-layer-design-decision bullets about `Literal["read", "write"]` and plain-primitive
`apply_policy()` parameters) — all unrelated to the routing-authority-count claim, untouched.

## Assumptions

1. Confirmed by direct read: this file's other bullets (KeyError-vs-None distinction, `Literal`
   return type rationale, `apply_policy()` primitive-parameter rationale, `is_side_effect()`
   parallel-duplication note) make no routing-priority claims of their own — only the one bullet
   quoted above needs editing.
2. The bullet's first sentence ("MCP ディスカバリ... で接続済み") remains accurate and unrelated to
   the fallback claim — only the final clause ("見つからない場合に `ToolRegistry` にフォールバック
   する") needs replacement.

## Implementation

### Target file

`docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`

### Procedure

1. Locate the bullet via `grep -n "見つからない場合に" docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`.
2. Replace the final clause "`ToolRouteResolver.resolve()` は RuntimeToolRegistry を最優先で解決し、
   見つからない場合に `ToolRegistry` にフォールバックする" with a sole-authority statement: e.g.
   "`ToolRouteResolver.resolve()` は RuntimeToolRegistry のみを参照して解決する。`ToolRegistry` へ
   のフォールバックは存在しない — 未解決のツール名は即座に `ValueError` となる。"
3. Keep the bullet's first sentence (discovery/wiring) unchanged.

### Method

Single-bullet prose edit (Japanese), no structural change to the surrounding interface listing or
code-signature block.

### Details

- After the edit, this file's description of `ToolRouteResolver.resolve()`'s behavior must exactly
  match the actual post-plan `resolve()` body (see the companion `route_resolver.py` implementation
  doc) — a two-line lookup-then-raise, no legacy branch.
- Cross-check against `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`
  (companion doc, same plan phase) — both files describe the same class from different angles (DTO/
  types doc vs. runtime/execution doc) and must not contradict each other post-edit.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Scoped grep | `grep -n "フォールバック" docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md` | No output |
| Docs consistency | `uv run check-mcp-docs` | Passes |
| Cross-doc consistency | manual diff against edited `90_shared_03_02` doc | No contradictory routing-authority claims |
