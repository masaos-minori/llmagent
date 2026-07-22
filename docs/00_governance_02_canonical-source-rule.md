## Purpose

This document defines canonical source rules for resolving conflicts between documents and between code and documents in the LLM agent design documentation set. When inconsistencies arise, these rules determine which source takes precedence and how to resolve them.

## General Rule

When conflicts occur between documents or between code and documents, the following hierarchy applies:
1. Code is the ultimate authority for behavioral claims
2. The most recently reviewed document is authoritative among conflicting documents
3. The area's document-guide identifies the canonical source within that area

## Canonical Documents by Area

Each area defines its own canonical sources through its document-guide. This document does not hard-code specific canonical documents because they may change over time. Refer to each area's document-guide for the current canonical sources.

## Conflict Resolution Rule

When two documents contradict each other:

1. Identify the area(s) each document belongs to
2. Determine if both documents are in the same area — if so, consult the area's document-guide for the canonical source
3. If documents span different areas, check whether one area's specification supersedes another's based on dependency direction
4. If neither rule resolves the conflict, register a Known Issue and defer resolution until the next review cycle

## Code vs Document Conflict Rule

When code contradicts a document, classify the conflict into one of five categories:

- **Outdated code** — Code has not been updated to reflect a recent design decision documented elsewhere
- **Design deviation** — Code intentionally deviates from the documented design (documented as such)
- **Provisional implementation** — Code implements a feature before formal documentation approval
- **Bug** — Code contains an error that produces behavior inconsistent with the documented intent
- **Missing documentation** — Code works correctly but no corresponding documentation exists

## Known Issues Registration Rule

Register a Known Issue when:

- A document-to-document conflict cannot be resolved using the Conflict Resolution Rule
- A code-vs-document conflict is classified as "design deviation" without documented justification
- A suspected bug requires investigation to confirm whether code or documentation is incorrect
- An unresolved conflict affects more than one area simultaneously

## Resolution Workflow

From detection to record-keeping:

1. Detect the conflict during normal review or through automated checks
2. Classify the conflict type using the rules above
3. Apply the appropriate resolution rule based on classification
4. Update affected documents or code to eliminate the conflict
5. Record the resolution in the relevant Known Issues document if applicable

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Known Issues Template](00_governance_04_known-issues-template.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
