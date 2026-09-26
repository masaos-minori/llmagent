## Goal

Investigate data-quality problems in Part 1 (Known Issues) and Part 2 (Needs Confirmation) of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: determine root causes of five NC-ID gaps between the closing statement's contiguous range assertion and the actual active list, and confirm dangling `Related` field references to non-existent Known Items. Then apply minimal corrections consistent with findings.

## Scope

Investigating the status of NC-022/026/030/032/038 and CI-001/003/007; correcting the Part 2 closing statement and Part 1 `Related` fields based on findings. No changes to Part 3 or Part 4; no changes to any other governance document.

## Assumptions

- The Current-Specification-Only Policy in Part 1 requires removal of resolved entries, not relocation to another section.
- The `Status=resolved` values for CI-001/003/007 accurately reflect their resolution state.
- The NC closing statement's contiguous range claim is incorrect regardless of whether the gaps represent resolved items or missing items.

## Design decisions

- Investigation-first approach: check git history and resolution records before applying corrections.
- Minimal correction: fix the closing statement to describe the active set without asserting a false contiguous range; update or clear dangling `Related` fields.
- Do not fabricate resolutions or invent new items.

## Alternatives considered

- Rewrite the closing statement to assert a different contiguous range: rejected — would still be incorrect if gaps exist.
- Leave dangling `Related` fields unchanged pending manual review: rejected — violates the removal-placeholder policy.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Investigate NC-ID gaps: search git history for commits that added or removed NC-022/026/030/032/038 entries.
2. Investigate dangling CI references: search git history for commits that added or removed CI-001/003/007 entries.
3. Check for resolution records or follow-up issues documenting the removal of these IDs.
4. Based on investigation findings, rewrite the Part 2 closing statement to accurately reflect the active NC-ID set.
5. Update the `Related` fields of CI-009, CI-010, CI-014, and CI-015 to drop absent CI-001/003/007 references.
6. Verify the Part 2 closing statement matches the actual active NC-ID set.
7. Verify every `Related` field reference in Part 1 points to an item present in the current inventory.

### Method

Investigation (git log + record search) followed by targeted edits.

### Details

**Step 1: Investigate NC-ID gaps**

Search git history for commits that affected NC-022, NC-026, NC-030, NC-032, NC-038:
```bash
cd /home/sugimoto/llmagent && git log --all --oneline -- docs/00_governance/governance_03_issue-and-uncertainty-management.md | rg 'NC-02[26]|NC-03[028]'
```

Also check for resolution records or follow-up issues:
```bash
rg -l 'NC-022|NC-026|NC-030|NC-032|NC-038' issues/ issues/done/ plans/ plans/done/ implementations/ implementations/done/ 2>/dev/null || true
```

Record findings: were these IDs legitimately resolved/removed, or are they genuinely missing?

**Step 2: Investigate dangling CI references**

Search git history for commits that affected CI-001, CI-003, CI-007:
```bash
cd /home/sugimoto/llmagent && git log --all --oneline -- docs/00_governance/governance_03_issue-and-uncertainty-management.md | rg 'CI-00[137]'
```

Check for resolution records:
```bash
rg -l 'CI-001|CI-003|CI-007' issues/ issues/done/ plans/ plans/done/ implementations/ implementations/done/ 2>/dev/null || true
```

Confirm whether CI-001/003/007 entries were fully removed (not just resolved).

**Step 3: Record investigation findings**

Document the root cause for each gap:
- For each NC gap: resolved/removed vs. still-open
- For each dangling CI ref: intentionally gone vs. should be restored

**Step 4: Rewrite Part 2 closing statement**

Current statement (line 727):
```
No other active items beyond NC-021 through NC-039 above.
```

Replace with a statement that accurately reflects the active NC-ID set without asserting a contiguous range. Based on investigation findings:
- If gaps are resolved/removed: e.g., "No other active items beyond NC-021 through NC-039 above, excluding NC-022, NC-026, NC-030, NC-032, and NC-038 which are resolved."
- If evidence is inconclusive: use neutral language such as "No other active items beyond NC-021 through NC-039 above." (remove the implication of contiguity while preserving the upper bound).

**Step 5: Update dangling Related fields**

Based on investigation findings from Step 2, update the following `Related` fields:

- CI-009 (line 229): Change `- **Related**: ADR-002, CI-001` to `- **Related**: ADR-002` (remove CI-001 if confirmed removed).
- CI-010 (line 249): Change `- **Related**: ADR-003, CI-003, CI-015` to `- **Related**: ADR-003, CI-015` (remove CI-003 if confirmed removed; keep CI-015 which is active).
- CI-014 (line 329): Change `- **Related**: ADR-009, CI-007` to `- **Related**: ADR-009` (remove CI-007 if confirmed removed).
- CI-015 (line 349): Change `- **Related**: ADR-003, CI-003, CI-010` to `- **Related**: ADR-003, CI-010` (remove CI-003 if confirmed removed; keep CI-010 which is active).

If investigation reveals that any of CI-001/003/007 should be restored rather than removed, adjust accordingly — do not remove references to items that should remain.

**Step 6: Verify Part 2 closing statement**

Confirm the rewritten closing statement:
- Matches the actual active NC-ID set
- Does not assert a contiguous range containing gaps
- Is consistent with investigation findings from Steps 1-3

**Step 7: Verify Related fields**

Confirm every `Related` field reference in Part 1 points to an item present in the current inventory:
- No dangling CI-001/003/007 references remain
- All remaining cross-references point to active entries

## Compatibility considerations

This change affects only the Part 2 closing statement and Part 1 `Related` fields. No downstream artifact consumes these sections programmatically — they are human-reviewed documentation and known-issue checks. No backward compatibility impact.

## Security considerations

None. This is a documentation-only edit with no code or configuration changes.

## Rollback considerations

Rollback is straightforward: restore the original closing statement and `Related` fields. A single `git checkout -- docs/00_governance/governance_03_issue-and-uncertainty-management.md` reverses the entire change.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Manual verification against Part 2 active NC list and Part 1 active Known Items | Read both sections side-by-side | Closing statement matches actual NC-ID set; no dangling CI-001/003/007 references in Related fields |
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Optional structural check | `uv run python tools/check_docs_structure.py docs/00_governance/*.md` | No new structural findings |

## Completion criteria

- The Part 2 closing statement matches the actual active NC-ID set and does not assert a contiguous range that contains gaps.
- Every `Related` field reference in Part 1 points to an item present in the current inventory; no dangling CI-001/003/007 references remain.
- Investigation findings are documented in the procedure notes.

## Out of scope

- Any change to Part 2 Needs Confirmation items themselves (only the closing statement prose).
- Adding or removing Needs Confirmation items based on this issue's own judgment.
- Changing the lifecycle/status vocabulary.
- Editing any part other than Part 1 `Related` fields and Part 2's closing statement.
- Editing any other governance document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate NC-ID gaps via git history and resolution records | Pending | — | — | REQ-001 |
| 2 | Investigate dangling CI refs via git history and resolution records | Pending | — | — | UNK-02 |
| 3 | Rewrite Part 2 closing statement based on findings | Pending | — | — | REQ-002 |
| 4 | Update CI-009 Related field to remove CI-001 reference | Pending | — | — | REQ-003 |
| 5 | Update CI-010 Related field to remove CI-003 reference | Pending | — | — | REQ-003 |
| 6 | Update CI-014 Related field to remove CI-007 reference | Pending | — | — | REQ-003 |
| 7 | Update CI-015 Related field to remove CI-003 reference | Pending | — | — | REQ-003 |
| 8 | Verify Part 2 closing statement matches actual NC-ID set | Pending | — | — | REQ-002 |
| 9 | Verify all Related field references point to active items | Pending | — | — | REQ-003 |
| 10 | Preserve ID-group ordering convention of both parts | Pending | — | — | REQ-004 |
| 11 | Leave all item substantive content unchanged beyond Related fields/closing statement | Pending | — | — | REQ-005 |
| 12 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005
- **Source issue**: issues/20260926-174250_investigate-nc-id-gaps-and-dangling-related-refs-in-governance_03-inventory.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260926-191144_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260927-061201
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
