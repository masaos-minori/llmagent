# Implementation procedure: `docs/04_mcp_03_01_dispatch-and-routing.md` (rewrite two-tier routing-authority language → sole authority)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 1).

Prior doc `implementations/done/20260716-131157_04_mcp_03_01_dispatch-and-routing.md.md` targets this
same file but for an unrelated edit (trimming the `MDQ_TOOLS` row's tool-name list at line 79) — read
in full, confirmed no overlap with routing-authority wording. This is a new document.

## Goal

Rewrite every place in this file that describes routing as a two-tier "RuntimeToolRegistry
(priority) → ToolRegistry (fallback)" model, so the doc instead states `RuntimeToolRegistry` is the
sole routing authority and `ToolRegistry` is no longer consulted for routing at all.

## Scope

**In scope**: `docs/04_mcp_03_01_dispatch-and-routing.md` — the "ToolRouteResolver" section (current
lines 58-90ish), the "④ レジストリ登録" line inside the ownership-layers diagram (line 129), and the
"ルーティングの信頼できる情報源" section (lines 163-192).

**Out of scope**: The "直列化メカニズムは2つ存在する" section (lines 143-161) — unrelated
two-mechanism discussion (serialization, not routing authority); the dispatch-cache/circuit-breaker
bullets earlier in the file (lines ~50-56) — unrelated to registries.

## Assumptions

1. Full grep of this file for `RuntimeToolRegistry|ToolRegistry|フォールバック|2層構成` (run
   directly against current source) surfaces **more locations than the plan's citation** ("lines
   ~58-70, 129, 165-175"): confirmed hits also at lines 72, 88, 104, 175, 177, 185, 190, 191, and 216
   (a bare `ToolRegistry` docstring-code-block reference near line 156, and `RuntimeToolRegistry` near
   164, inside what appears to be an embedded code/docstring excerpt). All must be reconciled, not
   just the plan's approximate range.
2. Line 185's "MCP ツール定義と所有権に関するフォールバックのルーティング権威" and line 190's table
   row appear to be a **second, separate description block** (possibly a duplicate/near-duplicate
   passage later in the file, distinct from the lines 163-177 block) — verify at implementation time
   whether this is truly a second occurrence needing its own edit, or an artifact of this doc's grep
   matching an embedded quotation; read the surrounding context at that location before editing.

## Implementation

### Target file

`docs/04_mcp_03_01_dispatch-and-routing.md`

### Procedure

1. **"ToolRouteResolver" section (lines 58-90 area)**:
   - Line 60: change "`RuntimeToolRegistry` または `ToolRegistry` を用いて" → "`RuntimeToolRegistry`
     を用いて" (drop "or ToolRegistry").
   - Lines 62-72 (numbered priority list "1. RuntimeToolRegistry（最優先）... 2. ToolRegistry
     （フォールバック）... 3. 未知のツールは即時失敗する"): collapse to a single item describing
     `RuntimeToolRegistry` as the only resolution step, followed by the unknown-tool-fails-immediately
     item (renumber 1→1, drop old item 2 entirely, old item 3 becomes item 2).
   - Line 88: "新しいツールは常に `ToolRegistry` を経由して（`tool_constants.py` の frozenset を
     介して）登録しなければならない" — verify against the current tool-addition procedure: if
     `tool_constants.py` frozensets still seed `ToolRegistry` for drift-detection purposes only (per
     the companion `tool_registry.py` doc), this sentence may still be accurate as a *registration*
     step (not a routing step) — reword only if it implies registration-via-`ToolRegistry` is what
     makes a tool *routable*; it is not, under the new model (only `RuntimeToolRegistry`'s live
     discovery makes a tool routable).
2. **Ownership-layers diagram (line 129)**: change "shared/tool_registry.py +
   shared/runtime_tool_registry.py（RuntimeToolRegistry が最優先、ToolRegistry がフォールバック）" to
   state `RuntimeToolRegistry` alone is the routing registry, with `ToolRegistry`'s role limited to
   drift-detection seed data (parenthetical rewrite, not a structural diagram change).
3. **"ルーティングの信頼できる情報源" section (lines 163-192)**:
   - Line 165: replace "ルーティング権威は2層構成: RuntimeToolRegistry（最優先）→ ToolRegistry
     （フォールバック）。" with a single-authority statement.
   - Table (lines 168-171): remove or relabel the `shared/tool_registry.py` row's "フォールバックの
     ルーティング権威" role description (change to "drift-detection input," matching the companion
     `tool_registry.py` docstring doc's wording) — do not delete the row entirely if the table still
     usefully lists `tool_registry.py` as a drift-detection input.
   - Line 175: "RuntimeToolRegistry は ... ToolRegistry より優先される" → drop the comparison;
     `ToolRegistry` is not a routing candidate to be "preferred over" anymore.
   - Line 177 ("未知のツールは `ValueError` で即時失敗する — フォールバックは存在しない"): already
     correct under the new model — no change needed, but verify it isn't contradicted by nearby edits.
   - Investigate lines 185-191 (per Assumption 2) and apply the same fix if it is a genuine second
     occurrence of the two-tier table.
4. Re-run `uv run check-mcp-docs` after edits — it validates "routing authority language
   consistency" project-wide; this file is likely one of its primary inputs.

### Method

Prose/table edits only, in Japanese (matching the file's existing language), no code blocks changed.
Preserve the file's existing heading structure and table formatting conventions.

### Details

- The plan's own risk section flags this exact file as needing careful, complete treatment (largest
  single "Medium" blast-radius doc). Do not do a partial find-replace of just "フォールバック" as a
  string — some occurrences (e.g., in the "直列化メカニズムは2つ存在する" section, if any incidental
  match exists) are about the *unrelated* serialization-mechanism discussion and must not be touched.
- After editing, `grep -n "フォールバック\|2層構成" docs/04_mcp_03_01_dispatch-and-routing.md`
  restricted to the routing-authority sections should show zero remaining hits in the ToolRouteResolver
  and "ルーティングの信頼できる情報源" sections specifically (the serialization section is out of
  scope and may still legitimately use "フォールバック" to describe execution downgrade behavior,
  which is a different, correct usage of the word — do not remove that one).

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Routing-authority language | `uv run check-mcp-docs` | Passes; no "two-layer"/priority+fallback wording flagged for this file |
| Scoped grep | `grep -n "フォールバック" docs/04_mcp_03_01_dispatch-and-routing.md` | Only hits remaining are in the serialization-mechanism section (lines ~143-161), none in the routing sections |
| Manual read | full re-read of edited sections | Single-authority framing throughout; no contradiction between the ToolRouteResolver section and the "信頼できる情報源" section |
