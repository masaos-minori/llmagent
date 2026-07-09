# Implementation Procedure: 90 Shared/DB Set Split and Normalization

## Goal

Split oversized Shared/DB documentation files at H2 boundaries and apply normalization (Front Matter, Keywords, Related Documents sections) to all Shared/DB documentation files.

## Scope

### In scope

- Split `90_shared_01`, `90_shared_02`, `90_shared_03`, `90_shared_04`, `90_shared_05` at H2 boundaries (further split at H3 if needed)
- Normalize `90_shared_00`, `90_shared_90` (add Front Matter, Keywords, Related Documents)
- Update File Index/AI Query Routing Table in `90_shared_00_document-guide.md` to reflect new file structure

### Out of scope

- Content modification beyond splitting and adding metadata sections
- Modifying source code or scripts
- Creating new content beyond what exists in original files

## Assumptions

1. Each Shared/DB file has exactly one H1 heading (verified previously).
2. The naming convention follows `<prefix>_<NN>_<slug>.md` format as defined in memo2.md.
3. Files will be split at H2 heading boundaries where possible.
4. No file should exceed 8KB after splitting.
5. Existing internal links point to real files; no broken links exist currently.

## Implementation

### Target files

| Original File | Action | Resulting Files |
|---|---|---|
| `90_shared_01_overview.md` (8KB+) | Split at H2/H3 | Multiple files based on shared infrastructure sections |
| `90_shared_02_types_and_protocols.md` (8KB+) | Split at H2/H3 | Multiple files based on types/protocols sections |
| `90_shared_03_runtime_and_execution.md` (8KB+) | Split at H2/H3 | Multiple files based on runtime/execution sections |
| `90_shared_04_db_architecture_and_schema.md` (8KB+) | Split at H2/H3 | Multiple files based on DB architecture sections |
| `90_shared_05_db_api_and_operations.md` (8KB+) | Split at H2/H3 | Multiple files based on DB operations sections |
| `90_shared_00_document-guide.md` | Normalize + update | Same filename (modified) |
| `90_shared_90_inconsistencies_and_known_issues.md` | Normalize only | Same filename (modified) |

### Procedure

#### Step 1: Split oversized Shared/DB files at H2 boundaries

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

#### Step 2: Normalize non-split Shared/DB files

For `90_shared_00_document-guide.md` and `90_shared_90_inconsistencies_and_known_issues.md`:

1. Read the full content of each file
2. Add YAML Front Matter at the beginning:
```yaml
---
title: "<Content-representing title>"
category: shared
tags:
  - shared
  - <additional-5-to-20-search-keywords>
related:
  - index.md
  - <other-related-Shared-DB-files>
source:
  - <original-filename-if-split>
---
```
3. Add Related Documents and Keywords sections at the end if not present

#### Step 3: Update `90_shared_00_document-guide.md`

1. After all Shared/DB files are split and renamed, read the updated `90_shared_00_document-guide.md`
2. Update the File Index section to list all new filenames instead of old ones
3. Update the AI Query Routing Table to reference correct file paths
4. Ensure all internal links within this file point to existing files

### Method

- **Splitting**: Use H2 headings (`##`) as primary split points. If an H2 section exceeds 6KB, further split at H3 boundaries. If H3 also exceeds 8KB, split by functional group (feature/API/workflow/procedure/configuration/troubleshooting/examples/reference). As a last resort, use sequential part files (`-part1`, `-part2`).
- **Naming**: Follow `<prefix>_<NN>_<slug>.md` format. For H3 sub-splits, append additional slug after hyphen.
- **Front Matter**: Follow the template defined in the plan. Category must be `shared`.
- **File tail**: Always append `## Related Documents` and `## Keywords` sections after the main content.

### Details

#### Front Matter template for Shared/DB files

```yaml
---
title: "<Content-representing title>"
category: shared
tags:
  - shared
  - <5-20 search keywords specific to this file's content>
related:
  - 90_shared_00_document-guide.md
  - <other-related-Shared-DB-files>
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
| File sizes | `wc -c docs/90_shared_*.md` | All files ≤ 8192 bytes |
| H1 count | `grep -c '^# ' docs/90_shared_*.md` | Exactly 1 per file |
| Front Matter | Verify each file starts with `---` YAML block | All files have it |
| Category value | Verify category = `shared` in all Front Matter | All files correct |
| Related Documents / Keywords | Verify heading presence at file end | All files have them |
| Internal links | Verify `[text](*.md)` link targets exist in Shared/DB set | Zero broken links |
| Code blocks/tables | Verify fenced code blocks and tables are not broken across splits | Zero breaks |
| File Index accuracy | Compare File Index against actual files | Matches current state |
| Routing Table accuracy | Compare routing table against actual files | Matches current state |
