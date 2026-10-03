## Goal

Remove dangling clause for DESIGN-2 from `ADR-009-rag-ft5-text-separation.md`, so `check_known_deviation_sync.py` reports no warning for this ID (REQ-001, REQ-002).

## Scope

- Remove the dangling `DESIGN-2` clause from the ADR's `### Known Issues` pointer bullet.
- Preserve surrounding text and other references in the same bullet.

## Assumptions

- DESIGN-2 can be classified as stale/legacy based on git history of `governance_03` and related closing plans.
- Removing a dangling clause from an ADR's `### Known Issues` section does not affect the ADR's decision or invariant.

## Design decisions

- Only remove the specific `ID (...)` clause; preserve surrounding text and other references in the same bullet.
- Never hide IDs behind full-width punctuation or reformat them to evade `_ID_LOOKAHEAD_RE`.

## Alternatives considered

- Add a canonical entry for DESIGN-2 in `governance_03` — rejected pending git history confirmation that it is stale.
- Leave the dangling clause and update the checker — rejected because the checker correctly identifies the problem.

## Implementation

### Target file

`docs/10_adr/ADR-009-rag-ft5-text-separation.md`

### Procedure

1. Confirm DESIGN-2 is stale via git history investigation (same as Row 1).
2. Delete the whole dangling `DESIGN-2 (...)` clause from the ADR's `### Known Issues` pointer bullet.
3. Verify the checker passes after changes.

### Method

- Locate line 362 in the ADR where the DESIGN-2 known issue is referenced.
- Delete only the `DESIGN-2 (...)` clause portion, preserving the rest of the bullet.

### Details

Current state:
- Line 362: `- **Known Issue**: DESIGN-2 — chunks_fts is derived from chunks, and direct INSERT/UPDATE is prohibited. However, no test guarantees that there is no path in application code that manipulates chunks_fts directly.`

If DESIGN-2 is confirmed stale, remove the entire bullet point or just the DESIGN-2 clause depending on whether other IDs share the same bullet.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Re-adding the dangling clause is straightforward if DESIGN-2 was incorrectly classified as stale. Document the reason for re-addition in a comment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-009-rag-ft5-text-separation.md | Checker validation | `uv run python tools/check_known_deviation_sync.py` | No `[WARNING]` for DESIGN-2 |

## Completion criteria

- Dangling DESIGN-2 clause removed from the ADR's `### Known Issues` section.
- `uv run python tools/check_known_deviation_sync.py` reports no `[WARNING]` for DESIGN-2.

## Out of scope

- Adding canonical entries for still-tracked IDs (covered by Row 1).
- Adding `**Status**: ...` field to `EVENTBUS-001` in `eventbus_01_system-overview.md` (covered by another row).
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate git history for DESIGN-2 | Pending | — | — | |
| 2 | Remove dangling clause for DESIGN-2 | Pending | — | — | |
| 3 | Validate with check_known_deviation_sync.py | Pending | — | — | |

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
- **Source issue**: issues/20261003-080956_kd003_dangling_and_unparsed_known_issue_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-150043_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-164558
- **Related target files**: docs/10_adr/ADR-009-rag-ft5-text-separation.md
