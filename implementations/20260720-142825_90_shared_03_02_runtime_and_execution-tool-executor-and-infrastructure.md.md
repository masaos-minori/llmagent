# Implementation procedure: `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` (rewrite "4a." routing-authority section + `resolve()` signature comment)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 8).

No prior implementation doc targets this filename (content-grep across `implementations/` and
`implementations/done/` for "90_shared_03_02_runtime_and_execution" returns only unrelated hits: a
tool-source doc sweep, plugin-and-tool-runtime doc fix, plugin-documentation removal — none touch
the "4a." routing section this plan concerns). This is a new document.

## Goal

Rewrite the "## 4a. `ToolRegistry` / `route_resolver` / `tool_routing_validation`" section's
responsibility-split bullets and the `ToolRouteResolver`/`resolve()` pseudocode's inline comments so
they describe sole-authority routing, not a two-tier priority/fallback model.

## Scope

**In scope**: `docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`,
section "## 4a." (current lines ~76-123 per direct read), specifically:
- Line 78: "`shared/runtime_tool_registry.py`: **最優先のルーティング権威**。..."
- Line 79: "`shared/tool_registry.py`: **フォールバックのルーティング権威**。..."
- Line 80: "`shared/route_resolver.py`: `ToolRouteResolver` ... **RuntimeToolRegistry が最優先で解決
  され、見つからない場合に ToolRegistry にフォールバックする**"
- Line 118: `runtime_registry: RuntimeToolRegistry | None = None,  # 最優先のルーティング権威` (inline
  comment inside the `ToolRouteResolver.__init__` pseudocode block).
- Line 123: `def resolve(self, tool_name: str) -> str   # RuntimeToolRegistry → ToolRegistry の順で
  解決; 未登録はValueError` (inline comment on the `resolve()` pseudocode signature).

**Out of scope**: The `ToolDefinition`/`ToolRegistry` class pseudocode block itself (lines 82-100) —
its API (`register`, `get_server_for_tool`, `get_tool_names`, etc.) is unchanged by this plan; only
the prose bullets describing its *routing role* change, not its method signatures. The
`validate_routing_against_config`/`validate_routing_against_live`/`validate_all_routing` function
signatures at the end of the section — unchanged (drift-detection functions, out of scope per plan).
Other unrelated content in this file (`is_side_effect()`, `tool_hash_key()` earlier in the file) —
untouched.

## Assumptions

1. Confirmed by direct read: this section's structure is "responsibility split" bullets (lines
   76-80) followed by two pseudocode blocks (`ToolRegistry` class, then `ToolRouteResolver` class)
   and a "Current behavior (Explicit in code)" bullet list (which itself, per direct read, does
   **not** repeat the fallback claim — it only says "`runtime_registry` が設定されている場合、
   `resolve()` で最初に RuntimeToolRegistry が検索される," which remains true and needs no edit,
   since after this plan there is nothing else to search after it, not because there's a priority
   order preserved).
2. `tool_routing_validation.py`'s function signatures (`validate_routing_against_config` etc.,
   listed at the very end of the section) are unaffected — these remain drift-detection-only tools
   querying `ToolRegistry`, matching the plan's explicit "Out of scope: Removing... drift-detection
   functions."

## Implementation

### Target file

`docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md`

### Procedure

1. Rewrite the three responsibility-split bullets (lines 78-80):
   - Line 78 (`shared/runtime_tool_registry.py`): drop "**最優先の**" (top-priority) qualifier —
     state it is simply "the routing authority" (sole, not first-among-several).
   - Line 79 (`shared/tool_registry.py`): change "**フォールバックのルーティング権威**" to
     "drift-detection input" (matching the companion `tool_registry.py` docstring doc's wording) —
     it is not a routing authority of any kind (fallback or otherwise) anymore.
   - Line 80 (`shared/route_resolver.py`): change "**RuntimeToolRegistry が最優先で解決され、見つから
     ない場合に ToolRegistry にフォールバックする**" to state `resolve()` consults only
     `RuntimeToolRegistry`; unresolved tools raise `ValueError` immediately.
2. Update the `ToolRouteResolver.__init__` pseudocode inline comment (line 118):
   `runtime_registry: RuntimeToolRegistry | None = None,  # 最優先のルーティング権威` →
   `runtime_registry: RuntimeToolRegistry | None = None,  # ルーティング権威（唯一の解決元）`.
3. Update the `resolve()` pseudocode inline comment (line 123):
   `def resolve(self, tool_name: str) -> str   # RuntimeToolRegistry → ToolRegistry の順で解決; 未登録
   はValueError` → `def resolve(self, tool_name: str) -> str   # RuntimeToolRegistry のみで解決;
   未登録はValueError`.
4. Also verify the pseudocode block no longer shows a `discovery_map`/`_legacy_registry`-adjacent
   parameter comment implying legacy lookup — cross-check against the companion `route_resolver.py`
   implementation doc's final `__init__` signature before finalizing this doc's pseudocode mirror.
5. Leave the "Current behavior (Explicit in code)" bullet list (below the pseudocode) unchanged per
   Assumption 1, except double-check the bullet about `known_tools`/coverage logging still reads
   correctly against the rewritten `_log_routing_coverage()` (companion doc) — it currently says "本番
   呼び出しは... 存在しない (2026-07時点)" which remains accurate (still no production caller passes
   `known_tools`).

### Method

Prose + pseudocode-comment edits (Japanese prose, English/Japanese-mixed pseudocode comments matching
the file's existing convention). No change to any actual function signature shown in the pseudocode
blocks (parameter names/types/defaults) beyond the inline comment text itself.

### Details

- This file's "4a." section is the most code-adjacent of the 8 docs in this plan phase (it embeds
  a `ToolRouteResolver.__init__`/`resolve()` pseudocode mirror) — after editing, diff it manually
  against the real, post-plan `scripts/shared/route_resolver.py` signature to ensure the pseudocode
  doesn't drift from actual code (a recurring risk this doc's own convention already guards against
  via "Explicit in code" annotations).
- Cross-check against `docs/90_shared_02_02_types_and_protocols-tool-and-execution-dto-part1.md`
  (companion doc, same plan phase) for consistency, per that doc's own note.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Scoped grep | `grep -n "フォールバック\|最優先" docs/90_shared_03_02_runtime_and_execution-tool-executor-and-infrastructure.md` | No output in the "4a." section |
| Docs consistency | `uv run check-mcp-docs` | Passes |
| Pseudocode-vs-code diff | manual comparison of this doc's `ToolRouteResolver` pseudocode vs. `scripts/shared/route_resolver.py` post-edit | Matching parameter list and comment semantics |
| Cross-doc consistency | manual diff against edited `90_shared_02_02` doc | No contradictory routing-authority claims |
