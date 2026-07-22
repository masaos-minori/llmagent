## Goal

Create a migration plan for transitioning existing Known Issues / Inconsistencies documents across all areas to the new common template, without modifying any existing content directly.

## Scope

Create `docs/00_governance_08_known-issues-migration-plan.md` — a single document containing:
- Purpose: Why this document exists
- Scope: What is included and excluded
- Target Files: Five areas' Known Issues documents to investigate
- Current Format Summary: Record of each area's current Known Issues format
- Migration Policy: Gradual transition approach emphasizing preservation
- Priority Criteria: Six categories for ordering migrations
- Suggested Migration Order: Proposed order based on priority criteria
- Risks: Potential issues and mitigation strategies
- Non-Goals: Topics explicitly excluded from this plan
- Acceptance Criteria for Future Migration: Requirements for each future migration issue

## Assumptions

- Five areas have Known Issues / Inconsistencies documents: RAG, MCP, Agent, EventBus, Shared/DB.
- Existing entries must not be modified during planning phase.
- Migration will be split into separate follow-up issues per area.
- Existing IDs and history must be preserved during migration.

## Design decisions

- Single-file governance document rather than splitting into multiple small files.
- Six priority criteria provide sufficient granularity for ordering migrations.
- Suggested migration order is advisory, not mandatory, allowing flexibility per area.

## Alternatives considered

- Migrating all areas simultaneously: rejected because it increases risk and makes rollback harder.
- Using a different priority model (e.g., alphabetical): rejected because it ignores business impact.
- Merging this with the Known Issues template: rejected because migration planning is a distinct concern requiring detailed per-area guidance.

## Implementation

### Target file

`docs/00_governance_08_known-issues-migration-plan.md`

### Procedure

1. Create the file under `docs/` root.
2. Write each section in order: Purpose → Scope → Target Files → Current Format Summary → Migration Policy → Priority Criteria → Suggested Migration Order → Risks → Non-Goals → Acceptance Criteria for Future Migration.
3. For each area, record the current format summary based on investigation.

### Method

Write Markdown with H2 headings for top-level sections. Use numbered lists for priority criteria and migration order. Use bullet lists for target files, risks, and non-goals. Use bold for emphasis on key terms.

### Details

- **Purpose**: One paragraph explaining why the migration plan exists.
- **Scope**: Two paragraphs defining what is included and excluded.
- **Target Files**: Bullet list of five areas' Known Issues documents.
- **Current Format Summary**: Table or subsection for each area recording entry count, severity/type/status classification presence, and unique conventions.
- **Migration Policy**: Five guidelines emphasizing gradual adoption and ID preservation.
- **Priority Criteria**: Numbered list of six categories for ordering migrations.
- **Suggested Migration Order**: Numbered list of five areas with rationale for each position.
- **Risks**: Three risk items with mitigation strategies.
- **Non-Goals**: Three exclusion statements.
- **Acceptance Criteria for Future Migration**: Four verification requirements for each future migration issue.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Priority criteria must be consistent with those used elsewhere in the governance documents.
- Migration policy must not conflict with the Known Issues template defined in `00_governance_04_known-issues-template.md`.
- Acceptance criteria must reference fields defined in the Known Issues template.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply delete the file.
- Cross-links in other governance documents pointing to this file will become broken; those links should be removed or updated separately.
- No data loss risk since this is purely documentation.

## Validation plan

- Verify all five areas are listed as investigation targets.
- Verify priority criteria cover all six categories from the issue.
- Verify migration order rationale is documented.
- Verify no existing Known Issues documents were modified.

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing Known Issues documents during this planning phase.
- Defining new priority criteria beyond the six specified.
- Resolving individual Known Issues entries.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-230524_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-233906
- Related target files: docs/00_governance_08_known-issues-migration-plan.md
