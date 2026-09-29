## Goal

Remove the NC-021 entry from `docs/00_governance/governance_03_issue-and-uncertainty-management.md` (Part 2, Needs Confirmation Inventory) and update the closing summary line, now that NC-021's remaining open question is resolved by the `test_recover_invalid_format` integration test landing (REQ-003 / AC-3).

## Scope

In-scope: delete the `#### NC-021` entry block and remove `NC-021` from the "No other active Needs Confirmation items..." summary line. Out-of-scope: any change to `scripts/db/recovery.py`, `tests/db/test_db_recovery.py`, or other governance sections; the NC-021 removal is gated on the test having landed and passed (see Rollback considerations).

## Assumptions

The `test_recover_invalid_format` test (implemented by the sibling implementation procedure for `tests/db/test_db_recovery.py`) has landed and passes before this doc change is applied, per the Plan's Implementation steps ordering (documentation removal is ordered after test validation passes).

## Design decisions

Remove only the NC-021 inventory entry and its mention in the summary line — the minimal change that closes the item — leaving every other NC entry and section intact. Keep the document's existing structure, heading style (`#### NC-xxx`), and field layout for the remaining entries.

## Alternatives considered

Leaving a resolved entry in place was rejected: the Plan's purpose (REQ-003) is to remove NC-021 from the Needs Confirmation inventory so it no longer blocks governance tracking. Rewriting surrounding entries was rejected as out of scope (AGENTS.md Global Rule 5).

## Implementation
### Target file

`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure

Two edits, in order:

1. **Delete the NC-021 entry.** Remove the entire `#### NC-021` block, currently at lines 207-223 (verified via `rg`: header at line 207; entry body spans through line 223, ending just before `#### NC-027` at line 224). Delete from the `#### NC-021` heading through the trailing blank line before `#### NC-027`. Do not alter the preceding `#### NC-01x` entry or the following `#### NC-027` entry.
2. **Update the closing summary line.** At line 343, remove `NC-021, ` from the enumeration. Change:

   `...listed here: NC-021, NC-027, NC-028, NC-029, NC-033, NC-034, NC-035, and NC-036.`

   to:

   `...listed here: NC-027, NC-028, NC-029, NC-033, NC-034, NC-035, and NC-036.`

   Verify the current text of line 343 via `rg -n "No other active Needs Confirmation items"` before editing — line numbers may have shifted if the repo changed between plan approval and execution; do not trust the plan's line numbers blindly.

### Method

```bash
# Locate the exact lines before editing (line numbers may have drifted):
rg -n "^#### NC-021$" docs/00_governance/governance_03_issue-and-uncertainty-management.md
rg -n "No other active Needs Confirmation items" docs/00_governance/governance_03_issue-and-uncertainty-management.md
```

Then edit the file: delete the `#### NC-021` block (heading through its final field line, e.g. `- **Blocking**: No` followed by the separating blank line), and remove `NC-021, ` from the summary line. Confirm the remaining entries still read cleanly with no orphaned blank runs or broken `#### NC-xxx` sequence.

### Details

- The NC-021 entry's **Source File** field references a deleted doc (`~~db_07_db_api_and_operations-recovery-and-reference~~ (deleted).md`); this is part of the entry being removed wholesale, so no cross-reference cleanup beyond the entry itself is needed.
- Cross-check that no other section of the document cites NC-021 (e.g. Related Documents, resolution history) before finishing; if another citation exists, remove it too rather than leaving a dangling reference. If such a citation exists in a section outside Part 2, treat it as part of this same doc change (it is within the same file already listed as a target).
- This is a documentation-only change: no `scripts/`/`config/*.toml` file changes, so `deploy/deploy.sh` requires no update.

## Compatibility considerations

N/A: documentation-only change with no code/runtime impact.

## Security considerations

N/A: removing a governance inventory entry; no secrets, credentials, or I/O touched.

## Rollback considerations

Re-add the NC-021 entry (the block deleted in Procedure step 1) and restore `NC-021, ` to the summary line to fully revert. Because this removal is ordered after the test lands and passes (Plan Implementation step 3), premature removal is mitigated by sequencing — if the test does not land, revert this doc change instead of proceeding.

## Validation plan
| Target File/Module | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `docs/00_governance/governance_03_issue-and-uncertainty-management.md` | Documentation consistency | Applicable checker(s) per `routing.md` Tools → "When to run which tool" | Passes; NC-021 absent from Part 2 and from the summary line; no structural/formatting regressions |

## Completion criteria

The `#### NC-021` entry is removed from Part 2 and `NC-021` is dropped from the "No other active Needs Confirmation items..." summary line (line ~343), the remaining NC entries form an unbroken `#### NC-xxx` sequence, and the applicable documentation checkers pass.

## Out of scope

Any change to `scripts/db/recovery.py`, `tests/db/test_db_recovery.py`, other governance sections, or production code. Any additional citation of NC-021 found outside this file would be an additional-target-file discovery requiring a Plan amendment — stop and report `Blocked` in that case.

## Execution Status

**Note (added 20260929):** This document and its own source Plan
(`plans/20260928-152012_plan.md`) were left unexecuted (all steps `Pending`)
since generation on 20260928. That Plan was separately found accidentally
archived without ever having been executed, corrected, and fully re-executed
under a new pass-timestamp
(`implementations/done/20260929-143826_02_....md.md`), which removed the
identical NC-021 entry this document also describes. Re-reading current
source confirms the `#### NC-021` heading is absent from
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`, and
the closing summary line no longer lists `NC-021`. No further action is
needed under this document.

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20260929-180700 | 20260929-180700 | N/A: code/test change is handled by the sibling implementation procedure for `tests/db/test_db_recovery.py` |
| 2 | Add or update tests per Validation plan | Completed | 20260929-180700 | 20260929-180700 | N/A: no tests added by this doc-only change |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20260929-180700 | 20260929-180700 | N/A: no code changed; documentation checkers applied instead, already run under the re-executed pass |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20260929-180700 | 20260929-180700 | Already applied via the re-executed pass — confirmed via direct read: `#### NC-021` heading absent, summary line no longer lists NC-021 |

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
- **Requirement ID**: REQ-003 (remove the NC-021 entry and update the summary line once its open question is resolved)
- **Source issue**: issues/20260927-211353_nc021_add-missing-integration-test-for-unreachable-invalid_format-branch.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260928-152012_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260928-175052
- **Related target files**: docs/00_governance/governance_03_issue-and-uncertainty-management.md
