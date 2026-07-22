## Purpose

This document manages references to old configuration files, concepts, and commands across the design documentation set. It prevents readers from following outdated information and ensures deprecated items are clearly distinguished from current specifications.

## Deprecated Configuration Files

Old configuration file names and their replacements:

- **config/rag_pipeline.toml**
  - Current Replacement: none (replacement unknown)
  - Status: Needs confirmation
  - Notes: File may have been replaced during reorganization
  - Evidence: Requires source code investigation

- **common.toml**
  - Current Replacement: none (replacement unknown)
  - Status: Needs confirmation
  - Notes: May have been consolidated into area-specific configs
  - Evidence: Requires source code investigation

## Deprecated Concepts

Obsolete architectural concepts:

- **workflow optional mode**
  - Current Replacement: none (replacement unknown)
  - Status: Needs confirmation
  - Notes: WorkflowEngine is now required, not optional
  - Evidence: Confirmed by current implementation

- **shared common config**
  - Current Replacement: none (replacement unknown)
  - Status: Needs confirmation
  - Notes: Config structure has evolved to area-specific files
  - Evidence: Requires source code investigation

## Deprecated Commands

Removed slash commands:

- **/note** — Replaced by note-taking conventions in Known Issues documents
- **/ingest** — Functionality moved to separate ingestion pipeline
- **/debug audit** — Replaced by /audit prefix command
- **/db** — Database operations handled through operational tools

## Deprecated Document References

Links to removed or superseded documents:

- **diagnostics.jsonl** — No longer written; session diagnostics stored in memory only
- **Old direct execution fallback explanations** — Removed; WorkflowEngine is now required

## How to Refer to Deprecated Items

Guidelines for referencing deprecated content:

- Always mark deprecated items with the "Deprecated" evidence label
- Include both the deprecated name and its replacement (or "none" if fully removed)
- Never remove deprecated items from this document without documenting what replaced them

## Maintenance Rule

Rules for adding/removing items:

- New deprecations must be added within one week of the change being made
- Items cannot be removed without documenting what replaced them
- "Needs confirmation" items must be reviewed quarterly

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
