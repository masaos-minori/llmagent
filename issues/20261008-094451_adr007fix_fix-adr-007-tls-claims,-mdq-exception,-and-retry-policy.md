# Fix ADR-007 TLS claims, mdq exception, and retry policy

## Priority
High

## Summary
Correct ADR-007 so it stops presenting TLS and separate-host deployment as benefits, records the mdq-mcp authentication exception and the rag-pipeline-mcp authentication gap, and states the real retry targets.

## Background
Source: local investigation notes (memo2.md, ADR-007 section; review findings H10, H04, H03, M15).

## Problem
- Rationale 2 and Consequences list TLS and separate-host placement as benefits, but TLS is not implemented and exposure beyond localhost is unsupported.
- mdq-mcp intentionally disables HTTP authentication, which the ADR does not record.
- rag-pipeline-mcp does not attach the Bearer authentication middleware, which is unrecorded (to be registered as MCP-005).
- Retry Policy omits that transport-level request errors other than timeouts are retried.

## Reason for Change
- Security-relevant claims in an Accepted ADR must match the implementation; INV-09 is currently stated as universal.
- Decision content changes, so an approval record is required.

## Implementation Intent
- Apply the revised Decision items 9 and 10, Rationale 2 and 3, Consequences, Invariants INV-09 and INV-10, a new Exceptions section for mdq-mcp, the revised Retry Policy, Known Deviations (MCP-005), and the Completion Checklist change from memo2.md.

## Target Files or Areas
- `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`

## Required Changes
- Apply every ADR-007 replacement listed in memo2.md.
- Add the Exceptions section stating mdq-mcp's security boundary (fail-closed allowed_dirs authorization, with a pointer to mcp_05_05).
- Record a new Approval Record in the same change.

## Constraints
- governance_01 ADR Change Protocol applies.
- MCP-005 must be registered before the ADR cites it.
- No concrete config values or line numbers.

## Acceptance Criteria
- ADR-007 no longer lists TLS or separate-host placement as an achieved benefit.
- The mdq exception and MCP-005 are recorded; Retry Policy matches the transport behavior documented elsewhere.
- Doc checkers pass.

## Testing Expectations
Run the doc checkers listed in `routing.md`, including Known Deviation sync and ADR structure checks. No code change.

## Documentation Impact
Documentation only: ADR-007 (Decision Details, Rationale, Consequences, Invariants, Exceptions, Retry Policy, Known Deviations, Completion Checklist, Approval Record).

## Out of Scope
- Adding authentication to rag-pipeline-mcp (see the ragauth01 issue).
- Implementing TLS.

## Dependencies
- Depends on the kiupd01 issue (MCP-005 registration).
- Related: `issues/20261007-153933_ragauth01_add-rag-http-delegation-authentication-and-fail-closed-responses.md`.

## Unresolved Questions
- N/A: none recorded in memo2.md for this ADR. Facts about mdq-mcp and the retry targets come from the cited documents and should be re-checked against the current docs when editing.

## AI Implementation Instruction
Edit only the listed sections. Verify the mdq and retry claims against mcp_05_05 and the transport document before writing them. Run the doc checkers before finishing.

## Traceability
- **Workflow phase**: issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20261008-094451
- **Related target files**: `docs/10_adr/ADR-007-http-mcp-adoption-and-stdio-non-support.md`
