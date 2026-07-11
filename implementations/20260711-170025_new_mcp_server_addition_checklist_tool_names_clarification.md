# Docs: tool_names Clarifying Line in New-MCP-Server Addition Checklist

## Goal

Prevent a maintainer following the new-MCP-server addition checklist from incorrectly
inferring that `tool_names` must be set for the new server's tools to become routable,
by adding one explicit clarifying line stating that `tool_names` is optional and
validation-only.

## Scope

**In scope:**
- `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`: one clarifying line.

**Out of scope:**
- No code changes.
- `docs/04_mcp_06_14_new-tool-registration-procedure.md` is a separate target file,
  covered by the sibling doc
  `new_tool_registration_procedure_tool_names_clarification`.

## Assumptions

- `docs/04_mcp_06_15_new-mcp-server-addition-checklist.md` was checked
  (`grep -n "tool_names"`) during the plan's research and does not currently state that
  `tool_names` is optional/non-blocking for routing — confirmed by direct read in the
  plan.
- A new server's tools become routable independent of whether `tool_names` is populated
  in that server's `[mcp_servers.<key>]` config section, provided the tools are present
  in the correct `tool_constants.py` frozenset — treated as given, per the plan's
  research (out of scope to re-verify in this doc phase).

## Implementation

### Target file

`docs/04_mcp_06_15_new-mcp-server-addition-checklist.md`

### Procedure

1. Read the file in full (not just `tool_names` grep hits) to confirm no other checklist
   item already implies `tool_names` is a mandatory step for routability — per the plan's
   Risks section, this re-read is required before inserting the clarifying line, and any
   conflicting checklist item found must be adjusted so it does not contradict the new
   line.
2. Insert one clarifying line at the checklist item that mentions or implies
   `tool_names`/config population (or, if no such item exists yet, at the config-section
   step of the checklist), stating that `tool_names` is optional and validation-only.
3. Match the file's existing checklist formatting (e.g. `- [ ]` items or numbered list)
   when inserting the note, rather than introducing a different formatting style.

### Method

Direct Markdown edit: insert one sentence (as a note attached to the relevant checklist
item, matching the file's existing style) at the point in the checklist most relevant to
config/`tool_names` handling.

### Details

- Line to add (verbatim, per the plan's Design section): "`tool_names` in the server's
  `[mcp_servers.<key>]` config section is optional and validation-only — a new tool is
  routable as soon as it is added to the correct `tool_constants.py` frozenset, regardless
  of whether `tool_names` is set."
- English only, per `rules/coding.md` conventions applied to docs as well.
- Do not restructure the rest of the checklist; this is a single-line clarifying
  insertion, not a rewrite.
- If the full re-read (step 1 above) surfaces a checklist item elsewhere in the same file
  that implies `tool_names` IS required before a server/tool is usable, correct that item
  in the same edit pass so the document is internally consistent (per the plan's Risks
  mitigation for this exact scenario).

## Validation plan

Filtered to checks relevant to this doc:

| Check | Tool | Target |
|---|---|---|
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
| Docs (MCP-specific) | `uv run check-mcp-docs` | Passes |
| Manual | `grep -n "tool_names" docs/04_mcp_06_15_new-mcp-server-addition-checklist.md` | Confirms the clarifying line is present and no contradictory passage remains |
