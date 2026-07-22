## Purpose

This document defines a common entry template for Known Issues / Inconsistencies documents across all areas of the design documentation set. It ensures consistent tracking, classification, and resolution of discrepancies between documentation and implementation.

## Known Issue Entry Template

Each Known Issue entry must contain the following 17 fields:

1. **ID** — Unique identifier in format `{AREA}-{NNN}` (e.g., AGENT-001)
2. **Title** — Brief description of the issue
3. **Status** — Current lifecycle state of the issue
4. **Severity** — Priority level of the issue
5. **Area** — Which area the issue belongs to
6. **Type** — Category of inconsistency
7. **Source** — File or location where the inconsistency was found
8. **Owner** — Person responsible for resolution
9. **First Found** — Date the issue was first discovered
10. **Target** — Target document(s) affected
11. **Related** — Related issues or references
12. **Summary** — Concise summary of the issue
13. **Current Description** — How the issue currently manifests
14. **Observed Implementation** — What the actual implementation shows
15. **Impact** — Consequences of the issue remaining unresolved
16. **Recommended Action** — Suggested resolution approach
17. **Resolution Notes** — History of resolution attempts

## Status Values

- **open** — Issue acknowledged but not yet investigated
- **investigating** — Investigation underway
- **fixed** — Issue resolved
- **deferred** — Resolution postponed to future work
- **deprecated** — Issue no longer relevant (obsolete feature)
- **wontfix** — Issue will not be addressed

## Type Values

- **document-code-mismatch** — Documentation contradicts code behavior
- **document-document-mismatch** — Two documents contradict each other
- **obsolete-description** — Description refers to removed/deprecated feature
- **missing-documentation** — Feature exists without documentation
- **ambiguous-behavior** — Behavior unclear due to insufficient specification
- **implementation-bug** — Code does not match documented intent
- **design-gap** — Missing design consideration
- **operational-gap** — Missing operational guidance

## Severity Values

- **High** — Requires immediate attention; affects safety or critical functionality
- **Medium** — Should be addressed soon; affects correctness or clarity
- **Low** — Can be deferred; minor inconsistency or formatting issue

## Owner Values

- **Unassigned** — No owner assigned
- **[Name]** — Assigned to specific person
- **Team** — Assigned to team decision

## Area Values

- Overview
- Deployment
- RAG
- MCP
- Agent
- EventBus
- Shared/DB
- Governance

## Lifecycle

- An issue remains in its current status until explicitly changed.
- Open → Investigating when investigation begins.
- Investigating → Fixed when resolved, or Deferred/Wontfix if not resolvable now.
- Deferred → Fixed when eventually addressed, or Wontfix if abandoned.
- Deprecated when the underlying feature is removed.

## Migration Notes

- Existing entries should be migrated gradually using a separate migration plan.
- Preserve original IDs during migration.
- Map old severity/type classifications to new values where possible.

## Related Governance Documents

Cross-cutting documentation rules and policies:

- [Documentation Governance](00_governance_01_documentation-governance.md)
- [Canonical Source Rule](00_governance_02_canonical-source-rule.md)
- [Evidence Labels](00_governance_03_evidence-labels.md)
- [Deprecated Items](00_governance_05_deprecated-items.md)
- [AI Reading Metadata](00_governance_06_ai-reading-metadata.md)
- [Needs Confirmation Inventory](00_governance_07_needs-confirmation-inventory.md)
