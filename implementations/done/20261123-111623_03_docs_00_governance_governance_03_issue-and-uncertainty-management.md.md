## Goal

Update the MCP-005 inventory entry so it states that regression tests now exist and only the Invariant decision remains open (REQ-003).

## Scope
**Release unit**: N/A: not part of a release unit

In scope: the Title, Summary, Observed Implementation, Impact, Recommended Action, and Resolution Target fields of the MCP-005 entry. Status stays `open`.

## Assumptions

- Verified in this cycle: the entry's Title, Summary, Observed Implementation, and Impact say there is no dedicated test; its other fields (ID, Status, Severity, Area, Type, Source, Owner, First Found, Target, Related, Current Description) stay as they are.
- The ADR-012 procedure (seq 02) and the test procedure (seq 01) are applied first so the cited class exists.

## Design decisions

- Reword only the statements about tests; the Invariant decision stays pending, so the entry stays open and no approval text is written.

## Alternatives considered

Rejected: removing the entry now (the Invariant decision is not recorded; Resolution Rules keep the Known Issue open until design and implementation agree).

## Implementation
### Target file
`docs/00_governance/governance_03_issue-and-uncertainty-management.md`

### Procedure
1. Title: drop `and has no dedicated test`.
2. Summary: end with the statement that regression tests for the two tools now exist (`TestHeadDestinationProtection` in `tests/mcp_servers/git/test_repository_state.py`) instead of saying no test covers them.
3. Observed Implementation: replace the closing clause about dirty-worktree-only tests with the statement that `TestHeadDestinationProtection` pins the protected HEAD rejection, the allowed cases, and the detached HEAD denial, and that the dirty-worktree reachability tests stay in `tests/mcp_servers/git/test_git_security_compliance.py`.
4. Impact: say the enforcement has no Invariant mandate but a regression now fails a test.
5. Recommended Action: the owner decides whether to add an Invariant (pending amendment through the ADR Approval Ledger, with its index row and citation count handled in a separate Plan) or record it as out of scope; no approval is written here.
6. Resolution Target: maintainer decision recorded in ADR-012 (Invariant plus pending amendment, or explicit out-of-scope statement); drop the clause about matching test coverage.

### Method
Edit each listed field of the MCP-005 entry with the Edit tool; do not touch other entries or Parts.

### Details
- Run the inventory conformance checker: the 17-field Known Issue shape must be unchanged.

## Compatibility considerations

N/A: no behavior change; production code is untouched.

## Security considerations

N/A: documentation or tests only; no approval text, approver, or date is written.

## Rollback considerations

N/A: revert the commit.

## Validation plan

- `uv run python tools/check_issue_inventory_conformance.py`, `check_known_deviation_sync.py`, and `check_needs_confirmation_inventory.py` report no findings.

## Completion criteria

- The entry no longer says there is no test, cites the new class, stays `open`, keeps its 17 fields, and the checkers pass.

## Out of Scope

Other inventory entries, Parts 2 to 5, and any approval text.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261123-112813 | 20261123-112813 | Changed: docs/00_governance/governance_03_issue-and-uncertainty-management.md (MCP-005 entry, status open) |
| 2 | Run the documentation checkers named in `rules/tool-gates.md` for a changed `docs/` file (`uv run python tools/run_validation_gates.py`) | Completed | 20261123-112813 | 20261123-112813 | N/A: documentation-only; inventory conformance, Needs Confirmation, known-deviation sync checkers and gates pass |

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
- **Requirement ID**: `REQ-003` (inventory MCP-005 entry matches the new state)
- **Source issue**: issues/20261123-104601_gov002_git-protected-head-tests.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261123-110851_gov002_git-protected-head-tests.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261123-111623
- **Related target files**: `docs/00_governance/governance_03_issue-and-uncertainty-management.md`
