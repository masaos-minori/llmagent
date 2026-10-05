## Goal

Update the EVENTBUS-001 entry in the governance issue inventory to reflect the resolved design decision (Option B): resume position accounts for both high-water mark and lowest unacked event.

## Scope

- Modify `docs/00_governance/governance_03_issue-and-uncertainty-management.md`: update EVENTBUS-001 entry status and resolution.

## Assumptions

- The governance document contains an EVENTBUS-001 entry that needs updating.
- The entry tracks the out-of-order ACK issue and its resolution.

## Design decisions

- Set status to "resolved" for EVENTBUS-001.
- Document the resolution as Option B: resume position accounts for lowest unacked event.
- Note that the fix preserves at-least-once delivery without requiring consumer-side ordering discipline.

## Alternatives considered

- Leave the entry as "open": rejected because the design decision has been made and documented in ADR-006.
- Create a separate governance issue for tracking: rejected because the existing entry already covers the scope.

## Implementation

### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

Update EVENTBUS-001 entry: set status to "resolved", add resolution description.

### Method

1. Locate the EVENTBUS-001 entry in the governance document.
2. Update the status field to "resolved".
3. Add a resolution description documenting Option B choice.

### Details

**Change — Update EVENTBUS-001 entry:**

Before:
```markdown
| EVENTBUS-001 | EventBus out-of-order ACK skips lower-seq events on reconnect | Open | ... |
```

After:
```markdown
| EVENTBUS-001 | EventBus out-of-order ACK skips lower-seq events on reconnect | Resolved | ... |
```

Add resolution description:
```markdown
**Resolution**: Option B — resume position accounts for lowest unacked event.
The fix computes `max(lowest_unacked_seq, stored_offset)` instead of using
`stored_offset` alone, ensuring no unacked event is skipped on reconnect while
still allowing fast-forward past already-acked events.
```

## Compatibility considerations

- Documentation-only change — no behavioral risk.
- The updated entry provides traceability between the governance issue and the implementation fix.

## Security considerations

- No security impact. Documentation update only.

## Rollback considerations

- Revert the status to "open" if the underlying implementation changes.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance/governance_03_issue-and-uncertainty-management.md | Static: format, lint | `uv run ruff format` / `ruff check` on the file | Clean; no new errors |
| Full suite | Regression | `uv run pytest tests/` | No new failures |

## Completion criteria

- [ ] EVENTBUS-001 status changed to "resolved".
- [ ] Resolution description added: Option B — resume position accounts for lowest unacked event.
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.

## Out of scope

- Changes to `delivery_repo.py` (separate procedure document).
- Changes to `subscribe_route.py` (separate procedure document).
- Adding an index on `consumer_delivery(acked_at)` (separate procedure document).
- Creating regression tests (separate procedure document).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | — | — |  |
| 2 | Add or update tests per Validation plan | Completed | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — |  |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | — | — |  |

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
- **Source issue**: issues/20261004-095313_eventbus001_eventbus-out-of-order-ack-skips-lower-seq-events-on-resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-100000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-073241
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md