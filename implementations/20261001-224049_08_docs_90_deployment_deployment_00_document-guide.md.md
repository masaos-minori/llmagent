# Implementation Procedure: Align deployment_00_document-guide.md with Registry

## Goal

Align the canonical-source section in `docs/90_deployment/deployment_00_document-guide.md` with the Canonical Source Registry, removing its independent hand-edited mapping.

## Scope

- Modify only `docs/90_deployment/deployment_00_document-guide.md`.
- In-Scope: Replace the area's own canonical-source table/rule with a reference to the Registry.
- Out-of-Scope: Adding Registry entries for Deployment (REQ-002); updating other area Document Guides (REQ-004–REQ-009); updating Needs Confirmation Inventory (REQ-003).

## Assumptions

- The area Document Guide currently maintains its own canonical-source mapping, contradicting the Policy's statement that the Registry supersedes hand-maintained mappings.
- A valid canonical source for Deployment was confirmed during canon001 investigation: `deploy/deploy.sh`.

## Design decisions

- **Approach**: Replace the area's independent canonical-source section with a subsection stating that canonical sources are defined in the Registry, consistent with how `docs/24_eventbus/eventbus_00_document-guide.md` defers to the Registry.
- **Handling confirmed canonical source**: Since a valid Deployment canonical source was identified (`deploy/deploy.sh`), it will be registered in the Registry during REQ-002 execution.

## Alternatives considered

- Keep the area's canonical-source section and mark it as derived from the Registry: rejected — the area guide should not maintain its own mapping even if derived.
- Delete the canonical-source section entirely: rejected — the section serves as a pointer to where canonical sources are defined.

## Implementation

### Target file

`docs/90_deployment/deployment_00_document-guide.md`

### Procedure

1. Locate the canonical-source section or rules in the document.
2. Replace it with a subsection referencing the Registry.

### Method

Edit `docs/90_deployment/deployment_00_document-guide.md` in-place using targeted edits.

### Details

**Step 1: Locate the canonical-source section**

Search for the canonical-source mapping section or rules in the document.

**Step 2: Replace with Registry reference**

Replace the entire canonical-source section with:

```markdown
## Canonical Sources

Canonical sources for this area are defined in the [Canonical Source Registry](../00_governance/governance_01_documentation-policy.md#canonical-source-registry). This area guide does not maintain an independent mapping.
```

## Compatibility considerations

- Existing references to the area's own canonical-source rules will need to be updated by downstream consumers.
- If the area guide previously cited specific source paths, those citations are now invalid until new Registry entries are added.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Restore the original canonical-source section with its independent mapping.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/90_deployment/deployment_00_document-guide.md` | Structure check | `uv run python tools/check_docs_structure.py` | Pass |
| `docs/90_deployment/deployment_00_document-guide.md` | Quality check | `uv run python tools/check_docs_quality.py` | Pass |

## Completion criteria

- The area's independent canonical-source section is replaced with a Registry reference.
- The Registry reference points to the correct location in the Policy.
- No contradictory canonical source declaration remains in the area guide.

## Out of scope

Adding Registry entries for Deployment (REQ-002). Updating other area Document Guides (REQ-004–REQ-009). Updating Needs Confirmation Inventory (REQ-003). Fixing the `eventbus.persistence-schema` Registry validation failure (canon002).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate the canonical-source section | Pending | — | — | REQ-008 |
| 2 | Replace with Registry reference | Pending | — | — | REQ-008 |

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
- **Requirement ID**: REQ-008 — classify nonexistent canonical source paths in documentation policy and align Policy, Registry, and Document Guides
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222351_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224049
- **Related target files**: docs/90_deployment/deployment_00_document-guide.md
