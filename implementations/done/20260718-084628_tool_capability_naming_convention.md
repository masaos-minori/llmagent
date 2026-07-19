# Implementation procedure: `docs/04_mcp_08_tool_capability_naming_convention.md` (new doc)

Source plan: `plans/20260717-131133_plan.md` ("Define MCP tool capability naming convention",
requirement `requires/20260717_13_require.md`), Implementation steps 1-2.

## Goal

Publish a new documentation file that defines an optional `domain.action`-style capability naming
convention for MCP tools (e.g. `filesystem.read`, `git.write`, `github.issue.write`), covering domain
prefixes, action suffixes (with an explicit read/write/delete/admin distinction), support for multiple
capabilities per tool, and worked examples. This requirement defines the convention only — it does not
mandate applying it to any existing tool's `TOOL_LIST` entry, and does not build any consumer
(policy/grouping/filter) that reads capability strings.

## Scope

**In scope**
- One new file: `docs/04_mcp_08_tool_capability_naming_convention.md`.
- Cross-reference additions to `docs/04_mcp_00_document-guide.md` (Reading Order stays `01→02→03→04→05→06→90`
  unchanged in spirit, but the File Index table and AI Query Routing Table gain one row each for `04_mcp_08`,
  and the `related:` front-matter lists on both `04_mcp_00_document-guide.md` and the new file cross-link
  each other), so the new doc is discoverable via the existing routing table, consistent with how
  `04_mcp_07_tool_schema_export_policy.md` was wired in.

**Out of scope**
- Editing any `mcp_servers/*/tools.py` `TOOL_LIST` entry to add a real capability string — deferred per the
  plan's own Out-of-scope section (requirement 13's own follow-on, not this step).
- Any policy/grouping/discoverability feature consuming capability strings (e.g. a
  `/mcp tools --capability filesystem.write` filter).
- `scripts/shared/runtime_tool.py` and `scripts/agent/services/mcp_tool_discovery.py` changes — tracked by
  separate implementation docs (`20260718-*_runtime_tool.py.md`, `20260718-*_mcp_tool_discovery.py.md`,
  written alongside this one).

## Assumptions

1. **Resolves the plan's only Unknown** ("exact target filename/number for the new doc"): confirmed via
   `ls docs/ | grep '^04_mcp_'` — the current sequence runs `04_mcp_00` through `04_mcp_07` (specifically
   `04_mcp_07_tool_schema_export_policy.md`, the highest numbered non-reserved section) plus the reserved
   `04_mcp_90_inconsistencies_and_known_issues.md` tail slot. No `04_mcp_08_*` file exists yet. This
   convention doc is a new, standalone top-level section (not a sub-split of an existing section, since it
   is not itself about tool-schema *export naming* — `04_mcp_07`'s subject — but about a distinct,
   optional per-tool *capability* metadata convention). Resolution: **`04_mcp_08_tool_capability_naming_convention.md`**.
2. The requirement's own stated path `docs/tool_capabilities.md` (flat, unnumbered) does not match this
   repo's established `04_mcp_NN_description.md` numbered-section convention (per the plan's Assumption 1,
   confirmed directly via `ls docs/`) — this doc is written at the corrected, convention-following path
   instead, matching how test-file path mismatches were handled elsewhere in this same batch (e.g.
   `implementations/20260718-084145_test_mcp_tool_discovery.py.md`'s flat-vs-nested correction).
3. Front-matter style mirrors `04_mcp_07_tool_schema_export_policy.md`'s YAML block (`title`, `category:
   mcp`, `tags:`, `related:`) and its bilingual convention (Japanese prose body, matching every other
   `04_mcp_*` file inspected: `04_mcp_00`, `04_mcp_07`). This new doc follows the same body-language
   convention for consistency with its sibling section files.
4. This doc is pure content — it does not itself change `RuntimeTool` or `mcp_tool_discovery.py`; those are
   separate implementation docs (per Scope) that this convention doc is a design prerequisite for (the
   `capabilities` field's *values* are meaningless without this convention defined first, but the field's
   *existence* — an opaque `tuple[str, ...]` — does not require this doc to compile/typecheck).

## Implementation

### Target file

`docs/04_mcp_08_tool_capability_naming_convention.md` (new).
Secondary edit: `docs/04_mcp_00_document-guide.md` (add cross-reference rows/related-list entries only).

### Procedure

1. Create `docs/04_mcp_08_tool_capability_naming_convention.md` with YAML front-matter:
   `title: "MCP Tool Capability Naming Convention"`, `category: mcp`,
   `tags: [mcp, tool-schema, capabilities, policy]`,
   `related: [04_mcp_00_document-guide.md, 04_mcp_03_02_tool-registry.md, 04_mcp_07_tool_schema_export_policy.md]`.
2. Body sections (Japanese prose, per Assumption 3), in this order:
   a. **概要 (Overview)** — states this is an *optional*, additive convention; no existing tool is required
      to adopt it; discovery tolerates its absence (cross-reference to the `mcp_tool_discovery.py` doc).
   b. **命名規則 (Naming rule)** — `{domain}.{action}` or `{domain}.{subdomain}.{action}` (3-part form, per
      the `github.issue.write` example), all-lowercase, dot-separated, no spaces/underscores within a
      segment. State this is regex-describable as roughly `^[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+$` for
      documentation purposes only — **no runtime regex validation is added anywhere by this requirement**
      (this doc defines the shape convention; it does not mandate a validator).
   c. **ドメイン (Domains)** — logical resource areas, not necessarily 1:1 with MCP server names:
      `filesystem`, `git`, `github`, `process`, `search`, and any future domain — explicitly state the list
      is open/extensible, not a closed enum.
   d. **アクション (Actions) と read/write/delete/admin の区別** — small extensible vocabulary anchored on
      `read`, `write`, `delete`, `execute` (process/shell-like actions), plus domain-specific verbs where a
      generic verb is insufficiently precise (e.g. `github.issue.write` rather than a bare `github.write`).
   e. **複数キャパビリティ (Multiple capabilities per tool)** — a tool may declare more than one capability
      (e.g. a tool that both reads and triggers a side effect); state this is why the corresponding
      `RuntimeTool` field is `tuple[str, ...]`, not a single string (cross-reference the `runtime_tool.py`
      doc without duplicating its content).
   f. **具体例 (Worked examples)** — reproduce, verbatim, the requirement's example list: `filesystem.read`,
      `filesystem.write`, `filesystem.delete`, `git.read`, `git.write`, `github.issue.write`,
      `process.execute`, `search.web`.
   g. **ステータス (Status)** — explicit statement that this is a proposed/standard convention not yet
      adopted by any real `TOOL_LIST` entry; adoption is future, separately-scoped work (per the plan's
      Risk #1 mitigation — avoid the doc reading as "already proven in practice").
3. Add a `## Related Documents` and `## Keywords` tail section, mirroring `04_mcp_07`'s own tail structure
   exactly (list of related file names; flat keyword list).
4. Edit `docs/04_mcp_00_document-guide.md`:
   - Add `04_mcp_08_tool_capability_naming_convention.md` to the front-matter `related:` list.
   - Add one row to the **AI Query Routing Table** (after the existing `04_mcp_07` row):
     `| toolのcapability命名規則(domain.action形式)は | \`04_mcp_08\` |`.
   - Add one row to the **File Index** table (after the `04_mcp_07` row):
     `| [04_mcp_08_tool_capability_naming_convention.md](04_mcp_08_tool_capability_naming_convention.md) |
     capability命名規則 |`.
   - Add the new file to the bottom `## Related Documents` list.
   - Leave the `## Reading Order` line (`01 → 02 → 03 → 04 → 05 → 06 → 90`) unchanged — it enumerates
     top-level chapter numbers (`01`-`06`, `90`), and `08` is a sibling of `07` within the same "chapter 04
     family" numbering scheme already used for `04_mcp_07`, not a new top-level chapter; no changes to that
     specific line are implied by adding `04_mcp_08`.

### Method

Pure Markdown content authoring, no code. Mirrors the structure, front-matter shape, and Japanese-prose
convention of the existing `04_mcp_07_tool_schema_export_policy.md` file exactly, so the new doc reads as
part of the same series rather than a stylistic outlier.

### Details

No production code in this doc (documentation-only artifact). Section skeleton to author (headings only,
content per Procedure step 2 above):

```
# MCPツールケイパビリティ命名規則

## 概要
## 命名規則
## ドメイン
## アクションと read/write/delete/admin の区別
## 複数キャパビリティ
## 具体例
## ステータス

## Related Documents
## Keywords
```

## Validation plan

| Check | Tool / Command | Target |
|---|---|---|
| Doc exists at resolved path | `ls docs/04_mcp_08_tool_capability_naming_convention.md` | file present |
| Required sections present | manual review | 概要, 命名規則, ドメイン, アクション/read-write-delete-admin区別, 複数キャパビリティ, 具体例, ステータス all present |
| Worked examples verbatim | manual review | all 8 examples from the requirement (`filesystem.read`, `filesystem.write`, `filesystem.delete`, `git.read`, `git.write`, `github.issue.write`, `process.execute`, `search.web`) appear |
| Cross-reference wiring | manual review of `docs/04_mcp_00_document-guide.md` | new File Index row, new AI Query Routing Table row, `related:` front-matter entries added on both files |
| Automated doc-consistency check | `uv run check-mcp-docs` (per `rules/toolchain.md`) | passes — confirms no broken cross-reference/routing-table drift introduced |
| No source/behavior change | `uv run pytest` | full suite unaffected (docs-only change) |
