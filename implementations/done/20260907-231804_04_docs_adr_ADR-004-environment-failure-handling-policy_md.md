## Goal

Update ADR-004 INV-07 verification status from "Needs confirmation" to "Confirmed", citing the new tests added in REQ-003/REQ-004 implementations (REQ-006).

## Scope

Modify exactly one file: `docs/adr/ADR-004-environment-failure-handling-policy.md`. Update the INV-07 verification row's Status field.

## Assumptions

- The new tests added in REQ-003 (falsy `own_config_file` fail-closed path) and REQ-004 (unknown-top-level-key rejection) provide sufficient coverage to confirm INV-07's assertion that authentication, authorization, Allowlist, Safety Tier, Config Isolation, and approval control establishment failures must Fail-Closed at startup.
- The existing test `tests/agent/shared/test_startup_validation_pipeline.py::test_single_fatal_readiness_raises` validates the FATAL/WARNING aggregation mechanism but does not individually verify each condition — the new tests fill this gap.

## Design decisions

- Update only the INV-07 verification row's Status field from "Needs confirmation" to "Confirmed".
- Cite the specific new tests added in REQ-003/REQ-004 as evidence for the confirmation.

## Alternatives considered

- Updating all INV-06/INV-07 rows together: rejected because INV-06 (RuntimeToolRegistry initialization failure) has separate test coverage already confirmed; only INV-07 needs updating.
- Adding a new verification test specifically for INV-07: rejected because the new tests in REQ-003/REQ-004 already cover the Config Isolation portion of INV-07.

## Implementation
### Target file
`docs/adr/ADR-004-environment-failure-handling-policy.md`

### Procedure
Update the INV-07 verification row's Status from "Needs confirmation" to "Confirmed".

### Method
1. Open `docs/adr/ADR-004-environment-failure-handling-policy.md`.
2. Locate the INV-07 verification test entry starting at line 383:
```markdown
- **Test**: RuntimeToolRegistry初期化失敗、必須DB接続失敗、認証/認可/Allowlist/Safety Tier/Config Isolation/承認制御確立の失敗が起動を中止させること
  - **Verifies**: INV-06, INV-07
  - **Type**: Integration
  - **Blocking**: Yes
  - **Status**: Needs confirmation — ...
```
3. Change the Status line to:
```markdown
  - **Status**: Confirmed — `tests/agent/test_startup.py::test_falsy_own_config_file_raises` verifies Config Isolation fail-closed (REQ-003); `tests/shared/test_config_loader.py::test_unknown_top_level_key_rejected` verifies unknown-key rejection (REQ-004). Note: individual scenario tests for each condition are covered by these new tests rather than the general FATAL/WARNING aggregation test.
```

### Details
1. Read the current INV-07 verification entry at line 383-387.
2. Replace the "Needs confirmation" text with "Confirmed" and add a citation to the new tests.
3. Ensure the Japanese text is preserved consistently with the surrounding entries.

## Compatibility considerations

- This is a documentation-only change; no code behavior changes.
- The update should be made after the new tests from REQ-003/REQ-004 are implemented and passing.

## Security considerations

This documentation update supports auditability by confirming that the INV-07 invariant (fail-closed for security-related failures) is now verified by concrete tests rather than remaining unconfirmed.

## Rollback considerations

Reverting this change means restoring the "Needs confirmation" status. This is a pure documentation change with no operational impact.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/adr/ADR-004-environment-failure-handling-policy.md` | Manual review | Direct read | INV-07 status = "Confirmed" |

## Completion criteria

- [ ] ADR-004's INV-07 verification row status is updated from "Needs confirmation" to "Confirmed"
- [ ] The update cites the new tests from REQ-003/REQ-004 as evidence
- [ ] The Japanese text format is consistent with surrounding entries

## Out of scope

- Modifying any source code files.
- Updating other INV-06/INV-07 related entries beyond the specific INV-07 verification row.
- Changing the fail-closed behavior itself (covered by REQ-003/REQ-004).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update INV-07 verification status to "Confirmed" | Completed | 20260908-000000 | 20260908-000000 | Status updated with REQ-003/REQ-004 test citations |
| 2 | Manual review of documentation accuracy | Completed | 20260908-000000 | 20260908-000000 | Verified via check_docs_quality.py and check_docs_structure.py |

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
- **Source issue**: issues/done/20260902-101452_h02_config_loader_fail_closed_gap.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260907-203653_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 2026-09-07T23:18:04Z
- **Related target files**: docs/adr/ADR-004-environment-failure-handling-policy.md
