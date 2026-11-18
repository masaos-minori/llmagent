## Goal

Keep the security policy mapping consistent with the approved posture and state the Agent-side versus
server-side control split (REQ-004, REQ-009, REQ-010).

## Scope
**Release unit**: boundary-and-adr-record

## Assumptions
- `docs/91_security/security_02_high-risk-tool-common-policy.md:119-124` defers the approval-to-tier
  mapping to `docs/22_mcp/mcp_05_03_fail-open-fail-closed-and-risk-tiers.md` (row 25); the deferral stays.
- The ADR-012 split (client-side approval, server-side git enforcement) is the authority text
  (`docs/10_adr/adr_02_03_012_mcp-git-server-side-write-enforcement.md:43`, INV-04 at `:133`).

## Design decisions
- Do not restate the tier mapping here: link to the registered canonical source, and state only which
  control lives on which side of the process boundary.

## Alternatives considered
N/A: documentation-only; REQ-010 forbids a second canonical source for the mapping claim.

## Implementation
### Target file
`docs/91_security/security_02_high-risk-tool-common-policy.md`
### Procedure
1. At `:119-124`, confirm the deferral still points at the row 25 document after that document changes.
2. Add one short subsection naming the Agent-side controls (risk classification, approval gate, allowed
   root, allowlist) and the server-side controls (refspec, protected branch, no forced update), citing
   ADR-012 and ADR-014 INV-03.
### Method
Two localized edits; no restructuring.
### Details
N/A: nothing beyond the deferral check and the split statement is not inferable from REQ-009/REQ-010.

## Compatibility considerations
Must remain consistent with rows 25, 27, 28 as they land in the same release unit.

## Security considerations
Wording must not imply the Agent duplicates or replaces server-side enforcement.

## Rollback considerations
N/A: revert the commit.

## Validation plan
- `uv run python tools/check_docs_quality.py`, `uv run python tools/check_docs_consistency.py --domain agent`.

## Completion criteria
The document states the Agent/server split consistent with ADR-012/ADR-014 and defers the tier mapping to
its registered canonical source (AC-009, AC-010).

## Out of Scope
ADR text (rows 27/28), the tier mapping table (row 25).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the deferral and add the control-split subsection | Pending | — | — | Phase 5 |
| 3 | Run the documentation checkers (`routing.md` Tools) | Pending | — | — | |

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
- **Requirement ID**: `REQ-004` (approved posture), `REQ-009` (boundary record), `REQ-010` (canonical source)
- **Source issue**: `issues/20261117-123003_adrchk003_agent-approval-policy.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261118-224457_adrchk003_agent-approval-policy.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261118-233456
- **Related target files**: `docs/91_security/security_02_high-risk-tool-common-policy.md`
