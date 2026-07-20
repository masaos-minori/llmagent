# Implementation procedure: `docs/04_mcp_08_tool_capability_naming_convention.md` (verify UNK-04 — likely no change)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 4, resolving
UNK-04).

Prior docs `implementations/done/20260718-084628_tool_capability_naming_convention.md` and
`implementations/done/20260718-084819_mcp_tool_discovery.py.md` both target this filename/topic but
for the file's original creation (capability naming convention itself) — read (headers), confirmed
unrelated to routing-authority/fallback wording. This is a new document.

## Goal

Resolve the plan's UNK-04: confirm whether this doc needs any routing-authority-fallback language
correction. The plan itself already notes a grep for `RuntimeToolRegistry`/`ToolRouteResolver`/
`fallback`/routing-authority language returned zero matches, and defaults to "likely no change
needed" pending a full read.

## Scope

**In scope**: A full read of `docs/04_mcp_08_tool_capability_naming_convention.md` to confirm the
plan's zero-match grep result and make the final judgment call.

**Out of scope**: The file's actual capability-naming-convention content (domain/action prefixes,
worked examples) — entirely unrelated subject matter, not touched regardless of this item's outcome.

## Assumptions

1. Direct grep of the current file for `RuntimeToolRegistry|ToolRegistry|フォールバック|routing`
   confirms only two hits, both cross-references to `04_mcp_03_02_tool-registry.md` describing that
   *other* document's ownership/routing role (line 23: "関連: ... ToolRegistry の所有権・ルーティング
   の役割について説明している（本ドキュメントのケイパビリティ命名規則とは異なる）" and a matching
   line 96 in a "Related" list) — both explicitly disclaim that this doc's own subject (capability
   naming) is *different from* `ToolRegistry`'s routing role, i.e., these are correctly-scoped
   cross-references, not stale claims about the two-tier model.
2. No sentence in this file makes any first-party assertion about `ToolRegistry`/`RuntimeToolRegistry`
   priority, fallback, or resolution order — the file simply points readers elsewhere for that topic.

## Implementation

### Target file

`docs/04_mcp_08_tool_capability_naming_convention.md`

### Procedure

1. Confirm via `grep -n "RuntimeToolRegistry\|ToolRegistry\|フォールバック\|routing"
   docs/04_mcp_08_tool_capability_naming_convention.md` that only the two cross-reference lines
   (23, 96) exist, and that neither makes a routing-authority claim of its own.
2. **No edit** — both cross-reference lines remain accurate regardless of how
   `04_mcp_03_02_tool-registry.md`'s content changes, since they only point to that other file by
   name/topic, without repeating its (now-corrected) routing-priority claims inline.
3. If a future re-grep after `04_mcp_03_02_tool-registry.md`'s edit reveals either cross-reference
   line was quoting stale wording verbatim (it is not, per Assumption 1) — this would be the only
   trigger for an actual edit here.

### Method

Verification-only; no production or doc edit performed under this item, per the plan's own recorded
default ("Non-blocking: mark as 'verify relevance during implementation; likely no change needed'").

### Details

- This confirms UNK-04 exactly as the plan anticipated: "grep found no routing-authority language
  — likely no change needed." This document is that verification, made concrete and traceable.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Confirm no first-party routing claims | `grep -n "RuntimeToolRegistry\|ToolRegistry\|フォールバック" docs/04_mcp_08_tool_capability_naming_convention.md` | Only lines 23 and 96, both scoped cross-references disclaiming overlap with this doc's own topic |
| Docs consistency | `uv run check-mcp-docs` | Passes (this file was never a source of the routing-authority-language check's findings) |
