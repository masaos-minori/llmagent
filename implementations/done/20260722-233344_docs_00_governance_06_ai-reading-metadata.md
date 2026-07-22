## Goal

Create a governance document defining metadata conventions for AI agents to select relevant documents when reading the design documentation set.

## Scope

Create `docs/00_governance_06_ai-reading-metadata.md` — a single document containing:
- Purpose: Why this document exists
- Existing Metadata Fields: Five fields to preserve (title, category, tags, related, keywords)
- Recommended Additional Fields: Eight new fields with definitions and allowed values
- Field Definitions: Detailed descriptions of each recommended field
- Allowed Values: Permitted values for each field
- Usage Examples: Complete Front Matter block showing both existing and new fields
- Migration Policy: Gradual adoption approach emphasizing no bulk changes
- Non-Goals: Topics explicitly excluded from this document

## Assumptions

- Existing metadata fields (title, category, tags, related, keywords) should be preserved and extended, not replaced.
- Metadata additions should be optional and gradually adopted during normal document updates.
- The eight recommended fields listed in the issue cover the primary AI selection needs.

## Design decisions

- Single-file governance document rather than splitting into multiple small files.
- Eight additional fields provide comprehensive AI agent selection capabilities.
- Gradual migration policy prevents disruption to existing documents.

## Alternatives considered

- Replacing existing metadata fields instead of extending them: rejected because it would break backward compatibility.
- Making all eight fields mandatory: rejected because gradual adoption reduces resistance and allows incremental improvement.
- Merging this with the Evidence Labels document: rejected because metadata conventions are a distinct concern requiring detailed per-field guidance.

## Implementation

### Target file

`docs/00_governance_06_ai-reading-metadata.md`

### Procedure

1. Create the file under `docs/` root.
2. Write each section in order: Purpose → Existing Metadata Fields → Recommended Additional Fields → Usage Examples → Migration Policy → Non-Goals.
3. For each recommended field, write name, description, allowed values, and example.

### Method

Write Markdown with H2 headings for top-level sections. Use numbered lists for the eight recommended fields. Use bullet lists for allowed values within each field. Use YAML code blocks for usage examples.

### Details

- **Purpose**: One paragraph explaining why AI reading metadata conventions exist.
- **Existing Metadata Fields**: Bullet list of five existing fields to preserve.
- **Recommended Additional Fields**: Numbered list of eight fields. Each contains:
  - Field name (bold)
  - Description
  - Allowed values (bullet list)
  - Example (YAML code block)
- **Usage Examples**: YAML code block showing complete Front Matter with both existing and new fields.
- **Migration Policy**: Four guidelines emphasizing gradual adoption.
- **Non-Goals**: Three exclusion statements.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Existing metadata fields must not conflict with any existing YAML Front Matter in current documents.
- Allowed values must be consistent with those used elsewhere in the governance documents.
- Migration policy must not require changes to documents outside their normal update cycles.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply delete the file.
- Cross-links in other governance documents pointing to this file will become broken; those links should be removed or updated separately.
- No data loss risk since this is purely documentation.

## Validation plan

- Verify all eight recommended fields are defined with allowed values.
- Verify usage example shows both existing and new fields together.
- Verify migration policy does not require bulk changes.
- Verify non-goals match the issue requirements.

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing documents with new metadata fields.
- Defining new metadata fields beyond the eight specified.
- Resolving individual metadata inconsistencies.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-230206_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-233344
- Related target files: docs/00_governance_06_ai-reading-metadata.md
