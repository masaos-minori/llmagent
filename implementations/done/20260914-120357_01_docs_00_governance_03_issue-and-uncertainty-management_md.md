## Goal

Elevate `NC-026` (registered chunk file retention/deletion policy gap) from
`docs/00_governance_03_issue-and-uncertainty-management.md` Part 2 (Needs Confirmation)
to a new Known Issue entry in Part 1, since it concerns undocumented operational behavior
rather than an unverified documentation claim. Per REQ-001, REQ-002.

## Scope

- Add one new `#### RAG-006` entry to Part 1 "Active Items" (after `#### RAG-005`, before
  `#### DESIGN-1`)
- Remove the now-superseded `#### NC-026` entry from Part 2 "Active Items"
- Populate all 16 required Known Issue fields per the Part 1 template
- Do NOT invent retention period, deletion trigger, or deletion ownership values

## Assumptions

- The next available Known Issue ID in the `RAG-*` series is `RAG-006`, derived from the
  highest existing `#### RAG-[0-9]+` heading (`RAG-005`)
- `NC-026`'s existing content (Evidence, Impact, Required Action) is current and correct
  as of this Plan's writing, and is reused directly for `RAG-006`'s corresponding fields
- "Elevating" `NC-026` means removing it from Part 2 once `RAG-006` exists in Part 1
- The Plan's frozen `Implementation Target Files` section accurately reflects scope

## Design decisions

- Insert RAG-006 between RAG-005's "- **Recommended Action**:" line (line 156) and
  DESIGN-1's "#### DESIGN-1" heading (line 158)
- Remove NC-026 between its "- **Blocking**: No" line (line 789) and the summary line
  ("No other active items beyond NC-021 through NC-032 above.")
- Populate RAG-006's fields from NC-026's existing content, adapting field names where
  necessary (e.g., NC-026's "Required Action" → RAG-006's "Recommended Action")
- Cross-reference NC-026 in RAG-006's "Related" field

## Alternatives considered

- Retaining NC-026 in Part 2 alongside RAG-006 in Part 1: rejected — this would
  resurrect the exact duplicate-tracking problem the Issue's Recommended Action seeks
  to resolve; Part 2's own removal rule applies once an item "no longer applies to the
  current system" as a Part 2 item
- Adding RAG-006 before RAG-005 instead of after: rejected — entries should be ordered
  numerically to maintain the Known Issues' chronological structure

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. **Add the new `#### RAG-006` entry** to Part 1 "Active Items" (REQ-001)
2. **Remove the `#### NC-026` entry** from Part 2 "Active Items" (REQ-002)

### Method

1. Read `docs/00_governance_03_issue-and-uncertainty-management.md` around lines 156-158
   (Part 1 insertion point) and lines 789-791 (Part 2 removal point)
2. Insert the new RAG-006 entry after line 156
3. Remove the NC-026 entry (lines 666-789)
4. Verify both changes meet acceptance criteria

### Details

**Step 1 — Add RAG-006 to Part 1:**

Current content around lines 156-158:
```
- **Recommended Action**: Accept this limitation and implement periodic cleanup of orphaned vectors, or migrate to a vector store that supports FK constraints. (Note: this is a known, accepted architectural limitation mitigated by deletion ordering, not an active defect being worked.)

#### DESIGN-1
```

After edit, lines 156-180:
```
- **Recommended Action**: Accept this limitation and implement periodic cleanup of orphaned vectors, or migrate to a vector store that supports FK constraints. (Note: this is a known, accepted architectural limitation mitigated by deletion ordering, not an active defect being worked.)

#### RAG-006

- **ID**: RAG-006
- **Title**: Missing operational guidance for rag-src/registered/ file lifecycle
- **Status**: open
- **Severity**: Low
- **Area**: RAG
- **Type**: operational-gap
- **Source**: `scripts/rag/ingestion/file_routing.py`, `scripts/rag/ingestion/ingester.py`
- **Owner**: Team
- **First Found**: 2026-09-13
- **Target**: `docs/03_rag_02_01_ingestion_pipeline-overview.md`, `docs/03_rag_02_04_ingestion_pipeline-ingester.md`
- **Related**: NC-026 (superseded — see Part 2 removal)
- **Summary**: What is the retention/deletion policy for chunk files moved to `rag-src/registered/` after successful ingestion? Who deletes them, when, and under what trigger?
- **Current Description**: After successful ingestion, chunk files are routed to `rag-src/registered/` via `FileRouter`. The File Lifecycle table in the ingestion pipeline overview documents creation but not deletion of these files. No deletion logic exists in `scripts/rag/ingestion/ingester.py` or `file_routing.py`.
- **Observed Implementation**: `FileRouter.__init__` creates `self._registered_dir = registered_dir / path.name`; `FileRouter.route()` writes successful chunks to `dest = self._registered_dir / path.name`. No corresponding cleanup or deletion call anywhere in either file.
- **Impact**: `rag-src/registered/` may grow unbounded over time; files may be deleted ad hoc without traceability if this gap is not tracked with appropriate visibility.
- **Recommended Action**: Owner review required to define the retention period, deletion trigger, and deletion ownership for `rag-src/registered/` files. Until defined, this directory's growth should be monitored.

#### DESIGN-1
```

**Step 2 — Remove NC-026 from Part 2:**

Current content around lines 789-791:
```
- **Blocking**: No

No other active items beyond NC-021 through NC-032 above.
```

After edit, lines 789-791:
```
- **Blocking**: No

No other active items beyond NC-021 through NC-032 above.
```

(Delete the entire NC-026 entry block: lines 666-789 — the `#### NC-026` heading through
its `- **Blocking**: No` line, plus the blank line after it.)

## Compatibility considerations

- Documentation-only change: no production code affected
- Removing NC-026 does not delete any information — it is preserved in RAG-006's fields
- The automated checker tool (`tools/check_needs_confirmation_inventory.py`) will no
  longer find NC-026 as a stale-resolved marker since it is removed entirely
- Future readers could still find the underlying policy question unresolved even after
  reclassification — this is explicitly out of scope (the question remains open pending
  Owner review)

## Security considerations

N/A: documentation update, no security-sensitive operations.

## Rollback considerations

- Revert both edits (insert RAG-006, remove NC-026) to restore original document
- No data loss risk — only additive/removal documentation changes

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Governance inventory consistency check | uv run python tools/check_needs_confirmation_inventory.py | No new errors/warnings attributable to the NC-026 removal or RAG-006 addition |
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation structure/quality check | uv run python tools/check_docs_quality.py && uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md | No new structural/formatting findings |

## Completion criteria

- [ ] New `#### RAG-006` entry inserted between RAG-005 and DESIGN-1
- [ ] All 16 template fields populated (ID, Title, Status, Severity, Area, Type, Source,
      Owner, First Found, Target, Related, Summary, Current Description, Observed
      Implementation, Impact, Recommended Action)
- [ ] `Type`: operational-gap
- [ ] `Status`: open
- [ ] `Area`: RAG
- [ ] `Related`: NC-026 (superseded — see Part 2 removal)
- [ ] No invented retention period, deletion trigger, or deletion-owner value
- [ ] `#### NC-026` entry removed from Part 2
- [ ] `uv run python tools/check_needs_confirmation_inventory.py` reports no new errors
- [ ] `uv run python tools/check_docs_quality.py` reports no new findings
- [ ] `uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md` reports no new findings

## Out of scope

- Determining or documenting the actual retention period, deletion trigger, or deletion
  ownership for `rag-src/registered/`
- Modifying `docs/03_rag_02_01_ingestion_pipeline-overview.md`,
  `docs/03_rag_02_04_ingestion_pipeline-ingester.md`, or any source code

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | N/A: documentation validated by tooling |
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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260913-183016_missing_ingestion_file_lifecycle_policy.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-092113_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-120357
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
