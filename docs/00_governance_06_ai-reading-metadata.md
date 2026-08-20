---
title: "AI Reading Metadata"
category: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---
## Purpose

This document defines metadata conventions for AI agents to select relevant documents when reading the design documentation set. It ensures AI agents can efficiently identify and retrieve appropriate documentation based on task context.

## Existing Metadata Fields

The following five metadata fields should be preserved in all documents:

- **title** — Document title
- **category** — Document category (e.g., overview, deployment, rag, mcp, agent, eventbus, shared-db, governance)
- **tags** — Keywords describing the document content
- **related** — Links to related documents
- **keywords** — Additional search terms for document retrieval

## Recommended Additional Fields

Eight new metadata fields to enhance AI agent document selection:

1. **scope** — Defines the boundary of what the document covers
   - Allowed values: overview, deployment, rag, mcp, agent, eventbus, shared-db, governance
   - Example:
     ```yaml
     scope: agent
     ```

2. **audience** — Intended reader level
   - Allowed values: beginner, intermediate, advanced, developer, operator
   - Example:
     ```yaml
     audience: developer
     ```

3. **status** — Current state of the document
   - Allowed values: stable, draft, deprecated, superseded
   - Example:
     ```yaml
     status: stable
     ```

4. **priority** — Importance level for AI selection
   - Allowed values: critical, high, medium, low
   - Example:
     ```yaml
     priority: high
     ```

5. **version** — Document version number
   - Allowed values: semantic versioning (e.g., 1.0.0, 2.1.3)
   - Example:
     ```yaml
     version: 1.0.0
     ```

6. **last_updated** — Date of last modification
   - Allowed values: ISO 8601 date format (YYYY-MM-DD)
   - Example:
     ```yaml
     last_updated: "2026-07-22"
     ```

7. **author** — Primary author or responsible team
   - Allowed values: Free text, but prefer team names over individuals
   - Example:
     ```yaml
     author: agent-team
     ```

8. **completeness** — How complete the document is relative to its scope
   - Allowed values: complete, partial, outline
   - Example:
     ```yaml
     completeness: partial
     ```

## Usage Examples

Complete Front Matter block showing both existing and new fields:

```yaml
---
title: Agent Reorganization
category: agent
tags: [architecture, reorganization]
related: [00_governance_01_documentation-governance.md]
keywords: [agent, architecture, structure]
scope: agent
audience: developer
status: stable
priority: high
version: 1.0.0
last_updated: "2026-07-22"
author: agent-team
completeness: complete
---
```

## Migration Policy

Guidelines for adopting new metadata fields:

- Add new metadata fields only during normal document update cycles
- Do not perform bulk changes to add metadata to all documents at once
- Prioritize adding metadata to documents that are frequently accessed by AI agents
- New documents should include all recommended fields from creation

## Non-Goals

Topics explicitly excluded from this document:

- Defining how AI agents parse or use these metadata fields
- Specifying enforcement mechanisms for metadata compliance
- Defining metadata for non-document assets (code, configuration files)

## Markdown Syntax Rules

### Code Blocks
- Wrap Python code with ```python
- Wrap shell commands with ```bash
- Wrap JSON with ```json

### Tables
- Use English headings for tables
- Include original (English) terminology alongside technical terms where necessary

### Keywords
- Mandatory: Must, Prohibited, Always
- Recommended: Recommended, Should, Avoid
- Optional: Optional, As needed

### Document Boundaries
- Separate sections using `##`
- Do not nest sections within sections
- Clearly separate sections with blank lines

## Guidelines for Recording Information Verifiable via Implementation Reference

Criteria for deciding whether to include implementation details in design documents.

### Information to be Deleted or Compressed Normally
- Implementation details at the file path or line number level
- Detailed module dependency structures or import hierarchies
- Default values of configuration settings (if verifiable in code)
- Enumeration of existing file structures
- Complete references to CLI arguments
- Redundant descriptions of JSON examples
- Full definitions of API schemas

### Information to be Retained
- Design intent and reasons for architectural decisions
- Boundaries and responsibilities between components
- Design decisions regarding error handling
- Design decisions regarding performance
- Design decisions regarding security
- Decisions regarding future extensibility

### Decision Categories

| Category | Condition | Example |
|---|---|---|
| Delete | Details verifiable through implementation alone | File paths, line numbers, import structures |
| Compress | Context is needed but details are not | CLI arguments $\rightarrow$ main options only |
| Replace with Source Reference | Implementation is the sole authority | Schema definition $\rightarrow$ "Refer to implementation" |
| Retain | Design decisions and intent | Error handling design decisions |
| Move to Known Issues | Discrepancy between implementation and documentation | Inconsistency between docs and code |
| Move to Needs Confirmation | Unknown matters | Unclear implementation intent |
