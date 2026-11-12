## Goal

Link ADR-007 to the new ADR-017 and drop its "Detailed implementation of security authentication (handled by a separate ADR)" out-of-scope line, narrowing ADR-007's authentication coverage to a pointer (`REQ-004`, `AC-4`).

## Scope
**Release unit**: N/A: not part of a release unit

## Assumptions
- ADR-017 exists (row 04) and defines the authentication rules ADR-007 now points to.
- ADR-007 Decision 9 (line 77) is the authentication decision; the out-of-scope line is at line 92.
- Editing ADR-007 is a decision-scope reduction (authentication detail moves out), so under `governance_05` it requires a maintainer approval record in the same change.

## Design decisions
- Replace the dangling out-of-scope sentence with a one-line pointer to ADR-017 rather than deleting the authentication topic entirely, preserving the document's structure.
- Add a marked pending maintainer approval record for the decision change, written the way ADR-010 records its withdrawal (never an invented approver/date).

## Alternatives considered
- Deleting the authentication mention from ADR-007 entirely: leaves a gap where a reader expects the decision. Rejected: keep a pointer.

## Implementation
### Target file
`docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`

### Procedure
1. In Decision 9 (line 77), add a link to `adr_02_03_017_mcp-authentication.md`.
2. Replace the out-of-scope line at line 92 ("Detailed implementation of security authentication (handled by a separate ADR)") with a pointer to ADR-017.
3. Add a marked pending maintainer approval record for the decision change in the Approval section.

### Method
- Edit only the two locations above; preserve all other ADR-007 text (verified by `check_adr_preservation.py`: only the intended change reported).

### Details
- The change is a decision-scope reduction, not a wording-only change, so it trips the `governance_05` "ADR edit that changes the decision" row (Required review + Required RACI approval + new approval record in the same change).

### Companion test files
N/A.

## Compatibility considerations
- ADR-017 (row 04) is the destination of this link; the index and document guide (rows 06-07) register ADR-017.

## Security considerations
- The pointer restates that authentication is governed by ADR-017; no token values are introduced.

## Rollback considerations
Revert the commit to restore ADR-007's original out-of-scope line.

## Validation plan
| Target | Strategy | Command | Expected |
|---|---|---|---|
| `adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md` | Preservation | `uv run python tools/check_adr_preservation.py` | Pass (only the intended change) |

## Completion criteria
- ADR-007 links to ADR-017 and no longer contains the "handled by a separate ADR" out-of-scope line.

## Out of Scope
- Any other ADR-007 text change.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Link ADR-017 from Decision 9 and replace the out-of-scope line; add pending approval record | Completed | — | 20261112-041530 | Decision change needs governance_05 approval Decision 9 pointer + Out of Scope pointer + pending Decision Change Approval Record added |
| 2 | Run `check_adr_preservation.py` (`rules/toolchain.md`) | Completed | — | 20261112-041530 | check_adr_preservation: only intended changes (Approval ERROR + Decision WARNING = intended signal per procedure); structure/reference: no issues |

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
- **Requirement ID**: `REQ-004` — ADR-007 links to ADR-017 and drops its non-existent-ADR out-of-scope line.
- **Source issue**: issues/20261109-113023_adrrev011_mcp-audit-auth-adr.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261111-095422_adrrev011_mcp-audit-auth-adr.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261111-231122
- **Related target files**: `docs/10_adr/adr_02_03_007_mcp-http-adoption-and-stdio-non-support.md`