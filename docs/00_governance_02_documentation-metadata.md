---
title: "Documentation Metadata"
area: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---

# Documentation Metadata

## Purpose

This document consolidates metadata conventions for AI agents to select relevant documents, terminology glossary, link rules, and markdown syntax rules for the LLM agent design documentation set.

## Existing Metadata Fields

The following five metadata fields should be preserved in all documents:

- **title** — Document title
- **category** — Document category (e.g., overview, deployment, rag, mcp, agent, eventbus, shared-db, governance)
- **tags** — Keywords describing the document content
- **related** — Links to related documents
- **keywords** — Additional search terms for document retrieval

## Recommended Additional Fields

Eight new metadata fields to enhance AI agent document selection:

### 1. scope

Defines the boundary of what the document covers.

- Allowed values: overview, deployment, rag, mcp, agent, eventbus, shared-db, governance
- Example:
```yaml
scope: agent
```

### 2. audience

Intended reader level.

- Allowed values: beginner, intermediate, advanced, developer, operator
- Example:
```yaml
audience: developer
```

### 3. status

Current state of the document.

- Allowed values: stable, draft, deprecated, superseded
- Example:
```yaml
status: stable
```

### 4. priority

Importance level for AI selection.

- Allowed values: critical, high, medium, low
- Example:
```yaml
priority: high
```

### 5. version

Document version number.

- Allowed values: semantic versioning (e.g., 1.0.0, 2.1.3)
- Example:
```yaml
version: 1.0.0
```

### 6. last_updated

Date of last modification.

- Allowed values: ISO 8601 date format (YYYY-MM-DD)
- Example:
```yaml
last_updated: "2026-07-22"
```

### 7. author

Primary author or responsible team.

- Allowed values: Free text, but prefer team names over individuals
- Example:
```yaml
author: agent-team
```

### 8. completeness

How complete the document is relative to its scope.

- Allowed values: complete, partial, outline
- Example:
```yaml
completeness: partial
```

## Front Matter Example

Complete Front Matter block showing both existing and new fields:

```yaml
---
title: Agent Reorganization
area: agent
tags: [architecture, reorganization]
related: [00_governance_01_documentation-policy.md]
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

## Terminology Glossary

| Term | Preferred Form | Alternative Forms | Notes |
|------|---------------|-------------------|-------|
| Constraint | Constraint | constraint | Capitalize when referring to design constraints |
| Decision | Decision | decision | Capitalize when referring to design decision |
| Alternative | Alternative | alternative | Capitalize when referring to considered alternatives |
| Trade-off | Trade-off | tradeoff | Hyphenate as noun; "tradeoff" acceptable as single word |
| Specification | Specification | specification | Capitalize when referring to formal spec document |
| Standardization | Standardization | standardisation | Use American English spelling (z) per project convention |
| Localization | Localization | Localisation | Use American English spelling (z) per project convention |
| Authorization | Authorization | Authorisation | Use American English spelling (or) per project convention |
| Behavior | Behavior | Behaviour | Use American English spelling (or) per project convention |
| Optimize | Optimize | Optimise | Use American English spelling (ze) per project convention |
| Organize | Organize | Organise | Use American English spelling (ze) per project convention |

### Usage Rules

1. **Proper nouns**: Always capitalize CamelCase terms (EventBus, ToolRegistry, WorkflowEngine).
2. **Abbreviations**: Always use uppercase form (MQ, NC, DLQ, ACK, DTO, etc.).
3. **Bilingual text**: Use English preferred form with Japanese alternative in parentheses on first occurrence.
4. **Hyphenation**: Use hyphens for compound adjectives (at-least-once delivery, fail-closed mode).
5. **Plurals**: Plural forms are acceptable when referring to multiple items (Known Issues, Needs Confirmations).
6. **First occurrence**: On first use in a document, include both preferred and alternative forms: "Needs Confirmation (Requires Confirmation)".
7. **Subsequent occurrences**: Use only the preferred form after first definition.

### Contradiction Note

The Terminology Glossary defines "canonical source" in a way that contradicts the Canonical Source Rule document itself. This discrepancy was identified during Task 20 analysis and should be resolved before merging.

## Link Rules

When referencing other documents:

- Use relative paths from the current document's directory
- Include anchor links where applicable (e.g., `#section-name`)
- For cross-area references, use full filenames with path
- For same-area references, use just the filename without extension
- For ADR references, use the ADR number format (ADR-001) rather than the filename

### Link Format Examples

Same area: `[Agent Guide](05_agent_01_system-overview.md)`
Cross area: `[RAG Specification](03_rag_01_system_overview.md)`
ADR: `[ADR-001](adr/ADR-001-workflow-engine-mandatory.md)`
Internal anchor: `[Section](05_agent_01_system-overview.md#workflow-engine)`

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
|----------|-----------|---------|
| Delete | Details verifiable through implementation alone | File paths, line numbers, import structures |
| Compress | Context is needed but details are not | CLI arguments → main options only |
| Replace with Source Reference | Implementation is the sole authority | Schema definition → "Refer to implementation" |
| Retain | Design decisions and intent | Error handling design decisions |
| Move to Known Issues | Discrepancy between implementation and documentation | Inconsistency between docs and code |
| Move to Needs Confirmation | Unknown matters | Unclear implementation intent |

## Related Documents

Cross-cutting documentation rules and policies:

- [Documentation Policy](00_governance_01_documentation-policy.md)
- [Issue and Uncertainty Management](00_governance_03_issue-and-uncertainty-management.md)
- [Documentation Checks](00_governance_04_documentation-checks.md)

## Keywords

metadata
terminology
glossary
link rules
markdown syntax
front matter
evidence labels
