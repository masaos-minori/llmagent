## Purpose

This document defines cross-cutting rules for maintaining the LLM agent design documentation set. It ensures consistency, traceability, and quality across all area documents by establishing shared conventions for document classification, update procedures, review gates, and change impact analysis.

## Scope

### In scope

The following eight areas are covered by these governance rules:

- Overview
- Deployment
- RAG
- MCP
- Agent
- EventBus
- Shared/DB
- Governance

### Out of scope

The following are explicitly excluded from this document:

- Source code itself (covered by architecture and coding conventions)
- Temporary notes and working drafts
- Personal verification notes
- EventBus/Workflow relationship reorganization
- Document splitting policy changes

## Document Classes

Documents in the design documentation set are classified into seven classes:

- **Governance** — Cross-cutting rules, policies, and standards that apply across areas
- **Guide** — Navigation documents that provide an overview of an area's documentation structure
- **Specification** — Detailed technical specifications describing how components work
- **Reference** — API references, command references, and configuration reference materials
- **Operations** — Operational guidance including monitoring, troubleshooting, and diagnostics
- **Note** — Working notes, investigation results, and temporary documentation
- **Known Issues** — Documents tracking known inconsistencies between documentation and implementation

## Update Rule

When a change occurs, the following documents must be updated based on the change type:

- **Architecture change** — Update Specification documents in the affected area, update Guide documents for cross-area impacts, update Operations documents if operational behavior changes
- **Configuration change** — Update Reference documents for the affected configuration, update Specification documents if behavior changes, update Guide documents if cross-area impacts exist
- **Command change** — Update Command Reference documents, update Guide documents for affected areas, update Known Issues if deprecations occur
- **Behavioral change** — Update Specification documents describing the behavior, update Operations documents if observable behavior changes, update Known Issues if discrepancies are found
- **Documentation-only change** — Update only the affected documents without triggering broader reviews

## Review Rule

The following conditions require review before merging:

- Any change to Governance-class documents
- Any change affecting more than three area documents simultaneously
- Any change that removes or renames a documented feature
- Any change that alters cross-area relationships or dependencies

## Change Impact Rule

To determine which documents are affected by a change:

1. Identify the change category (architecture, configuration, command, behavioral, documentation-only)
2. Map the change to affected areas using the area dependency graph
3. List all documents in affected areas that reference the changed element
4. Prioritize updates by document class priority: Specification > Guide > Reference > Operations > Note

## Non-Goals

This document does not cover:

- Source code review processes
- Testing strategy per area
- Individual area architectural decisions
- Document formatting conventions within Specification documents

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
