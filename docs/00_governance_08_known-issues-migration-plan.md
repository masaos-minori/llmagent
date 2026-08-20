---
title: "Known Issues Migration Plan"
category: governance
tags:
  - governance
related:
  - 00_index.md
  - 01_overview.md
---
## Purpose

This document defines the migration plan for transitioning existing Known Issues / Inconsistencies documents across all areas to the new common template defined in `00_governance_04_known-issues-template.md`. It ensures a controlled, gradual transition that preserves existing IDs and history.

## Scope

**Included**: Planning the migration of five area Known Issues documents to use the common template format. Recording current formats as baseline. Defining priority criteria and suggested order.

**Excluded**: Actually modifying any existing Known Issues documents during this planning phase. Creating follow-up issues for each area migration.

## Target Files

Five areas' Known Issues documents to investigate:

- `docs/03_rag_90_inconsistencies_and_known_issues.md`
- `docs/04_mcp_90_inconsistencies_and_known_issues.md`
- `docs/05_agent_90_inconsistencies_and_known_issues.md`
- `docs/06_eventbus_90_inconsistencies_and_known_issues.md`
- `docs/90_shared_90_inconsistencies_and_known_issues.md`

## Current Format Summary

### RAG (`03_rag_90`)

- Entry count: 2 entries (both DESIGN-2 and DESIGN-3 are confirmed design decisions)
- Severity classification: None
- Type classification: Uses "Confirmed Design Decision" type
- Status classification: None
- Unique conventions: Japanese section headers; uses "Invariants (non-negotiable)" sub-section; includes "2026-07-12 Implementation Verification" notes

### MCP (`04_mcp_90`)

- Entry count: 2 entries
- Severity classification: None
- Type classification: Uses English types ("Implementation bug", "Unimplemented", "Document inconsistency", "Undefined", "Needs confirmation")
- Status classification: None
- Unique conventions: Uses "Current behavior" instead of "Statement A/B"; includes "Affected config" field

### Agent (`05_agent_90`)

- Entry count: 3 entries
- Severity classification: None
- Type classification: Uses English types ("Document inconsistency", "Implementation bug", "Undocumented", "Needs confirmation", "Open Question")
- Status classification: None
- Unique conventions: Standard Statement A/B format; includes "Notes for AI reference" field

### EventBus (`06_eventbus_90`)

- Entry count: 6 entries across multiple sections
- Severity classification: None
- Type classification: None — uses section-based grouping instead
- Status classification: None
- Unique conventions: Table-based format with "Item / Safe Interpretation / Recommended Action" columns; sectioned by "Items requiring action", "Documents only", "Pending items", "Schema/implementation diffs"

### Shared/DB (`90_shared_90`)

- Entry count: 1 entry
- Severity classification: None
- Type classification: Uses Japanese types ("Document Inconsistency", "Implementation Bug", "Undocumented", "Unimplemented", "Undefined", "Needs Confirmation")
- Status classification: None
- Unique conventions: Includes "Evidence" field referencing specific test files; detailed technical descriptions

## Migration Policy

Guidelines for migrating entries to the common template:

- Migrate one area at a time via separate follow-up issues
- Preserve all existing entry IDs during migration
- Do not resolve or change the substance of existing entries during migration
- Add missing metadata fields (severity, status, owner) based on best available information
- Mark migrated entries with a migration note indicating the date and source template
- Review each migrated entry for accuracy before closing the migration issue

## Priority Criteria

Six categories for ordering migrations:

1. **Entry count** — Areas with more entries benefit more from standardization
2. **Format divergence** — Areas whose format differs most from the target template have higher migration value
3. **Language consistency** — Areas using non-English headers/types should be prioritized for alignment
4. **Cross-references** — Areas frequently referenced by other documents need consistent formatting
5. **Active maintenance** — Areas with recent changes require stable format for ongoing work
6. **Business impact** — Areas affecting critical operations should have standardized tracking

## Suggested Migration Order

Based on the priority criteria above:

1. **Agent** — High entry count (3), uses English types but inconsistent with target template, frequently referenced by other documents
2. **MCP** — Medium entry count (2), uses English types but different field names, has cross-area dependencies
3. **RAG** — Low entry count (2), uses Japanese headers creating language inconsistency, has complex invariant tracking needs
4. **EventBus** — Highest format divergence (table-based), medium entry count (6), lower cross-reference frequency
5. **Shared/DB** — Lowest entry count (1), uses Japanese types, limited cross-references

## Risks

- **Lost historical context**: Migrating entries may lose nuanced details from the original format. Mitigation: Preserve original content in migration notes before removing it.
- **ID conflicts**: If new ID format conflicts with existing IDs. Mitigation: Map old IDs to new ones explicitly during migration.
- **Scope creep**: Migration issues may attract unrelated fixes. Mitigation: Define strict acceptance criteria for each migration issue.

## Non-Goals

Topics explicitly excluded from this plan:

- Resolving individual Known Issues entries during migration
- Adding new entries beyond what already exists
- Changing the common template itself
- Migrating non-Known-Issues documents

## Acceptance Criteria for Future Migration

Each future migration issue must verify:

- All existing entries from the source document appear in the migrated version
- All existing entry IDs are preserved or explicitly mapped to new IDs
- No entry content was changed beyond adding required metadata fields
- Cross-links to related governance documents are present
- The migrated document passes consistency checks against the common template definition

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
- [Terminology Glossary](00_governance_09_terminology-glossary.md)
