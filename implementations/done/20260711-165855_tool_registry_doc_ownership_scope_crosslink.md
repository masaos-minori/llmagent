# Implementation: State ToolRegistry's ownership/routing-only scope in `04_mcp_03_02_tool-registry.md`

## Goal

Make `docs/04_mcp_03_02_tool-registry.md` explicitly state that `ToolRegistry`'s
responsibility is tool-to-server ownership and routing only — not a schema registry —
and cross-link `docs/04_mcp_07_tool_schema_export_policy.md` as the canonical source for
LLM-visible tool schemas.

## Scope

**In-Scope:**
- `docs/04_mcp_03_02_tool-registry.md`: add a short paragraph stating ToolRegistry's
  ownership/routing-only scope, noting `ToolDefinition.description`/`input_schema` are
  reserved and unpopulated, and cross-linking to
  `docs/04_mcp_07_tool_schema_export_policy.md`.

**Out-of-Scope:**
- Any change to `scripts/shared/tool_registry.py` (covered by a separate implementation
  document for this plan).
- Any content change to `docs/04_mcp_07_tool_schema_export_policy.md` beyond the
  reciprocal cross-link (covered by a separate implementation document for this plan).
- Restructuring any other section of `04_mcp_03_02_tool-registry.md`.

## Assumptions

1. The doc is written in Japanese (confirmed by direct read — headings, tables, and
   prose are all Japanese). The new paragraph should match this convention for
   consistency with the rest of the document, even though the plan's own Design section
   drafts the added text in English; translate/adapt the added paragraph to Japanese to
   match surrounding style, preserving the technical terms (`ToolRegistry`,
   `ToolDefinition.description`, `input_schema`, `TOOL_LIST`) verbatim.
2. The doc already has a "主要 API" (Main API) section (around line 67-77) showing
   `from shared.tool_registry import get_registry, validate_all_routing` and a
   "ドリフト検証" (Drift verification) section (lines 20-41) listing the three
   validation functions. The new ownership/scope paragraph fits best either immediately
   after the title/intro (before "ドリフト検証") or as a new short subsection near the
   top, so a reader sees the scope statement before the API details.
3. `docs/04_mcp_07_tool_schema_export_policy.md` exists and already documents `TOOL_LIST`
   (per each server's `tools.py`) as the canonical LLM-visible tool schema export name —
   confirmed by direct read. No new content needs inventing there; this phase only adds
   the forward cross-link from `03_02` to `07`.
4. This doc's YAML frontmatter `related:` list (lines 8-13) does not currently include
   `04_mcp_07_tool_schema_export_policy.md`. Per the existing pattern used by other
   `related:` entries in this file, add it there in addition to (not instead of) an
   inline Markdown link in the body paragraph, and also add it to the "Related
   Documents" section near the end of the file (lines 116-122) for consistency with the
   file's existing structure.

## Implementation

### Target file

`docs/04_mcp_03_02_tool-registry.md`

### Procedure

1. Read the full current file to confirm exact line numbers for: the YAML frontmatter
   `related:` list, the title/intro (before "### ドリフト検証"), and the "Related
   Documents" section near the end.
2. Insert a new short paragraph (or subsection) stating:
   - `ToolRegistry`'s responsibility is tool-to-server ownership and routing only.
   - It is not a schema registry: `ToolDefinition.description`/`input_schema` are
     reserved and unpopulated.
   - The canonical, LLM-visible tool schema source is each server's own `TOOL_LIST`
     (link to `04_mcp_07_tool_schema_export_policy.md`).
   Place this immediately after the title (`# Tool Registry: ...`) and before
   "### ドリフト検証", so it establishes scope before the detailed API/behavior
   sections.
3. Add `04_mcp_07_tool_schema_export_policy.md` to the YAML frontmatter `related:` list.
4. Add `04_mcp_07_tool_schema_export_policy.md` to the "Related Documents" bullet list
   near the end of the file.

### Method

- Single or small number of targeted Markdown insertions; do not reorder or rewrite any
  existing section content.
- Match the file's existing Japanese technical-writing style (short declarative
  sentences, code-formatted identifiers in backticks, Markdown link syntax
  `[text](file.md)` for cross-references, consistent with existing links such as the
  `04_mcp_06_11_...` reference at line 35).

### Details

- Exact paragraph content (English source per the plan's Design section, to be adapted
  to Japanese matching file style):
  > "ToolRegistry's responsibility is tool-to-server ownership and routing only. It is
  > not a schema registry: `ToolDefinition.description`/`input_schema` are reserved and
  > unpopulated. The canonical, LLM-visible tool schema source is each server's own
  > `TOOL_LIST` (see
  > [04_mcp_07_tool_schema_export_policy.md](04_mcp_07_tool_schema_export_policy.md))."
- Do not modify the "ドリフト検証" table's function names in this phase — the source
  drift-detection docstring in `tool_registry.py` is fixed in a separate implementation
  document; this doc already correctly lists
  `validate_routing_against_config`/`validate_routing_against_live`/`validate_all_routing`.
- Do not touch the "新しいツールの追加" (Adding a new tool), "検証" (Verification),
  "主要 API" (Main API), "キャッシュの挙動" (Cache behavior), "並行数制限"
  (Concurrency limits), or "副作用検出" (Side-effect detection) sections.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Docs consistency | `uv run python tools/check_docs_consistency.py` | Passes |
| Manual grep (cross-link present) | `grep -n "04_mcp_07_tool_schema_export_policy" docs/04_mcp_03_02_tool-registry.md` | At least one match in body, one in frontmatter `related:`, one in "Related Documents" |
| Manual read | Visual review of inserted paragraph placement | Paragraph appears before "### ドリフト検証", matches surrounding Japanese style |
| No unrelated changes | `git diff docs/04_mcp_03_02_tool-registry.md` | Only the described insertions appear; no other section altered |
