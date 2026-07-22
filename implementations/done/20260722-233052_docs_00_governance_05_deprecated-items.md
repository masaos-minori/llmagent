## Goal

Create a centralized Deprecated Items document to manage references to old configuration files, concepts, and commands across the design documentation set.

## Scope

Create `docs/00_governance_05_deprecated-items.md` — a single document containing:
- Purpose: Why this document exists
- Deprecated Configuration Files section: Old config file names and their replacements
- Deprecated Concepts section: Obsolete architectural concepts
- Deprecated Commands section: Removed slash commands
- Deprecated Document References section: Links to removed or superseded documents
- How to Refer to Deprecated Items section: Guidelines for referencing deprecated content
- Maintenance Rule section: Rules for adding/removing items

## Assumptions

- The four initial candidates listed in the issue are accurate: config/rag_pipeline.toml, common.toml, workflow optional mode, shared common config.
- Items marked as "Needs confirmation" require verification before being treated as definitively deprecated.
- This document supplements rather than replaces existing Known Issues documents.

## Design decisions

- Single-file governance document rather than splitting into multiple small files.
- Five required metadata fields per entry ensure traceability for each deprecated item.
- "Needs confirmation" status used for unverified items to prevent misleading claims.

## Alternatives considered

- Merging this with the Known Issues template: rejected because deprecated items tracking is distinct from general issues tracking.
- Making all entries "Verified" by default: rejected because many deprecations cannot be verified without source code investigation.
- Using a different status model: rejected because Active/Needs confirmation/Verified provides sufficient granularity.

## Implementation

### Target file

`docs/00_governance_05_deprecated-items.md`

### Procedure

1. Create the file under `docs/` root.
2. Write each section in order: Purpose → Deprecated Configuration Files → Deprecated Concepts → Deprecated Commands → Deprecated Document References → How to Refer to Deprecated Items → Maintenance Rule.
3. For each deprecated item section, list items with the five required metadata fields.

### Method

Write Markdown with H2 headings for top-level sections. Use bullet lists for deprecated items within each section. Use bold for field names within text. Include the four initial candidate items with "Needs confirmation" status.

### Details

- **Purpose**: One paragraph explaining why the Deprecated Items document exists.
- **Deprecated Configuration Files**: Bullet list of deprecated config files with metadata fields.
- **Deprecated Concepts**: Bullet list of deprecated concepts with metadata fields.
- **Deprecated Commands**: Bullet list of removed slash commands with metadata fields.
- **Deprecated Document References**: Bullet list of removed/superseded document links with metadata fields.
- **How to Refer to Deprecated Items**: Three guidelines for referencing deprecated content.
- **Maintenance Rule**: Three rules for adding/removing items including quarterly review cadence.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Deprecated Commands must match the actual removed commands documented elsewhere.
- "Needs confirmation" status must be consistent with the Evidence Labels definition.
- Maintenance Rule must reference the quarterly review cadence specified in the issue.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply delete the file.
- Cross-links in other governance documents pointing to this file will become broken; those links should be removed or updated separately.
- No data loss risk since this is purely documentation.

## Validation plan

- Verify all five required sections are present.
- Verify all four initial candidates are listed with "Needs confirmation" status.
- Verify no definitive claims are made about unconfirmed items.
- Verify maintenance rules include quarterly review requirement.

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing documents with links to this document.
- Verifying or resolving "Needs confirmation" items.
- Resolving individual Known Issues entries.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-230104_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-233052
- Related target files: docs/00_governance_05_deprecated-items.md
