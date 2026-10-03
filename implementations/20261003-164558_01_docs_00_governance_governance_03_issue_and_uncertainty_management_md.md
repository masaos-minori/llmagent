## Goal

Add canonical `#### <ID>` entries with parseable `**Status**: ...` fields to `governance_03` for Known Issue IDs that are still tracked/valid, resolving dangling references flagged by `check_known_deviation_sync.py` (REQ-001, REQ-002).

## Scope

- Add `#### <ID>` entries to `governance_03` for IDs confirmed as still tracked/valid during Step 1 investigation.
- Each entry must include a parseable `**Status**: ...` field matching the checker's regex (`^#{3,4} ([A-Z]+-\d+)(?::|\s*$)`).

## Assumptions

- The Known Issue IDs flagged as dangling can be classified as either "still tracked/valid" or "stale/legacy" based on git history of `governance_03` and related closing plans.
- Adding a `#### <ID>` entry to `governance_03` is sufficient to resolve the dangling reference; no additional cross-references need updating.

## Design decisions

- Follow the existing format exactly in `governance_03`; use the checker's own regex as the source of truth for what constitutes a valid canonical header.
- For IDs that have dedicated overview sections (e.g., `EVENTBUS-001` in `eventbus_01_system-overview.md`), keep the dual-entry pattern rather than consolidating — this preserves the existing documentation structure.

## Alternatives considered

- Consolidate all Known Issue tracking into a single location per ID — rejected because the existing dual-entry pattern (canonical + overview section) is already established for some IDs.
- Remove the `#### <ID>` requirement from the checker — rejected because it would mask unresolved dangling references.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Investigate git history of `governance_03` to determine which of the 9 flagged IDs are still tracked/valid vs. stale/legacy.
2. For each still-tracked ID, add a `#### <ID>: <title>` heading followed by a `**Status**: ...` field and a brief description.
3. Verify the checker passes after changes.

### Method

- Run `git log --oneline --diff-filter=M -- docs/00_governance/governance_03_issue-and-uncertainty-management.md` to identify commits that closed each Known Issue.
- Cross-check against related closing plans in `plans/done/` for context.
- Classify each ID:
  - Still tracked/valid → add canonical entry
  - Stale/legacy → skip (handled by removing dangling clauses from ADRs)

### Details

The following IDs require investigation (UNK-01):

| ID | Current State | Action |
|---|---|---|
| EVENTBUS-001 | Has overview section but no canonical entry | Add canonical entry with `**Status**: Open` |
| EVENTBUS-003 | DLQ dual promotion path incompletely documented | Determine if still open via git history |
| EVENTBUS-004 | Dead code `promote_to_dlq()` exists | Determine if still open via git history |
| EVENTBUS-009 | `nack_event` lacks idempotency guard | Determine if still open via git history |
| EVENTBUS-010 | `since_seq=0` ambiguity | Determine if still open via git history |
| INV-07 | At-Least-Once Delivery baseline | Check if resolved by duplicate detection |
| DESIGN-1 | Corpus difference undocumented | Determine if still open via git history |
| DESIGN-2 | No test guarantees no direct `chunks_fts` manipulation | Determine if still open via git history |
| EVENTBUS-008 | Resolved 2026-09-14 | Skip — already resolved |

For each ID added, follow this format:

```markdown
#### <ID>: <Title>

**Severity**: <High/Medium/Low>
**Status**: <Open/Resolved>
**Description**: <Brief description>
```

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Removing a `#### <ID>` entry after adding it would re-introduce the dangling reference. If an ID was incorrectly classified as "still tracked," revert the addition and leave the reference as-is until proper resolution.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Checker validation | `uv run python tools/check_known_deviation_sync.py` | No `[WARNING]` for any of the 9 flagged IDs |

## Completion criteria

- All still-tracked IDs have `#### <ID>` entries with parseable `**Status**: ...` fields in `governance_03`.
- `uv run python tools/check_known_deviation_sync.py` reports no `[WARNING]` for the IDs covered by this document.

## Out of scope

- Removing dangling clauses from ADRs (covered by other rows).
- Adding `**Status**: ...` field to `EVENTBUS-001` in `eventbus_01_system-overview.md` (covered by another row).
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Investigate git history for each flagged ID | Pending | — | — | |
| 2 | Add canonical entries for still-tracked IDs | Pending | — | — | |
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
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
