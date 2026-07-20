# Implementation procedure: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md` (verify "Implementation status" callout for stale fallback wording)

Source plan: `plans/done/20260720-134821_plan.md`, Implementation step Phase 3 (item 3, Low priority).

Prior doc `implementations/done/20260718-101441_04_mcp_03_06_tool-runtime-availability-metadata.md`
is this file's original creation doc (requirement 19: `config_dependent`/`enabled`/`disabled_reason`
metadata spec) — read in full, confirmed it does not address today's routing-authority wording since
`RuntimeToolRegistry` wiring was, at that time, itself only partially landed. This is a new document.

## Goal

Verify whether the "Implementation status" callout (current line 22) implies a still-existing
`ToolRegistry` fallback; edit only if it does. Per the plan's own Affected Areas note, this is a Low
blast-radius, verify-first item — not a guaranteed edit.

## Scope

**In scope**: `docs/04_mcp_03_06_tool-runtime-availability-metadata.md`, line 22 (the blockquote
"Implementation status" callout) only.

**Out of scope**: The rest of the file (`config_dependent`/`enabled`/`disabled_reason` contract
sections 1-3+) — unrelated to routing-authority fallback language; not touched.

## Assumptions

1. Full read of line 22 (current text, confirmed by direct read):
   > **Implementation status:** As of 2026-07-20 `config_dependent` is adopted for browser-mcp
   > `browser_fetch` tool. `enabled`/`disabled_reason` fields are not yet implemented in MCP server
   > responses. RuntimeToolRegistry wiring is complete — see `04_mcp_03_01_dispatch-and-routing.md`
   > for details.
   This sentence does **not** itself assert a two-tier fallback model — it says "RuntimeToolRegistry
   wiring is complete" and defers to `04_mcp_03_01` for routing details. It contains no "フォール
   バック"/"priority" wording of its own.
2. Therefore, per the plan's own conditional phrasing ("if it implies fallback still exists"), this
   line likely needs **no edit** — its only routing-relevant claim is a cross-reference, and the
   cross-referenced document (`04_mcp_03_01_dispatch-and-routing.md`) is the one being corrected
   directly (see companion doc). Confirm this conclusion holds after that companion doc's edit lands
   (a cross-reference to a now-corrected doc requires no change on this side).

## Implementation

### Target file

`docs/04_mcp_03_06_tool-runtime-availability-metadata.md`

### Procedure

1. Re-read line 22 after `docs/04_mcp_03_01_dispatch-and-routing.md`'s edit lands (companion doc in
   this same plan phase).
2. If line 22 still reads as above (a pure cross-reference, no embedded fallback claim): make **no
   edit** to this file. Record the verification outcome (e.g., in the implementation PR description)
   rather than editing prose that isn't wrong.
3. If, on re-read, "RuntimeToolRegistry wiring is complete" is judged ambiguous (could be misread as
   "wiring complete" meaning "the fallback wiring is complete," i.e. still implying two tiers exist):
   optionally strengthen to "RuntimeToolRegistry is the sole routing authority; wiring is complete"
   — this is a judgment call, not a mandatory edit.

### Method

Verification pass; conditional single-sentence edit only if judged necessary. No other content in
this file changes.

### Details

- This item mirrors the pattern already used for a sibling verify-only item in this same plan phase
  (see the `04_mcp_08_tool_capability_naming_convention.md` doc, which similarly concludes "likely no
  change" after a full grep found no relevant language) — both follow the plan's own explicit
  "verify, edit only if stale language is found" instruction rather than forcing an edit where none
  is warranted.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Content check | `grep -n "フォールバック\|priority\|優先" docs/04_mcp_03_06_tool-runtime-availability-metadata.md` | No output before or after — confirms no edit was actually required |
| Docs consistency | `uv run check-mcp-docs` | Passes |
| Cross-reference sanity | manual read of `04_mcp_03_01_dispatch-and-routing.md`'s post-edit routing section | Consistent with this file's "wiring is complete" claim (no contradiction) |
