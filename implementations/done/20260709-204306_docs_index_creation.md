# Implementation Procedure: docs/index.md Creation

## Goal

Create a new top-level navigation document (`docs/index.md`) that provides overview, category listing, recommended reading order, and Known Issues links for the entire documentation set.

## Scope

### In scope

- Create `docs/index.md` as the top-level navigation document
- Include documentation overview section
- Include category listing (Overview / Deployment / RAG / MCP / Agent / Event Bus / Shared·DB / Known Issues)
- Include links to each category's `*_00_document-guide.md` equivalent file
- Include recommended reading order
- Maintain `01_overview.md` as system overview index separately (different role from `index.md`)

### Out of scope

- Modifying existing documentation files
- Adding new content beyond navigation structure
- Technical content that belongs in category-specific guides

## Assumptions

1. All category guide files (`*_00_document-guide.md`) will exist after previous steps complete.
2. The category values used in Front Matter match the categories listed here.
3. `01_overview.md` continues to serve as the system overview index (not replaced by `index.md`).
4. The Recommended Reading Order follows a logical progression from overview → deployment → domain-specific → known issues.

## Implementation

### Target file

`docs/index.md` (new file)

### Procedure

#### Step 1: Create index.md structure

1. Create a new file `docs/index.md`
2. Add H1 heading: `# Documentation Overview`
3. Add documentation overview paragraph explaining the purpose of this documentation set

#### Step 2: Add category listing

Add a category listing section with links to each category's guide file:

```markdown
## Categories

- [Overview](01_overview.md) — System overview and architecture
- [Deployment](02_deployment.md) — Environment setup and deployment
- [RAG](03_rag_00_document-guide.md) — Retrieval-Augmented Generation pipeline
- [MCP](04_mcp_00_document-guide.md) — Model Context Protocol servers
- [Agent](05_agent_00_document-guide.md) — Agent system and behavior
- [Event Bus](06_eventbus_00_document-guide.md) — Event Bus infrastructure
- [Shared/DB](90_shared_00_document-guide.md) — Shared infrastructure and database layer
- [Known Issues](05_agent_90_inconsistencies_and_known_issues.md) — Known inconsistencies and issues
```

Note: Adjust category names and descriptions based on actual content after all splitting is complete.

#### Step 3: Add recommended reading order

Add a Recommended Reading Order section:

```markdown
## Recommended Reading Order

1. [System Overview](01_overview.md) — Start here for system context
2. [Deployment Guide](02_deployment.md) — Set up your environment
3. Choose your area of interest:
   - [RAG Pipeline](03_rag_00_document-guide.md)
   - [MCP Servers](04_mcp_00_document-guide.md)
   - [Agent System](05_agent_00_document-guide.md)
   - [Event Bus](06_eventbus_00_document-guide.md)
   - [Shared Infrastructure](90_shared_00_document-guide.md)
4. [Known Issues](05_agent_90_inconsistencies_and_known_issues.md) — Review known issues
```

#### Step 4: Add YAML Front Matter

Add YAML Front Matter at the beginning of the file:

```yaml
---
title: "Documentation Overview"
category: overview
tags:
  - documentation
  - navigation
  - overview
  - index
  - knowledge-base
related:
  - 01_overview.md
  - 02_deployment.md
  - 03_rag_00_document-guide.md
  - 04_mcp_00_document-guide.md
  - 05_agent_00_document-guide.md
  - 06_eventbus_00_document-guide.md
  - 90_shared_00_document-guide.md
---
```

#### Step 5: Add Related Documents and Keywords sections

Add Related Documents and Keywords sections at the end of the file:

```markdown
## Related Documents

- `01_overview.md`
- `02_deployment.md`
- `03_rag_00_document-guide.md`
- `04_mcp_00_document-guide.md`
- `05_agent_00_document-guide.md`
- `06_eventbus_00_document-guide.md`
- `90_shared_00_document-guide.md`

## Keywords

documentation
navigation
overview
index
knowledge-base
```

### Method

- **Structure**: Follow standard Markdown conventions with clear hierarchy (H1 → H2 → H3)
- **Linking**: Use relative links to other Markdown files in the same directory
- **Front Matter**: Follow the template defined in the plan. Category should be `overview`.
- **Content**: Keep descriptions concise and focused on what each category covers

### Details

#### Key design decisions

1. **Role separation**: `index.md` serves as the documentation navigation hub; `01_overview.md` continues to serve as the system overview index. This separation prevents confusion about which document serves which purpose.
2. **Category naming**: Use consistent category names that match the Front Matter `category` field values.
3. **Recommended reading order**: Provide a logical progression that helps users find relevant information quickly while allowing them to jump directly to their area of interest.

## Validation Plan

| Check | Method | Target |
|---|---|---|
| File size | `wc -c docs/index.md` | Reasonable size (< 8KB) |
| H1 count | `grep -c '^# ' docs/index.md` | Exactly 1 H1 |
| Front Matter | Verify file starts with `---` YAML block | Present and valid |
| Category links | Verify all category links point to existing files | Zero broken links |
| Recommended reading order | Verify all links in reading order point to existing files | Zero broken links |
| Known Issues link | Verify Known Issues link points to existing file | Valid target |
| Content completeness | Verify all 8 categories are listed | All present |
