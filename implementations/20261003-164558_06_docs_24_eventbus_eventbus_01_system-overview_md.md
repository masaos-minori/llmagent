## Goal

Add a parseable `**Status**: ...` field to the EVENTBUS-001 entry in `eventbus_01_system-overview.md`, so `check_known_deviation_sync.py` can parse the Status field (REQ-004).

## Scope

- Add `**Status**: Open` (or appropriate value) to the EVENTBUS-001 entry at line 62.
- The format must match the checker's regex: `^#{3,4} ([A-Z]+-\d+)(?::|\s*$)` for the header and `**Status**: <value>` for the status field.

## Assumptions

- EVENTBUS-001 is still open (no closing plan found during git history investigation).
- The existing `### EVENTBUS-001: Offset Monotonicity Not Guaranteed` heading is sufficient; only the `**Status**: ...` field needs to be added.

## Design decisions

- Use `**Status**: Open` since EVENTBUS-001 has no evidence of being resolved.
- Place the `**Status**: ...` field immediately after the heading, before the description paragraph.

## Alternatives considered

- Rename the heading to include the status (e.g., `### EVENTBUS-001: Offset Monotonicity Not Guaranteed [Open]`) — rejected because the checker expects `**Status**: ...` as a separate field, not part of the heading.
- Move the entire EVENTBUS-001 entry to `governance_03` — rejected because the dual-entry pattern is established and the overview section provides useful context.

## Implementation

### Target file

`docs/24_eventbus/eventbus_01_system-overview.md`

### Procedure

1. Confirm EVENTBUS-001 is still open via git history investigation (same as Row 1).
2. Add `**Status**: Open` field after the EVENTBUS-001 heading.
3. Verify the checker passes after changes.

### Method

- After line 62 (`### EVENTBUS-001: Offset Monotonicity Not Guaranteed`), insert a blank line followed by:
  ```markdown
  **Status**: Open
  ```
- Then continue with the existing description text.

### Details

Current state (lines 62-64):
```markdown
### EVENTBUS-001: Offset Monotonicity Not Guaranteed

Offset monotonicity is NOT guaranteed across all scenarios...
```

After modification:
```markdown
### EVENTBUS-001: Offset Monotonicity Not Guaranteed

**Status**: Open

Offset monotonicity is NOT guaranteed across all scenarios...
```

The checker's regex requires a parseable `**Status**: ...` field. Without it, the entry is skipped from cross-check (as noted in the Plan's Background).

## Compatibility considerations

N/A: documentation-only change.

## Security considerations

N/A: documentation-only change.

## Rollback considerations

Removing the `**Status**: ...` field would re-introduce the unparseable Status finding. If the status value was incorrect, update rather than remove.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/24_eventbus/eventbus_01_system-overview.md | Parser validation | Read entry format against checker regex | Parseable `**Status**: ...` field present |

## Completion criteria

- EVENTBUS-001 entry has a parseable `**Status**: ...` field.
- `uv run python tools/check_known_deviation_sync.py` reports no warning for EVENTBUS-001's Status field.

## Out of scope

- Adding canonical entries for still-tracked IDs in `governance_03` (covered by Row 1).
- Removing dangling clauses from ADRs (covered by other rows).
- The two pre-existing `[ERROR]` status-mismatch findings (`CI-001`, `CI-016`).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Confirm EVENTBUS-001 status | Pending | — | — | |
| 2 | Add **Status**: Open field | Pending | — | — | |
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
- **Requirement ID**: REQ-004
- **Source issue**: issues/20261003-080956_kd003_dangling_and_unparsed_known_issue_references.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/done/20261003-150043_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261003-164558
- **Related target files**: docs/24_eventbus/eventbus_01_system-overview.md
