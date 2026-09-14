## Goal

Add a new Needs Confirmation Inventory entry (NC-033) in
`docs/00_governance_03_issue-and-uncertainty-management.md` for the untracked
`lang` field enforcement marker in `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md`,
so the item is trackable to resolution rather than silently accepted as fact. Per REQ-001.

## Scope

- Append exactly one new `#### NC-033` entry to Part 2 inventory section of
  `docs/00_governance_03_issue-and-uncertainty-management.md`
- Populate all 15 required fields per the Entry Template
- Modeled on the existing `#### NC-027` entry (same Source File value, different Section/Line Number/Question/Evidence)

## Assumptions

- The next available ID is `NC-033`, derived from the highest existing `#### NC-\d+` heading
  (`NC-032`) found via grep across the full inventory file
- The inline marker text at `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` line 194
  (Plan claims line 192; discrepancy noted during adversarial verification) is accurate
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Insert the new entry between NC-032's "- **Blocking**: No" line and the summary line
  ("No other active items beyond NC-021 through NC-032 above.")
- Use the same field structure and tone as the existing NC-027 entry for consistency
- Include the pending approval ID in the denial message for debugging purposes

## Alternatives considered

- Using a different field order for the NC-033 entry: rejected — following the existing
  template ensures consistency with the automated checker tool
- Adding the entry before NC-027 instead of after NC-032: rejected — entries should be
  ordered numerically to maintain the inventory's chronological structure

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. **Locate the insertion point** — between NC-032's "- **Blocking**: No" line (line 789)
   and the summary line (line 791)

2. **Insert the new NC-033 entry** with all 15 fields populated

### Method

1. Read `docs/00_governance_03_issue-and-uncertainty-management.md` around lines 789-791
2. Insert the new entry after line 789 (before the summary line)
3. Verify the entry has all 15 required fields

### Details

**Step 1 — Locate the insertion point:**

Current content around lines 789-791:
```
- **Blocking**: No

No other active items beyond NC-021 through NC-032 above.
```

**Step 2 — Insert the new NC-033 entry:**

After edit, lines 789-806:
```
- **Blocking**: No

#### NC-033

- **Source File**: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- **Section**: lang Field Validation
- **Line Number**: ~194
- **Question**: Is `lang` field enforcement against `LanguageCode` values intended?
- **Evidence**: The document states: "any non-empty string accepted; the en/ja value set
  (LanguageCode) is convention only — not enforced at parse time (Needs confirmation: whether
  enforcement is intended)"
- **Impact**: If lang-field enforcement is actually intended but not implemented, downstream
  language-handling code could behave incorrectly without anyone flagging it as an open question
- **Required Action**: Owner confirmation or investigation of scripts/rag/ validation logic
  for the lang field
- **Status**: open
- **Assigned To**: Unassigned
- **Last Reviewed**: 2026-09-14
- **Priority**: Low
- **Related NC**: None
- **Resolution Target**: Next ChunkSplitter specification review
- **Blocking**: No

No other active items beyond NC-021 through NC-032 above.
```

Note: Line number adjusted to ~194 (actual location of the marker in the chunksplitter doc,
corrected from the Plan's claim of line 192).

## Compatibility considerations

- Documentation-only change: no production code affected
- New entry follows the existing format exactly — no structural changes to the inventory
- The automated checker tool (`tools/check_needs_confirmation_inventory.py`) tracks coverage
  per Source File, so this addition does not affect its behavior for the already-tracked file

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert the single insert step above to restore original inventory
- No data loss risk — only additive documentation change

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Governance inventory consistency check | uv run python tools/check_needs_confirmation_inventory.py | No new errors/warnings attributable to the NC-033 addition |
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md | No new structural/formatting findings |

## Completion criteria

- [ ] New `#### NC-033` entry inserted between NC-032 and the summary line
- [ ] All 15 template fields present and non-empty
- [ ] **Source File**: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
- [ ] **Line Number**: ~194 (actual location of the marker)
- [ ] **Question**: whether `lang` field enforcement against `LanguageCode` values is intended
- [ ] **Evidence**: quote of the inline marker text
- [ ] **Status**: open
- [ ] **Assigned To**: Unassigned
- [ ] **Priority**: Low
- [ ] **Related NC**: None
- [ ] **Resolution Target**: Next ChunkSplitter specification review
- [ ] **Blocking**: No
- [ ] `uv run python tools/check_needs_confirmation_inventory.py` reports no new errors
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` reports no new findings

## Out of scope

- Investigating or resolving whether `lang` field enforcement is actually intended
- Modifying `docs/03_rag_02_03_ingestion_pipeline-chunksplitter.md` itself
- Modifying any source code (`scripts/rag/...`)
- Fixing the file-scoped detection limitation of `tools/check_needs_confirmation_inventory.py`

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: governance doc validated by tooling |
| 3 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A: docstring update in Phase 2 |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260913-183003_lang_enforcement_needs_confirmation.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-091010_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-115646
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
