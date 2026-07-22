## Goal

Create a centralized inventory of all "Needs confirmation" items found across the design documentation set, making unconfirmed statements trackable and actionable.

## Scope

Create `docs/00_governance_07_needs-confirmation-inventory.md` — a single document that:
- Extracts all "Needs confirmation" labeled statements from Markdown files under `docs/`
- Lists each item with structured metadata including ID, source location, question, evidence, impact, and required action
- Does not modify the source documents from which items are extracted

## Assumptions

- The eleven fields listed in the issue are sufficient for tracking each item.
- The NC-{NNN} ID format is acceptable.
- The five status values cover all lifecycle states needed.
- No source documents should be modified during extraction.

## Design decisions

- Single-file governance document rather than splitting into multiple small files.
- Eleven required fields ensure complete tracking information for each item.
- NC-{NNN} ID format provides clear numbering and area identification.

## Alternatives considered

- Using a different ID format (e.g., AREA-{NNN}): rejected because NC prefix clearly indicates "Needs Confirmation" regardless of area.
- Making some fields optional: rejected because incomplete tracking leads to unactionable entries.
- Merging this with the Deprecated Items document: rejected because needs-confirmation tracking is a distinct concern requiring detailed per-item guidance.

## Implementation

### Target file

`docs/00_governance_07_needs-confirmation-inventory.md`

### Procedure

1. Create the file under `docs/` root.
2. Write each section in order: Purpose → Inventory Entry Fields → Status Values → Extraction Process → Inventory Items → Non-Goals.
3. For each needs-confirmation item, populate all eleven required fields.

### Method

Write Markdown with H2 headings for top-level sections. Use numbered lists for the eleven entry fields. Use bullet lists for status values. Use YAML code blocks for usage examples.

### Details

- **Purpose**: One paragraph explaining why the Needs Confirmation Inventory exists.
- **Inventory Entry Fields**: Numbered list of eleven fields, each with name and brief description.
- **Status Values**: Bullet list of five statuses with one-line definitions.
- **Extraction Process**: Numbered list of five steps for extracting items from source documents.
- **Inventory Items**: Table or list of extracted items with all eleven fields populated.
- **Non-Goals**: Three exclusion statements.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Status values must be consistent with those used elsewhere in the governance documents.
- NC-{NNN} ID format must not conflict with any existing ID schemes.
- Extraction process must not modify source documents.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply delete the file.
- Cross-links in other governance documents pointing to this file will become broken; those links should be removed or updated separately.
- No data loss risk since this is purely documentation.

## Validation plan

- Verify all entries have all eleven required fields populated.
- Verify IDs follow NC-{NNN} format sequentially.
- Verify no source documents were modified.
- Verify uncertain items retain "Needs confirmation" status rather than being guessed.

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing documents with "Needs confirmation" labels.
- Defining new status values beyond the five specified.
- Resolving individual Known Issues entries.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-230422_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-233736
- Related target files: docs/00_governance_07_needs-confirmation-inventory.md
