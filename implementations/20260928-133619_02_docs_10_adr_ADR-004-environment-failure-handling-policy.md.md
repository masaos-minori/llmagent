## Goal

Update `docs/10_adr/ADR-004-environment-failure-handling-policy.md` to reflect that INV-14 (undefined criticality → startup must not continue) now has automated test coverage, marking its status resolved (REQ-001 acceptance criterion).

## Scope

Edits three locations in ADR-004 that currently record INV-14 as unverified: the Completion Checklist, the Manual Review list, and the CI-016 Known Deviation. No other file is modified.

## Assumptions

- The REQ-001 test (this plan's Row 1) has landed before these doc edits are applied — the edits assert that automated verification now exists.
- Line numbers below are current as of freeze; re-locate each section with grep if the file has shifted.

## Design decisions

- Update the specific stale claims rather than rewriting ADR-004 wholesale, keeping the change scoped to the INV-14 / unverified story.
- Resolve the CI-016 Known Deviation by recording it as closed (its sole premise was the absence of a test), consistent with how the D1/D2 entries were marked Resolved.

## Alternatives considered

- Leaving CI-016 in place and only checking the Completion Checklist: rejected — would leave a self-contradictory Known Deviation claiming INV-14 is untested while the Checklist says otherwise.
- Rewriting the Invariants section: out of scope — INV-14's definition text is correct and unchanged.

## Implementation

### Target file

`docs/10_adr/ADR-004-environment-failure-handling-policy.md`

### Procedure

1. Locate the three targets with grep: `## Completion Checklist`, the `### Manual Review` subsection, and `### CI-016:` under `## Known Deviations`.
2. **Completion Checklist**: check off the item listing INV-14 as Manual-Review-only and remove INV-14 from its "unverified" parenthetical.
3. **Manual Review**: replace the INV-14 bullet that states it is not enforced in the current implementation with a statement that INV-14 is now verified by the REQ-001 automated test.
4. **CI-016 Known Deviation**: mark the entry Resolved, recording that the missing-test premise no longer holds because the REQ-001 test now covers the `required=True` default. Point the resolution at this plan's Row 1 test.
5. Confirm no remaining text elsewhere describes INV-14 as unenforced/unverified.

### Method

- Completion Checklist (current line ~626): change
  `- [ ] 自動化可能な検証がManual Reviewだけになっていない（INV-01, INV-14はManual Review/未検証のまま；INV-08, INV-09はConfirmed）`
  to
  `- [x] 自動化可能な検証がManual Reviewだけになっていない（INV-01はConfirmed；INV-14はREQ-001の自動テストで確認；INV-08, INV-09はConfirmed）`
- Manual Review (current line ~451): change the INV-14 bullet from "INV-14（未定義の必須性による起動継続禁止）は現行実装で強制されていない（Known Deviations参照）" to "INV-14（未定義の必須性による起動継続禁止）は REQ-001 の単体テストで自動化検証済み（`tests/shared/test_mcp_config.py::TestRequiredDefault`）。"
- CI-016 Known Deviation (current lines ~529-539): set `- **Status**: Resolved (automated test added)` and update `- **Observed Implementation**` / `- **Recommended Action**` to note the REQ-001 test now verifies the `required=True` default (`scripts/shared/mcp_config.py:104`).

### Details

- Preserve the document's Japanese prose style for edited lines.
- Do not touch unrelated Known Deviations (D1-D4) or other Invariants.
- The CI-016 entry also exists in `docs/00_governance/governance_03_issue-and-uncertainty-management.md`; that occurrence is removed by that row, not this one.

## Compatibility considerations

- Documentation-only; no code, config, or schema impact.
- Keep the edit minimal so downstream `docs/10_adr/adr-index.md` cross-references remain valid.

## Security considerations

- N/A: documentation edit; no secret or access-control change.

## Rollback considerations

- Revert is a plain revert of the three edited regions; the ADR returns to its pre-edit state.

## Validation plan

- Read back the three edited regions and confirm INV-14 is described as verified and no stale "unenforced / unverified" language remains.
- Confirm the document still parses as Markdown (no broken heading/table structure).

## Completion criteria

- Completion Checklist line for automated verification is checked and no longer lists INV-14 as unverified.
- Manual Review no longer states INV-14 is unenforced.
- CI-016 Known Deviation is recorded as resolved/closed with a pointer to the REQ-001 test.

## Out of scope

- Adding new Invariants or changing INV-14's definition.
- Other ADRs' completion checklists.
- Removing CI-016 from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` — handled by that row.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260929-142226 | 20260929-142226 |  |
| 2 | Add or update tests per Validation plan | Completed | 20260929-142226 | 20260929-142226 | N/A: documentation-only change. INV-14 is covered by the pre-existing REQ-001 automated test (tests/shared/test_mcp_config.py::TestRequiredDefault); no new test added. |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260929-142226 | 20260929-142226 | N/A: code toolchain (ruff/mypy/etc.) inapplicable to .md. Ran check_docs_quality, check_docs_structure, check_docs_content_policy: no ADR-004 findings (pre-existing >24KB size-limit warning unrelated to this edit). |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260929-142226 | 20260929-142226 |  |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20260927-211347_ci016_add-unit-test-for-adr-004-undefined-criticality-safe-default.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-094534_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-133619
- **Related target files**: docs/10_adr/ADR-004-environment-failure-handling-policy.md