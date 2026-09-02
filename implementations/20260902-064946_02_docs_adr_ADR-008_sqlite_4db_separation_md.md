# Implementation Procedure: Update ADR-008 Known Deviations entry

## Goal

Update ADR-008's Known Deviations section to mark the INV-17 gap resolved, per REQ-003.

## Scope

**In-Scope**: Update the Known Issue entry at line ~435 of ADR-008 to reflect that the INV-17 violation has been fixed.

**Out-of-Scope**: Modify any other sections of ADR-008; add new Known Issues; change ADR-008 structure or formatting beyond the Known Issue entry.

## Assumptions

- The fix in `scripts/db/recovery.py` (separate implementation procedure) has been implemented and validated before this documentation update.
- The Known Issue entry text should clearly state what was changed and why it is now resolved.
- The existing Known Issue formatting style should be preserved for consistency.

## Design decisions

- Change the Known Issue status from "not yet fixed" to "resolved".
- Update the Summary and Impact fields to describe the current state post-fix.
- Remove the Resolution Target field since the resolution is complete.
- Keep the entry in the same location within the Known Issues section for traceability.

## Alternatives considered

- **Alternative 1: Move the resolved entry to a "Resolved Issues" subsection.** Rejected: adds unnecessary structural complexity; keeping it in place preserves historical context.
- **Alternative 2: Delete the entry entirely.** Rejected: removes historical record of the gap; future readers may need to understand why INV-17 was initially violated.
- **Alternative 3: Create a new entry with the fix details.** Rejected: duplicates information; the existing entry already documents the issue and its resolution.

## Implementation

### Target file

`docs/adr/ADR-008-sqlite-4db-separation.md`

### Procedure

1. Locate the Known Issue entry at line ~435 (INV-17 violation).
2. Update the entry to reflect the fix:
   - Change the summary to indicate the fix has been applied.
   - Update the Impact field to describe the current state.
   - Remove the Resolution Target field.
   - Add a note indicating when and how the issue was resolved.

### Method

Replace the existing Known Issue block with an updated version:

**Before:**
```markdown
- **Known Issue**: `recover_corruption()`（`scripts/db/recovery.py`）は、Unknown分類（`DbCondition.UNKNOWN`）をCorruption分類と同一に扱い、`rag`/`session`に対しては自動的にバックアップからのリストアを試みる。これはINV-17（Unknownまたは分類不能な障害は対象DBを保持し運用者の介入を要求する）を現時点では満たしていない。
  - **Type**: Implementation Gap
  - **Summary**: Unknown分類がCorruptionと同一挙動になっており、対象DBの保持・運用者介入要求が実装されていない
  - **Impact**: 分類不能な整合性チェック失敗であっても、`rag`/`session`では自動的にリストアが実行され得る
  - **Resolution Target**: `recover_corruption()`のUnknown分類分岐を、リストアを試みずに対象DBを保持し運用者介入を要求する経路へ分離する
```

**After:**
```markdown
- **Resolved Issue**: `recover_corruption()`（`scripts/db/recovery.py`）のUnknown分類（`DbCondition.UNKNOWN`）処理 — INV-17 violation fixed.
  - **Type**: Implementation Gap (Resolved)
  - **Summary**: Unknown分類がCorruptionと同一挙動になっていた問題を修正
  - **Impact**: 分類不能な整合性チェック失敗の場合、`rag`/`session`でも自動的にリストアが実行され得た
  - **Resolution**: `recover_corruption()`にUNKNOWN分岐を追加し、対象DBを保持して運用者介入を要求する経路へ分離した
```

### Details

- Line reference: Replace the Known Issue block starting at line ~435 through line ~439.
- Preserve Japanese language style consistent with surrounding entries.
- Use "Resolved Issue" prefix instead of "Known Issue" to distinguish resolved items.
- Keep the original issue description in the Impact field for historical context.
- Document the resolution approach in the Resolution field.

## Compatibility considerations

- This is a documentation-only change. No code or configuration impact.
- The entry format change ("Known Issue" → "Resolved Issue") should not affect downstream consumers that parse ADR-008 programmatically, as they likely look for the issue content rather than the label.

## Security considerations

- No security implications. This is a documentation update only.

## Rollback considerations

- To rollback: revert the Known Issue entry to its pre-fix state using git history.
- No operational risk — documentation changes are always reversible.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/adr/ADR-008-sqlite-4db-separation.md | Verify entry reflects resolved status | Manual review of Known Issues section | Entry shows "Resolved Issue" with resolution details |
| docs/adr/ADR-008-sqlite-4db-separation.md | Verify no unintended changes elsewhere | `git diff` comparison | Only Known Issue entry modified |

## Completion criteria

- [ ] Known Issue entry at line ~435 updated to show "Resolved Issue" status.
- [ ] Summary field updated to describe the fix.
- [ ] Impact field retained for historical context.
- [ ] Resolution field added describing the fix approach.
- [ ] Resolution Target field removed.
- [ ] No other sections of ADR-008 modified.

## Out of scope

- Modifying any other Known Issues or Known Issues section structure.
- Adding new Known Issues entries.
- Changing ADR-008 formatting conventions or section organization.
- Updating related ADRs (e.g., ADR-011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update ADR-008 Known Deviations entry per Procedure/Method/Details | Pending | — | — | |
| 2 | Validate no unintended changes via git diff | Pending | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260831-181721_adr008_01_recover_corruption_unknown_classification_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260901-064946_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260901-064946
- **Related target files**: docs/adr/ADR-008-sqlite-4db-separation.md
