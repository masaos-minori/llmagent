# Implementation Procedure: Annotate example-link placeholders in governance_04_documentation-checks.md

## Goal

Annotate the example-link placeholders in `governance_04_documentation-checks.md` (lines 276-279) so they are clearly illustrative and cannot be mistaken for real file references, per REQ-002.

## Scope

Single-file edit: `docs/00_governance/governance_04_documentation-checks.md`. Only the "Link format examples" section is modified. No other content changes.

## Assumptions

- Angle-bracketed filenames (e.g., `<agent_01_system-overview_00_document-guide.md>`) sufficiently distinguish illustrative placeholders from real file references, consistent with the Plan's Assumptions section.
- The same annotation style used in `governance_02_documentation-metadata.md` (angle brackets) applies here for consistency across both REQ-002 documents.
- The existing link format structure (same-area, cross-area, ADR, internal anchor) should be preserved; only the placeholder filenames need annotation.

## Design decisions

- Use angle brackets (`<...>`) around placeholder filenames, matching the approach in the related REQ-002 document for `governance_02_documentation-metadata.md`.
- The angle-bracket convention is widely understood in technical writing as indicating a non-literal value.

## Alternatives considered

- Adding an "example only" caption after each example: more verbose, less visually immediate.
- Using italics or strikethrough: less standard convention for indicating non-real values.
- Replacing placeholder filenames with generic descriptions like `[Agent Guide](<agent-guide>)`: loses the filename-level detail that the examples are meant to illustrate.

## Implementation

### Target file

`docs/00_governance/governance_04_documentation-checks.md`

### Procedure

Wrap the placeholder filenames in the "Link format examples" section with angle brackets to make them unmistakably illustrative.

### Method

1. Open `docs/00_governance/governance_04_documentation-checks.md`.
2. Navigate to the "Link format examples:" section (lines 275-279).
3. Replace the bare placeholder filenames with angle-bracketed versions.
4. Verify the rest of the section structure is preserved.

### Details

Current content (lines 276-279):
```markdown
- Same area: `[Agent Guide](agent_01_system-overview_00_document-guide.md)`
- Cross area: `[RAG Specification](rag_01_system_overview_00_document-guide.md)`
- ADR: `[ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md)`
- Internal anchor: `[Section](agent_01_system-overview_00_document-guide.md#workflow-engine)`
```

Changed to:
```markdown
- Same area: `[Agent Guide](<agent_01_system-overview_00_document-guide.md>)`
- Cross area: `[RAG Specification](<rag_01_system_overview_00_document-guide.md>)`
- ADR: `[ADR-001](../10_adr/ADR-001-workflow-engine-mandatory.md)`
- Internal anchor: `[Section](<agent_01_system-overview_00_document-guide.md>#workflow-engine)`
```

Notes on the changes:
- Same area and Cross area rows: wrap the entire placeholder filename in angle brackets inside the Markdown link syntax.
- ADR row: unchanged — `../10_adr/ADR-001-workflow-engine-mandatory.md` is a relative path within the repo, not a placeholder.
- Internal anchor row: wrap the placeholder filename portion in angle brackets; keep the anchor fragment outside the brackets since it refers to a section within the hypothetical file.

## Compatibility considerations

This change affects only documentation rendering. No code, tooling behavior, or other artifacts consume these links. The angle-bracket convention is purely visual and does not affect Markdown parsing semantics.

## Security considerations

N/A: documentation-only change, no sensitive data involved.

## Rollback considerations

Revert the angle brackets around the placeholder filenames. No data loss risk.

## Validation plan

1. After editing, verify the Link format examples section reads as clearly illustrative by inspection.
2. Confirm no real file references were accidentally modified.
3. Run `uv run python tools/check_docs_structure.py docs/00_governance/*.md` and confirm none of the flagged findings from the original issue remain.

## Completion criteria

- Lines 276-279 in `governance_04_documentation-checks.md` have angle-bracketed placeholder filenames.
- The ADR line remains unchanged (it is a valid relative path, not a placeholder).
- No other content in the file is altered.
- `check_docs_structure.py` passes without the illustrative-placeholder finding.

## Out of scope

- Changes to `governance_02_documentation-metadata.md` (handled in the related REQ-002 document).
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
- **Requirement ID**: REQ-002: Make example-link placeholders explicitly illustrative
- **Source issue**: issues/20260926-174633_cleanup-batch-for-governance-docs:-stale-plan-ref,-illustrative-example-links,-missing-keywords.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-194234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-063107
- **Related target files**: docs/00_governance/governance_04_documentation-checks.md
