# Implementation Procedure: 04 MCP Set Split and Normalization

## Goal

Split oversized MCP documentation files at H2/H3 boundaries and apply normalization (Front Matter, Keywords, Related Documents sections) to all MCP documentation files.

## Scope

### In scope

- Split `04_mcp_02`, `04_mcp_03`, `04_mcp_04`, `04_mcp_05`, `04_mcp_06` at H2 boundaries (further split at H3 if H2 > 8KB, e.g., Watchdog Behavior, MDQ vs RAG Boundary sections)
- Normalize `04_mcp_00`, `04_mcp_01`, `04_mcp_07`, `04_mcp_90` (add Front Matter, Keywords, Related Documents)
- Update File Index/AI Query Routing Table in `04_mcp_00_document-guide.md` to reflect new file structure

### Out of scope

- Content modification beyond splitting and adding metadata sections
- Modifying source code or scripts
- Creating new content beyond what exists in original files

## Assumptions

1. Each MCP file has exactly one H1 heading (verified previously).
2. The naming convention follows `<prefix>_<NN>_<slug>.md` format as defined in memo2.md.
3. Files will be split at H2 heading boundaries where possible.
4. No file should exceed 8KB after splitting.
5. Existing internal links point to real files; no broken links exist currently.

## Implementation

### Target files

| Original File | Action | Resulting Files |
|---|---|---|
| `04_mcp_02_protocol_and_transport.md` (8KB+) | Split at H2/H3 | Multiple files based on protocol/transport sections |
| `04_mcp_03_routing_lifecycle_and_execution.md` (8KB+) | Split at H2/H3 | Multiple files based on routing/lifecycle sections |
| `04_mcp_04_server_catalog.md` (8KB+) | Split at H2/H3 | Multiple files based on server catalog sections |
| `04_mcp_05_security_and_safety_model.md` (8KB+) | Split at H2/H3 | Multiple files including Watchdog Behavior, MDQ vs RAG Boundary |
| `04_mcp_06_configuration_and_operations.md` (8KB+) | Split at H2/H3 | Multiple files based on configuration topics |
| `04_mcp_00_document-guide.md` | Normalize + update | Same filename (modified) |
| `04_mcp_01_system_overview.md` | Normalize only | Same filename (modified) |
| `04_mcp_07_mcp_status.md` | Normalize only | Same filename (modified) |
| `04_mcp_90_inconsistencies_and_known_issues.md` | Normalize only | Same filename (modified) |

### Procedure

#### Step 1: Split oversized MCP files at H2/H3 boundaries

For each file that exceeds 8KB:

1. Read the full content of the file
2. Identify H2 headings (`##`) that define natural section boundaries
3. Evaluate each H2 section size:
   - If H2 section ≤ 6KB: keep as single file
   - If H2 section > 6KB but ≤ 8KB: keep as single file (acceptable boundary)
   - If H2 section > 8KB: split at H3 boundaries within that H2 section
4. Create new files based on H2/H3 boundaries:
   - For H2-only splits: name as `<prefix>_<NN>_<h2-slug>.md`
   - For H3 sub-splits: name as `<prefix>_<NN>_<h2-slug>-<h3-slug>.md`
5. For each new file:
   - Copy the H1 heading from the original
   - Include the relevant H2 section and its subsections (H3+)
   - Add YAML Front Matter with appropriate title, category, tags, related documents
   - Add Related Documents and Keywords sections at the end
6. Delete original files after verification

#### Step 2: Normalize non-split MCP files

For `04_mcp_00_document-guide.md`, `04_mcp_01_system_overview.md`, `04_mcp_07_mcp_status.md`, and `04_mcp_90_inconsistencies_and_known_issues.md`:

1. Read the full content of each file
2. Add YAML Front Matter at the beginning:
```yaml
---
title: "<Content-representing title>"
category: mcp
tags:
  - mcp
  - <additional-5-to-20-search-keywords>
related:
  - index.md
  - <other-related-MCP-files>
source:
  - <original-filename-if-split>
---
```
3. Add Related Documents and Keywords sections at the end if not present

#### Step 3: Update `04_mcp_00_document-guide.md`

1. After all MCP files are split and renamed, read the updated `04_mcp_00_document-guide.md`
2. Update the File Index section to list all new filenames instead of old ones
3. Update the AI Query Routing Table to reference correct file paths
4. Ensure all internal links within this file point to existing files

### Method

- **Splitting**: Use H2 headings (`##`) as primary split points. If an H2 section exceeds 6KB, further split at H3 boundaries. If H3 also exceeds 8KB, split by functional group (feature/API/workflow/procedure/configuration/troubleshooting/examples/reference). As a last resort, use sequential part files (`-part1`, `-part2`).
- **Naming**: Follow `<prefix>_<NN>_<slug>.md` format. For H3 sub-splits, append additional slug after hyphen.
- **Front Matter**: Follow the template defined in the plan. Category must be `mcp`.
- **File tail**: Always append `## Related Documents` and `## Keywords` sections after the main content.

### Details

#### Front Matter template for MCP files

```yaml
---
title: "<Content-representing title>"
category: mcp
tags:
  - mcp
  - <5-20 search keywords specific to this file's content>
related:
  - 04_mcp_00_document-guide.md
  - <other-related-MCP-files>
source:
  - <original filename if split>
---
```

#### File tail template

```markdown
## Related Documents

- `xxx.md`

## Keywords

keyword
keyword
```

#### Splitting rules

1. Primary unit: H2 headings
2. If H2 > 6KB: re-split at H3 boundaries
3. If H3 > 8KB: split by functional group (feature/API/workflow/procedure/configuration/troubleshooting/examples/reference)
4. Last resort: sequential part files (`-part1`, `-part2`, ...)

## Validation Plan

| Check | Method | Target |
|---|---|---|
| File sizes | `wc -c docs/04_mcp_*.md` | All files ≤ 8192 bytes |
| H1 count | `grep -c '^# ' docs/04_mcp_*.md` | Exactly 1 per file |
| Front Matter | Verify each file starts with `---` YAML block | All files have it |
| Related Documents / Keywords | Verify heading presence at file end | All files have them |
| Internal links | Verify `[text](*.md)` link targets exist in MCP set | Zero broken links |
| Code blocks/tables | Verify fenced code blocks and tables are not broken across splits | Zero breaks |
| File Index accuracy | Compare File Index against actual files | Matches current state |
| Routing Table accuracy | Compare routing table against actual files | Matches current state |
