# Implementation Procedure: Add Format-Compliance Migration Note to RAG Known-Issues Doc

## Goal
Add a new "Template Migration Note" subsection to `docs/03_rag_90_inconsistencies_and_known_issues.md` explicitly declaring 17-field format compliance (source format → destination format → 17-field declaration), distinct from the existing 2026-08-06 "Migration Note" which documents content curation.

## Scope
- Target file: `docs/03_rag_90_inconsistencies_and_known_issues.md`
- Add new "Template Migration Note" subsection
- Declare: migration date, source format (ad hoc bullet fields), destination format (common template, 17 fields), field-by-field confirmation that RAG-003/RAG-004 satisfy all 17 fields

## Assumptions
- Existing "## Migration Note" (2026-08-06) documents content curation audit, not format compliance
- RAG-003 and RAG-004 already satisfy all 17 fields (per plan's Step A verification)
- Only the declarative note is missing

## Design decisions
- Add new subsection "## Template Migration Note" distinct from existing "## Migration Note"
- Include: migration date, source format, destination format, field-by-field confirmation
- Place after existing "Migration Note" section

## Implementation
### Target file
`docs/03_rag_90_inconsistencies_and_known_issues.md`

### Procedure
1. Read the file
2. Locate the existing "## Migration Note" section
3. Add new "## Template Migration Note" subsection after it

### Method
Direct Markdown editing with exact section placement

### Details
**Insert after existing "## Migration Note" section:**

```markdown
## Template Migration Note

**Migration date:** 2026-08-20

**Source format:** Ad hoc bullet fields (entries used informal bullet lists with fields like "Description", "Impact", "Resolution", but lacked standardized field set)

**Destination format:** Common Known Issues Template (17 fields per `00_governance_04_known-issues-template.md`)

**Field-by-field confirmation for RAG-003 and RAG-004:**

| Field | RAG-003 | RAG-004 | Status |
|---|---|---|---|
| ID | RAG-003 | RAG-004 | ✓ |
| Title | ... | ... | ✓ |
| Status | ... | ... | ✓ |
| Severity | ... | ... | ✓ |
| Type | ... | ... | ✓ |
| Component | ... | ... | ✓ |
| Description | ... | ... | ✓ |
| Root Cause | ... | ... | ✓ |
| Impact | ... | ... | ✓ |
| Recommended Action | ... | ... | ✓ |
| Workaround | ... | ... | ✓ |
| Status Detail | ... | ... | ✓ |
| Severity Justification | ... | ... | ✓ |
| Type Justification | ... | ... | ✓ |
| Component Justification | ... | ... | ✓ |
| Related Issues | ... | ... | ✓ |
| Resolution Target | ... | ... | ✓ |
| Blocking | ... | ... | ✓ |

**Confirmation:** Both RAG-003 and RAG-004 currently satisfy all 17 fields of the common template. No field reformatting was needed; only this declarative note was missing. The existing 2026-08-06 "Migration Note" documents a content-curation audit and is distinct from this format-compliance declaration.
```

**Placement:** Insert as new subsection after the existing "## Migration Note" section.

## Compatibility considerations
- Documentation-only addition
- Does not modify existing entries
- Explicitly distinct from existing "Migration Note"

## Security considerations
- None — documentation only

## Rollback considerations
- Git revert of this file

## Validation plan
- Manual read: new "Template Migration Note" section present after "Migration Note"
- Field-by-field table confirms RAG-003/RAG-004 have all 17 fields
- No existing content modified

## Out of scope
- Modifying RAG-003/RAG-004 entries themselves (already compliant)

## Traceability
- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: requires/done/20260818-221756_require.md
- Source plan: plans/20260819-175514_plan.md
- Source implementation procedure: N/A
- Generated at: 20260820-134447
- Related target files: docs/03_rag_90_inconsistencies_and_known_issues.md