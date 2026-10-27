## Goal

Add the request-error cause variant to the documented `[Retry exhausted]` message template in
`docs/91_security/security_01_architecture-and-trust-boundaries.md` so the operator-facing
template stays complete after the cause part is added (REQ-005; AC-5).

## Scope

- The "Operator-facing examples" code block (current L265-267): the single template line
  `[Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> after <attempts> attempts`
  gains the optional `last_error=` cause segment.
- No other line or section of the file changes.

## Assumptions

- The template renders the status-variant today; the change records both optional parts in the
  fixed order rather than adding a second example block, matching the single-message contract
  implemented by `20261028-010601_01`.
- High-churn file (28 commits/30d per the plan's Affected areas): rebase immediately before
  editing and re-locate the template line by its literal text, not by line number.

## Design decisions

- One template line with bracket-free optional segments annotated in a trailing comment line inside
  the code block, instead of two example blocks: keeps a single canonical shape operators can
  pattern-match.

## Alternatives considered

- Adding a second fenced example block for the request-error variant: rejected — two blocks invite
  drift between them; the parts are optional segments of one message, not two message shapes (plan
  Design, uniform exhaustion surface).

## Implementation

### Target file

`docs/91_security/security_01_architecture-and-trust-boundaries.md`

### Procedure

1. Locate the "Operator-facing examples" section (current L263-267) and replace the fenced line
   (current L266):
   ```
   [Retry exhausted] tool=<tool_name> status=<last retryable HTTP status> after <attempts> attempts
   ```
   with:
   ```
   [Retry exhausted] tool=<tool_name> [status=<last retryable HTTP status>] [last_error=<error class>: <error message>] after <attempts> attempts
   ```
   where the bracketed segments denote optional parts — `status=` appears when a retryable HTTP
   status was seen, `last_error=` when a non-timeout `httpx.RequestError` was retried — and parts
   keep this order.

### Method

Single-line replacement inside an existing fenced code block.

### Details

- If surrounding prose in the section explains the example lines, confirm no adjacent sentence
  restates the old status-only shape; current audit shows the section lists examples only
  (the `[FATAL]` example at L269 is unrelated).
- Keep the line inside the same fenced block boundaries (L265/L267) so the doc structure checks
  still parse it.

## Compatibility considerations

- Implement in the same change set as `20261028-010601_01` and `20261028-010601_03` — the three
  documents describe one message contract and must land together (REQ-005).
- High churn: rebase immediately before implementing (plan Risks mitigation); the edit is one line
  so conflict handling is trivial.
- No `docs/00_index.md` task-scope conflict: the plan's Documentation Impact scopes this file to
  the message-template line it already contains; the 22_mcp domain check covers `mcp_03_03`.

## Security considerations

- The documented template continues to show no raw response bodies, secrets, or headers; the cause
  segment shows class name + connection message only.

## Rollback considerations

- Revert this line together with the code revert (`20261028-010601_01` Rollback) and the
  `20261028-010601_03` bullet revert; all three are one contract description.

## Validation plan

- `rules/toolchain.md` documentation consistency check (91_security domain) — template includes
  the request-error cause variant (plan Validation plan).
- Cross-check the template against the message assembly in `20261028-010601_01` step 2 and the
  assertions in `20261028-010601_02` step 1.

## Completion criteria

- The template line shows `tool=`, optional `status=`, optional `last_error=`, and the attempt
  suffix in the implemented order (AC-5).
- 91_security documentation consistency check passes.

## Out of Scope

- All other security-doc content (EventBus auth section, failure-mode tables) — untouched.
- The 22_mcp retry bullet — covered by `20261028-010601_03`.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-10-28 | — | Rebase first: high-churn file |
| 2 | Add or update tests per Validation plan | In Progress | 2026-10-28 | — | N/A: documentation file |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-10-28 | — | Docs consistency check |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | In Progress | 2026-10-28 | — | This document is the docs procedure |

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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20261027-001424_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261027-103707_mcpinv003_discarded-transporterror-httptransport-call.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-010601
- **Related target files**: docs/91_security/security_01_architecture-and-trust-boundaries.md
