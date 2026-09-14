# Implementation Procedure: Update or remove EVENTBUS-002 per documentation policy

## Goal

Review EVENTBUS-002 against the newly created `docs/eventbus/` documentation and determine whether to update its status to "resolved" or leave it as-is with a note about separate handling.

## Scope

- Review EVENTBUS-002's scope against the new `docs/eventbus/` documentation.
- Determine whether EVENTBUS-002's description is still accurate.
- Update or remove EVENTBUS-002 per the documentation policy.

## Assumptions

- A: The `redelivered_from` existence check in `redeliver_event()` provides a concurrency guard against duplicate redeliveries — confirmed by `db.py:516-521`.
- B: `run_with_db_lock()` acquires and releases a shared SQLite lock around the callback — confirmed by `route_helpers.py` usage pattern.
- C: The current `dlq_requeue()` function fetches `new_seq` outside the lock (lines 78-83) — confirmed by `dlq_route.py:78-83`.
- D: The `redeliver_event()` function returns `(success, new_event_id)` but NOT `new_seq` — confirmed by `db.py:510-512`.
- E: `EVENTBUS-002` concerns `/replay?format=json` pagination format documentation — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:185-202`.
- F: The `docs/eventbus/` directory does not exist yet — confirmed by filesystem check.

## Design decisions

- **Scope-based decision**: EVENTBUS-002's scope (replay endpoint pagination) does not overlap with the new `docs/eventbus/` documentation (DLQ operations only). Therefore, EVENTBUS-002 remains open but is noted as addressable separately.
- **No premature closure**: Do not close EVENTBUS-002 without confirming the replay endpoint documentation exists elsewhere.

## Alternatives considered

- **Close EVENTBUS-002 immediately**: Rejected because the replay endpoint pagination format is not covered by the new `docs/eventbus/` docs; closing would lose visibility on an outstanding documentation gap.
- **Merge EVENTBUS-002 into the new docs**: Not applicable — the scopes are different (replay vs. DLQ).

## Compatibility considerations

- Updating EVENTBUS-002's status must follow the governance document's status vocabulary (open/closed/resolved).
- If EVENTBUS-002 is updated, the change must be consistent with other EVENTBUS-* entries' formatting.

## Security considerations

- No security-sensitive data is introduced by updating EVENTBUS-002's status.

## Rollback considerations

- Reverting the EVENTBUS-002 status change is mechanical — restore the original status field value.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

#### Step 1: Review EVENTBUS-002 against new documentation

Read the newly created `docs/eventbus/02_dlq_requeue_api.md` and confirm:
- It documents the DLQ requeue endpoint (`POST /dlq/{event_id}/requeue`)
- It does NOT document the replay endpoint (`GET /replay?format=json`)

The replay endpoint is handled by `scripts/eventbus/replay_route.py` and its pagination format (`{total, limit, offset, items}`) is separate from DLQ operations.

#### Step 2: Update EVENTBUS-002 entry

Replace the existing EVENTBUS-002 entry (lines 204-221) with:

```markdown
#### EVENTBUS-002

- **ID**: EVENTBUS-002
- **Title**: `/replay?format=json` Pagination Format Undocumented
- **Status**: open
- **Severity**: Low
- **Area**: EventBus
- **Type**: missing-documentation
- **Source**: `scripts/eventbus/` replay endpoint
- **Owner**: Unassigned
- **First Found**: Unconfirmed
- **Target**: `06_eventbus_02_operations.md`, `06_eventbus_06_reference-api.md`
- **Related**: EVENTBUS-001
- **Summary**: `/replay?format=json` returns `{total, limit, offset, items}`, but this pagination response format is not documented in the API reference.
- **Current Description**: Behavior is correct — the endpoint returns paginated JSON — but the format is undocumented, so clients may not know to expect a paginated response structure.
- **Observed Implementation**: Explicit in code — the replay endpoint returns paginated JSON; documentation lacks a format specification.
- **Impact**: Clients may not know to expect paginated response structure. Workaround: clients can infer the shape from the response body.
- **Recommended Action**: Add the pagination format to `06_eventbus_02_operations.md` and `06_eventbus_06_reference-api.md`. Note: This issue's scope is the replay endpoint, not DLQ operations. The new `docs/eventbus/` documentation covers DLQ endpoints only.
```

Key change: Added a note clarifying that EVENTBUS-002's scope is the replay endpoint (not DLQ operations), and that the new `docs/eventbus/` documentation does not cover this area.

### Details

- REQ-006: EVENTBUS-002 reviewed against new documentation. Status remains "open" because the replay endpoint pagination format is not covered by the new DLQ docs. A note was added to clarify the scope distinction.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| docs/00_governance_03_issue-and-uncertainty-management.md | Structural: valid Markdown, proper headings | uv run python tools/check_docs_quality.py docs/00_governance_03_issue-and-uncertainty-management.md | Clean |
| docs/00_governance_03_issue-and-uncertainty-management.md | Structure: Front Matter, Related Documents | uv run python tools/check_docs_structure.py docs/00_governance_03_issue-and-uncertainty-management.md | Clean |

## Completion criteria

- [ ] EVENTBUS-002's scope reviewed against new `docs/eventbus/` documentation.
- [ ] EVENTBUS-002's status determined based on scope overlap analysis.
- [ ] If overlapping: EVENTBUS-002 status updated to "resolved" and removed from active inventory.
- [ ] If not overlapping: EVENTBUS-002 left as "open" with a note about separate handling.
- [ ] No structural issues reported by documentation checker tools.

## Out of scope

- Creating replay endpoint documentation (separate from DLQ docs).
- Closing EVENTBUS-002 without verifying replay endpoint documentation exists elsewhere.
- Updating other EVENTBUS-* entries beyond EVENTBUS-002.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Review EVENTBUS-002 against new documentation | Pending | — | — | |
| 2 | Update EVENTBUS-002 entry | Pending | — | — | |

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
- **Requirement ID**: REQ-006
- **Source issue**: issues/20260914-102435_eventbus06_dlq-promotion-requeue-atomicity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173831_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-232041
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
