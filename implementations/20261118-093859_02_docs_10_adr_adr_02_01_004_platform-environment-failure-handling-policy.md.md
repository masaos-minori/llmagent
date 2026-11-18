## Goal
Give every ADR-004 Exception an approval reference or NC ID, list the registered deviations, and show the pending amendments in the pending-amendment form (REQ-002, REQ-008).

## Scope
**Release unit**: N/A: not part of a release unit
- `## Exceptions`, `## Known Deviations`, and the `### Approval Record` bullets.
- Phase 1 steps run first; the Phase 3 steps run after the ledger exists.

## Assumptions
- The Known Issue IDs are those the procedure for the issue-management governance document adds (expected `MCP-001` for the overlay-only fail-open and `MCP-002` for the post-open warning-only exception); read them from the live file.
- The ledger ID prefix `AAL-` and the ledger location (a new part of `docs/00_governance/governance_03_issue-and-uncertainty-management.md`) are the Source plan's proposed defaults (UNK-01); a different maintainer decision changes the cited IDs only.
- Decision Group 10 is the amendment the first `Current Decision Approval` bullet excludes; its ledger ID is AAL-002 and the INV-14 bullet's is AAL-003.

## Design decisions
- The approved bullet keeps its Group 10 exclusion (dropping it would imply Group 10 is approved) and points to a new `(pending)` bullet that carries the amendment.
- No rationale is written: the ADR already states one for each exception; only the approval reference is added.

## Alternatives considered
N/A: the form and the registration route are fixed by the governance change.

## Implementation
### Target file
`docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
### Procedure
1. `## Exceptions`: in the overlay-only fail-open and post-open warning-only bullets replace `Maintainer approval record: written by a maintainer; not fabricated here.` with a pointer to its Known Issue ID; add to the subprocess spawn-failure bullet that it falls under the task-level approval recorded in `### Approval Record`; cite NC-001 in the Group 1 `path_denylist` exception sentence and keep the inline marker.
2. `## Known Deviations`: replace `Not applicable` with one top-level bullet per Known Issue ID, each starting with the ID.
3. (After the ledger exists) in `### Approval Record` add a `Current Decision Approval (pending)` bullet for the Group 10 amendment citing AAL-002, change the approved bullet's `Pending maintainer statement` wording into a pointer to it, and add AAL-003 to the INV-14 bullet.
### Method
Edit existing lines in place; do not write a rationale or an approval statement.
### Details
- The two 2026-11-11 exceptions are the only ones needing a Known Issue (git history of the exception texts).
- The inline `PENDING (Needs confirmation)` marker stays until the maintainer supplies the rationale (NC-001 Required Action).

## Compatibility considerations
N/A: Exceptions text keeps its meaning; Known Deviations moves from `Not applicable` to registered IDs.

## Security considerations
N/A: documentation-only change; the exceptions are registered, not approved or widened.

## Rollback considerations
N/A: revert the commit

## Validation plan
- `uv run python tools/check_adr_structure.py`, `uv run python tools/check_adr_authority.py`, `uv run python tools/check_adr_invariant_matrix.py`, `uv run python tools/check_adr_preservation.py` (its Approval-section reports are reviewed and justified, not suppressed)
- `uv run python tools/check_known_deviation_sync.py`, `uv run python tools/check_needs_confirmation_inventory.py`, `uv run python tools/check_canonical_source_registry.py`
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_structure.py`, `uv run python tools/check_docs_content_policy.py`, `uv run python tools/check_docs_japanese.py`

## Completion criteria
- Each Exception has an approval reference or an NC ID; Known Deviations lists the Known Issue IDs.
- Both pending bullets cite a ledger ID and the Group 10 amendment is a pending bullet.
- The `Status` line is still `Accepted`.

## Out of Scope
- Writing the `path_denylist` rationale or any approval text.
- Deciding the RAG-related exception substance (another issue).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Edit Exceptions and Known Deviations (Phase 1, REQ-002) | Pending | — | — | Needs the Known Issue IDs of procedure 01 |
| 2 | Confirm the ledger exists, then restate Group 10 as a pending bullet and add AAL-002 and AAL-003 (REQ-008) | Pending | — | — | Stop if the ledger is absent |
| 3 | Run the checkers listed in Validation plan | Pending | — | — |  |

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
- **Requirement ID**: `REQ-002`: register the ADR-004 Exceptions; `REQ-008`: apply the pending form
- **Source issue**: issues/20261117-123011_adrchk011_adr-approval-governance.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261118-092611_adrchk011_adr-approval-governance.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-093859
- **Related target files**: `docs/10_adr/adr_02_01_004_platform-environment-failure-handling-policy.md`
