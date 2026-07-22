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

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
