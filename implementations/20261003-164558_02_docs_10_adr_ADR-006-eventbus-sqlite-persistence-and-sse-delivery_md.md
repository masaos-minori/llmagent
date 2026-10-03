## Goal

Remove dangling clauses for Known Issue IDs confirmed stale from `ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`, so `check_known_deviation_sync.py` reports no warnings for these IDs (REQ-001, REQ-002).

## Scope

- Remove dangling `EVENTBUS-003`, `EVENTBUS-004`, `EVENTBUS-009`, `EVENTBUS-010`, `INV-07` clauses from the ADR's `### Known Issues` pointer bullets.
- Preserve surrounding text and other references in the same bullet.

## Assumptions

- The Known Issue IDs flagged as dangling can be classified as either "still tracked/valid" or "stale/legacy" based on git history of `governance_03` and related closing plans.
- Removing a dangling clause from an ADR's `### Known Issues` section does not affect the ADR's decision or invariant.

## Design decisions

- Only remove the specific `ID (...)` clause; preserve surrounding text and other references in the same bullet.
- Never hide IDs behind full-width punctuation or reformat them to evade `_ID_LOOKAHEAD_RE`.

## Alternatives considered

- Move the dangling reference to `governance_03` instead of removing — rejected because the ID is stale and should not appear anywhere.
- Leave the dangling clause and update the checker — rejected because the checker correctly identifies the problem.

## Implementation

### Target file

`docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md`

### Procedure

1. Confirm each ID is stale via git history investigation (same as Row 1).
2. Delete the whole dangling `ID (...)` clause from the ADR's `### Known Issues` pointer bullet.
3. Verify the checker passes after changes.

### Method

- For each ID confirmed stale, locate its line in the ADR and delete only the `ID (...)` clause portion.
- Lines affected:
  - Line 368: `EVENTBUS-003` dangling clause
  - Line 374: `EVENTBUS-004` dangling clause
  - Line 392: `EVENTBUS-009` dangling clause
  - Line 399: `EVENTBUS-010` dangling clause
  - Line 225: `INV-07` dangling clause

### Details

Current state of each ID (from investigation):

| ID | Line | Current Text | Action |
|---|---|---|---|
| EVENTBUS-003 | 368 | `- **Known Issue**: EVENTBUS-003 — DLQ dual promotion path...` | Remove if stale |
| EVENTBUS-004 | 374 | `- **Known Issue**: EVENTBUS-004 — Dead code promote_to_dlq()...` | Remove if stale |
| EVENTBUS-009 | 392 | `- **Known Issue**: EVENTBUS-009 — nack_event lacks idempotency...` | Remove if stale |
| EVENTBUS-010 | 399 | `- **Known Issue**: EVENTBUS-010 — since_seq=0 ambiguity...` | Remove if stale |
| INV-07 | 225 | `- INV-07: At-Least-Once Delivery is the baseline...` | Check if resolved by duplicate detection |

Note: INV-07 appears twice in the ADR — once at line 225 (Known Issues) and once at lines 409/419 (invariants/resolved). The line 225 entry may need removal if INV-07 was resolved by the duplicate detection mechanism described at line 419.

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Re-adding the dangling clause is straightforward if an ID was incorrectly classified as stale. Document the reason for re-addition in a comment.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md | Checker validation | `uv run python tools/check_known_deviation_sync.py` | No `[WARNING]` for EVENTBUS-003, EVENTBUS-004, EVENTBUS-009, EVENTBUS-010, INV-07 |

## Completion criteria

- All stale ID clauses removed from the ADR's `### Known Issues` section.
- `uv run python tools/check_known_deviation_sync.py` reports no `[WARNING]` for the IDs covered by this document.

## Out of scope

- Adding canonical entries for still-tracked IDs (covered by Row 1).
- Adding `**Status**: ...` field to `EVENTBUS-001` in `eventbus_01_system-overview.md` (covered by another row).
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate git history for each flagged ID | Pending | — | — | |
| 2 | Remove dangling clauses for stale IDs | Pending | — | — | |
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
- **Related target files**: docs/10_adr/ADR-006-eventbus-sqlite-persistence-and-sse-delivery.md
