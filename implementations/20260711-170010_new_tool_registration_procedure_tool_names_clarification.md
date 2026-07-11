# Docs: tool_names Clarifying Line in New-Tool-Registration Procedure

## Goal

Prevent a maintainer following the new-tool-registration procedure from incorrectly
inferring that `tool_names` must be set for a new tool to become routable, by adding one
explicit clarifying line stating that `tool_names` is optional and validation-only.

## Scope

**In scope:**
- `docs/04_mcp_06_14_new-tool-registration-procedure.md`: one clarifying line.

**Out of scope:**
- No code changes.
- `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md` is a separate target file,
  covered by the sibling doc
  `new_mcp_server_addition_checklist_tool_names_clarification`.

## Assumptions

- `docs/04_mcp_06_14_new-tool-registration-procedure.md` was checked
  (`grep -n "tool_names"`) during the plan's research and does not currently state that
  `tool_names` is optional/non-blocking for routing — confirmed by direct read in the
  plan.
- A new tool becomes routable as soon as it is added to the correct `tool_constants.py`
  frozenset, independent of whether `tool_names` is set in any server's TOML config —
  confirmed by direct read of routing logic elsewhere in the plan's research (out of
  scope for this doc phase to re-verify, treated as given).

## Implementation

### Target file

`docs/04_mcp_06_14_new-tool-registration-procedure.md`

### Procedure

1. Read the file in full (not just `tool_names` grep hits) to confirm no other passage
   already implies `tool_names` is a mandatory step — per the plan's Risks section, this
   re-read is required before inserting the clarifying line, and any conflicting passage
   found must be adjusted so it does not contradict the new line.
2. Insert one clarifying line at an appropriate point in the procedure (e.g. wherever the
   procedure discusses config/TOML updates or registration steps), stating that
   `tool_names` is optional and validation-only.
3. If the existing procedure has a numbered/checklist step structure, prefer adding the
   clarification as a note attached to the relevant step rather than as a disconnected
   standalone paragraph.

### Method

Direct Markdown edit: insert one sentence (as a note, parenthetical, or short paragraph
matching the file's existing style) at the point in the procedure most relevant to
config/`tool_names` handling.

### Details

- Line to add (verbatim, per the plan's Design section): "`tool_names` in the server's
  `[mcp_servers.<key>]` config section is optional and validation-only — a new tool is
  routable as soon as it is added to the correct `tool_constants.py` frozenset, regardless
  of whether `tool_names` is set."
- English only, per `rules/coding.md` conventions applied to docs as well.
- Do not restructure the rest of the procedure; this is a single-line clarifying
  insertion, not a rewrite.
- If the full re-read (step 1 above) surfaces a passage elsewhere in the same file that
  implies `tool_names` IS required, correct that passage in the same edit pass so the
  document is internally consistent (per the plan's Risks mitigation for this exact
  scenario).

## Validation plan

Filtered to checks relevant to this doc:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Docs (MCP-specific) | `uv run check-mcp-docs` | Passes |
| Manual | `grep -n "tool_names" docs/04_mcp_06_14_new-tool-registration-procedure.md` | Confirms the clarifying line is present and no contradictory passage remains |
