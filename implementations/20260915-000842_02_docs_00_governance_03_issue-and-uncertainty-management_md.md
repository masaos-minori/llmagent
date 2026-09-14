# Implementation Procedure: Reconcile Governance Doc Entries Against Current State

## Goal

Update `docs/00_governance_03_issue-and-uncertainty-management.md` to reconcile the active issue inventory against current implementation reality, specifically addressing:
- CI-001 still listed as "open" despite being marked "Resolved" in ADR-002
- Confirming EVENTBUS-008 and CI-005 removals are correctly documented

## Scope

- Modify only `docs/00_governance_03_issue-and-uncertainty-management.md`
- Update CI-001 status from "open" to "resolved" with reference to ADR-002 resolution
- Verify all other active entries remain accurate

## Assumptions

- CI-001 resolution (2026-08-25) documented in ADR-002 is valid and complete
- No new issues have emerged since the last review cycle
- The governance doc's removal notes for EVENTBUS-008 and CI-005 are accurate

## Design decisions

- Update CI-001 status field only; preserve the existing entry structure
- Add cross-reference to ADR-002 CI-001 entry in the governance doc
- Do not remove CI-001 entirely — it serves as historical audit trail

## Alternatives considered

### Alternative A: Remove CI-001 entirely from governance doc

**Reason for rejection:** CI-001 documents an important architectural deviation that operators need visibility into. Removing it would lose audit trail. The ADR-002 Known Deviation section preserves the same information.

### Alternative B: Move CI-001 to a "Historical Resolutions" section

**Reason for rejected:** The governance doc does not currently have a separate historical section. Adding one would be scope creep beyond reconciliation.

## Implementation

### Target file

`docs/00_governance_03_issue-and-uncertainty-management.md`

### Procedure

1. Read CI-001 entry (lines 288-305) and verify accuracy against current implementation
2. Compare CI-001 status with ADR-002 Known Deviation CI-001 entry (lines 363-375)
3. Update CI-001 status from "open" to "resolved" with cross-reference to ADR-002
4. Verify EVENTBUS-008 removal note (line 284-286) is accurate
5. Verify CI-005 removal note (line 332-334) is accurate
6. Run `tools/check_known_deviation_sync.py --file docs/00_governance_03_issue-and-uncertainty-management.md` to validate consistency

### Method

Direct file modification with targeted edits.

### Details

#### Step 1: Verify CI-001 entry

Current CI-001 entry (lines 288-305):
```markdown
#### CI-001

- **ID**: CI-001
- **Title**: EventBus process reads configuration directly instead of using ConfigLoader
- **Status**: open
- **Severity**: High
- **Area**: EventBus
- **Type**: document-code-mismatch
- **Source**: `scripts/eventbus/config.py`; `scripts/shared/config_loader.py`
- **Owner**: Unassigned
- **First Found**: 2026-08-22
- **Target**: `02_config_isolation_02_01_config-loader-design.md`
- **Related**: ADR-002
- **Summary**: ADR-002 requires that all processes load configuration via ConfigLoader to ensure process-level config isolation. EventBus reads its own TOML configuration directly without going through ConfigLoader, violating this invariant.
- **Current Description**: EventBus's `config.py` loads TOML files directly using `tomllib.load()` or similar, bypassing ConfigLoader entirely.
- **Observed Implementation**: `scripts/eventbus/config.py` opens TOML files and parses them independently; `scripts/shared/config_loader.py` is never imported or used by the EventBus module.
- **Impact**: EventBus operates with a configuration loading path that differs from other processes, potentially leading to inconsistent config handling across the system.
- **Recommended Action**: Refactor EventBus configuration loading to use ConfigLoader, ensuring consistent config access across all processes.
```

Verify:
- Status: "open" — needs update to "resolved"
- Recommended Action: "Refactor EventBus configuration loading to use ConfigLoader" — stale, resolution was via local invariant instead
- Owner: "Unassigned" — may need assignment

#### Step 2: Compare with ADR-002 CI-001 entry

ADR-002 CI-001 entry (lines 363-375) shows:
- Status: "Resovled (2026-08-25)"
- Recommended Action describes the actual resolution mechanism
- Owner: "TBD"

The governance doc CI-001 entry is stale — it shows "open" status while ADR-002 marks it as resolved.

#### Step 3: Update CI-001 entry

Change:
```markdown
- **Status**: open
```
to:
```markdown
- **Status**: resolved
```

And update Recommended Action:
```markdown
- **Recommended Action**: Resolved via local invariant: load_config()'s docstring states callers must pass get_config_path()'s return value, and a regression test in tests/eventbus/test_eventbus_config.py locks both call sites in app.py to that invariant. See ADR-002 CI-001 Known Deviation for details.
```

#### Step 4: Verify EVENTBUS-008 removal note

Line 284-286 confirms:
- EVENTBUS-008 was resolved 2026-09-14
- Removed from active inventory per policy
- Code inspection confirms auth middleware exists
- This is correct — no action needed

#### Step 5: Verify CI-005 removal note

Line 332-334 confirms:
- CI-005 was resolved and removed 2026-09-14
- ConfigLoader.load_all() strict=True default ensures fail-closed behavior
- This is correct — no action needed

#### Step 6: Validate consistency

Run:
```bash
python tools/check_known_deviation_sync.py --file docs/00_governance_03_issue-and-uncertainty-management.md
```

## Compatibility considerations

- Existing consumers of this governance doc rely on the active issue list for operational awareness
- Updating CI-001 status changes the perceived risk profile of the EventBus subsystem
- Operators should be aware that the local invariant resolution is not a full architectural fix

## Security considerations

- CI-001 represents a known security gap (EventBus can potentially access configs outside its scope)
- The local invariant resolution mitigates but does not fully eliminate the risk
- Marking CI-001 as "resolved" may reduce operational vigilance — this should be communicated

## Rollback considerations

- Changes are documentation-only; no code rollback needed
- If CI-001 resolution is later found insufficient, revert the Status field to "open"

## Validation plan

1. Manual review of CI-001 entry against current implementation
2. Confirm EventBus config.py still uses tomllib (no regression back to ConfigLoader)
3. Confirm regression test in `tests/eventbus/test_eventbus_config.py` still passes
4. Cross-check CI-001 status with ADR-002 Known Deviation entry
5. Run `tools/check_known_deviation_sync.py` to validate consistency

## Completion criteria

- [ ] CI-001 status updated to "resolved" in governance doc
- [ ] CI-001 Recommended Action updated to reflect actual resolution mechanism
- [ ] Cross-reference to ADR-002 CI-001 entry added
- [ ] EVENTBUS-008 removal note verified as accurate
- [ ] CI-005 removal note verified as accurate
- [ ] Consistency validation passes

## Out of scope

- Modifying CI-001 Title, Severity, Area, Type fields
- Adding new active issues discovered during verification
- Changing EVENTBUS-008 or CI-005 removal notes
- Updating other governance documents
- Implementing the architectural fix for CI-001

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify CI-001 entry accuracy | Pending | — | — | |
| 2 | Compare CI-001 with ADR-002 Known Deviation | Pending | — | — | |
| 3 | Update CI-001 status and Recommended Action | Pending | — | — | |
| 4 | Verify EVENTBUS-008 removal note | Pending | — | — | |
| 5 | Verify CI-005 removal note | Pending | — | — | |
| 6 | Run consistency validation | Pending | — | — | |

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
- **Requirement ID**: REQ-002 (config isolation enforcement)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-000842
- **Related target files**: docs/00_governance_03_issue-and-uncertainty-management.md
