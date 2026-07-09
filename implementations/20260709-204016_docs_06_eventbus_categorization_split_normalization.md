# Implementation Procedure: 06 Event Bus Set Formal Categorization, Split and Normalization

## Goal

Formally categorize Event Bus documentation as a top-level category, split oversized files at H2 boundaries, and apply normalization (Front Matter, Keywords, Related Documents sections) to all Event Bus documentation files.

## Scope

### In scope

- Split `06_eventbus_02`, `06_eventbus_05`, `06_eventbus_06` at H2 boundaries (further split at H3 if needed)
- Normalize `06_eventbus_00`, `06_eventbus_01`, `06_eventbus_03`, `06_eventbus_04`, `06_eventbus_90` (add Front Matter, Keywords, Related Documents)
- Position `06_eventbus_00_document-guide.md` as top-level category guide referenced from `docs/index.md`

### Out of scope

- Content modification beyond splitting and adding metadata sections
- Modifying source code or scripts
- Creating new content beyond what exists in original files

## Assumptions

1. Each Event Bus file has exactly one H1 heading (verified previously).
2. The naming convention follows `<prefix>_<NN>_<slug>.md` format as defined in memo2.md.
3. Files will be split at H2 heading boundaries where possible.
4. No file should exceed 8KB after splitting.
5. Existing internal links point to real files; no broken links exist currently.
6. Event Bus is being elevated from undocumented status to formal top-level category.

## Implementation

### Target files

| Original File | Action | Resulting Files |
|---|---|---|
| `06_eventbus_02_http_api_and_runtime.md` (8KB+) | Split at H2/H3 | Multiple files based on HTTP API/runtime sections |
| `06_eventbus_05_configuration_deploy_and_operations.md` (8KB+) | Split at H2/H3 | Multiple files based on configuration topics |
| `06_eventbus_06_reference_api.md` (8KB+) | Split at H2/H3 | Multiple files based on API reference sections |
| `06_eventbus_00_document-guide.md` | Normalize + position as guide | Same filename (modified) |
| `06_eventbus_01_system-overview.md` | Normalize only | Same filename (modified) |
| `06_eventbus_03_persistence_schema_and_replay.md` | Normalize only | Same filename (modified) |
| `06_eventbus_04_dlq_offsets_and_delivery_semantics.md` | Normalize only | Same filename (modified) |
| `06_eventbus_90_inconsistencies_and_known_issues.md` | Normalize only | Same filename (modified) |

### Procedure

#### Step 1: Split oversized Event Bus files at H2 boundaries

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

#### Step 2: Normalize non-split Event Bus files

For `06_eventbus_00_document-guide.md`, `06_eventbus_01_system-overview.md`, `06_eventbus_03_persistence_schema_and_replay.md`, `06_eventbus_04_dlq_offsets_and_delivery_semantics.md`, and `06_eventbus_90_inconsistencies_and_known_issues.md`:

1. Read the full content of each file
2. Add YAML Front Matter at the beginning:
```yaml
---
title: "<Content-representing title>"
category: eventbus
tags:
  - event-bus
  - <additional-5-to-20-search-keywords>
related:
  - index.md
  - <other-related-EventBus-files>
source:
  - <original-filename-if-split>
---
```
3. Add Related Documents and Keywords sections at the end if not present

#### Step 3: Position Event Bus as top-level category

1. After all Event Bus files are normalized, ensure `06_eventbus_00_document-guide.md` serves as the category guide
2. This file should be referenced from `docs/index.md` as the Event Bus category entry point
3. Ensure consistent category value (`eventbus`) is used in all Front Matter blocks

### Method

- **Splitting**: Use H2 headings (`##`) as primary split points. If an H2 section exceeds 6KB, further split at H3 boundaries. If H3 also exceeds 8KB, split by functional group (feature/API/workflow/procedure/configuration/troubleshooting/examples/reference). As a last resort, use sequential part files (`-part1`, `-part2`).
- **Naming**: Follow `<prefix>_<NN>_<slug>.md` format. For H3 sub-splits, append additional slug after hyphen.
- **Front Matter**: Follow the template defined in the plan. Category must be `eventbus`.
- **File tail**: Always append `## Related Documents` and `## Keywords` sections after the main content.

### Details

#### Front Matter template for Event Bus files

```yaml
---
title: "<Content-representing title>"
category: eventbus
tags:
  - event-bus
  - <5-20 search keywords specific to this file's content>
related:
  - 06_eventbus_00_document-guide.md
  - <other-related-EventBus-files>
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
| File sizes | `wc -c docs/06_eventbus_*.md` | All files ≤ 8192 bytes |
| H1 count | `grep -c '^# ' docs/06_eventbus_*.md` | Exactly 1 per file |
| Front Matter | Verify each file starts with `---` YAML block | All files have it |
| Category value | Verify category = `eventbus` in all Front Matter | All files correct |
| Related Documents / Keywords | Verify heading presence at file end | All files have them |
| Internal links | Verify `[text](*.md)` link targets exist in Event Bus set | Zero broken links |
| Code blocks/tables | Verify fenced code blocks and tables are not broken across splits | Zero breaks |
| index.md reference | Verify `docs/index.md` references `06_eventbus_00_document-guide.md` | Present and correct |
