# Implementation Procedure: Add ## Keywords section to governance_00_document-guide.md

## Goal

Add a `## Keywords` body section to `governance_00_document-guide.md`, following the metadata policy, per REQ-003.

## Scope

Single-file edit: `docs/00_governance/governance_00_document-guide.md`. Only the addition of the `## Keywords` section is performed. No other content changes.

## Assumptions

- The metadata policy requires a `## Keywords` body-section heading (not a front-matter key) for governance documents, as stated in the Plan's Assumptions section.
- The `## Keywords` section should follow the existing section ordering convention used by other governance documents (place after `## Related Documents`), as noted in the Plan's Risks mitigation.
- The keywords should reflect the document's actual content: governance, document-guide, metadata, reading-order, canonical-source-rule.

## Design decisions

- Place the `## Keywords` section after `## Related Documents` (the last existing section), consistent with the ordering in other governance documents (governance_01, governance_02, governance_03, governance_04 all have `## Keywords` near the end).
- Use a simple bullet list under the heading, matching the style in other governance documents' Keywords sections.
- Include keywords that describe the document's purpose and scope, enabling accurate categorization by the structure checker.

## Alternatives considered

- Adding keywords as front-matter YAML keys: the metadata policy explicitly states `keywords` is not a front-matter key (see governance_02_documentation-metadata.md line 27).
- Placing the section before `## Related Documents`: inconsistent with the ordering in other governance documents.
- Omitting the section entirely: would fail the structure checker, which flags missing `## Keywords` headings.

## Implementation

### Target file

`docs/00_governance/governance_00_document-guide.md`

### Procedure

Append a `## Keywords` section after the `## Related Documents` section at the end of the file.

### Method

1. Open `docs/00_governance/governance_00_document-guide.md`.
2. Locate the `## Related Documents` section (last section, lines 51-56).
3. Append a blank line followed by the `## Keywords` section after the Related Documents content.
4. Verify the section ordering matches other governance documents.

### Details

Current end of file (lines 51-56):
```markdown
## Related Documents

- `governance_01_documentation-policy.md`
- `governance_02_documentation-metadata.md`
- `governance_03_issue-and-uncertainty-management.md`
- `governance_04_documentation-checks.md`
```

Append after the last `- ` line:
```markdown

## Keywords

- governance
- document-guide
- metadata
- reading-order
- canonical-source-rule
```

The resulting end of file will be:
```markdown
## Related Documents

- `governance_01_documentation-policy.md`
- `governance_02_documentation-metadata.md`
- `governance_03_issue-and-uncertainty-management.md`
- `governance_04_documentation-checks.md`

## Keywords

- governance
- document-guide
- metadata
- reading-order
- canonical-source-rule
```

## Compatibility considerations

This change affects only documentation structure. No code, tooling behavior, or other artifacts are affected. The structure checker (`tools/check_docs_structure.py`) expects this section for governance documents.

## Security considerations

N/A: documentation-only change, no sensitive data involved.

## Rollback considerations

Remove the appended `## Keywords` section. No data loss risk.

## Validation plan

1. After editing, verify the `## Keywords` section appears after `## Related Documents` and contains appropriate keyword entries.
2. Run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` and confirm the "missing Keywords" finding is resolved.
3. Compare the section ordering against other governance documents to ensure consistency.

## Completion criteria

- `governance_00_document-guide.md` contains a `## Keywords` body section after `## Related Documents`.
- The Keywords section includes relevant keyword entries (at minimum: `governance`, `document-guide`).
- No other content in the file is altered.
- `check_docs_structure.py` passes without the missing Keywords finding.

## Out of scope

- Changes to any other governance document.
- Canonical-map path shorthand correction.
- Document-size limit decisions.
- Changing any governance rule's substance.
- Editing any document outside `docs/00_governance/`.

## execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — | |
| 2 | Add or update tests per Validation plan | Completed | — | — | N/A: documentation-only |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — | N/A: this document is the documentation update |

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
- **Requirement ID**: REQ-003: Add ## Keywords body section to governance_00_document-guide.md
- **Source issue**: issues/20260926-174633_cleanup-batch-for-governance-docs:-stale-plan-ref,-illustrative-example-links,-missing-keywords.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-194234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-063107
- **Related target files**: docs/00_governance/governance_00_document-guide.md
