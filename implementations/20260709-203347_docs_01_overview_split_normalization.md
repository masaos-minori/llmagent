# Implementation Procedure: 01 Overview / 02 Deployment Split and Normalization

## Goal

Split oversized files under H2 boundaries and apply normalization (Front Matter, Keywords, Related Documents sections) to overview and deployment documentation.

## Scope

### In scope

- Split `01_overview-arch.md` (12.1KB) into 3 files at H2 boundaries
- Split `01_overview-files.md` (40.5KB) into 6 files at directory-based logical boundaries
- Add Front Matter, Keywords, Related Documents to `01_overview.md`
- Add Front Matter, Keywords, Related Documents to `02_deployment.md`

### Out of scope

- Content modification beyond splitting and adding metadata sections
- Modifying source code or scripts
- Creating new content beyond what exists in original files

## Assumptions

1. All existing internal links point to real files; no broken links exist currently.
2. Each file has exactly one H1 heading (verified previously).
3. The naming convention follows `<prefix>_<NN>_<slug>.md` format as defined in memo2.md.
4. Files will be split at H2 heading boundaries where possible.
5. No file should exceed 8KB after splitting.

## Implementation

### Target files

| Original File | Action | Resulting Files |
|---|---|---|
| `01_overview-arch.md` (12.1KB) | Split at H2 | `01_overview-arch-process.md`, `01_overview-arch-pipelines.md`, `01_overview-arch-features.md` |
| `01_overview-files.md` (40.5KB) | Split at directory boundaries | `01_overview-files-build.md`, `01_overview-files-rag.md`, `01_overview-files-scripts.md`, `01_overview-files-shared.md`, `01_overview-files-config.md`, `01_overview-files-misc.md` |
| `01_overview.md` | Normalize only | Same filename (modified) |
| `02_deployment.md` | Normalize only | Same filename (modified) |

### Procedure

#### Step 1: Split `01_overview-arch.md`

1. Read the full content of `01_overview-arch.md`
2. Identify H2 headings that define natural section boundaries
3. Create three new files based on H2 sections:
   - `01_overview-arch-process.md` — Process architecture section
   - `01_overview-arch-pipelines.md` — Pipeline architecture section
   - `01_overview-arch-features.md` — Feature architecture section
4. For each new file:
   - Copy the H1 heading from the original
   - Include the relevant H2 section and its subsections (H3+)
   - Add YAML Front Matter with appropriate title, category, tags, related documents
   - Add Related Documents and Keywords sections at the end
5. Delete the original `01_overview-arch.md` after verification

#### Step 2: Split `01_overview-files.md`

1. Read the full content of `01_overview-files.md`
2. Identify directory-based logical boundaries within the file
3. Create six new files based on directory groupings:
   - `01_overview-files-build.md` — Build-related content
   - `01_overview-files-rag.md` — RAG-related content
   - `01_overview-files-scripts.md` — Scripts-related content
   - `01_overview-files-shared.md` — Shared infrastructure content
   - `01_overview-files-config.md` — Configuration-related content
   - `01_overview-files-misc.md` — Miscellaneous content
4. For each new file:
   - Copy the H1 heading from the original
   - Include the relevant directory section and its subsections
   - Add YAML Front Matter with appropriate title, category, tags, related documents
   - Add Related Documents and Keywords sections at the end
5. Delete the original `01_overview-files.md` after verification

#### Step 3: Normalize `01_overview.md`

1. Read the full content of `01_overview.md`
2. Add YAML Front Matter at the beginning:
```yaml
---
title: "System Overview"
category: overview
tags:
  - system-overview
  - architecture
  - introduction
related:
  - index.md
source:
  - 01_overview.md
---
```
3. Add Related Documents and Keywords sections at the end if not present

#### Step 4: Normalize `02_deployment.md`

1. Read the full content of `02_deployment.md`
2. Add YAML Front Matter at the beginning:
```yaml
---
title: "Deployment Guide"
category: deployment
tags:
  - deployment
  - environment
  - setup
related:
  - index.md
source:
  - 02_deployment.md
---
```
3. Add Related Documents and Keywords sections at the end if not present

### Method

- **Splitting**: Use H2 headings (`##`) as primary split points. If an H2 section exceeds 6KB, further split at H3 boundaries. If H3 also exceeds 8KB, split by feature/API/workflow/procedure/configuration/troubleshooting/examples/reference groups. As a last resort, use sequential part files (`-part1`, `-part2`).
- **Naming**: Maintain existing hyphenated naming for `01_overview-arch` and `01_overview-files` families. Append descriptive suffixes to indicate content type.
- **Front Matter**: Follow the template defined in the plan. Category values must be one of: `overview`, `deployment`, `rag`, `mcp`, `agent`, `eventbus`, `shared`.
- **File tail**: Always append `## Related Documents` and `## Keywords` sections after the main content.

### Details

#### Front Matter template

```yaml
---
title: "<Content-representing title>"
category: <overview|deployment|rag|mcp|agent|eventbus|shared>
tags:
  - <5-20 search keywords>
related:
  - <related Markdown files>
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
| File sizes | `wc -c docs/*.md` | All files ≤ 8192 bytes |
| H1 count | `grep -c '^# ' docs/*.md` | Exactly 1 per file |
| Front Matter | Verify each file starts with `---` YAML block | All files have it |
| Related Documents / Keywords | Verify heading presence at file end | All files have them |
| Internal links | Verify `[text](*.md)` link targets exist | Zero broken links |
| Code blocks/tables | Verify fenced code blocks and tables are not broken across splits | Zero breaks |
