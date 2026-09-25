# Implementation Procedure: Add "Consumed by" cross-reference to Maintenance Rules in policy document

## Goal

Insert a single "Consumed by" cross-reference line after the three Maintenance Rules bullet points in `docs/00_governance/00_governance_01_documentation-policy.md`, establishing bidirectional awareness with `docs/00_governance/00_governance_04_documentation-checks.md`. Driven by REQ-001.

## Scope

- Insert exactly one line after line 524 in `docs/00_governance/00_governance_01_documentation-policy.md`.
- No changes to the three Maintenance Rules bullet points themselves.
- No changes to any other file.

## Assumptions

- Line 524 is the third Maintenance Rules bullet point; line 526 starts `## Non-Goals`.
- The insertion point is between lines 524 and 526 (after the bullets, before the next heading).
- The cross-reference format `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)` follows the same convention as existing cross-references in the policy document (e.g., `[Policy's Merge Conditions]`, `[Policy's Review Rule]`).
- The checks document already correctly references the policy document's Maintenance Rules section (commit df6cf9eb).

## Design decisions

- Minimal surgical insertion: one line added, no restructuring, no content changes to surrounding bullets.
- Use "Consumed by" phrasing as specified in the plan; adjust to equivalent phrasing only if UNK-01 resolution reveals inconsistency with existing conventions.

## Alternatives considered

- Using "Referenced in" instead of "Consumed by" (rejected unless UNK-01 reveals "Consumed by" is inconsistent with existing conventions).
- Adding a footnote-style reference instead of inline link (rejected: inline links match existing cross-reference style in the policy document).
- Updating both documents simultaneously (rejected: the checks document already has the correct cross-reference; only the policy document needs modification).

## Implementation

### Target file

`docs/00_governance/00_governance_01_documentation-policy.md`

### Procedure

1. Read `docs/00_governance/00_governance_04_documentation-checks.md` line 377 to confirm the existing cross-reference format for consistency (UNK-01 resolution).
2. Verify existing cross-reference conventions in `docs/00_governance/00_governance_01_documentation-policy.md` for consistency (UNK-01 resolution).
3. Locate line 524 in `docs/00_governance/00_governance_01_documentation-policy.md` (third Maintenance Rules bullet).
4. Insert a new line after line 524: `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)`.
5. Preserve all characters on surrounding lines (lines 522-524 bullets remain unchanged; line 526 `## Non-Goals` remains unchanged).

### Method

Edit-only: use the Write tool to insert a new line after line 524. The context around the insertion point before:

```
- [ADR Index](../adr-index.md)
- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)
## Non-Goals
```

The context after:

```
- [ADR Index](../adr-index.md)
- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)
## Non-Goals
```

Note: The inserted line appears between the last Maintenance Rules bullet and the `## Non-Goals` heading.

### Details

- This is a Path A change (≤ 3 files, no public/runtime interface change, no DB schema change).
- The insertion preserves all existing content; only one new line is added.
- After editing, verify:
  - Lines 522-524 are unchanged.
  - Line 525 contains `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)`.
  - Line 526 starts with `## Non-Goals`.

## Compatibility considerations

- This change does not affect runtime behavior, API contracts, or data formats.
- It only affects documentation navigation within the governance docs set.
- The relative link `(00_governance_04_documentation-checks.md)` resolves correctly from the same directory (`docs/00_governance/`).

## Security considerations

N/A: documentation-only change; no code execution, no user input, no authentication.

## Rollback considerations

- Revert the single-line insertion: delete the inserted line after line 524.
- No data loss risk; no downstream dependencies affected.
- No migration or schema rollback needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/00_governance_01_documentation-policy.md` | Static link-reachability check | `uv run python tools/check_docs_structure.py docs/00_governance/00_governance_01_documentation-policy.md` | No `broken link` errors; size/H1/front-matter within limits |

## Completion criteria

- AC-1: Line 525 of `docs/00_governance/00_governance_01_documentation-policy.md` contains `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)`.
- AC-2: Lines 522-524 (three Maintenance Rules bullet points) are unchanged.
- AC-3: No additional content beyond the single cross-reference line is present.
- AC-4: `check_docs_structure.py` reports no new broken links for the policy document.

## Out of scope

- Modifying the three Maintenance Rules bullet points.
- Modifying `docs/00_governance/00_governance_04_documentation-checks.md`.
- Applying this bidirectional pattern to other sections (Merge Conditions, Review Rule, etc.).
- Restructuring the Maintenance Rules section.
- Adding automated link-checking to CI.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | 20260926-062818 |  |
| 2 | Add or update tests per Validation plan | Completed | — | 20260926-062821 | Doc-only change; no tests added |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | 20260926-062825 |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | 20260926-062828 | N/A |

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
- **Requirement ID**: REQ-001 — add "Consumed by" cross-reference to Maintenance Rules section pointing to `docs/00_governance/00_governance_04_documentation-checks.md`
- **Source issue**: issues/20260925-133802_l004_duplicate-maintenance-rules-text-across-governance-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-204505_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-224007
- **Related target files**: docs/00_governance/00_governance_01_documentation-policy.md