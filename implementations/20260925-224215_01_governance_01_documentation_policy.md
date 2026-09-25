# Implementation Procedure: Add Bidirectional Consumer Reference to Maintenance Rules

## Goal

Add a "Consumed by" cross-reference line after the three Maintenance Rules bullets in `docs/00_governance/governance_01_documentation-policy.md`, establishing bidirectional awareness with `docs/00_governance/governance_04_documentation-checks.md`. Driven by REQ-001.

## Scope

- **In-Scope**: Insert a single "- Consumed by:" cross-reference line after line 524 in `docs/00_governance/governance_01_documentation-policy.md`
- **Out-of-Scope**: Modifying the three Maintenance Rules bullet points; modifying `docs/00_governance/governance_04_documentation-checks.md`; applying this pattern to other sections

## Assumptions

- The "Consumed by" convention is acceptable for this repository's governance writing style
- The cross-reference format `- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)` follows the same convention as other cross-references in the policy document (e.g., `[Policy's Merge Conditions]`, `[Policy's Review Rule]`)
- Only the policy document needs modification; the checks document already correctly references the policy document

## Design decisions

- Use "Consumed by" phrasing as stated in the Plan. If adversarial verification during implementation reveals that existing cross-references in the policy document use a different convention (e.g., "Referenced in"), adjust accordingly.
- The cross-reference uses a relative path (`00_governance_04_documentation-checks.md`) consistent with the existing cross-reference from the checks document back to the policy document at line 377: `See [Policy's Maintenance Rules](governance_01_documentation-policy.md#maintenance-rules)`.

## Alternatives considered

- **"Referenced in"** — equivalent phrasing if "Consumed by" does not align with existing conventions
- **Anchor-based link** — e.g., `[Documentation Checks](00_governance_04_documentation-checks.md#maintenance-rules)` — but the checks document's cross-reference does not use an anchor, so consistency suggests omitting it here too

## Implementation

### Target file

`docs/00_governance/governance_01_documentation-policy.md`

### Procedure

Insert a single line after line 524 (the third Maintenance Rules bullet):

```markdown
- Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)
```

Preserve all other characters on surrounding lines. No restructuring, no content changes to the bullets themselves.

### Method

1. Open `docs/00_governance/governance_01_documentation-policy.md`
2. Locate line 524: `- "Needs confirmation" items must be reviewed quarterly`
3. Verify line 526 exists and contains `## Non-Goals`
4. Insert the new line between lines 524 and 526:
   ```markdown
   - Consumed by: [Documentation Checks](00_governance_04_documentation-checks.md)
   ```
5. Ensure the inserted line has the same indentation level as the existing bullet points (single dash followed by space)

### Details

- The inserted line must match the bullet-point style of the Maintenance Rules section (dash-space prefix)
- The link text `[Documentation Checks]` matches the title used in the checks document's cross-reference at line 377
- The link target `00_governance_04_documentation-checks.md` is a relative path from the policy document's directory, consistent with the existing cross-reference at line 544 which also uses a relative path
- No anchor fragment is added because the checks document's reverse reference does not include one
- After insertion, verify that line numbers shift by +1 for all subsequent lines (line 526 becomes line 527, etc.)

## Compatibility considerations

- The change adds a single cross-reference line; it does not modify any existing content
- The cross-reference format must be consistent with existing patterns in the policy document (verified against line 377 in the checks document)
- If the "Consumed by" convention is not present elsewhere in the policy document, consider using "Referenced in" instead for consistency

## Security considerations

N/A: This is a documentation-only change with no security implications.

## Rollback considerations

Simple rollback: remove the inserted line. No data loss risk since only a single line is added.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_01_documentation-policy.md` | Static link-reachability check | `uv run python tools/check_docs_structure.py docs/00_governance/governance_01_documentation-policy.md` | No `broken link` errors; size/H1/front-matter within limits |

## Completion criteria

- The "Consumed by" cross-reference line appears after the three Maintenance Rules bullets in `docs/00_governance/governance_01_documentation-policy.md`
- The three original Maintenance Rules bullet points remain unchanged
- No additional content beyond the single cross-reference line is present
- `check_docs_structure.py` reports no new broken links for the policy document

## Out of scope

- Detecting indirect circular references (A→B→A chains)
- Auto-fixing self-references (report-only, like other structural checks)
- Validating self-references in non-Markdown files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | REQ-001 — Verify cross-reference format in checks document (UNK-01) | Pending | — | — | |
| 2 | REQ-001 — Insert "Consumed by" cross-reference in policy document | Pending | — | — | |
| 3 | REQ-004 — Validate with `check_docs_structure.py` | Pending | — | — | |

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
- **Requirement ID**: REQ-001 — Add bidirectional consumer reference to Maintenance Rules
- **Source issue**: issues/20260925-133802_l004_duplicate-maintenance-rules-text-across-governance-docs.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260925-204505_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260925-224215
- **Related target files**: docs/00_governance/governance_01_documentation-policy.md
