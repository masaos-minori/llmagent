## Goal
Register the unapproved ADR-004 Exceptions as Known Issues (REQ-002) and define the ADR approval ledger with one pending entry per inventory item (REQ-004).

## Scope
**Release unit**: N/A: not part of a release unit
- Part 1: two Known Issue entries (no decision needed).
- New ledger part after Part 4 and before `## Resolution Rules` (needs the maintainer decision).

## Assumptions
- UNK-04 is resolved: the overlay-only fail-open and the post-open warning-only exceptions were added 2026-11-11, after the task-level approvals of 2026-10-13 and 2026-11-10.
- The spawn-failure exception (added 2026-10-13) is treated as covered and gets no Known Issue; the `path_denylist` exception keeps NC-001.
- The ledger ID prefix `AAL-` and the ledger location (a new part of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`) are the Source plan's proposed defaults (UNK-01); a different maintainer decision changes the cited IDs only.
- The Part 1 ID-prefix convention lists `MCP-*`; both entries are `MCP` area, so the IDs are the next unused numbers of that group (expected `MCP-001`, `MCP-002`; check the live file) and sit before the `SHARED-*` group.

## Design decisions
- Known Issue, not NC: `tools/check_known_deviation_sync.py` parses only Part 1 IDs in Known Deviations bullets (Part 2 `NC-` headings are excluded at the `## Part 2` boundary).
- The ledger part sits after the Part 2 boundary and its ID prefix is outside the Known Issue prefix list, so the sync checker does not read ledger IDs as Known Issue IDs.

## Alternatives considered
A new governance document for the ledger was rejected (adds a path and index entries); an NC entry per exception was rejected (not accepted in Known Deviations).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`
### Procedure
1. Part 1 (Phase 1, no decision): add two Known Issue entries with all 17 fields of the Entry Template, Status open, Area MCP, Type missing-documentation, Target the ADR-004 path, Owner Repository owner, First Found the ADR approval governance re-verification. Source cites the ADR-004 `## Exceptions` bullet; Observed Implementation cites `scripts/mcp_servers/dispatch.py` and `scripts/shared/mcp_dedup.py` as the ADR text does (verify both before citing).
2. Gate: Confirm that the maintainer decision this document needs (D1 to D4 and UNK-01 to UNK-03 of the Source plan) is recorded as a maintainer comment on the Source plan; stop and ask when it is not. Write no approval text.
3. Ledger part (Phase 2): insert `## Part 5: ADR Approval Ledger` after the Part 4 Active Items and before `## Resolution Rules` with Purpose, Entry Fields (ID, ADR, Decision, Approver, Date, Scope), ID format (`AAL-NNN`, three digits), Citation Format, and Active Items.
4. One `#### AAL-NNN` entry per inventory item, Approver and Date `Not recorded`, Scope naming the ADR text the pending bullet covers. No entry for a past approval.
### Method
Edit the document in place with the heading style of Part 1 to Part 4. Do not edit the Part 2 NC entries or the CSC-001 entry.
### Details
- Ledger ID assignment (ADR number order, then bullet order in the file): AAL-001 ADR-001 INV-02; AAL-002 ADR-004 Decision Group 10; AAL-003 ADR-004 INV-14; AAL-004 and AAL-005 ADR-005; AAL-006 to AAL-009 ADR-006; AAL-010 and AAL-011 ADR-008; AAL-012 ADR-009; AAL-013 ADR-010 withdrawal; AAL-014 and AAL-015 ADR-012; AAL-016 ADR-014; AAL-017 ADR-015; AAL-018 ADR-016.
- Each entry's Decision field restates the pending bullet in one clause; read it from the live ADR.

## Compatibility considerations
N/A: additive governance text; existing entries and the Part 2 boundary are untouched.

## Security considerations
N/A: documentation-only change; no approval text and no past-approval entry is written.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`
- If `check_docs_structure.py` reports a file-size finding, stop and report a Plan Gap.

## Completion criteria
- Both Known Issue entries exist and `tools/check_known_deviation_sync.py` reports no ERROR.
- The ledger part defines location, fields, ID format, and citation format, with one pending entry per inventory item and none for a past approval.

## Out of Scope
- Correcting the CSC-001 Validation evidence path (UNK-06).
- Editing ADR files, `docs/00_governance/governance_01_documentation-policy.md`, or the checker.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add the two Known Issue entries to Part 1 (REQ-002) | Pending | — | — |  |
| 2 | Confirm the maintainer sign-off for the ledger definition | Pending | — | — | Stop and ask if absent |
| 3 | Add the ledger part and the pending entries (REQ-004) | Pending | — | — |  |
| 4 | Run the checkers listed in Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-002`: register the ADR-004 Exceptions; `REQ-004`: define the ADR approval ledger
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
