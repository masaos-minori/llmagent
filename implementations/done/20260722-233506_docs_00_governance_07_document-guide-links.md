## Goal

Add Governance section links from each area's document-guide to the six governance documents, providing navigation paths to cross-cutting rules without modifying existing document structure.

## Scope

Add a short Governance subsection to each existing document-guide containing links to:
- `00_governance_01_documentation-governance.md`
- `00_governance_02_canonical-source-rule.md`
- `00_governance_03_evidence-labels.md`
- `00_governance_04_known-issues-template.md`
- `00_governance_05_deprecated-items.md`
- `00_governance_06_ai-reading-metadata.md`

## Assumptions

- All five document-guides exist and will be updated. If any do not exist, report them without creating them.
- The flat `docs/` directory structure means all links use filenames directly without subdirectory prefixes.
- This change adds only a small section; it does not modify existing reading order, file index, or related documents lists.

## Design decisions

- Single Governance section added to each document-guide rather than scattered individual links.
- Identical section content across all document-guides ensures consistency.
- Placement after main content but before File Index maintains existing structure.

## Alternatives considered

- Adding individual links throughout each document-guide: rejected because it scatters governance references and makes updates harder.
- Creating a separate governance navigation page: rejected because it adds an extra step for readers who want quick access.
- Modifying existing sections instead of adding a new one: rejected because it changes existing reading order and structure.

## Implementation

### Target files

Five document-guide files:
- `docs/03_rag_00_document-guide.md`
- `docs/04_mcp_00_document-guide.md`
- `docs/05_agent_00_document-guide.md`
- `docs/06_eventbus_00_document-guide.md`
- `docs/90_shared_00_document-guide.md`

### Procedure

1. Read each of the five document-guide files to confirm they exist and identify insertion point.
2. Add the Governance section with all six links to each file.
3. Verify link paths work in the flat `docs/` structure.
4. Report which files were modified and which did not exist.

### Method

For each document-guide file, insert the following Markdown section after the main content but before the File Index section:

```markdown
## Governance

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
```

### Details

- Section heading: H2 "Governance"
- Introductory sentence: "Cross-cutting documentation rules and policies:"
- Six bullet links using relative filenames (no subdirectory prefix due to flat `docs/` structure)
- No blank line between intro and first link for compact appearance

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Relative link paths must remain valid if governance documents are moved within `docs/`.
- Section placement must not interfere with existing document structure or reading order.
- If any document-guide does not exist, the missing file should be reported rather than silently skipped.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply remove the Governance section from each file.
- No data loss risk since this is purely adding links.
- If governance documents are later moved to subdirectories, all six link paths in all five files must be updated together.

## Validation plan

- Verify all six governance links appear in each document-guide.
- Verify no existing content was deleted or restructured.
- Verify links resolve correctly in flat `docs/` layout.
- Verify no new subdirectories were created under `docs/`.

## Out of scope

- Creating any of the six governance documents referenced here.
- Updating non-document-guide files with governance links.
- Resolving individual Known Issues entries.
- Modifying existing document structure beyond adding the single section.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-230316_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-233506
- Related target files: docs/03_rag_00_document-guide.md, docs/04_mcp_00_document-guide.md, docs/05_agent_00_document-guide.md, docs/06_eventbus_00_document-guide.md, docs/90_shared_00_document-guide.md
