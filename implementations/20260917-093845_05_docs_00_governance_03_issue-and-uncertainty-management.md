## Goal

Remove `NC-027`, `NC-028`, `NC-034`, `NC-035` from Part 2's Active Items and add a consolidation-decision note recording that all four entries were reviewed and resolved together as one tuning-parameter pass. Per REQ-005, REQ-006; AC-2, AC-3.

## Scope

- Delete four NC entries from the Active Items section
- Insert a single consolidation-decision note in their place
- Documentation-only change — no code modification

## Assumptions

- The source issue's Constraint ("Keep each Needs Confirmation entry open until rationale or an explicit heuristic marker exists at the definition site") is read as the controlling instruction — an explicit heuristic marker is sufficient grounds to close an entry
- REQ-001 through REQ-004 satisfy that condition for all four entries (heuristic markers added at each constant's definition site)
- The consolidation decision applies uniformly to all four entries since the chunk-splitter and crawler constants interact as noted in the source issue

## Design decisions

- Place the consolidation note where the four removed entries previously sat in Part 2's Active Items, preserving the document's structural flow
- Record a future measurement/benchmark pass as recommended follow-up work (not performed by this Plan)

## Alternatives considered

- Removing each entry individually without a consolidated note: rejected because the source issue requires recording the consolidation decision
- Resolving entries one-by-one with separate notes: rejected because the source issue groups them under NC-034 and NC-035

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

Delete four NC entries and insert a consolidation-decision note.

### Method

Edit Part 2's Active Items section: remove NC-027, NC-028, NC-034, NC-035 entries; insert a consolidation note in their place.

### Details

**REQ-005: Remove four NC entries.**

Current state (lines 630-663):
```
#### NC-027

- **Source File**: `03_rag_02_03_ingestion_pipeline-chunksplitter.md`
... [full NC-027 body] ...
- **Blocking**: No

#### NC-028

- **Source File**: `03_rag_02_08_ingestion_pipeline-shared.md`
... [full NC-028 body] ...
- **Blocking**: No
```

Current state (lines 755-787):
```
#### NC-034

- **Source File**: `chunk_splitter.py` / `config/chunk_splitter.toml`
... [full NC-034 body] ...
- **Blocking**: No

#### NC-035

- **Source File**: `crawler.py` / `config/crawler.toml`
... [full NC-035 body] ...
- **Blocking**: No
```

**REQ-006: Add consolidation-decision note.**

Insert the following prose note where the four removed entries previously sat (after the last remaining entry before NC-027, i.e., after NC-026):
```
**Consolidation note (2026-09-17)**: NC-027, NC-028, NC-034, and NC-035 were reviewed and resolved together as one tuning-parameter pass. All four tracked undocumented tuning constants received explicit "unvalidated heuristic, pending performance tuning" markers at their definition sites (see `scripts/rag/ingestion/chunk_splitter.py`, `scripts/rag/repository.py`, `config/chunk_splitter.toml`, `config/crawler.toml`). No recoverable rationale was found for any of the seven constants via repository history or originating issues. Recommended future follow-up: a measurement/benchmark pass against actual retrieval quality to validate these values — not performed by this Plan.
```

Also update the closing sentence on line 789 from "No other active items beyond NC-021 through NC-035 above." to reflect the removal of these four entries.

## Compatibility considerations

N/A: documentation-only change, no runtime behavior impact.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

If the consolidation note proves inaccurate later, the rollback is removing the inserted note and restoring the four NC entries — no code revert needed.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Documentation structural check | `uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md` | Passes with no new findings |
| docs/00_governance_03_issue-and-uncertainty-management.md | Manual re-scan | `grep -n "^#### NC-027\|^#### NC-028\|^#### NC-034\|^#### NC-035"` | No output |

## Completion criteria

- [ ] AC-2: NC-027, NC-028, NC-034, NC-035 are removed from the Part 2 active inventory
- [ ] AC-3: A consolidation decision is recorded in the document

## Out of scope

- Changing any NC entry's Status value
- Editing `docs/03_rag_*.md` specification documents' own inline markers (a separate concern from the inventory entries this Plan resolves)
- Adding retrieval-quality regression tests
- Running an actual measurement/benchmark pass

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Remove NC-027, NC-028, NC-034, NC-035 from Active Items | Pending | — | — | |
| 2 | Add consolidation-decision note | Pending | — | — | |
| 3 | Update closing sentence | Pending | — | — | |
| 4 | Run validation sequence (check_docs_quality.py) | Pending | — | — | |

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
- **Requirement ID**: REQ-005, REQ-006
- **Source issue**: issues/20260915-200627_rag03_establish-rationale-for-undocumented-chunking-and-crawler-tuning-constants.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260916-153123_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260917-093845
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
