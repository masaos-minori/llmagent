# Implementation Procedure: Add canonical-source section to overview_00_document-guide.md

## Goal

Add a canonical-source section to `docs/01_overview/overview_00_document-guide.md` that references the Canonical Source Registry, since the document currently has no canonical-source section.

## Scope

- Modify only `docs/01_overview/overview_00_document-guide.md`.
- In-Scope: Add a canonical-source section referencing the Registry.
- Out-of-Scope: Adding Registry entries for Overview (REQ-002); updating other area Document Guides (REQ-004–REQ-009); updating Needs Confirmation Inventory (REQ-003).

## Assumptions

- The Overview area Document Guide currently has no canonical-source section, unlike other area guides.
- A candidate replacement for `docs/architecture.md` was identified during canon001 investigation: `docs/01_overview/overview-arch-01-process.md`.

## Design decisions

- **Approach**: Add a canonical-source section similar to how other area guides express their canonical-source declarations, but defer to the Registry as the system of record.
- **Registry-first principle**: The Overview area guide should not maintain its own canonical-source mapping; it should point to the Registry.

## Alternatives considered

- Add a direct canonical-source table for the Overview area: rejected — contradicts the Policy's explicit statement that the Registry supersedes hand-maintained mappings.
- Leave the section absent: rejected — the area guide should have a canonical-source section for consistency with other area guides.

## Implementation

### Target file

`docs/01_overview/overview_00_document-guide.md`

### Procedure

1. Identify the appropriate location in the document for a canonical-source section.
2. Add a canonical-source section referencing the Registry.

### Method

Edit `docs/01_overview/overview_00_document-guide.md` in-place using targeted edits.

### Details

**Step 1: Identify insertion point**

Find the end of the existing content sections (before any appendix or references) to insert the canonical-source section.

**Step 2: Add canonical-source section**

Insert the following section:

```markdown
## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.
```

## Compatibility considerations

- The addition of a new section may affect the document's structure index or navigation.
- If the area guide previously had implicit canonical-source assumptions, they are now explicitly deferred to the Registry.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Remove the added canonical-source section.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/01_overview/overview_00_document-guide.md` | Structure check | `uv run python tools/check_docs_structure.py` | Pass |
| `docs/01_overview/overview_00_document-guide.md` | Quality check | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- A canonical-source section exists in the Overview area Document Guide.
- The section references the Canonical Source Registry in the Policy.
- No independent canonical-source mapping remains in the area guide.

## Out of scope

Adding Registry entries for Overview (REQ-002). Updating other area Document Guides (REQ-004–REQ-009). Updating Needs Confirmation Inventory (REQ-003). Fixing the `eventbus.persistence-schema` Registry validation failure (canon002).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Identify insertion point | Pending | — | — | REQ-007 |
| 2 | Add canonical-source section | Pending | — | — | REQ-007 |

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
- **Requirement ID**: REQ-007 — classify nonexistent canonical source paths in documentation policy and align Policy, Registry, and Document Guides
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222351_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224049
- **Related target files**: docs/01_overview/overview_00_document-guide.md
