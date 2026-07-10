# Implementation Procedure: 05 Agent Set Split and Normalization

## Goal

Split oversized Agent documentation files at H2/H3 boundaries and apply normalization (Front Matter, Keywords, Related Documents sections) to all Agent documentation files.

## Scope

### In scope

- Split `05_agent_03`, `05_agent_04`, `05_agent_06`, `05_agent_07`, `05_agent_08`, `05_agent_09`, `05_agent_10`, `05_agent_11`, `05_agent_12` at H2/H3 boundaries (Memory Module Reference requires functional group-based 3-4 splits)
- Normalize `05_agent_00`, `05_agent_01`, `05_agent_02`, `05_agent_05`, `05_agent_13`, `05_agent_90` (add Front Matter, Keywords, Related Documents)
- Update File Index/AI Query Routing Table/Recommended Reading Order in `05_agent_00_document-guide.md` to reflect new file structure
- Update `routing.md` Docs→task mapping to follow new file names

### Out of scope

- Content modification beyond splitting and adding metadata sections
- Modifying source code or scripts
- Creating new content beyond what exists in original files

## Assumptions

1. Each Agent file has exactly one H1 heading (verified previously).
2. The naming convention follows `<prefix>_<NN>_<slug>.md` format as defined in memo2.md.
3. Files will be split at H2 heading boundaries where possible.
4. No file should exceed 8KB after splitting.
5. Existing internal links point to real files; no broken links exist currently.
6. `routing.md` contains fixed path references to `docs/05_agent_*.md` that must be updated after splitting.

## Implementation

### Target files

| Original File | Action | Resulting Files |
|---|---|---|
| `05_agent_03_turn-processing-flow.md` (8KB+) | Split at H2/H3 | Multiple files based on turn processing stages |
| `05_agent_04_state-and-persistence.md` (8KB+) | Split at H2/H3 | Multiple files based on state/persistence sections |
| `05_agent_06_tool-execution-and-approval.md` (8KB+) | Split at H2/H3 | Multiple files based on tool execution stages |
| `05_agent_07_cli-and-commands.md` (8KB+) | Split at H2/H3 | Multiple files based on CLI/command sections |
| `05_agent_08_configuration.md` (8KB+) | Split at H2/H3 | Multiple files based on configuration topics |
| `05_agent_09_data-layer.md` (8KB+) | Split at H2/H3 | Multiple files based on data layer sections |
| `05_agent_10_operations-and-observability.md` (8KB+) | Split at H2/H3 | Multiple files based on operations topics |
| `05_agent_11_extension-points.md` (8KB+) | Split at H2/H3 | Multiple files based on extension points |
| `05_agent_12_memory.md` (8KB+, Memory Module Reference) | Functional group split (3-4 files) | Multiple files by memory module groups |
| `05_agent_00_document-guide.md` | Normalize + update | Same filename (modified) |
| `05_agent_01_system-overview.md` | Normalize only | Same filename (modified) |
| `05_agent_02_runtime-architecture.md` | Normalize only | Same filename (modified) |
| `05_agent_05_llm-and-streaming.md` | Normalize only | Same filename (modified) |
| `05_agent_13_reference-api.md` | Normalize only | Same filename (modified) |
| `05_agent_90_inconsistencies_and_known_issues.md` | Normalize only | Same filename (modified) |

### Procedure

#### Step 1: Split oversized Agent files at H2/H3 boundaries

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

**Special handling for `05_agent_12_memory.md`:**
- Memory Module Reference is large and requires functional group-based splitting
- Split into 3-4 files by memory module categories (e.g., layer, store, retriever, extract, jsonl_store, embedding_client, ingestion, injection)
- Name as `05_agent_12_memory-{layer,store,retriever,extract}.md` or similar functional groupings

#### Step 2: Normalize non-split Agent files

For `05_agent_00_document-guide.md`, `05_agent_01_system-overview.md`, `05_agent_02_runtime-architecture.md`, `05_agent_05_llm-and-streaming.md`, `05_agent_13_reference-api.md`, and `05_agent_90_inconsistencies_and_known_issues.md`:

1. Read the full content of each file
2. Add YAML Front Matter at the beginning:
```yaml
---
title: "<Content-representing title>"
category: agent
tags:
  - agent
  - <additional-5-to-20-search-keywords>
related:
  - index.md
  - <other-related-Agent-files>
source:
  - <original-filename-if-split>
---
```
3. Add Related Documents and Keywords sections at the end if not present

#### Step 3: Update `05_agent_00_document-guide.md`

1. After all Agent files are split and renamed, read the updated `05_agent_00_document-guide.md`
2. Update the File Index section to list all new filenames instead of old ones
3. Update the AI Query Routing Table to reference correct file paths
4. Update the Recommended Reading Order to reference correct file paths
5. Ensure all internal links within this file point to existing files

#### Step 4: Update `routing.md`

1. Read the full content of `routing.md`
2. Find all references to `docs/05_agent_*.md` in the Docs→task mapping section
3. Update each reference to point to the new file names after splitting
4. Ensure no broken references remain in `routing.md`

### Method

- **Splitting**: Use H2 headings (`##`) as primary split points. If an H2 section exceeds 6KB, further split at H3 boundaries. If H3 also exceeds 8KB, split by functional group (feature/API/workflow/procedure/configuration/troubleshooting/examples/reference). As a last resort, use sequential part files (`-part1`, `-part2`).
- **Naming**: Follow `<prefix>_<NN>_<slug>.md` format. For H3 sub-splits, append additional slug after hyphen.
- **Front Matter**: Follow the template defined in the plan. Category must be `agent`.
- **File tail**: Always append `## Related Documents` and `## Keywords` sections after the main content.

### Details

#### Front Matter template for Agent files

```yaml
---
title: "<Content-representing title>"
category: agent
tags:
  - agent
  - <5-20 search keywords specific to this file's content>
related:
  - 05_agent_00_document-guide.md
  - <other-related-Agent-files>
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
| File sizes | `wc -c docs/05_agent_*.md` | All files ≤ 8192 bytes |
| H1 count | `grep -c '^# ' docs/05_agent_*.md` | Exactly 1 per file |
| Front Matter | Verify each file starts with `---` YAML block | All files have it |
| Related Documents / Keywords | Verify heading presence at file end | All files have them |
| Internal links | Verify `[text](*.md)` link targets exist in Agent set | Zero broken links |
| Code blocks/tables | Verify fenced code blocks and tables are not broken across splits | Zero breaks |
| File Index accuracy | Compare File Index against actual files | Matches current state |
| Routing Table accuracy | Compare routing table against actual files | Matches current state |
| Recommended Reading Order accuracy | Compare against actual files | Matches current state |
| routing.md references | Verify all `docs/05_agent_*` references are valid | Zero broken references |
