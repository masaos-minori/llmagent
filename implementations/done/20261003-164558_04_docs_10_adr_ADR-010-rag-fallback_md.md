## Goal

Remove dangling clause for DESIGN-1 from `ADR-010-rag-fallback.md`, so `check_known_deviation_sync.py` reports no warning for this ID (REQ-001, REQ-002).

## Scope

- Remove the dangling `DESIGN-1` clause from the ADR's `### Known Issues` pointer bullet.
- Preserve surrounding text and other references in the same bullet.

## Assumptions

- DESIGN-1 can be classified as stale/legacy based on git history of `governance_03` and related closing plans.
- Removing a dangling clause from an ADR's `### Known Issues` section does not affect the ADR's decision or invariant.

## Design decisions

- Only remove the specific `ID (...)` clause; preserve surrounding text and other references in the same bullet.
- Never hide IDs behind full-width punctuation or reformat them to evade `_ID_LOOKAHEAD_RE`.

## Alternatives considered

- Add a canonical entry for DESIGN-1 in `governance_03` — rejected pending git history confirmation that it is stale.
- Leave the dangling clause and update the checker — rejected because the checker correctly identifies the problem.

## Implementation

### Target file

`docs/10_adr/ADR-010-rag-fallback.md`

### Procedure

1. Confirm DESIGN-1 is stale via git history investigation (same as Row 1).
2. Delete the whole dangling `DESIGN-1 (...)` clause from the ADR's `### Known Issues` pointer bullet.
3. Verify the checker passes after changes.

### Method

- Locate line 342 in the ADR where the DESIGN-1 known issue is referenced.
- Delete only the `DESIGN-1 (...)` clause portion, preserving the rest of the bullet.

### Details

Current state:
- Line 342: `- **Known Issue**: DESIGN-1 — The corpus difference between the external RAG and the local RAG is not documented. Because result consistency is not guaranteed, users may get unexpected results.`

If DESIGN-1 is confirmed stale, remove the entire bullet point or just the DESIGN-1 clause depending on whether other IDs share the same bullet.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Re-adding the dangling clause is straightforward if DESIGN-1 was incorrectly classified as stale. Document the reason for re-addition in a comment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-010-rag-fallback.md | Checker validation | `uv run python tools/check_known_deviation_sync.py` | No `[WARNING]` for DESIGN-1 |

## Completion criteria

- Dangling DESIGN-1 clause removed from the ADR's `### Known Issues` section.
- `uv run python tools/check_known_deviation_sync.py` reports no `[WARNING]` for DESIGN-1.

## Out of scope

- Adding canonical entries for still-tracked IDs (covered by Row 1).
- Adding `**Status**: ...` field to `EVENTBUS-001` in `eventbus_01_system-overview.md` (covered by another row).
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate git history for DESIGN-1 | Pending | — | — | |
| 2 | Remove dangling clause for DESIGN-1 | Pending | — | — | |
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
- **Related target files**: docs/10_adr/ADR-010-rag-fallback.md
