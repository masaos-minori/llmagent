## Goal

Create a governance document defining a common entry template for Known Issues / Inconsistencies documents across all areas of the design documentation set.

## Scope

Create `docs/00_governance_04_known-issues-template.md` — a single document containing:
- Purpose: Why this document exists
- Known Issue Entry Template with 17 required fields
- Status values (6 types)
- Type values (8 types)
- Severity values (3 levels)
- Owner values (3 options)
- Area values (8 areas)
- Lifecycle rules describing status transitions
- Migration notes for transitioning existing entries

## Assumptions

- Each area maintains its own Known Issues document; this template standardizes entry format only.
- The eight type values listed in the issue cover all known categories.
- Six status values are sufficient for tracking issue lifecycle.
- Three severity levels (High/Medium/Low) are adequate.
- Eight area values match the areas defined in the governance document.

## Design decisions

- Single-file governance document rather than splitting into multiple small files.
- Template includes all 17 fields to ensure complete tracking information.
- Eight area values align with the six governance documents created as part of this batch.

## Alternatives considered

- Reducing the number of template fields to simplify adoption: rejected because incomplete tracking leads to unactionable entries.
- Merging this with the Deprecated Items document: rejected because Known Issues tracking is a distinct concern requiring detailed per-entry guidance.
- Using a different ID format: rejected because {AREA}-{NNN} provides clear area identification.

## Implementation

### Target file

`docs/00_governance_04_known-issues-template.md`

### Procedure

1. Create the file under `docs/` root.
2. Write each section in order: Purpose → Known Issue Entry Template → Status Values → Type Values → Severity Values → Owner Values → Area Values → Lifecycle → Migration Notes.
3. Add cross-links to related governance documents in the final section.

### Method

Write Markdown with H2 headings for top-level sections. Use numbered lists for the entry template fields. Use bullet lists for enumerated value sets (Status, Type, Severity, Owner, Area). Use bold for field names within text.

### Details

- **Purpose**: One paragraph explaining why the Known Issues template exists.
- **Known Issue Entry Template**: Numbered list of 17 fields, each with name and brief description.
- **Status Values**: Bullet list of six statuses with one-line definitions.
- **Type Values**: Bullet list of eight types with one-line definitions.
- **Severity Values**: Bullet list of three severities with one-line definitions.
- **Owner Values**: Bullet list of three owner options with one-line definitions.
- **Area Values**: Bullet list of eight areas matching the governance document structure.
- **Lifecycle**: Bullet list of four status transition rules.
- **Migration Notes**: Bullet list of three migration guidelines.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Area values must match those used in other governance documents.
- Status values must be consistent with those referenced in the Needs Confirmation Inventory document.
- Type values must align with those defined in the Evidence Labels document.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply delete the file.
- Cross-links in other governance documents pointing to this file will become broken; those links should be removed or updated separately.
- No data loss risk since this is purely documentation.

## Validation plan

- Verify all 17 template fields are present.
- Verify all six status values are defined.
- Verify all eight type values are defined.
- Verify lifecycle transitions are clear and complete.
- Verify migration notes address preserving existing IDs.

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing Known Issues documents with the new template.
- Defining new status/type/severity values beyond those specified.
- Resolving individual Known Issues entries.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-225952_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-232904
- Related target files: docs/00_governance_04_known-issues-template.md
