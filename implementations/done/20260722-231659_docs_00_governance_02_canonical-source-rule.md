## Goal

Create a governance document defining canonical source rules for resolving conflicts between documents and between code and documents in the LLM agent design documentation set.

## Scope

Create `docs/00_governance_02_canonical-source-rule.md` — a single document containing:
- Purpose: Why this document exists
- General Rule: High-level principle for canonical source resolution
- Canonical Documents by Area: Framework for identifying canonical sources per area (without hard-coding specific documents)
- Conflict Resolution Rule: Procedure for resolving document-to-document conflicts
- Code vs Document Conflict Rule: Classification of five conflict types when code contradicts documents
- Known Issues Registration Rule: Criteria for registering Known Issues when conflicts are found
- Resolution Workflow: Step-by-step process from detection to record-keeping
- Related Documents: Links to related governance documents

## Assumptions

- Each area already has its own document-guide identifying local canonical sources.
- No single document is universally canonical across all areas.
- Code is not always correct — it can be outdated, deviated from design, provisional, or buggy.
- Five classification categories for code-vs-document conflicts are sufficient.

## Design decisions

- Single-file governance document rather than splitting into multiple small files.
- Framework-only approach for canonical sources — do not hard-code specific documents.
- Code-vs-document conflicts classified into five distinct categories rather than a binary correct/incorrect model.

## Alternatives considered

- Hard-coding canonical documents per area in this file: rejected because it would require updates whenever area-specific canonical sources change.
- Binary code-vs-document classification (code is right vs code is wrong): rejected because it oversimplifies reality — code can be outdated, provisional, or buggy.
- Merging this with the main governance document: rejected because canonical source resolution is a distinct concern requiring detailed procedures.

## Implementation

### Target file

`docs/00_governance_02_canonical-source-rule.md`

### Procedure

1. Create the file under `docs/` root.
2. Write each section in order: Purpose → General Rule → Canonical Documents by Area → Conflict Resolution Rule → Code vs Document Conflict Rule → Known Issues Registration Rule → Resolution Workflow → Related Documents.
3. Add cross-links to related governance documents in the final section.

### Method

Write Markdown with H2 headings for each top-level section. Use numbered lists for ordered procedures (Conflict Resolution Rule, Resolution Workflow). Use bullet lists for enumerated classifications (Code vs Document Conflict Rule categories).

### Details

- **Purpose**: One paragraph explaining why canonical source rules exist.
- **General Rule**: One sentence stating the core principle.
- **Canonical Documents by Area**: Explain that each area defines its own canonical sources via its document-guide; this document provides the framework but lists no specific documents.
- **Conflict Resolution Rule**: Numbered four-step procedure for resolving document-to-document conflicts.
- **Code vs Document Conflict Rule**: Bullet list of five classification categories with brief descriptions.
- **Known Issues Registration Rule**: Bullet list of four conditions triggering Known Issues registration.
- **Resolution Workflow**: Numbered five-step process from detection to record-keeping.
- **Related Documents**: Link entries referencing other governance documents.

## Compatibility considerations

- Must align with the six governance documents created as part of this same batch of work.
- Conflict Resolution Rule must be consistent with the canonical source identification method used in other governance documents.
- Known Issues Registration Rule must reference the Known Issues template defined in `00_governance_04_known-issues-template.md`.

## Security considerations

N/A — this is a documentation document with no code execution or access control implications.

## Rollback considerations

- If the document needs to be reverted, simply delete the file.
- Cross-links in other governance documents pointing to this file will become broken; those links should be removed or updated separately.
- No data loss risk since this is purely documentation.

## Validation plan

- Verify all required sections are present
- Verify no specific canonical documents are listed (framework only)
- Verify code-vs-document classification covers all five categories
- Verify Known Issues registration criteria are clear

## Out of scope

- Creating any of the other governance documents referenced here.
- Updating existing document-guides with links to this document.
- Listing specific canonical documents for any area.
- Resolving individual document conflicts.

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260722-225744_plan.md
- Source implementation procedure: N/A
- Generated at: 20260722-231659
- Related target files: docs/00_governance_02_canonical-source-rule.md
