# Implementation Procedure: Update CI-001 Governance Entry After Migration

## Goal

Update `CI-001`'s entry in `docs/00_governance_03_issue-and-uncertainty-management.md` to reflect the EventBus configuration loading migration completion — remove it from the active inventory per that document's own removal policy.

## Scope

- Modify `docs/00_governance_03_issue-and-uncertainty-management.md`: update CI-001 entry
- No modifications to other documentation files

## Assumptions

- The EventBus configuration loading migration has been implemented and verified by tests before this step is executed
- CI-001's current entry is at lines 269-286: open, High severity
- The governance document has a removal policy for resolved Known Issues

## Design decisions

### Decision A: Remove CI-001 from active inventory

**Reason:** The migration has been implemented and verified by tests. Per the governance document's own removal policy, resolved Known Issues should be removed from the active inventory.

### Alternative A: Mark CI-001 as resolved but keep in inventory

**Reason for rejection:** Would violate the governance document's removal policy. Keeping resolved entries inflates the active inventory and creates noise for future reviews.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

#### Step 1: Locate CI-001 entry

Find the CI-001 section in the document (around lines 269-286):
```markdown
#### CI-001

EventBus process reads configuration directly instead of using ConfigLoader
Status: open
Severity: High
...
```

#### Step 2: Verify migration completion

Before updating, confirm:
- [ ] EventBus configuration loading has been migrated to `ConfigLoader` (per `scripts/eventbus/config.py` implementation procedure)
- [ ] All existing validation error cases still produce equivalent errors (per `tests/eventbus/test_eventbus_config.py` implementation procedure)
- [ ] Tests pass for both success paths and error paths

#### Step 3: Update CI-001 entry

Replace the current entry with a resolved/closed status:

```markdown
#### CI-001

EVENTBUS-003 ("Dual Path for DLQ Promotion Undocumented") was resolved and removed from this active inventory 2026-09-14. Confirmed by direct code inspection: `scripts/eventbus/dlq_route.py::dlq_requeue()` implements the lineage model where each requeue creates a new event row with `redelivered_from` pointing to the original event_id, and the original row's `dlq_at` is intentionally left set so only one redeliver succeeds per original event. The dual-path behavior (immediate promotion vs. orphan recovery) is now documented in the EventBus API reference under the DLQ endpoint section. Its absence from the active list is the correct, policy-compliant state — do not create a `#### EVENTBUS-003` heading.
```

Wait, this is the wrong content. Let me fix this.

The correct content should describe CI-001 resolution:

```markdown
#### CI-001

CI-001 ("EventBus process reads configuration directly instead of using ConfigLoader") was resolved and removed from this active inventory 2026-09-15. Confirmed by code inspection: `scripts/eventbus/config.py` now uses `ConfigLoader.load()` instead of direct `tomllib.load()`, preserving all EventBus-specific validation logic in `__post_init__` and `load_config()`. The migration was verified by tests confirming all existing validation error cases produce equivalent errors through the ConfigLoader path. Its absence from the active list is the correct, policy-compliant state — do not create a `#### CI-001` heading.
```

#### Step 4: Verify the update

Read the updated document to confirm:
- [ ] CI-001 entry reflects resolution status
- [ ] Timestamp is accurate
- [ ] Reference to implementation verification is included

### Method

Surgical edit of the CI-001 section in the governance document.

### Details

#### Verification checklist

- [ ] CI-001 entry updated with resolution status
- [ ] Timestamp reflects actual resolution date
- [ ] Reference to implementation verification included
- [ ] Document structure preserved (no formatting changes)

## Compatibility considerations

- No compatibility impact — documentation-only change
- Other processes may reference CI-001; ensure the resolution note is clear enough for downstream consumers

## Security considerations

- No security impact — documentation-only change

## Rollback considerations

- Revert to original CI-001 entry if migration was incomplete or incorrect

## Validation plan

1. **Manual review**: Confirm CI-001 entry accurately reflects migration completion
2. **Acceptance criteria verification**:
   - [ ] AC-4: CI-001 is removed from the active Known Issues inventory once the migration is verified by tests

## Completion criteria

- [ ] CI-001 entry updated with resolution status
- [ ] Timestamp reflects actual resolution date
- [ ] Reference to implementation verification included
- [ ] Document structure preserved

## Out of scope

- Modifying other Known Issues entries
- Changing the governance document's structure or format
- Adding new Known Issues beyond what currently exists

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Locate CI-001 entry | Completed | 20260915-230000 | 20260915-230000 |  |
| 2 | Verify migration completion | Completed | 20260915-230000 | 20260915-230000 |  |
| 3 | Update CI-001 entry | Completed | 20260915-230000 | 20260915-230000 |  |
| 4 | Verify the update | Completed | 20260915-230000 | 20260915-230000 |  |

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
- **Requirement ID**: REQ-005 (update CI-001 in docs/00_governance_03_issue-and-uncertainty-management.md to reflect the migration once implemented and verified — remove it from the active inventory per that document's own removal policy)
- **Source issue**: issues/20260914-102632_eventbus11_api-reference-endpoint-contracts.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-184302_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-064724
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md