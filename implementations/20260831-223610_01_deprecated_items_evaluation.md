## Goal

Evaluate `docs/00_governance_05_deprecated-items.md` against the Current-Specification-Only Policy and determine whether its content remains applicable to the current system.

## Scope

Read and evaluate `docs/00_governance_05_deprecated-items.md` against the Current-Specification-Only Policy defined in `docs/00_governance_01_documentation-policy.md`. Determine if any content should be relocated to current canonical documents or if the document should be removed entirely.

## Assumptions

- The Deprecated Items document describes removed compatibility formats from MCP Schema 2.0 enforcement and RAG ingestion pipeline workstreams
- The Current-Specification-Only Policy requires that still-applicable design knowledge be preserved in current canonical documents
- If the entire document is purely historical with no remaining value, it should be deleted

## Design decisions

- Evaluate each entry individually against the policy, not the document as a whole
- Only relocate content that constitutes still-applicable design knowledge (why a particular constraint was chosen), not descriptions of removed features

## Alternatives considered

- Keeping the document as-is — rejected because the Current-Specification-Only Policy explicitly prohibits retaining purely historical content
- Moving the entire document to an archive directory — rejected because the policy requires removal of non-compliant content, not relocation to another location

## Implementation

### Target file

`docs/00_governance_05_deprecated-items.md`

### Procedure

1. Read `docs/00_governance_05_deprecated-items.md` and `docs/00_governance_01_documentation-policy.md`
2. For each entry in the Deprecated Items document:
   - Determine if the entry describes a removed feature that no longer applies to the current system → remove
   - Determine if the entry contains still-applicable design knowledge (rationale for a constraint) → relocate to appropriate current canonical document
   - Determine if the entry is purely historical with no remaining value → remove
3. Update the document per findings: either remove the entire document or edit it to retain only compliant content

### Method

Manual evaluation — read the document, compare each entry against the Current-Specification-Only Policy definition, and decide per-entry.

### Details

```markdown
# Evaluation criteria per entry:
1. Does this entry describe a feature/format that is still present in the current system?
   - Yes → keep, possibly relocate to current canonical document
   - No → check #2
2. Does this entry contain rationale/design knowledge that explains why a current constraint was chosen?
   - Yes → relocate rationale to appropriate current canonical document
   - No → remove this entry

# Outcome options:
- Remove entire document if ALL entries are non-compliant
- Edit document to remove non-compliant entries while keeping compliant ones
- Create new issue to track relocation of compliant entries if needed
```

## Compatibility considerations

- REQ-001: Any still-applicable requirements must be relocated to the appropriate current canonical document before removal
- This task may affect multiple governance documents if content needs to be moved

## Security considerations

N/A: This is a documentation evaluation task. No security-sensitive code changes involved.

## Rollback considerations

- If content is removed from the document, git history preserves the original content
- If content is relocated, ensure the destination document has proper attribution

## Validation plan

| Target | Strategy | Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance_05_deprecated-items.md` | Manual review against Current-Specification-Only Policy | Read document + policy definition | Document either removed or compliant |

## Completion criteria

- [ ] Each entry evaluated against Current-Specification-Only Policy (REQ-001)
- [ ] Still-applicable design knowledge relocated to current canonical documents
- [ ] Non-compliant content removed from the document
- [ ] Decision documented: document removed, edited, or flagged for follow-up

## Out of scope

- Changes to governance policy documents themselves
- Re-litigating the decision to remove the Archived Items table or Migration Plan
- Modifying governance-policy documents already updated by the prior task

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Read deprecated items document and Current-Specification-Only Policy | Pending | — | — | |
| 2 | Evaluate each entry against the policy | Pending | — | — | |
| 3 | Relocate compliant content or remove non-compliant entries | Pending | — | — | |

### Blocker Log

| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created

| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260831-162016_govdocs001_historical_content_removal_and_transfer.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260831-223610_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-01T00:00:00Z
- **Related target files**: docs/00_governance_05_deprecated-items.md
