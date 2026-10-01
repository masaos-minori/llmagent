# Implementation Procedure: Update governance_01_documentation-policy.md

## Goal

Update `docs/00_governance/governance_01_documentation-policy.md` to remove or subordinate the hand-maintained `## Area Canonical Maps` table, resolve all inline `Needs Confirmation — path does not exist in repository` markers, correct the `**Status column note:**` paragraph, and remove references to obsolete plan files.

## Scope

- Modify only `docs/00_governance/governance_01_documentation-policy.md`.
- In-Scope: Replace `## Area Canonical Maps` with a derived-from-Registry subsection; resolve inline Needs Confirmation markers; correct Status column note; remove obsolete plan references.
- Out-of-Scope: Adding Registry entries for uncovered areas (REQ-002); updating area Document Guides (REQ-004–REQ-009); updating Needs Confirmation Inventory (REQ-003).

## Assumptions

- The Policy's size limit (`check_docs_structure.py`) must not be exceeded. Changes should preferably reduce the Policy's size by removing the hand-maintained table.
- Inline Needs Confirmation markers cite paths that were confirmed nonexistent during canon001 investigation.
- References to `plans/done/20260905-185329_plan.md` in current specification text are obsolete.

## Design decisions

- **Approach**: Subordinate `## Area Canonical Maps` to the Registry rather than deleting it entirely — preserves historical context while making clear it is derived.
- **Inline marker resolution**: Remove markers for obsolete references; update markers for renamed paths to point to current locations; register missing-canonical-source gaps as follow-up issues.
- **Status column note correction**: Rewrite to reflect the final table state after subordination.

## Alternatives considered

- Delete the `## Area Canonical Maps` table entirely: rejected — loses historical context needed for understanding why certain paths were originally designated.
- Keep both the table and the Registry as parallel sources: rejected — contradicts the Policy's explicit statement that the Registry supersedes the hand-maintained table.

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

1. Replace the `## Area Canonical Maps` table body with a derived-from-Registry notice.
2. Resolve all inline `Needs Confirmation — path does not exist in repository` markers.
3. Correct the `**Status column note:**` paragraph.
4. Remove references to `plans/done/20260905-185329_plan.md` from current specification text.

### Method

Edit `docs/00_governance/governance_01_documentation-policy.md` in-place using targeted edits.

### Details

**Step 1: Replace `## Area Canonical Maps` table**

Replace the entire `## Area Canonical Maps` section with:

```markdown
## Area Canonical Maps (derived from Registry)

This section is derived from the Canonical Source Registry above.
It is maintained automatically and must not be edited manually.
For the authoritative mapping, see the Registry above.
```

**Step 2: Resolve inline Needs Confirmation markers**

For each marker found in the file:
- If the cited path was confirmed nonexistent (e.g., `docs/architecture.md`, `deploy.sh`): remove the marker and the associated row from the table body.
- If the cited path was renamed (e.g., `docs/00_governance_01_documentation-policy.md` → `docs/00_governance/governance_01_documentation-policy.md`): update the marker to the current path.
- For missing-canonical-source gaps: register as a concrete follow-up issue in `issues/` before removing the marker.

**Step 3: Correct `**Status column note:**` paragraph**

Rewrite the paragraph to reflect that Governance entries are no longer marked `Active` based on nonexistent paths, but are instead derived from the Registry.

**Step 4: Remove obsolete plan references**

Remove any reference to `plans/done/20260905-185329_plan.md` from current specification text.

## Compatibility considerations

- The Policy size limit (`check_docs_structure.py`) must not be exceeded. Changes should preferably reduce the Policy's size.
- Existing references to `plans/done/20260905-185329_plan.md` in current specification text must be removed.

## Security considerations

N/A: documentation-only change; no runtime security surface.

## Rollback considerations

Restore the original `## Area Canonical Maps` table, revert inline marker changes, restore the original Status column note, and restore obsolete plan references.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Structure check | `uv run python tools/check_docs_structure.py` | Pass (size within limit) |
| `docs/00_governance/governance_01_documentation-policy.md` | Quality check | `uv run python tools/check_docs_quality.py` | Pass |
| Repository-wide | Old path removal verification | `grep -n "path does not exist in repository" docs/00_governance/governance_01_documentation-policy.md` | No matches, or every remaining marker has a matching Active Item in the central Inventory |
| Repository-wide | Obsolete plan reference removal | `rg -n "20260905-185329_plan" docs/00_governance/governance_01_documentation-policy.md` | No matches |

## Completion criteria

- `## Area Canonical Maps` is either removed or explicitly derived from/subordinate to the Registry.
- `grep -n "path does not exist in repository" docs/00_governance/governance_01_documentation-policy.md` returns no matches, or every remaining marker has a matching Active Item in the central Inventory.
- The `**Status column note:**` paragraph accurately reflects the final table state.
- No reference to `plans/done/20260905-185329_plan.md` remains in current specification text.
- Policy size does not exceed the limit enforced by `check_docs_structure.py`.

## Out of scope

Adding Registry entries for uncovered areas (REQ-002). Updating area Document Guides (REQ-004–REQ-009). Updating Needs Confirmation Inventory (REQ-003). Writing new area Specification documents. Fixing the `eventbus.persistence-schema` Registry validation failure (canon002). Fixing checker defects (canon003, ncinv001). Correcting wrong governance-document path references outside this file (govpath001). Reducing the Policy below the size limit beyond what this change naturally achieves (docsize001).

## Execution Status

### Execution Status

| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `## Area Canonical Maps` with derived-from-Registry notice | Pending | — | — | REQ-001 |
| 2 | Resolve inline Needs Confirmation markers | Pending | — | — | REQ-001 |
| 3 | Correct `**Status column note:**` paragraph | Pending | — | — | REQ-001 |
| 4 | Remove obsolete plan references | Pending | — | — | REQ-001 |

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
- **Requirement ID**: REQ-001 — classify nonexistent canonical source paths in documentation policy and align Policy, Registry, and Document Guides
- **Source issue**: N/A: no standalone requirement document is generated
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261001-222351_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261001-224049
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
