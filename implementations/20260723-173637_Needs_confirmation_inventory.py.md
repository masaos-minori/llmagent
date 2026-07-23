## Goal

Turn the Needs Confirmation inventory into an actionable uncertainty-management tool by adding priority classification, related-item tracking, resolution targets, and blocking indicators, then apply initial prioritization and audit major design documents for evidence-label consistency.

## Scope

**In**:
- Add Priority, Related NC, Resolution Target, Blocking fields to `00_governance_07_needs-confirmation-inventory.md`
- Document Japanese priority values (High/Medium/Low)
- Apply initial prioritization to NC-003, NC-008, NC-010, NC-014
- Audit 6 major design documents for evidence-label usage normalization

**Out**:
- Resolving any individual NC items
- Creating a new evidence label system
- Modifying non-major-design documents
- Changing existing evidence label definitions

## Assumptions

1. All target governance and design documents exist at their expected paths.
2. The existing NC IDs (NC-001 through NC-017) are stable and should not be renamed.
3. Evidence labels defined in `00_governance_03_evidence-labels.md` are the canonical reference.

## Design decisions

- Append four new fields after "Last Reviewed" in each NC entry rather than reordering existing fields.
- Use exact field names specified in the requirement.
- Prioritize only the four items mentioned in the requirement; leave others without priority until future triage.
- Preserve all existing content — no deletions or rewrites.

## Alternatives considered

- Reorder all fields to put Priority first: increases diff churn across all entries.
- Create a separate priority classification document: fragments the inventory unnecessarily.
- Auto-classify priorities based on Impact field: introduces subjective logic not yet validated.

## Implementation

### Target file

`docs/00_governance_07_needs-confirmation-inventory.md`, 6 major design documents for evidence-label audit

### Procedure

1. Verify all target documents exist at expected paths
2. Read `00_governance_07_needs-confirmation-inventory.md` and locate end of Inventory Entry Fields section
3. Add Priority, Related NC, Resolution Target, Blocking field definitions after Last Reviewed in Inventory Entry Fields section
4. Add Japanese priority values subsection under Inventory Entry Fields section
5. For each of NC-003, NC-008, NC-010, NC-014: add Priority, Resolution Target, Blocking fields with values
6. Audit 6 major design documents for evidence-label usage against `00_governance_03_evidence-labels.md`
7. Normalize evidence labels only where clarity materially improves

### Method

Append new field definitions and values to existing inventory document; audit design documents for consistency.

### Details

```markdown
# In 00_governance_07_needs-confirmation-inventory.md (add after Last Reviewed in Inventory Entry Fields):

12. **Priority** — Classification of urgency: High (must resolve before next release), Medium (resolve within sprint), Low (nice-to-have)
13. **Related NC** — Other NC items that share the same root cause or dependency
14. **Resolution Target** — Date or milestone by which this item should be resolved
15. **Blocking** — Whether this item blocks other work (Yes/No)

# Add subsection after Inventory Entry Fields:

### プライオリティ値（日本語）

- **高** (High) — 次のリリース前に解決必須
- **中** (Medium) — スプリント内で解決すべき
- **低** (Low) — やりたいが必須ではない
```

For NC-003 (ETagManager bug):
```markdown
- **Priority**: High
- **Resolution Target**: Next sprint
- **Blocking**: Yes
```

For NC-008 (workflow_id multi-workflow):
```markdown
- **Priority**: High
- **Resolution Target**: Next sprint
- **Blocking**: Yes
```

For NC-010 (gen_rag_reference.py output target):
```markdown
- **Priority**: Medium
- **Resolution Target**: Current sprint
- **Blocking**: No
```

For NC-014 (same root cause as NC-010):
```markdown
- **Priority**: Medium
- **Resolution Target**: Current sprint
- **Blocking**: No
- **Related NC**: NC-010
```

## Compatibility considerations

None — only appends to existing document; no behavioral changes.

## Security considerations

N/A — documentation-only change.

## Rollback considerations

Remove appended field definitions and values from both sections; no data migration or config changes required.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Markdown rendering | Manual review | Correct rendering |
| Governance consistency | Manual review | No contradictions with existing rules |

## Out of scope

- Resolving any individual NC items
- Creating a new evidence label system
- Modifying non-major-design documents
- Changing existing evidence label definitions

## Traceability

- Workflow phase: plan-to-implementation-procedure
- Source issue: N/A
- Source requirement: N/A
- Source plan: plans/20260723-165042_plan.md
- Source implementation procedure: N/A
- Generated at: 20260723-173637
- Related target files: Implementation-dependent — needs confirmation inventory, design documents
