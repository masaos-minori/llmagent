## Goal

Update the confirmed-deviations sentence of the ADR document guide so it lists only the deviations that remain, or states that none remain (`REQ-006`: guide sentence).

## Scope

- Edit the single sentence under `## Known Deviations` in the target file.

## Assumptions

- After rows 01 to 04, no Known Issue targets an ADR, so the guide states that none remain. If Plan Phase 1 kept any entry, list the remaining IDs and their ADRs instead.
- `check_known_deviation_sync.py` is run after this row, as the last of the five.
- Plan overlap check: no other Frozen Plan targets this file.

## Design decisions

- Keep the pointer to `governance_03` Part 1 and the rule that each affected ADR cites its deviations, and replace only the ID list with the state "none remain".

## Alternatives considered

N/A: single-sentence docs edit.

## Implementation
### Target file

`docs/10_adr/adr_00_document-guide.md`

### Procedure

1. Locate the sentence (`rg -n "Confirmed deviations are tracked" <target>`).
2. If no entry remains, rewrite it as: `Confirmed deviations are tracked in `docs/00_governance/governance_03_issue-and-uncertainty-management.md` Part 1 and cited in each affected ADR's `Known Deviations`. No confirmed deviation remains.`
3. If an entry remains, keep the sentence and list only the remaining IDs with their ADRs.

### Method

One exact-string edit.

### Details

- Do not add a count or a date.

## Compatibility considerations

N/A: documentation only.

## Security considerations

N/A: no secret is involved.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_known_deviation_sync.py` (final run after all five rows).
- `check_docs_quality.py`, `check_docs_structure.py` on this file, `check_docs_content_policy.py --strict`, `check_docs_japanese.py`.

## Completion criteria

- The sentence lists no removed ID and states that none remain (or lists exactly the remaining ones).
- `check_known_deviation_sync.py` and `check_issue_inventory_conformance.py` report no finding.

## Out of Scope

- The ledger and the ADR files (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rewrite the confirmed-deviations sentence | Completed | 20261027-121448 | 20261027-121507 | Changed: docs/10_adr/adr_00_document-guide.md (confirmed-deviations sentence: no deviation remains). Stale detector clean. |
| 2 | Run the documentation checkers and the final sync check | Completed | 20261027-121507 | 20261027-121507 | Pass: docs_quality, docs_structure, content_policy --strict, japanese, adr_structure, issue_inventory_conformance, needs_confirmation_inventory. Final check_known_deviation_sync.py after all five rows: No issues found (EVENTBUS-023 warning cleared). |

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
- **Requirement ID**: `REQ-006` (guide sentence)
- **Source issue**: issues/20261027-102048_govrev006_eventbus-ledger-stale-entries.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103437_govrev006_eventbus-ledger-stale-entries.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261027-111029
- **Related target files**: docs/10_adr/adr_00_document-guide.md