## Goal

Implementation step 6 of `plans/20260717-180307_plan.md` (requirement 19): add a short
cross-reference paragraph inside the existing `## MCPConfig (`cfg.mcp.*`)` section of
`docs/05_agent_08_04_configuration-mcp-approval-obs.md`, pointing readers at the new
`docs/04_mcp_03_06_tool-runtime-availability-metadata.md` file for the RuntimeToolRegistry
consumption model — additive only, not duplicating the full spec on the agent side.

## Scope

**In scope**: insert one short paragraph inside the `## MCPConfig` section of
`docs/05_agent_08_04_configuration-mcp-approval-obs.md` (between its last existing paragraph and
the section-closing `---`), cross-referencing `04_mcp_03_06`.

**Out of scope**: rewriting or restructuring any existing content in this file; documenting the
full `enabled`/`disabled_reason`/RuntimeToolRegistry contract here (it stays single-sourced in
`04_mcp_03_06`, per the plan's Canonical Source Rules note).

## Assumptions

- The file currently documents only `cfg.mcp.*` agent.toml fields (`startup_mode`, `transport`,
  `url`, `cmd`) and has no existing mention of tool availability metadata or
  RuntimeToolRegistry — confirmed by reading the file in full (115 lines). The addition is
  purely additive.
- The repo's existing "Canonical Source Rules" convention (used elsewhere in `docs/04_mcp_00`)
  favors a short cross-reference over duplicating spec content across files — this addition
  follows that pattern.

## Implementation

### Target file

`docs/05_agent_08_04_configuration-mcp-approval-obs.md` (115 lines total, edit in place)

### Procedure

1. Locate the `## MCPConfig (`cfg.mcp.*`)` section: heading at L23, running through its two
   `###` subsections (`### Agent-side MCP fields` at L28, `### Server-local application config`
   at L41), ending with a cross-reference sentence at L59 (`McpServerConfig`のフィールドについ
   ては[04_mcp_06_03_...]を参照。), followed by a section-closing horizontal rule `---` at L61
   (with `## ApprovalConfig` starting at L63).
2. Insert a new short paragraph immediately after L59 and before the L61 `---`, e.g.:
   ```
   ツールの実行時可用性（`config_dependent` / `enabled` / `disabled_reason`）とRuntimeToolRegistry
   での扱いについては[04_mcp_03_06_tool-runtime-availability-metadata.md](../04_mcp_03_06_tool-runtime-availability-metadata.md)
   を参照。
   ```
   (adjust the relative link path to match this repo's actual cross-directory link convention —
   verify whether `docs/05_agent_*.md` files link to `docs/04_mcp_*.md` files with a bare
   filename or a `../` prefix by checking one existing cross-reference in this same file, e.g.
   the `04_mcp_06_03` reference at L59, and mirror its exact link syntax.)
3. Do not touch any other section (`## ApprovalConfig`, `## ObservabilityConfig`, `## Related
   Documents`, `## Keywords`).

### Method

Direct Markdown insertion of one paragraph (with one relative link), no restructuring.

### Details

Existing MCPConfig table (L30-37, unchanged by this step, quoted for anchor context):
```
| Field | Default | Description |
|---|---|---|
| `startup_mode` | `"none"` | `"none"` / `"persistent"` / `"subprocess"` |
| `transport` | 必須 | `TransportType.HTTP`（`"http"`） |
| `url` | 必須 | HTTPサーバのベースURL |
| `cmd` | `[]` | subprocess起動コマンド |
```

"## Related Documents" section (L103-108, unchanged by this step, shown as an alternate
insertion-format reference in case a full new bullet entry there is preferred instead of an
inline paragraph):
```
## Related Documents

- `05_agent_00_document-guide.md`
- `05_agent_08_01_configuration-loading-agent-config-part1.md`
- `05_agent_08_02_configuration-llm-rag.md`
- `05_agent_08_03_configuration-tools-memory.md`
```
If the inline-paragraph approach (Procedure step 2) is judged too disruptive to the section's
prose flow, an equivalent alternative is to add a
`- 04_mcp_03_06_tool-runtime-availability-metadata.md` bullet to this "Related Documents" list
instead — either satisfies the plan's "short cross-reference note ... pointing at the new
`04_mcp_03_06` file" requirement. The inline-paragraph placement is preferred because it sits
directly next to the MCPConfig content it clarifies, rather than only in a generic footer list.

## Validation plan

- `grep -n "04_mcp_03_06" docs/05_agent_08_04_configuration-mcp-approval-obs.md` → expect at
  least 1 match after this step.
- Manual read-through: confirm the new paragraph/bullet is inside or immediately adjacent to the
  `## MCPConfig` section (not accidentally placed inside `## ApprovalConfig` or
  `## ObservabilityConfig`).
- Manual check: confirm the relative link path matches this file's existing cross-reference link
  convention (mirror the L59 `04_mcp_06_03` link's exact syntax) so the link is not broken.
- `uv run check-mcp-docs` — confirm no regression in the real-file consistency checks (this file
  is outside `docs/04_mcp_*`, so most `04_mcp`-specific checks in
  `tools/check_mcp_docs_consistency.py` do not apply to it, but running the full check confirms
  no unintended side effect).
- `git diff docs/05_agent_08_04_configuration-mcp-approval-obs.md` — confirm only the one
  intended addition, no other line changed.
